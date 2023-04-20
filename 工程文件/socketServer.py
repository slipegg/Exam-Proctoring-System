import asyncio
import websockets
import websockets_routes
import datetime
import ssl
import sys
import os
import subprocess
from globalVar import *


def getNowTime():
    return datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


log = open('webrtc.log', 'a+')
log.write('--------' + getNowTime() + ' server start!This is a log file--------\n')
log.flush()
log_lock = threading.Lock()


def writeLog(s):
    log_lock.acquire()
    log.write(s)
    log.flush()
    log_lock.release()


from DBhelper import db_helper

router = websockets_routes.Router()

socket_id_cnt = 0
socket_id_cnt_lock = threading.Lock()

video_lock = threading.Lock()

def convertVideoFile(latest_file_name: str):
    def convert():
        video_lock.acquire()
        try:
            # repair single file and rename file.repair to its original name (file)
            for file in video_list:
                cmd = ffmpeg_pos + ' -i {0} -vcodec copy -acodec copy {1}'.format(file, file + '.repair.webm')
                subprocess.Popen(cmd, shell=True).communicate()  # stderr=subprocess.DEVNULL
                os.remove(file)
                os.rename(file + '.repair.webm', file)

            cmd = ffmpeg_pos + ' -f concat -safe 0 -i {0} -c copy {1}'.format(video_list_file, dst_file_name)
            subprocess.Popen(cmd, shell=True).communicate()  # stderr=subprocess.DEVNULL
            # delete video clips and list file.
            for tmp_file in video_list:
                os.remove(tmp_file)
            os.remove(video_list_file)
        except Exception as e:
            writeLog(getNowTime() + ' convert video error, error is ' +  e.__str__())
        finally:
            video_lock.release()

    if latest_file_name is None:
        return

    # split id of socket and filename
    last_dot_idx = latest_file_name.rfind('.')
    socket_id = latest_file_name[last_dot_idx + 1:]
    # use id to distinguish files to be merged and put them into a list
    pwd = os.path.split(latest_file_name)[0]
    video_list = []
    for name in os.listdir(pwd):
        if name.endswith('.' + socket_id):
            video_list.append(os.path.join(pwd, name).replace('\\', '/'))
    if len(video_list) == 0:
        return
    # name of destination file is the furthest on time.
    video_list.sort()
    farthest_file_name = video_list[0]
    # remove .id
    dst_file_name = farthest_file_name[:farthest_file_name.rfind('.')]

    # write files to be merged to a list file whose name is socket_id.tmp
    video_list_file = os.path.join(pwd, socket_id + '.tmp').replace('\\', '/')
    with open(video_list_file, 'w', encoding='gbk') as f:
        for file in video_list:
            f.write('file \'' + file + '\'\n')

    if sys.platform == 'win32':
        ffmpeg_pos = 'D:/ffmpeg/ffmpeg-n4.4-latest-win64-gpl-shared-4.4/bin/ffmpeg'
    elif sys.platform == 'linux':
        ffmpeg_pos = 'ffmpeg'
    else:
        print('platform error')

    threading.Thread(target=convert).start()


def getVideoFile(client_id, mode, socket_id):
    path_prefix = getRootDir() + 'u' + client_id + '/'
    path_prefix = path_prefix.replace('\\', '/')
    if not os.path.exists(path_prefix):
        os.mkdir(path_prefix)
    info = ['u' + client_id, clients[client_id]['username'], mode, getNowTime()]
    file_name = path_prefix + '-'.join(info) + '.webm.' + str(socket_id)
    return open(file_name, 'wb'), file_name


async def recvOneClip(fd):
    try:
        clip = await fd.recv()
    except websockets.ConnectionClosed:
        clip = None
    return clip


async def monitorConnectHandler(fd, params):
    """
    save information about monitor and client.
    send 'restart' signal to corresponding client.
    :param fd:
    :param params:
    :return:
    """
    if 'monitor_id' not in params or 'client_id' not in params or 'mode' not in params:
        print('monitor request error')
        return

    monitor_id = params['monitor_id']
    client_id = params['client_id']

    # add information of monitor
    monitor_lock.acquire()
    if monitor_id not in monitors:
        monitors[monitor_id] = {}
    monitor = monitors[monitor_id]
    # client to be monitored isn't registered.
    # this connection can be either camera or screen.
    if client_id not in monitor:
        monitor[client_id] = {}
        monitor[client_id]['camera'] = {'fd': None, 'force_close': False}
        monitor[client_id]['screen'] = {'fd': None, 'force_close': False}

    # refuse reconnecting
    if monitor[client_id][params['mode']]['fd'] is not None:
        monitor_lock.release()
        writeLog(getNowTime() + ' monitor(' + monitor_id + ') try to get ' + params['client_id'] + '(' + params[
            'mode'] + ') again, reject it\n')
        return

    writeLog(getNowTime() + ' monitor(id) ' + monitor_id + ' comes to get(id) ' + params['client_id'] + ' ' + params[
        'mode'] + '\n')

    monitor[client_id][params['mode']]['fd'] = fd
    monitor_lock.release()

    client_lock.acquire()
    if params['client_id'] not in clients:
        monitorCloseHandler(monitor_id, client_id, params['mode'])
        client_lock.release()
        return 'client not existed'

    # add information of monitor to corresponding client
    if monitor_id not in clients[client_id]['monitor_id']:
        clients[client_id]['monitor_id'].append(monitor_id)
    client_lock.release()

    await clients[client_id][params['mode']]['fd'].send('restart')

    while True:
        try:
            if monitor[client_id][params['mode']]['force_close']:
                break
            msg = await fd.recv()
        except Exception as e:
            break
    monitorCloseHandler(monitor_id, params['client_id'], params['mode'])
    writeLog('monitor ' + monitor_id + ' close ' + params['client_id'] + ' ' + params['mode'] + '\n')


def monitorCloseHandler(monitor_id, client_id, mode):
    monitor_lock.acquire()
    if monitor_id not in monitors:
        monitor_lock.release()
        return
    monitor = monitors[monitor_id]
    if client_id in monitor:
        monitor[client_id][mode]['fd'] = None
    if monitor[client_id]['camera']['fd'] is None and monitor[client_id]['screen']['fd'] is None:
        del monitor[client_id]
    # doesn't monitor any client
    if not monitor:
        del monitors[monitor_id]
    monitor_lock.release()
    if client_id in clients:
        client_lock.acquire()
        if client_id in clients:
            try:
                clients[client_id]['monitor_id'].remove(monitor_id)
            # monitor has been deleted from client
            except ValueError:
                pass
        client_lock.release()


async def clientCloseHandler(client_id, mode, video_file_name):
    """
    delete client from clients and monitors
    :param mode:
    :param video_file_name:
    :param client_id:
    :return:
    """
    if client_id in clients:
        client = clients[client_id]
        # close socket from monitors
        monitor_lock.acquire()
        for monitor_id in client['monitor_id']:
            monitor = monitors[monitor_id]
            if monitor[client_id][mode]['fd'] is not None:
                monitor[client_id][mode]['force_close'] = True
        monitor_lock.release()
        # delete socket from clients
        client_lock.acquire()
        client[mode]['fd'] = None
        if client['camera']['fd'] is None and client['screen']['fd'] is None:
            del clients[client_id]
        client_lock.release()

        login_user_lock.acquire()
        login_user[client_id][mode] = False
        login_user_lock.release()

        # convert video
        if video_file_name is not None:
            writeLog(getNowTime() + ' convert video of client(id) ' + client_id + ', mode is ' + mode + ' \n')
            convertVideoFile(video_file_name)


async def clientService(client_id, mode):
    """
    save video clips received from client and send them to monitor
    :param client_id:
    :param mode:
    :return:
    """
    video_file = None
    client = clients[client_id]
    global socket_id_cnt
    socket_id_cnt_lock.acquire()
    socket_id = socket_id_cnt
    socket_id_cnt += 1
    socket_id_cnt_lock.release()

    video_file_name = None

    while True:
        clip = await recvOneClip(client[mode]['fd'])
        # socket closed
        if clip is None:
            if video_file is not None:
                video_file.close()
            await clientCloseHandler(client_id, mode, video_file_name)
            return
        elif len(clip) > 0:
            valid_clip = clip[2:]
            flag = clip[0]
            # create video file. clip[0] == 49 (1) is the flag of a new video.
            if flag == 49:
                if video_file is not None:  # video_file is None when first connect.
                    video_file.close()
                video_file, video_file_name = getVideoFile(client_id, mode, socket_id)
            # clip[0] == 48 (0) is the flag of normal data.
            elif flag != 48:
                raise Exception("invalid clip flag")

            client_lock.acquire()
            if clip[1] == 49:
                client[mode]['audio'] = True
            elif clip[1] == 48:
                client[mode]['audio'] = False
            else:
                raise Exception("音频位错误")
            client_lock.release()

            if video_file is None or not video_file.writable():
                raise Exception("video file is None or not writable")
            video_file.write(valid_clip)
            writeLog(getNowTime() + ' write to ' + video_file_name + ' , data length is ' + str(len(valid_clip)) + ' \n')
            # send to monitor
            try:
                if len(client['monitor_id']) > 0:
                    for monitor_id in client['monitor_id']:
                        if monitors[monitor_id][client_id][mode]['fd'] is not None:
                            try:
                                await monitors[monitor_id][client_id][mode]['fd'].send(valid_clip)
                            except websockets.ConnectionClosed:
                                if monitor_id not in monitors:
                                    client['monitor_id'].remove(monitor_id)
                                    writeLog(getNowTime() + ' error: monitor has closed client ' + client_id + '(' + mode + '), but client still sends data')
            # monitor mustn't affect client, so catch all errors even if we don't know the reason
            except Exception as e:
                writeLog('unknown error in clientService():' + e.__str__())
                pass


async def clientConnectHandler(fd, params):
    client_lock.acquire()
    print("params['client_id']:", params['client_id'])
    print("clients:", clients)
    if params['client_id'] not in clients:
        clients[params['client_id']] = {}
        client_info = clients[params['client_id']]
        client_info['screen'] = {}
        client_info['screen']['fd'] = None
        client_info['screen']['audio'] = False
        client_info['camera'] = {}
        client_info['camera']['fd'] = None
        client_info['camera']['audio'] = False
        client_info['monitor_id'] = []
        client_info['username'] = db_helper.getUsername(params['client_id'])

    fd_info = clients[params['client_id']]

    # refuse reconnecting
    if fd_info[params['mode']]['fd'] is not None:
        client_lock.release()
        writeLog(getNowTime() + ' client(' + params['client_id'] + ') try to reconnect ' + params['mode'] + ', reject it\n')
        return

    fd_info[params['mode']]['fd'] = fd
    client_lock.release()

    login_user_lock.acquire()
    login_user[params['client_id']][params['mode']] = True
    login_user_lock.release()

    writeLog(getNowTime() + ' client(id) ' + params['client_id'] + ' comes (' + params['mode'] + ' )\n')
    await clientService(params['client_id'], params['mode'])
    writeLog(getNowTime() + ' client(id) ' + params['client_id'] + ' leaves (' + params['mode'] + ' )\n')


# mode: ['screen', 'camera']

# client
# 1951973 kyf camera
# url:8000/1951973/camera
@router.route('/{client_id}/{mode}')
async def clientSocketHandler(websocket, path):
    await clientConnectHandler(websocket, path.params)


# monitor
# 1001 1951973 camera
# url:8000/1001/1951973/camera
@router.route('/{monitor_id}/{client_id}/{mode}')
async def monitorSocketHandler(websocket: websockets.WebSocketServerProtocol, path):
    await monitorConnectHandler(websocket, path.params)


async def start(ip, port):
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain('CA/secret.pem', 'CA/secret.key')
    async with websockets.serve(lambda websocket, path: router(websocket, path), ip, port, ssl=ssl_context):
        print('socket server running on wss://{0}:{1}/'.format(ip, port))
        await asyncio.Future()
