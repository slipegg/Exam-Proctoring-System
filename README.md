# Exam-Proctoring-System

本系统是一个基于webRtc的线上考试监考系统，服务器端使用Python实现，客户端分为学生端和监控端，都是网页，主要依靠JavaScript实现。

学生端开始考试后，网页会调用webRtc会通过电脑前置摄像头录制考生及环境，同时还会捕获屏幕视频，以达到监考的效果。

监控端可以在考试过程中随时查看所有考生的任意视频，并通过小窗展示以同时查看多个学生。

视频信息交互通过webSocket实现。学生端将视频流通过webSocket传输给服务器，服务器对其进行存储，如果有监考端发出对某些学生的实时查看需求服务器就会给这些学生对应的学生端发送重新抓获的信令，然后学生端会重新捕获视频流，然后服务器在接收到这些信息的时候会在他们存储的同时将其转发给监控端进行查看。

## 数据流图

数据流主要为视频数据，由client 端发往server，再由server 发往monitor

![image](https://user-images.githubusercontent.com/65942634/233391374-ccc43d83-4bce-4c43-aa21-719f8d341723.png)

## 控制信令关系

本系统主要信令为： 
* 登录信令：由client 或monitor 发往server，信令格式为：
  https://{{public_ip}}:{{public_https_port}}/user 
* 开始考试信令：由client 发往server，信令格式为：
  wss://${socketIP}/{{client_id}}/${mode} 
* 视频信令：由client 发往server，通过全双工的、client 发起的websocket 传送 
* 重新开始信令：由server 发往client，使client 停下重新开始录制以获得新的视频头。信令格式为restart，通过全双工的、client 发起的websocket 传送 
* client 退出考试信令：由client 发往server，信令格式为：
  https://{{public_ip}}:{{public_https_port}}/exit 
* monitor 查询学生在线情况信令：由monitor 发往server，信令格式为：/queryStu 
* monitor 查看视频信令：由monitor 发往server，信令格式为：
  ${socketUrl}/{{monitor_id}}/${stuNo}/${mode} 
* 视频信令：由server 发往monitor，通过全双工的、monitor 发起的websocket 传送 
* monitor 结束考试信令：由monitor 发往server，信令格式为：
  https://{{public_ip}}:{{public_https_port}}/exit

![image](https://user-images.githubusercontent.com/65942634/233391752-936fbd02-1816-4f2c-8ecb-0d38558705e9.png)

## 视频编解码标准

视频采用VP8 的编码模式，清晰度、帧率和码率设置如下 

![image](https://user-images.githubusercontent.com/65942634/233391836-537cf700-1caa-4e6a-a9a3-5900115d9b7d.png)

## 配置文件修改

配置文件webrtc-hkl.conf位于根目录下，可以配置以下信息，还可以添加注释。

![image](https://user-images.githubusercontent.com/65942634/233391929-0bce3cd7-f1ef-4a5e-b5f3-49187c20ab82.png)

## 系统性能

经实际在高程考试课程上的测试，本系统能支持30 人双路视频录制四小时。在设置width=1280；height=720 ；rate = 12 ；audioBitsPerSecond=128000 ；videoBitsPerSecond=500000 的情况下，系统资源占用情况如下：

![全部性能指标](https://user-images.githubusercontent.com/65942634/233392096-8b36fbed-984e-499a-a551-9d34e334ee05.png)
