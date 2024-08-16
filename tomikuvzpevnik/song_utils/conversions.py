import re
from bs4 import BeautifulSoup

VALID_CHORDS = ["C", "C#","D","D#","E","F", "F#","G","G#","A","B","H","Bb"]

h_converter = {"Bb":"B","B":"H"}
    
CHORD_HTML = '<span class="chord"><span class="innerchord" tone="{0}" type="{1}">{0}{1}</span></span>'
CHORD_WRORD_HTML = '<span class="chord_word">{0}</span>'
BR = '<br>'
VERSE_START = '<p class="{0}">'
VERSE_END = '</p>'
HIGHLIGHT_HTML = '<i>{0}</i>'
CHORD_SYMBOL = "*"
NOT_CHORD = ["bridge","intro","outro"]

def split_chord(chord:str,use_h = True):
    chord = chord.strip()
    if chord.strip().lower() in NOT_CHORD:
        return chord, None
    elif len(chord) == 0:
        return "",""
    elif len(chord) == 1:
        chord = chord.upper()
        return chord if use_h else h_converter.get(chord,chord), ""
    else:
        chord = chord[0].upper() + chord[1:]
        if chord[:2] in VALID_CHORDS:
            return chord[:2] if use_h else h_converter.get(chord[:2],chord[:2]), chord[2:]
        else:
            return chord[:1] if use_h else h_converter.get(chord[:1],chord[:1]), chord[1:]



def replace_chord(matchobj):
    chord,chord_type = split_chord(matchobj.group(0).lstrip("[").rstrip("]"))
    if chord_type is None:
        return HIGHLIGHT_HTML.format(chord)
    return CHORD_HTML.format(chord,chord_type)

def base_to_html(text:str):
    verses = []
    current_verse = []
    for line in text.split("\n"):
        line = line.strip()
        if line == "":
            if len(current_verse)>0:
                verse_type = "verse"
                if current_verse[0]==CHORD_SYMBOL + BR:
                    verse_type = "chorus"
                    del current_verse[0]
                verses.append([VERSE_START.format(verse_type)] + current_verse + [VERSE_END])
                current_verse = []
            continue

        line = re.sub(r"(\S*\[[^:\]][^\]]*\]\S*)",CHORD_WRORD_HTML.format(r"\1"),line)
        line = re.sub(r"\[[^\]:][^\]]*\]",replace_chord,line)
        current_verse.append(line + BR)

    if len(current_verse)>0:
        verse_type = "verse"
        if current_verse[0]==CHORD_SYMBOL + BR:
            verse_type = "chorus"
            del current_verse[0]
        verses.append([VERSE_START.format(verse_type)] + current_verse + [VERSE_END])
        current_verse = []

    return "".join(["".join(verse) for verse in verses])

def html_to_base(html_text):
    html_text = html_text.replace("\n","")
    soup = BeautifulSoup(html_text, "html.parser")

    song = soup.find("div",class_="song_container")
    if not song is None:
        soup = song

    verses = []

    for verse in soup.findAll("p",{"class":["verse","chorus"]}):
        for br in verse.find_all("br"):
            br.replace_with("\n")

        for span in verse.find_all("span", {"class":"innerchord"}):
            chord = span.get_text()
            span.replace_with(f"[{chord}]")

        processed_text = verse.get_text()
        processed_text = processed_text.strip("\n")

        if "chorus" in verse.attrs["class"]:
            verses.append("*\n" + processed_text)
        else:
            verses.append(processed_text)

    return "\n\n".join(verses)
