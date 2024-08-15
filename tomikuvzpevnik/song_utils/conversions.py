import re

VALID_CHORDS = ["C", "C#","D","D#","E","F", "F#","G","G#","A","B","H","Bb"]

h_converter = {"Bb":"B","B":"H"}
    
CHORD_HTML = '<span class="chord" tone="{0}" type="{1}"><span class="innerchord">{0}{1}</span></span>'
BR = '<br>'
VERSE_START = '<p class="{0}">'
VERSE_END = '</p>'
CHORD_SYMBOL = "*"

def split_chord(chord:str,use_h = True):
    chord = chord.strip()
    if len(chord) == 0:
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
        
        line = re.sub(r"(\[[^\]]+\])",replace_chord,line)
        current_verse.append(line + BR)

    if len(current_verse)>0:
        verse_type = "verse"
        if current_verse[0]==CHORD_SYMBOL:
            verse_type = "chorus"
            del current_verse[0]
        verses.append([VERSE_START.format(verse_type)] + current_verse + [VERSE_END])
        current_verse = []

    return "".join(["".join(verse) for verse in verses])