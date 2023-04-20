#!/bin/bash
#安装ffmpeg
echo '安装ffmpeg中'
yum install -y git
git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg
yum install -y epel-release
yum install -y yasm
cd ffmpeg
./configure
make -j4
make install
echo '安装ffmpeg完成'
ffmpeg -version
cd ..

#安装python相关的库
echo '安装python相关的库中'
cd config 
pip3 install -r ./config/require.txt
echo 'python相关的库安装完成'

#移动相关文件
echo '复制文件到/home/1951108-webRtc中'
CRTDIR=$(pwd)
echo $CRTDIR
cp ./config/webRtc.config ./source/webRtc.config
cp ./config/auto_run_script.sh ./source/auto_run_script.sh
mkdir /home/1951108-webRtc
cp ./source/*  /home/1951108-webRtc/
echo '复制完毕，可在/home/1951108-webRtc中查看'

#配置开机自动运行
echo '配置开机自启动中'
chmod +x /home/1951108-webRtc/auto_run_script.sh
echo /home/1951108-webRtc/auto_run_script.sh >> /etc/rc.d/rc.local
echo '配置开机自启动完成，输入init 6重启后即可自动运行，或者输入python3 /home/1951108-webRtc/mainServer.py自己启动，注意使用到的端口是443-网站访问端口,11000-websockeet先服务器连接的端口，请确保这两个端口开放了'
