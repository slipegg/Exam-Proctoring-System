#-*-coding:gbk -*-

import sys
from socketServer import start
import asyncio
from flask import Flask, render_template, request, redirect, has_request_context, copy_current_request_context
import os
from globalVar import *
from DBhelper import *
import shutil
from functools import wraps
from concurrent.futures import Future, ThreadPoolExecutor

app = Flask(__name__, template_folder='templates', static_folder='./static')

def run_async(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        call_result = Future()
        def _run():
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(func(*args, **kwargs))
            except Exception as error:
                call_result.set_exception(error)
            else:
                call_result.set_result(result)
            finally:
                loop.close()
        loop_executor = ThreadPoolExecutor(max_workers=10)
        if has_request_context():
            _run = copy_current_request_context(_run)
        loop_future = loop_executor.submit(_run)
        loop_future.result()
        return call_result.result()
    return _wrapper


@app.route('/')
def index():
    server_args = config['server-args']
    return render_template('login.html', public_ip=server_args['public_ip'], public_https_port=server_args['public_https_port'])

@app.route('/exit')
def exit():
    return "已退出，感谢使用！"


@app.route('/user', methods=['POST'])
def user():
    username = request.form.get('user')
    password = request.form.get('pwd')
        
    # verify identification
    user = db_helper.verifyId(username, password)
    if user is None or not user['enable_login']:
        return redirect('/')

    server_args = config['server-args']

    # {'id':, 'username':, 'is_client':, 'enable_login':,}
    if password == user['id']:
        return render_template('modifyPasswd.html',msg="",
        public_ip=server_args['public_ip'], public_https_port=server_args['public_https_port'])

    
    if user['is_client']:

    #     path_prefix = getRootDir() + 'u' + user['id'] + '/'
    #     dst_folder = getRootDir() + 'old/'
    #     if os.path.exists(path_prefix):
    #         for name in os.listdir(path_prefix):
    #             shutil.move(os.path.join(path_prefix, name).replace('\\', '/'),
    #                         os.path.join(dst_folder, name).replace('\\', '/'))

        info = {'frame': {}, 'reconnect':{}}
        info['frame']['width'] = config['frame']['width']
        info['frame']['height'] = config['frame']['height']
        info['frame']['rate'] = config['frame']['rate']
        info['frame']['audioBitsPerSecond'] = config['frame']['audioBitsPerSecond']
        info['frame']['videoBitsPerSecond'] = config['frame']['videoBitsPerSecond']
        info['reconnect']['try_times'] = config['reconnect']['try_times']
        js = render_template('js/client.js', public_ip=server_args['public_ip'], public_socket_port=server_args['public_socket_port'],
                             client_id=user['id'], public_https_port=server_args['public_https_port'], info=info)
        return render_template('client.html', js=js)
    else:
        js = render_template('js/watch.js', public_ip=server_args['public_ip'], public_socket_port=server_args['public_socket_port'],
                             public_https_port=server_args['public_https_port'], monitor_id=user['id'])
        return render_template('watch.html', js=js)


@app.route('/modifyPasswd', methods=['POST'])
def modifyPasswd():
    username = request.form.get('user')
    old_password = request.form.get('old_pwd')
    new_password = request.form.get('new_pwd')
    if db_helper.modifyPasswd(username, old_password, new_password):
        return redirect('/')
    else:
        return render_template('modifyPasswd.html',
        msg="username or password not match!",
        public_ip=server_args['public_ip'], 
        public_https_port=server_args['public_https_port'])



@app.route('/queryStu')
def queryStu():
    # it's required that monitor can see all clients whether or not they are online.
    client_info = {'stuInfo': []}
    for client_id, client in login_user.items():
        client_info['stuInfo'].append({
            'name': client['username'],
            'stuNo': client_id,
            'online': 1 if client_id in clients else 0,
            'camera': 1 if client_id in clients and clients[client_id]['camera']['fd'] is not None else 0,
            'screen': 1 if client_id in clients and clients[client_id]['screen']['fd'] is not None else 0,
            'cameraAudio': 1 if client_id in clients and clients[client_id]['camera']['audio'] else 0,
            'screenAudio': 1 if client_id in clients and clients[client_id]['screen']['audio'] else 0
        })
    return client_info


@app.route('/terminate')
@run_async
async def terminate():
    client_lock.acquire()
    for client in clients.values():
        for mode in ['screen', 'camera']:
            if client[mode]['fd'] is not None:
                await client[mode]['fd'].send('exit')
                print('A'*10)
                print('ntify ', client['username'])
    client_lock.release()
    return 'ok'


def startSocketServer():
    server_args = config['server-args']
    asyncio.run(start(server_args['local_ip'], server_args['local_socket_port']))


def daemonize():
    pid = os.fork()
    if pid:
        sys.exit(0)
    os.umask(0)
    os.setsid()
    sys.stdout.flush()
    sys.stderr.flush()


if __name__ == '__main__':
    server_args = config['server-args']
    if server_args['is_daemon'] == 'True':
        daemonize()
    threading.Thread(target=startSocketServer).start()
    app.run(host=server_args['local_ip'], port=server_args['local_https_port'],
            ssl_context=(server_args['CA_pem'], server_args['CA_key']))
