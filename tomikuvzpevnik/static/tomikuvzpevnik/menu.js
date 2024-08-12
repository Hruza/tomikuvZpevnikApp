var open = document.getElementById("open_pdf_menu");
open.addEventListener("click", function(event){
    document.getElementById("sidebar").classList.toggle("active");
    document.getElementById("hide").classList.toggle("active");
})

var close = document.getElementById("close_pdf_menu");
close.addEventListener("click", function(event){
    document.getElementById("sidebar").classList.toggle("active");
    document.getElementById("hide").classList.toggle("active");
})

var hide = document.getElementById("hide");
hide.addEventListener("click", function(event){
    document.getElementById("sidebar").classList.toggle("active");
    document.getElementById("hide").classList.toggle("active");
})