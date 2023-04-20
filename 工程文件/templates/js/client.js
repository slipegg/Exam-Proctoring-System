'use strict'

//否 从index.html中取出cookie，用websocket发送（默认第一个包是cookie）剩下的都是数据
//用{{client_id}}
//如果黑客直接建立socket攻击
const Url = "{{public_ip}}:{{public_socket_port}}"
// const Url = "127.0.0.1:8181"
const AUDIO = new Blob([0x01])
const NOAUDIO = new Blob([0x00])
const TRUE = new Blob([0x01])
const FALSE = new Blob([0x00])
const PIC_WIDTH = {{ info['frame']['width'] }}
const PIC_HEIGHT = {{ info['frame']['height'] }}
const FRAME_RATE = {{ info['frame']['rate'] }}
const RECONNECT_MAX = {{ info['reconnect']['try_times'] }}
// console.log("RECONNECT_MAX",RECONNECT_MAX)
//视频码率
const VBPS = {{ info['frame']['videoBitsPerSecond'] }}
//音频码率
const ABPS = {{ info['frame']['audioBitsPerSecond'] }}
//加【0】是dom对象，不加是jquery对象
$("#user").text("用户学号：" + {{ client_id }})
var confirmBtn = $("#confirmBtn")[0];
// var recordBtn = $("#recordBtn")[0];
//var downloadBtn = $("#downloadBtn");
//var restartBtn = $("#restartBtn");
var stopBtn = $("#stopBtn")[0];
// var recnnectBtn = $("#recnnectBtn")[0];
// console.log($("#confirmBtn"), confirmBtn, $("#recordBtn"), recordBtn)
var camera = null
var screen = null
// var recordBtn = $("#recordBtn");
class Video {
    /*
    playerName:html视频播放器名称
    audioBoxName:html音频选择框名称
    socketIP:ip+port
    mode:camera or screen
    */
    constructor(playerName, audioBoxName, socketIP, mode) {
        // console.log("constructor")
        // this.assess = false
        this.isRestart = 0
        this.timeConnect = 0
        //this.isHead = null;
        this.player = $("#" + playerName)[0];
        this.mode = mode;
        this.socketService = `wss://${socketIP}/{{client_id}}/${mode}`   //client_id 由flask传
        this.openSocket()

        this.buffer = []
        // this.fileData =[]
        this.audioInput = $('#' + audioBoxName)[0]
        this.isAudio = AUDIO

        this.socketsFunction()
        this.callForAccess()

        // 开始录制 按钮点击事件
        // recordBtn.addEventListener("mousedown", () => {
        //     if (recordBtn.innerHTML === '开始考试') {
        //         this.record()
        //     } else if (recordBtn.innerHTML === '停止考试') {
        //         this.stopRecord()
        //     }
        // }, false)

        //断线重连
        // recnnectBtn.addEventListener("click", () => {
        //     this.socket.close();
        // })

        //断开连接退出
        // stopBtn.addEventListener("mousedown", () => {
        //     //this.stopRecord();
        //     this.closeSocket()

        //     //window.location.href = "https://{{public_ip}}/exit"
        // }, false)

    }

    socketsFunction() {
        //let classObj = this
        //接收socket信息并触发restart   
        this.socket.onmessage = (event) => {
            // console.log(event.data)
            // console.log('abcd')
            if (event.data == "restart") {
                console.log('restart')
                this.restart()
            } else if (event.data == "exit") {
                console.log("!!!!!!!!!!exit")
                //this.stopBtn.mouseup()
                window.location.href = "https://{{public_ip}}:{{public_https_port}}/exit"
            }
        }
        this.socket.onclose = async () => {
            console.log('服务器已经断开');
            await sleep(3000);
            this.reconnect();
        };
    }
    // 重连
    async reconnect() {
        this.isRestart = 1;
        //停止录制
        this.stopRecord();

        // 进行重连

        this.timeConnect++
        if (RECONNECT_MAX >= 0 && this.timeConnect > RECONNECT_MAX) {
            alert("重连超时，连接断开");
        }
        console.log("第" + this.timeConnect + "次重连");
        // console.log(this.socketService);

        this.openSocket()
        console.log("刚刚new", this.socket.readyState)

        let loop = 1
        while (loop) {
            await sleep(3000);
            console.log("setTimeout 判断", this.socket.readyState)
            if (this.socket.readyState == WebSocket.CONNECTING) {
                ;
            } else if (this.socket.readyState == WebSocket.OPEN) {
                this.record()
                loop = 0
                // clearInterval(interval2);
                // clearInterval(interval);

            } else if (this.socket.readyState == WebSocket.CLOSED
                || this.socket.readyState == WebSocket.CLOSING) {
                // clearInterval(interval2);
                loop = 0
                this.closeSocket()
            } else {
                console.log("!!!!!ERROR WebSocket readyState error", this.socket.readyState)
            }
        }

    }
    callForAccess() {
        // console.log("音频", this.audioInput.checked)
        this.isAudio = this.audioInput.checked ? AUDIO : NOAUDIO
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia
            || !navigator.mediaDevices.getDisplayMedia) {//getDisplayMedia//getUserMedia
            alert('不支采集音视频数据！请检查您的摄像头是否打开（如笔记本的F8快捷键）并重新');
        } else {
            if (this.mode == "camera") {
                // 采集音频数据
                var constrants = {
                    video: {
                        width: PIC_WIDTH,	    // 宽带
                        height: PIC_HEIGHT,     // 高度
                        frameRate: { max: 16, ideal: FRAME_RATE, min: 8 },  // 帧率
                        facingMode: 'enviroment', //  设置为后置摄像头
                    },
                    audio: this.audioInput.checked
                };
                navigator.mediaDevices.getUserMedia(constrants)
                    .then((stream) => {
                        //此处this是class
                        this.mediaStream = stream;
                        this.player.srcObject = stream;
                        this.record()
                        // this.assess = true
                        // setRecordBtn()
                    })
                    .catch(handleError);
            } else if (this.mode == "screen") {
                // 采集音频数据
                var constrants = {
                    video: {
                        width: PIC_WIDTH,	    // 宽带
                        height: PIC_HEIGHT,     // 高度
                        frameRate: { max: 16, ideal: FRAME_RATE },  // 帧率
                    },
                    audio: this.audioInput.checked
                };
                navigator.mediaDevices.getDisplayMedia(constrants)
                    .then((stream) => {
                        //此处this是class
                        this.mediaStream = stream;
                        this.player.srcObject = stream;
                        this.record()
                        // this.assess = true
                        // setRecordBtn()
                    })
                    .catch(handleError);
            }
        }

    }
    //开始录制
    record() {
        console.log("----------record---------------")
        // this.fileData = []
        this.isHead = TRUE
        // var options = { mimeType: 'video/webm;codecs=vp8' };
        var options = { audioBitsPerSecond: ABPS, videoBitsPerSecond: VBPS, mimeType: 'video/webm;codecs=vp8,opus' };

        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            alert('不支持' + options.mimeType);
            return;
        }

        try {
            this.mediaRecoder = new MediaRecorder(this.mediaStream, options);
            console.log("获取成功");
        } catch (e) {
            alert('创建MediaRecorder失败!请检查您的摄像头及录屏设备，重新登录');
            return;
        }
        this.mediaRecoder.ondataavailable = (e) => {
            // console.log(this)
            //console.log("handelData this ",this.testThis)
            if (e && e.data && e.data.size > 0) {
                if (this.isRestart == 1) {
                    if (this.isHead == FALSE) {
                        return
                    } else {
                        this.isRestart = 0
                    }
                }
                // console.log("new data size:" + e.data.size, "ishead", this.isHead == TRUE, "isAudio", this.isAudio == AUDIO)
                //console.log('TRUE',TRUE.size)
                //var MyBlobHead = new Blob([this.isHead],{type:"text/plain"})
                //console.log('TRUEBlob',MyBlobHead.size)
                //合并为二进制数据
                //console.log(e.data.size)
                var MyBlob = new Blob([this.isHead, this.isAudio, e.data], { type: "text/plain" })
                //console.log('MyBlob',MyBlob.size)
                //this.buffer.push(MyBlob);
                // this.buffer.push(this.isHead,e.data)
                if (this.socket.readyState == WebSocket.OPEN) {
                    try {
                        this.socket.send(MyBlob);
                    } catch (e) { console.log("!!!!!ERROR this.socket.send", e) }

                    // for (var item of this.buffer) {
                    //     console.log("send size", item.size)
                    //     this.socket.send(item);
                    //     // this.socket.send(item);
                    // }
                    //this.buffer = []

                }

                // this.fileData.push(e.data)
                // console.log("this.fileData",this.fileData)
                this.isHead = FALSE
            }
        }
        // 开始录制，设置录制时间片 调用handleDataAvailable
        this.mediaRecoder.start(1000);
    }

    //停止录制
    stopRecord() {
        try {
            if (this.mediaRecoder.state != "inactive")
                this.mediaRecoder.stop();
        } catch (e) {
            console.log("!!!!!!!!ERROR stopRecord", e)
        }
    }
    //重新开始录制
    restart() {
        this.isRestart = 1
        this.stopRecord();
        setTimeout(() => {
            this.record();
        }, 1000);
    }

    openSocket() {
        try {
            this.socket = new WebSocket(this.socketService);
            this.socketsFunction()
        } catch (e) {
            console.log("!!!!!!!!!ERROR this.socket = new WebSocket", e)
            console.log("this.socket.readyState", this.socket.readyState)
        }
    }
    //关闭socket
    closeSocket() {
        this.stopRecord();
        try {
            this.socket.close();
        } catch (e) {
            console.log("!!!!!ERROR  this.close", e)
        }
    }
}
// newPlayer.controls = true;//是否显示播放控件

//确认音频
confirmBtn.addEventListener("click", () => {
    // console.log("confirm button click")

    var isCamera = $("#cameraVideo")[0].checked;    //Boolean
    var isScreen = $("#screenVideo")[0].checked;

    if (isCamera) {
        camera = new Video("player", "cameraAudio", Url, "camera");
        // camera.player.requestPictureInPicture();
    } if (isScreen) {
        screen = new Video("player2", "screenAudio", Url, "screen");
        // screen.player.requestPictureInPicture();
    }

    confirmBtn.disabled = true
}, false)

// 开始录制 按钮点击事件（不含socket）onclick>click>on()
// recordBtn.addEventListener("mouseup", () => {
//     // console.log("record btn on")

//     if (recordBtn.innerHTML === '开始考试') {   //text是jquery，innerHTML是DOM
//         recordBtn.innerHTML = '停止考试'
//         console.log('开始考试')
//     } else if (recordBtn.innerHTML === '停止考试') {
//         //修改按钮属性
//         //recordBtn.innerHTML = '开始考试'
//         console.log('停止考试');
//         //stopBtn.click()
//     }
// }, false)

//断线重连（不含socket）    无

//断开连接
stopBtn.addEventListener("click", () => {
    // console.log("stop btn on")
    window.location.href = "https://{{public_ip}}:{{public_https_port}}/exit"
}, false)

// function setRecordBtn() {
//     let flag = 0
//     if (!camera || camera && camera.assess) flag++
//     if (!screen || screen && screen.assess) flag++
//     if (flag == 2){
//         this.record()
//     }
//         //recordBtn.disabled = false   //attr是jquery， setAttribute是dom，但是disabled=false也是disabled

// }
// // 下载按钮点击事件
// downloadBtn.click(function () {
//     function download(buffer,fileName){
//         var blob = new Blob(buffer, { type: 'video/webm' });
//         // 根据缓存数据生成url
//         var url = window.URL.createObjectURL(blob);
//         // 创建一个a标签，通过a标签指向url来下载
//         var a = document.createElement('a');
//         a.href = url;
//         a.style.display = 'none'; // 不显示a标签
//         a.download = fileName; // 下载的文件名
//         a.click(); // 调用a标签的点击事件进行下载
//     }

//     download(camera.fileData,'camera.webm')
//     download(screen.fileData,'screen.webm')
// });
// restartBtn.click(function () {
//     if(camera)camera.restart();
//     screen.restart()
// });

// 采集音频数据失败时调用的方法
function handleError(err) {
    alert(err.name + ':' + err.message);
}
function sleep(time) {
    return new Promise((resolve) => setTimeout(resolve, time));
}