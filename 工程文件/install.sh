#!/bin/bash
#��װffmpeg
echo '��װffmpeg��'
yum install -y git
git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg
yum install -y epel-release
yum install -y yasm
cd ffmpeg
./configure
make -j4
make install
echo '��װffmpeg���'
ffmpeg -version
cd ..

#��װpython��صĿ�
echo '��װpython��صĿ���'
cd config 
pip3 install -r ./config/require.txt
echo 'python��صĿⰲװ���'

#�ƶ�����ļ�
echo '�����ļ���/home/1951108-webRtc��'
CRTDIR=$(pwd)
echo $CRTDIR
cp ./config/webRtc.config ./source/webRtc.config
cp ./config/auto_run_script.sh ./source/auto_run_script.sh
mkdir /home/1951108-webRtc
cp ./source/*  /home/1951108-webRtc/
echo '������ϣ�����/home/1951108-webRtc�в鿴'

#���ÿ����Զ�����
echo '���ÿ�����������'
chmod +x /home/1951108-webRtc/auto_run_script.sh
echo /home/1951108-webRtc/auto_run_script.sh >> /etc/rc.d/rc.local
echo '���ÿ�����������ɣ�����init 6�����󼴿��Զ����У���������python3 /home/1951108-webRtc/mainServer.py�Լ�������ע��ʹ�õ��Ķ˿���443-��վ���ʶ˿�,11000-websockeet�ȷ��������ӵĶ˿ڣ���ȷ���������˿ڿ�����'
