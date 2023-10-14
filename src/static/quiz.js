var triggerAudioInput=()=>{
var buttonBox = document.getElementById("addButtonBox");
var audioInput = document.createElement('input');
audioInput.classList.add("form-control")
audioInput.type = "file";
buttonBox.appendChild(audioInput);
}


function startTimer(duration, display) {
    var timer = duration, minutes, seconds;
    setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        display.textContent = minutes + ":" + seconds;

        if (--timer < 0) {
            timer = duration;
        }

        if(minutes < 1){
            display.style.color = 'red'
        }

    }, 1000);
}

window.onload = function () {
    var fiveMinutes = 60 * 10,
        display = document.getElementById('counter');
    startTimer(fiveMinutes, display);
};