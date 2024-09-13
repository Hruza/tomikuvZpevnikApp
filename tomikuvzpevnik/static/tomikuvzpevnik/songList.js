window.onload = setupSearch;

var list;
var owner_filter;
var string_filter = "";

function onlyUnique(value, index, array) {
    return array.indexOf(value) === index;
}

function setupSearch() {
    list = document.querySelectorAll('div.song_item');
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
        if (content.includes(string_filter)) {
          item.style.display = 'block';
        } else {
          item.style.display = 'none';
        }
    });
}
