var open_left = document.getElementById("open_pdf_menu");
open_left.addEventListener("click", function(event){
    document.getElementById("sidebar-left").classList.toggle("active");
    document.getElementById("hide").classList.toggle("active");
})

var close_left = document.getElementById("close_pdf_menu");
close_left.addEventListener("click", function(event){
    document.getElementById("sidebar-left").classList.toggle("active");
    document.getElementById("hide").classList.toggle("active");
})

var hide = document.getElementById("hide");
hide.addEventListener("click", function(event){
    document.getElementById("hide").classList.toggle("active");
    var sidebar_left = document.getElementById("sidebar-left")
    if(sidebar_left != null && sidebar_left.classList.contains('active')){
        sidebar_left.classList.remove('active')    
    }
    var sidebar_right = document.getElementById("sidebar-right")
    if(sidebar_right != null && sidebar_right.classList.contains('active')){
        sidebar_right.classList.remove('active')        
    }
})

var open_right = document.getElementById("account-button");
open_right.addEventListener("click", function(event){
    document.getElementById("sidebar-right").classList.toggle("active");
    document.getElementById("hide").classList.toggle("active");
})

var close_right = document.getElementById("close_account_menu");
close_right?.addEventListener("click", function(event){
    document.getElementById("sidebar-right").classList.toggle("active");
    document.getElementById("hide").classList.toggle("active");
})
