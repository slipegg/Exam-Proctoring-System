import os
import subprocess
import sys
import threading


def convertVideoFile2(latest_file_name:str):
    def convert():
        subprocess.Popen(cmd, shell=True).wait()  # stderr=subprocess.DEVNULL
        with open(video_list_file, 'r', encoding='utf-8') as video_list:
            for tmp_file in video_list.readlines():
                os.remove(os.path.join(tmp_file.replace('\n','').replace('')).replace('\\', '/'))
        os.remove(video_list_file)
        os.rename(tmp_dst_file_name, dst_file_name)

    if latest_file_name is None:
        return
    # split id of socket and filename
    last_dot_idx= latest_file_name.rfind('.')
    socket_id = latest_file_name[last_dot_idx + 1:]
    # use id to distinguish files to be merged and put them into a list
    pwd = os.path.split(latest_file_name)[0]
    video_list = []
    for name in os.listdir(pwd):
        if name.endswith('.' + socket_id):
            video_list.append(os.path.join(pwd, name).replace('\\', '/'))
    if len(video_list) == 0:
        return

    video_list.sort()
    farthest_file_name = video_list[0]
    dst_file_name = farthest_file_name[:farthest_file_name.rfind('.')]
    tmp_dst_file_name = dst_file_name + '.webm'



    video_list_file = os.path.join(pwd, socket_id + '.tmp').replace('\\', '/')
    with open(video_list_file, 'w', encoding='utf-8') as f:
        for file in video_list:
            os.rename(file, file[:file.rfind('.')])
            f.write('file \'' + file[:file.rfind('.')] + '\'\n')


    if sys.platform == 'win32':
        cmd = 'D:/ffmpeg/ffmpeg-n4.4-latest-win64-gpl-shared-4.4/bin/ffmpeg -f concat -safe 0 -i {0} -c copy {1}'.format(video_list_file, tmp_dst_file_name)
    elif sys.platform == 'linux':
        # cmd = 'ffmpeg -i {0} -vcodec copy -acodec copy {1}'.format(video_file_name, dst_file_name)
        cmd = 'ffmpeg -f concat -safe 0 -i {0} -c copy {1}'.format(video_list_file, tmp_dst_file_name)
    else:
        print('platform error')
        return


    print('pwd:', pwd)
    print('video list:', video_list)
    print('dst file:', dst_file_name)
    print('cmd', cmd)

    threading.Thread(target=convert).start()



name = 'E:/computer_network/小组作业/WebRTC远程录屏/src/video/u2/u2-xxx-camera-2022-06-18-14-56-29.webm.2'
convertVideoFile(name)

