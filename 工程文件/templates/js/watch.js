'use strict'
const socketUrl = '{{public_ip}}:{{public_socket_port}}'
const queryUrl = '/queryStu'
var a = undefined
// console.log("a == undefined",a == undefined,"typeof(a)",typeof(a),typeof(a)==undefined)
var videosWatching = {}

var data = {
    "stuInfo": [{ name: "kyf", stuNo: "123", online: 1, camera: 1, screen: 1, cameraAudio: 1, screenAudio: 1 },
    { name: "kyf2", stuNo: "456", online: 0, cameraAudio: 1, screenAudio: 1 }]
}
var videoCanvas = $("#videos")[0]

class Video {
    constructor(isAudio, socketURL, name, stuNo, mode) {
        this.id = name + mode
        let title = name + " " + stuNo + " " + mode
        this.isAudio = isAudio
        this.socketService = `wss://${socketURL}`

        //断线重连设置参数
        this.timeConnect = 0

        // this.player = document.createElement("VIDEO");//$("#"+playerName)[0];
        // this.player.disablePictureInPicture;
        //this.player.setAttribute("autoplay")//autoplay playsinline
        //this.player.setAttribute("playsinline")//autoplay playsinline
        //console.log(this.player)
        //videoCanvas.appendChild(this.player)

        //缓存参数
        this.bufDict = {}   //存储尚未添加到sourcebuffer的数据? 格式：cnt，data
        this.count = 0;//添加计数，避免添加和待空闲后添加冲突

        //将blob转换为array的转换器
        this.reader = new FileReader();

        //视频文件
        this.sourceBuffer = null  //mediaSource 自动续借视频数据buffer
        this.mediaSource = new MediaSource();
        //视频文件 内存维护
        this.removeSecound = -100 //sourceBuffer已删除到的秒
        this.beginSecond = 50
        this.flag = 0    //是否要执行remove的flag（append和remove都会触发
        this.cnt = 0    //取出计数

        try {
            this.page = window.open('', title, 'width=400,height=200');
            var html = "<head><title>" + title + "</title></head><body style='background:black'><div style='width:100%;height: 100%; object-fit: fill;margin:auto;'><video muted='muted' controls width='100%' autoplay src='" + window.URL.createObjectURL(this.mediaSource) + "'><ideo></div></body>"
            this.page.document.write(html);
        } catch (e) {
            alert("您的网络状态不好，请隐藏重新查看")
            console.log("!!!!!ERROR new page", e)
        }

        // this.player.src = window.URL.createObjectURL(this.mediaSource);//将播放器的url设置为mediaSource生成的url
        // this.player.controls = true;//是否显示播放控件

        //sourceopen事件是在给video.src赋值（新建page)之后触发
        this.mediaSource.addEventListener("sourceopen", () => {
            var codecMode = this.isAudio == "1" ? "video/webm;codecs=vp8,opus" : "video/webm;codecs=vp8"
            // console.log("this.isAudio", this.isAudio, typeof (this.isAudio), codecMode)
            this.sourceBuffer = this.mediaSource.addSourceBuffer(codecMode);//编码格式要相同
            //由于mediaSource空闲之前不可以添加，所以必须用
            this.sourceBuffer.addEventListener("updateend", this.removeFromSourceBuffer);//绑定添加数据的函
        });
        //sourceBuffer有新数据
        this.reader.onload = (event) => {//将最新的blob转换为array，放入sourceBuffer
            this.sourceBuffer.appendBuffer(event.target.result);
            // if (this.isPlay == 0) {//播放
            //     var promise = this.player.play()
            //         .then((v) => { console.log("then", v) })
            //         .catch((e) => { console.log("catch", e) })
            //     // console.log(promise)
            //     this.isPlay = 1;
            // }
        }


        this.appendToSourceBuffer = () => {
            //this可用
            // console.log("mediaSource.readyState ", this.mediaSource.readyState,
            //     "this.sourceBuffer.updating", this.sourceBuffer.updating,
            // "this.reader.readyState", this.reader.readyState)
            if (
                //this.last_count != this.count &&//注意不能重复添加，用其他的方法也可以
                this.mediaSource.readyState === "open" &&
                this.sourceBuffer &&
                this.sourceBuffer.updating === false &&    //未空闲不得插入新
                this.reader.readyState != 1 //EMPTY 0 LOADING 1 DONE 2
            ) {

                //可以开始插,只插入一
                for (var key in this.bufDict) {
                    this.cnt++
                    console.log("append", this.cnt, this.bufDict[key].size)
                    // this.buffer.push(this.bufDict[key])
                    // console.log('buffer:',this.buffer)
                    this.reader.readAsArrayBuffer(this.bufDict[key]);
                    delete this.bufDict[key]
                    //this.bufDict.remove(key)
                    break
                }

            }
        }
        this.removeFromSourceBuffer = () => {
            //每2次执行1次
            if (this.flag) {
                //console.log("seccond",this.removeSecound)
                if (this.removeSecound > this.beginSecond) {
                    console.log("remove", this.removeSecound)
                    this.sourceBuffer.remove(this.removeSecound, this.removeSecound + 1);
                }
                this.removeSecound++
            }
            this.flag = ~this.flag
        }

        //新建websocket
        try {
            this.socket = new WebSocket(this.socketService);
        } catch (e) {
            alert("您的网络状态不好，请隐藏重新查�?")
            console.log("!!!!!ERROR new websocket", e)
        }

        //含socket的事
        //心跳包发
        setInterval(() => {
            if (this.socket.readyState == WebSocket.OPEN)
                this.socket.send("connecting");
        }, 3000);

        //有视频数据从websocket传来
        this.socket.onmessage = (event) => {
            //暂存数据
            this.bufDict[this.count++] = new Blob([event.data], { type: "video/webm;codecs=vp8,opus" })
            //this.count++
            // console.log("onmessage data",typeof(event.data),event.data.size)
            // this.buffer.push(this.bufDict[this.count-1])
            // console.log('buffer:',this.buffer)
            setTimeout(() => { this.appendToSourceBuffer() }, 3000)

        }

        //检测到socket断开 关page
        this.socket.onclose = () => {
            console.log("websocket断开", videosWatching)

            if (this.page.closed == false) this.page.close()
            //this.player.remove()

            if (this.id in videosWatching) {
                // console.log("delete")
                delete videosWatching[this.id]
            }
            getStuInfo()
            //this.reconnect()
        }

        //检测到page被关则关socket
        setInterval(() => {
            //console.log("page closed", this.page.closed)
            if (this.page.closed == true && this.socket.readyState == WebSocket.OPEN) {
                //此处做关闭后的操
                this.socket.close()
                if (this.id in videosWatching) {
                    // console.log("delete")
                    delete videosWatching[this.id]
                }
                getStuInfo()
            }
        }, 1000)
    }

    stop() {
        //if(videosWatching[this.id]!=undefined)delete videosWatching[this.id]
        if (this.page.closed == false) this.page.close()
        //this.player.remove()
        this.socket.close()
    }

    // // 重连
    // reconnect() {
    //     // var classObj = this
    //     // lockReconnect加锁，防止onclose、onerror两次重连
    //     if (this.limitConnect > 0) {
    //         this.limitConnect--;
    //         this.timeConnect++;
    //         console.log("" + this.timeConnect + "次重");
    //         // 进行重连
    //         setTimeout(()=> {
    //             console.log(this.socketService)
    //             this.socket = new WebSocket(this.socketService);
    //         }, 20000);
    //     } else {
    //         console.log("连接已超");
    //     }
    // };


}

window.onload = getStuInfo

function getStuInfo() {
    try {
        $.get(`${queryUrl}`, function (data, status) {
            paserStuIndo(data);
        });
    } catch (e) {
        console.log("ERROR getStuInfo", e)
    }
}
setInterval(getStuInfo, 3000);

function paserStuIndo(data) {
    //console.log("paser")
    //从json数据中取出学生信息并显示在页面上
    var json = JSON.parse(JSON.stringify(data))
    var students = json.stuInfo
    //找到待操纵的html元素
    //var elem = $('#elem')[0]
    var table = $('#stuInfo')[0]
    //清空旧元
    table.innerHTML = "<tr><td>学生</td><td>状态</td><td>camera操作</td><td>screen操作</td></tr>"
    //table.appendChild(elem)
    //console.log(elem,table)
    /**
    <tr>
        <td>姓名 学号</td>
        <td></td>
        <td><button name="" stuNo="" audio="" mode="camera">查看</button></td>
        <td><button name="" stuNo="" audio="" mode="screen">查看</button></td>
    </tr>
                 */
    //逐个插入新信
    // console.log("---------------------------------")
    // console.log("videosWatching",videosWatching)
    for (var i = 0; i < students.length; i++) {
        // console.log(students[i].name, students[i].cameraAudio, students[i].screenAudio,
        //    "online",students[i].camera,students[i].screen)
        var elem = document.createElement('tr')

        //学生信息
        var student = document.createElement('td')
        student.innerHTML = students[i].name + " " + students[i].stuNo
        elem.appendChild(student)

        //是否在线
        var online = document.createElement('td')
        online.innerHTML = students[i].online ? "yes" : "no"
        elem.appendChild(online)

        //camera 查看
        let buttonCameraTD = document.createElement('td')
        if (students[i].camera) {
            let buttonCamera = document.createElement('button')
            buttonCamera.setAttribute("name", students[i].name)
            buttonCamera.setAttribute("stuNo", students[i].stuNo)
            buttonCamera.setAttribute("audio", students[i].cameraAudio)
            buttonCamera.setAttribute("mode", "camera")
            buttonCamera.setAttribute("onclick", "ckeckVideo(this)")
            if (!students[i].online) {
                buttonCamera.setAttribute("disabled")
            }
            if (students[i].name + "camera" in videosWatching) {
                buttonCamera.innerHTML = "隐藏"
            } else {
                buttonCamera.innerHTML = "查看"
            }
            buttonCameraTD.appendChild(buttonCamera)
        } else {
            buttonCameraTD.innerHTML = "无"
        }

        //screen 查看
        let buttonScreenTD = document.createElement('td')
        if (students[i].screen) {
            let buttonScreen = document.createElement('button')
            buttonScreen.setAttribute("name", students[i].name)
            buttonScreen.setAttribute("stuNo", students[i].stuNo)
            buttonScreen.setAttribute("audio", students[i].screenAudio)
            buttonScreen.setAttribute("mode", "screen")
            buttonScreen.setAttribute("onclick", "ckeckVideo(this)")
            if (!students[i].online) {
                buttonScreen.setAttribute("disabled")
            }
            if (students[i].name + "screen" in videosWatching) {
                buttonScreen.innerHTML = "隐藏"
            } else {
                buttonScreen.innerHTML = "查看"
            }
            buttonScreenTD.appendChild(buttonScreen)
        } else {
            buttonScreenTD.innerHTML = "无"
        }

        elem.appendChild(buttonCameraTD)
        elem.appendChild(buttonScreenTD)

        table.appendChild(elem)
    }
    // console.log("---------------------------------")
}


function ckeckVideo(obj) {
    if (obj.innerHTML == "查看") {

        let name = obj.getAttribute("name")//姓名
        let stuNo = obj.getAttribute("stuNo")//学号
        let audio = obj.getAttribute("audio")//音频
        let mode = obj.getAttribute("mode")//模式
        console.log(`${socketUrl}/{{monitor_id}}/${stuNo}/${mode}`)
        let id = name + mode
        videosWatching[id] = new Video(audio, `${socketUrl}/{{monitor_id}}/${stuNo}/${mode}`, name, stuNo, mode);//wss连接的url
        obj.innerHTML = "隐藏"

    } else {
        let name = obj.getAttribute("name")//姓名
        let mode = obj.getAttribute("mode")//模式
        if (name + mode in videosWatching)
            videosWatching[name + mode].stop()
        //delete videosWatching[name + mode]
        obj.innerHTML = "查看"
        //console.log(camera)
        // camera[choosed].stop()
    }
}
var stopBtn = $("#stopBtn")
var exitBtn = $("#exitBtn")
//断开连接
exitBtn.click(() => {
    window.location.href = "https://{{public_ip}}:{{public_https_port}}/exit"
})
stopBtn.click(() => {
    $.get(`${"/terminate"}`, function (data, status) { alert("结束考试", data) })
    //exitBtn.click()
})
function sleep(time) {
    return new Promise((resolve) => setTimeout(resolve, time));
}
// newPlayer.controls = true;//是否显示播放控件
// var downloadBtn = $("#download")
// downloadBtn.click(function () {
//     function download(buffer,fileName){
//         var blob = new Blob(buffer, { type: 'video/webm' });//下载buffer
//         // var blob = new Blob(screen["c"].sourceBuffer, { type: 'video/webm' });
//         // 根据缓存数据生成url
//         var url = window.URL.createObjectURL(blob);
//         // 创建一个a标签，通过a标签指向url来下
//         var a = document.createElement('a');
//         a.href = url;
//         a.style.display = 'none'; // 不显示a标签
//         a.download = fileName; // 下载的文件名
//         a.click(); // 调用a标签的点击事件进行下
//     }
//     download(screen['c'].buffer,"screenMonitor.webm")
//     // download(camera['c'].buffer,"cameraMonitor.webm")
// })