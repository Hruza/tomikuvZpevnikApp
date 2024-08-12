window.onload = fillDropdown;

var list;
var owner_filter;
var string_filter = "";

function onlyUnique(value, index, array) {
    return array.indexOf(value) === index;
}

function fillDropdown() {
    list = document.querySelectorAll('div.song_item');
    var owners = [];
    for (let i = 0; i < list.length; i++) {
        owners.push(list[i].getAttribute("owner"));
    }
    var unique = owners.filter(onlyUnique);
    owner_filter = new Set(unique);
    document.getElementsByClassName("items")[0].innerHTML = "";
    unique.forEach(element => {
        document.getElementsByClassName("items")[0].innerHTML += '<li><input type="checkbox" onchange="toggleVisibility(this,'+"'"+element+"'"+')" checked/>' + element + '</li>'
    });
    var checkList = document.getElementById('list1');
    checkList.getElementsByClassName('anchor')[0].onclick = function (evt) {
        if (checkList.classList.contains('visible'))
            checkList.classList.remove('visible');
        else
            checkList.classList.add('visible');
    }
    document.getElementById('searchInput').addEventListener('input',search);
}


function toggleVisibility(obj,owner) {
    if(obj.checked){
        owner_filter.add(owner);
    }
    else {
        owner_filter.delete(owner);
    }
    refreshFilter();
}


function search(){
    string_filter = this.value.toLowerCase();
    refreshFilter();
}

function refreshFilter() {
    list.forEach(function(item) {
        var content = item.textContent.toLowerCase();
        if (content.includes(string_filter) && owner_filter.has(item.getAttribute("owner"))) {
          item.style.display = 'block';
        } else {
          item.style.display = 'none';
        }
    });
}
