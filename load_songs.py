from tomikuvzpevnik.models import Song
from django.core.exceptions import ObjectDoesNotExist
import os
from bs4 import BeautifulSoup
from tomikuvzpevnik.song_utils.conversions import html_to_base
from django.contrib.auth.models import User
import pandas as pd
from SongBook import SongBook

folder = r"C:\Users\hruza\Documents\django\tomikuvZpevnik\docs\songs"

df = pd.read_csv(r"C:\Users\hruza\Documents\django\tomikuvZpevnik\songs\00_songdb.csv")
allsongs = Song.objects.all()

for i,row in df.iterrows():
    song_name = row["name"]
    title = song_name.replace("_"," ")
    owner = row["owner"]
    artist = row["author"]
    capo = int(row["capo"])
    print(song_name)
    try:
        with open("C:/Users/hruza/Documents/django/tomikuvZpevnik/"+row['path'],"r", encoding='utf-8') as tex:
            content=tex.read()
    except FileNotFoundError:
        print("  ==================File not found")

    html_text = SongBook.songToHtml(content)
    
    soup = BeautifulSoup(html_text, 'html.parser')

    lyrics = html_to_base(html_text)

    if owner in ["H","T"]:
        owner = User.objects.get(pk={"T":2,"H":1}[owner])
    else:
        owner = User.objects.get(username=owner)

    try:
        song = allsongs.get(title=title)
        print("  updating existing...")
        song.title=title
        song.artist=artist
        song.capo=capo
        song.owner=owner
        song.lyrics=lyrics
        song.save()
    except ObjectDoesNotExist:
        song = Song(
            title=title,
            artist=artist,
            capo=capo,
            owner=owner,
            lyrics=lyrics
        )
        print("  creating new...")
        song.save()
