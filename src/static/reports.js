let deptSelect = document.getElementById('dept');
        let classSelect = document.getElementById("class");
        deptSelect.onchange = function(){
            dept = deptSelect.value;
            let optionHTML = '';
            let sections = ["A","B","C","D"]
            for(let section of sections){
                optionHTML += `<option value="I-${dept}-${section}">${dept}-${section}</option>`;
            }
            classSelect.innerHTML = optionHTML;
        }


window.onload = ()=>{
    let dashButton = document.getElementById('dashButton');
let downloadButton = document.getElementById('downloadButton')
document.getElementById('reportForm').onsubmit = function(){
    dashButton.style.display = "block";
    downloadButton.style.display = "block";
}
}

