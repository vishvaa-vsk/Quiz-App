function startTimer(duration, display) {
    var timer = duration, minutes, seconds;
    var counter = setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        display.textContent = minutes + ":" + seconds;

        if (--timer < 0) {
            timer = duration;
            function enable_disable(){
                // not("#sumbitButton")
                $("#Quiz :input").prop("disabled",true);
            };
            enable_disable();
            clearInterval(counter);
            alert("Time Up!")
        }

        if(minutes < 1){
            display.style.color = 'red'
        }
    }, 1000);
}


function progressBar(minutes){
    value = minutes;
    var progress = setInterval(function(){
        --value;
        document.querySelector(".progress-bar").style.width= value+"%";
        if(document.querySelector(".progress-bar").style.width == "10%"){
            document.querySelector(".progress-bar").classList.remove("bg-success");
            document.querySelector(".progress-bar").classList.add("bg-danger");
        }
    },1000);
    if (value <= 0){
        clearInterval(progress);
    }
}

window.onload = function () {
    var fiveMinutes = 60 * 0.5,
    display = document.getElementById('counter');
    startTimer(fiveMinutes, display);
    progressBar(fiveMinutes);
};


var myAudio = document.getElementById("myAudio");