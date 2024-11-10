import re
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import html

VALID_CHORDS = ["C", "C#","D","D#","E","F", "F#","G","G#","A","B","H","Bb"]

h_converter = {"Bb":"B","B":"H"}

CHORD_HTML = '<span class="chord"><span class="innerchord" tone="{0}" type="{1}">{0}{1}</span></span>'
CHORD_WRORD_HTML = '<span class="chord_word">{0}</span>'
BR = '<br>'
VERSE_START = '<p class="{0}">'
VERSE_END = '</p>'
HIGHLIGHT_HTML = '<i>{0}</i>'
CHORD_SYMBOL = "*"
NOT_CHORD = ["bridge","intro","outro","ending"]

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

def ultimate_to_base(url):
    try:
        parsed_url = urlparse(url)
        hostname = str(parsed_url.netloc)
        if not hostname.endswith("ultimate-guitar.com"):
            return None 
        response = requests.get(url)
    except requests.exceptions.InvalidURL:
        return None

    song_html = response.text

    byArtI = song_html.find('"byArtist": {')
    byArtE = song_html[byArtI:].find("}")
    titleI = song_html[byArtI:].find('"name":"')
    titleE = song_html[titleI+byArtI+8:].find('"')
    artist = song_html[titleI+byArtI:8+titleI+byArtI+titleE].replace('"name":"','')
    # print(artist)
    byArtI = byArtI + byArtE
    titleI = song_html[byArtI:].find('"name":"')
    titleE = song_html[titleI+byArtI+8:].find('"')
    title = song_html[titleI+byArtI:8+titleI+byArtI+titleE].replace('"name":"','')

    firstWord = '{&quot;content&quot;:&quot;'
    lastWord = '&quot;,&quot;revision_id&quot'
    song_html = song_html[song_html.find(firstWord)+len(firstWord)+1:]
    song_html = song_html[:10000]
    song_html = song_html[:song_html.find(lastWord)]
    song_html = song_html.replace("\\r\\n","\n")

    song_html = html.unescape(song_html)

    output_text = []
    chords = None
    for line in song_html.split("\n")[1:300]:
        line = line.rstrip()
        if (
            not line.startswith("[tab]")
            and line.startswith("[")
            and line.endswith("]")
            and not line.startswith("[ch]")
        ):
            line = line.strip("[]")
            # Start of verse
            if len(output_text)>0:
                output_text.append("")
            if not line[:5] in ['Bridg','Verse','Choru','Pre-C']:
                # using sart because verse can be numbered
                output_text.append("[" + line + "]")
            elif line == 'Chorus':
                output_text.append("*")
        elif line.startswith("[tab]"):
            # Line contains chords for the next line
            line = line.removeprefix("[tab]")
            chords = re.findall("([ ]*)\[ch\]([^\[]*)\[/ch\]",line)
            chords = [(len(spaces),chord) for spaces,chord in chords]
        elif line == "":
            pass
        elif not chords is None:
            # Line to apply chords to
            line = line.removesuffix("[/tab]")   

            line_segments = []
            start_index = 0
            prior_offset = 0
            for space,chord in chords:
                space = space + prior_offset
                line_segments.append(line[start_index:start_index+space])
                start_index += space
                line_segments.append(f"[{chord}]") 
                prior_offset = len(chord)
            if start_index < len(line):
                line_segments.append(line[start_index:])   
            line = "".join(line_segments)

            line = line.replace("[ch]","[")
            line = line.replace("[/ch]","]")
            output_text.append(line)
            chords = None
        else:
            # Other lines that may contain chords - e.g. instrumental
            line = line.replace("[ch]", "[")
            line = line.replace("[/ch]", "]")
            output_text.append(line)

    return {
        "title":title,
        "artist":artist,
        "lyrics":"\n".join(output_text),
        "capo":0,
    }
