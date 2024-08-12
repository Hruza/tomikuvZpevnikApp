let trans = 0;

const notes = ["C", "C#","D","D#","E","F", "F#","G","G#","A","B","H"];

const mindist = 5; //minimal distance between chords in pixels

function transpose(dir) {
    trans+= dir;
    if(trans==12 || trans ==-12){
        trans=0
    } 
    document.getElementById("trans").innerHTML = trans.toString();
    let tone;
    let type;
    let index;

    let chords = document.getElementsByClassName("chord")
    for (let i = 0; i < chords.length; i++) {
        const chord = chords[i];
        tone = chord.getAttribute("tone");
        type = chord.getAttribute("type"); 
        index = notes.indexOf(tone);
        tone = notes[(index + trans + 12) % 12 ];

        chord.getElementsByClassName("innerchord")[0].innerHTML = tone + type;
    }
    calibrateChords();
}

function chordsOverlap(el1, el2) {
    const domElement1 = el1.getBoundingClientRect();
    const domElement2 = el2.getBoundingClientRect();
    if (domElement2.bottom > domElement1.top && domElement1.bottom > domElement2.top && domElement2.left >= domElement1.left && domElement2.right > domElement1.left){
        return Math.max(domElement1.right - domElement2.left+mindist,0);
    }else{
        return 0;
    }

  }
  
  
  // Function to callibrate the chords so that they do not overlap
  function calibrateChords() {
    const chords = document.querySelectorAll('span.chord');
    const inner_chords = document.querySelectorAll('span.innerchord');
    for (let i = 0; i < chords.length; i++) {
        chords[i].style.marginLeft = '';
      }
    for (let i = 0; i < chords.length - 1; i++) {
      let ch1 = inner_chords[i];
      let ch2 = inner_chords[i + 1];
      let diff = chordsOverlap(ch1, ch2);
      if (diff>0) {
        chords[i + 1].style.marginLeft = (Math.round(diff)+mindist).toString() + 'px';
      } 
    }
  }
  
window.onload = calibrateChords;

function scrollpage() {
  window.scrollBy(0,1);
  if ((window.innerHeight + window.scrollY) < document.body.offsetHeight) { //scrolling stops at the bottom
    scrolldelay = setTimeout(scrollpage,70);
  }
}
