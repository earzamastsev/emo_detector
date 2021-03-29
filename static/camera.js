let img = new Image();
let intervalID;
let buffer = [];
let seq = 0;
let iframeElem = document.querySelector("iframe");
const video = document.getElementById('video');
const canvas = document.createElement("canvas");
canvas.width = video.clientWidth;
canvas.height = video.clientHeight;
setEventListeners();


function show() {
    const elem = document.querySelector(".btn-toast-show")
    if (elem.classList.contains('active')) {
            elem.classList.toggle('active');
            elem.textContent = "Show emotion";
            elem.classList.replace('btn-danger', 'btn-info');
            $('.toast').toast('hide');
}
        else {
            elem.textContent = "Hide emotion";
            elem.classList.toggle('active');
            elem.classList.replace('btn-info', 'btn-danger')
            $('.toast').toast('show');
};

};

let stop = function () {
    let stream = video.srcObject;
    let tracks = stream.getTracks();
    for (let i = 0; i < tracks.length; i++) {
        let track = tracks[i];
        track.stop();
    }
    video.srcObject = null;
    clearInterval(intervalID1);
    clearInterval(intervalID2);
}

let start = function () {
        const vendorUrl = window.URL || window.webkitURL;
    if (navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: {width:400, height:315} })
            .then(function (stream) {
                video.srcObject = stream;
            }).catch(function (error) {
                console.log("Something went wrong!");
            });
    }
    const elem = document.querySelector(".btn-toast-show");
    elem.classList.remove('disabled');
    intervalID1 = setInterval(() => {detect()}, 300);
    intervalID2 = setInterval(() => {loadFromBuffer()}, 300);

}

function setEventListeners() {
    const startStopElem = document.querySelector(".start");
    startStopElem.addEventListener("click", (e) => {
    if (e.target.classList.contains('start')) {
        e.target.textContent = "Stop Cam";
        e.target.classList.replace('btn-success', 'btn-danger');
        e.target.classList.remove('start')
        start();
    }
    else {
        e.target.classList.add('start')
        e.target.textContent = "Start Cam";
        e.target.classList.replace('btn-danger', 'btn-success');
        stop();
    }
    })

    const openFullscreenElem = document.querySelector(".open-fullscreen");
    openFullscreenElem.addEventListener("click", (e) => {
         let fullscreenCard = document.querySelector(".fullscreen");
         let base = document.querySelector(".base");
         base.style.visibility='hidden';
         fullscreenCard.style.visibility='visible';
         let tmp = document.querySelector(".fullscreen .card-body");
         iframeElem.classList.add('iframe-fullscreen');
         iframeElem.removeAttribute("width");
         iframeElem.removeAttribute("height");
         tmp.insertAdjacentElement("afterBegin", iframeElem);
         const emoBtnElem = document.querySelector(".btn-toast-show");
         document.querySelector(".fullscreen .card-body .text-center").insertAdjacentElement('beforeEnd', emoBtnElem)
         });


    const closeFullscreenElem = document.querySelector(".close-fullscreen");
    closeFullscreenElem.addEventListener("click", (e) => {
         let fullscreenCard = document.querySelector(".fullscreen");
         const emoBtnElem = document.querySelector(".btn-toast-show");
         let base = document.querySelector(".base");
         fullscreenCard.style.visibility='hidden'
         base.style.visibility='visible';
         let tmp = document.querySelector(".base .card-body");
         iframeElem.classList.remove('iframe-fullscreen');
         iframeElem.setAttribute("width", 400);
         iframeElem.setAttribute("height", 315);
         tmp.insertAdjacentElement("afterBegin", iframeElem);
         document.querySelector(".base .webcam").insertAdjacentElement('beforeEnd', emoBtnElem)
          });

    const getPlotElem = document.querySelector(".get-graph");
    getPlotElem.addEventListener("click", (e) => {
        e.preventDefault();
        let getPlotElem = document.querySelector(".get-graph");
        fetch(getPlotElem.href)
            .then(response => {
            showSpinner();
            return response.text()})
            .then(result => {
                if (result) {
                    hideSpinner();
                }
                $('.show-graph').html(result);
            });
    } );
}

function getSnapshot(videoElem) {
    canvas.getContext('2d').drawImage(videoElem, 0, 0, canvas.width, canvas.height);
    const image = new Image()
    image.src = canvas.toDataURL();
    return image;
    }

function showSnapshot(imgElem) {
    const canvas = document.querySelector('canvas#picture');
    const ctx  = canvas.getContext('2d');
    imgElem.onload = () => {
        ctx.drawImage(imgElem,0,0);
    }
}

let loadFromBuffer = function () {
        if (buffer.length > 2) {
        let canvas = document.querySelector('canvas#picture');
        let bufferCtx  = canvas.getContext('2d');
        let current = buffer.shift();
        const image = new Image();
        image.onload = function() {
            bufferCtx.drawImage(image, 0,0);
            bufferCtx.strokeStyle = "#2ec4b6";
            bufferCtx.lineWidth = 3;
            bufferCtx.fillStyle = "#2ec4b6";
            bufferCtx.strokeRect(current.result.x, current.result.y, current.result.w, current.result.h);
            bufferCtx.font = "bold 22px serif";
            bufferCtx.fillText(current.result.emo, current.result.x, current.result.y-2);
            }
        image.src = URL.createObjectURL(current.blob);
        }
        else {
        console.log('Buffer is empty (<2)...')}
};

async function detect() {
    formData = new FormData();
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
        formData.append("file", blob);
        formData.append("seq", seq);
        fetch('/detect/', {
        "method": "POST",
        "body": formData
    })
        .then(response => response.json())
        .then(result => {
            if (result.status == 'error') {
                console.log('No face detected');
            } else {
                seq += 1;
                buffer.push({"blob":blob, "result":result});
                console.log(result.timer)
                }
        })
    }, "image/jpeg", 0.90);
};

function hideSpinner() {
    document.getElementById('spinner').style.display = 'none';
}
function showSpinner() {
    document.getElementById('spinner').style.display = '';
}
