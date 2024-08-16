#!/usr/bin/python
# -*- coding: utf-8 -*-

# Class to control Tomas songbook
from calendar import c
import urllib.request
import os
import re
from pathlib import Path,PurePosixPath
import locale
import pandas as pd


class SongBook:
    def __init__(self,songsDir,songBookTex):
        '''initialization function -- load all songs, give info about song book'''

        self.songsDir = songsDir
        self.songBookTex = songBookTex
        self.dbPath = Path(self.songsDir).joinpath("00_songdb.csv")
        self.colOfDb = ["name","path","owner","author","hname","capo"]
        self.owners = ["Domca","Honzik","Kiki","Lucka","Ybokem"]
        self.loadSongs()
        # self.info()

    def comparator(song):
        czech_alphabet = '0123456789 aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzž'
        return [(czech_alphabet.index(c) if c in czech_alphabet else 50) for c in song[0].lower()]


    def generateDB(self):
        print("Generating database from song files...")
        songPaths = Path(self.songsDir).rglob("*.tex")
        songLst=[]
        for path in songPaths:
            nazev = path.name.split('.')[0]
            if nazev in ['index','00-title','ZZ-endsongs','ŽŽŽ-endsongs','AA_intro']:
                pass
            else:
                if path.parents[0].name[:2]=="ŽŽ":
                    owner = path.parents[0].name[3]
                else:
                    owner = "T"
                
                with open(path,"r", encoding='utf-8') as f:
                    content=f.read()
                capo = re.search(r'\\capo{([0-9]*)}',content)
                if capo is None:
                    capo=0
                else:
                    capo = int(capo.group(1))
                info=re.match(r'\\sclearpage\\beginsong{(.*)}\[by={(.*)}\]',content)
                if info is None:
                    songLst.append([nazev,str(PurePosixPath(path)),owner,"","",nazev,capo])
                else:
                    songLst.append([nazev,str(PurePosixPath(path)),owner,info.group(2),info.group(1),capo])

        #self.songsLst = pd.DataFrame(sorted(songLst,key=SongBook.comparator),columns=["name","path","owner","author","hname"])
        self.songsLst = pd.DataFrame(songLst,columns=self.colOfDb)
        
        #sorted(self.songsLst,key=SongBook.comparator)
        self.nSongs = len(self.songsLst)
        self.saveDB()

    def saveDB(self):
        self.songsLst ['capo'] = (self.songsLst['capo']).astype(int)
        # sort by name and owner
        lst = zip(list(self.songsLst["name"]),self.songsLst.index)
        lst = sorted(lst,key=SongBook.comparator)
        self.songsLst = self.songsLst.reindex([element[1] for element in lst])
        self.songsLst.reset_index(inplace=True,drop=True)
        self.songsLst["temp_index"]=self.songsLst.index
        ownerOrder = pd.DataFrame(data=[["T",0],["D",1],["H",2],["K",3],["L",4]],columns=["owner","owner_index"])
        self.songsLst = self.songsLst.merge(ownerOrder,how='left',on="owner")
        self.songsLst = self.songsLst.sort_values(["owner_index","temp_index"])
        self.songsLst = self.songsLst.drop(["temp_index","owner_index"],axis=1)
        self.songsLst.reset_index(inplace=True,drop=True)

        self.songsLst.to_csv(self.dbPath,encoding="utf-8",index=False)

    def loadSongs(self):
        '''load songs function -- update songs list and number of songs'''

        if not self.dbPath.exists():
            self.generateDB()
        else:
            self.songsLst = pd.read_csv(self.dbPath,encoding="utf-8") 
            self.nSongs = len(self.songsLst)
    
    def info(self):
        '''give info about songbook'''

        print('Song book by Tomas\nnumber of songs: %d\nsongs: %s'%(self.nSongs,[song[0] for song in self.songsLst]))
    
    def giveIntro(self):
        '''Write start of the program'''

        print('Control program for songbook by Tomas\n')
    
    def askIfQuit(self):
        '''Prepare questions on what to do'''

        wTD = (input('\nWhat you would like to do?\n'+
                            '\t["A"] Add song.\n'+ 
                            '\t["S"] Show info about songbook\n'
                            '\t["C"] Compile songbook\n'
                            '\t["O"] Open songbook\n'
                            '\t["Q"] Quit\n'
                ))
        if wTD == 'Q':
            return True
        else:
            if 'A' in wTD:
                self.addSong()
                self.createSongBook()
                self.loadSongs()
                self.info()
            elif 'S' in wTD:
                self.info()
            elif 'C' in wTD:
                self.createSongBook()
                self.loadSongs()
            elif 'O' in wTD:
                os.system('open %s.pdf'%self.songBookTex)
            else:
                print('I dont understand you')
    
    def createSongBook(self, runFromWeb = False):
        '''create songbook'''
        print('\n not important stuff from here')
        if runFromWeb:
            os.chdir('../')
        os.system('./link-doc.sh %s.pdf > log'%self.songBookTex)
        os.system('texlua ./songidx.lua titleidx.sxd titleidx.sbx > log')
        # os.system('./songidx titleidx.sxd titleidx.sbx > log')
        os.system('pdflatex --shell-escape %s.tex > log'%self.songBookTex)
        os.system('texlua ./songidx.lua titleidx.sxd titleidx.sbx > log')
        # os.system('./songidx titleidx.sxd titleidx.sbx > log')
        os.system('pdflatex --shell-escape %s.tex > log'%self.songBookTex)
        print('end of not important stuff\n')
        if runFromWeb:
            os.chdir('./django')

    def addSong(self, runFromWeb = False, pageStrW=""):
        '''function to add song into the songbook'''

        # default parameters
        songAdded = False
        owner = ''          # default owner --->me
        firstWord = '<div class="js-store"'
        lastWord = '<'
        capo = ''
        transpose = 0
        listOfPosibilities = ['Outro','Intro','Bridge','Chorus','Verse']

        # prepare page to load
        if pageStrW == "":
            pageStrW = input('Link for song: ')
        # page = urllib.request.urlopen(pageStrW)

        # if not runFromWeb:
        req = urllib.request.Request(
            url=pageStrW, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        page = urllib.request.urlopen(req)
        pageStr = (page.read()).decode('utf-8')
        # else:
        #     os.system('wget --user-agent="Mozilla" %s -O tmp.html' % pageStrW)
        #     with open('tmp.html','r') as f:
        #         pageStr = f.read()
        #     os.system('rm -f tmp.html')
        #     print(pageStr)


        # name of the song
        try:
            nameI = pageStr.find("tag.setTargeting('song'")
            nameIF = pageStr[nameI:].find(")")
            name = pageStr[nameI:nameI+nameIF].replace("tag.setTargeting('song'",'').split('"')[1]

            # artist
            nameI = pageStr.find("tag.setTargeting('artist',")
            nameIF = pageStr[nameI:].find(")")
            artist = pageStr[nameI:nameI+nameIF].replace("tag.setTargeting('artist',",'').split('"')[1]
        
        except:
            byArtI = pageStr.find('"byArtist": {')
            byArtE = pageStr[byArtI:].find("}")
            nameI = pageStr[byArtI:].find('"name":"')
            nameE = pageStr[nameI+byArtI+8:].find('"')
            artist = pageStr[nameI+byArtI:8+nameI+byArtI+nameE].replace('"name":"','')
            # print(artist)
            byArtI = byArtI + byArtE
            nameI = pageStr[byArtI:].find('"name":"')
            nameE = pageStr[nameI+byArtI+8:].find('"')
            name = pageStr[nameI+byArtI:8+nameI+byArtI+nameE].replace('"name":"','')
            # print(name)
            # artist = 
            # print([m.start() for m in re.finditer("}", pageStr[byArtI:])])

        # prepare raw text
        # delete bordel
        toDel = pageStr.split(' ')
        for i in range(len(toDel)):
            canWanish = True
            for pos in listOfPosibilities:
                if (pos in toDel[i]):
                    canWanish = False
            if 'quot' in toDel[i] and canWanish:
                pageStr = pageStr.replace(toDel[i],'')
        cuttedText = pageStr.replace('&','').replace('iacute;','í').replace('oacute;','ó').replace('uacute;','ú').replace('aacute;','á').replace('eacute;','é').replace('yacute;','ý').replace('scaron;','š').replace('Scaron;','Š').replace('ocirc;','o').replace('auml;','a').replace('rsquo;',"'").replace('#039;',"'")

        while not songAdded:            
            #find indices of the first and last Word
            zacatekI = cuttedText.find(firstWord)
            konecI = cuttedText[zacatekI+1:].find(lastWord)

            # cut the text according to data 
            myStr = cuttedText[zacatekI+1:zacatekI+konecI]
            # print(myStr,zacatekI,konecI)
            # print(myStr,cuttedText,zacatekI,konecI)
            
            # prepare lst of individual lines
            i = 0
            strHere = ''
            myStrLst = []
            while i < len(myStr)-1:
                if myStr[i] == '\\' and myStr[i+1] == 'n':
                    strHereFin = ''
                    while strHere[0] == ' ':
                        strHere = strHere[1:]
                    
                    for j in range(len(strHere)-1):
                        if not ((strHere[j] == '\\' and strHere[j+1] == 'r')or(strHere[j-1] == '\\' and strHere[j] == 'r')):
                            strHereFin += strHere[j]
                    strHereFin = strHereFin.replace('[tab]','').replace('[/tab]','')
                    myStrLst.append(strHereFin)
                    strHere = ''
                    i = i + 2
                else:
                    strHere += myStr[i]
                    i = i + 1
            myStrLst.append(strHere)
            
            # go through cycle
            finLst = []
            chordsL = False
            playingNow = False
            for i in range(len(myStrLst)):
                line = myStrLst[i]
                # print('line',line)
                lineFin = ''
                if '[ch]' in line:
                    chords = []
                    chordsI = []
                    pocitAkordy = 0
                    for j in range(len(line)):
                        if '[' == line[j] and 'c' == line[j+1]:
                            chords.append((line[j+4:j+4+line[j+4:].find('[')]))
                            chordsI.append(j-pocitAkordy*9)
                            pocitAkordy += 1
                            chordsL = True
                elif (chordsL and chords != []) or ('[:' in line):
                    pocitAkordy = 0
                    if len(line) >= chordsI[-1]:
                        for j in range(len(line)):
                            if pocitAkordy < len(chordsI):
                                if j == chordsI[pocitAkordy]:
                                    lineFin += '\\[' + chords[pocitAkordy] + ']' + line[j]
                                    pocitAkordy += 1
                                else:
                                    lineFin += line[j]
                            else:
                                lineFin += line[j]
                    else:
                        for j in range(chordsI[-1]+10):
                            if pocitAkordy < len(chords):
                                if j == chordsI[pocitAkordy]:
                                    if len(line) > j:
                                        lineFin += '\\[' + chords[pocitAkordy] + ']' + line[j]
                                    else:
                                        lineFin += '\\[' + chords[pocitAkordy] + ']' 
                                    pocitAkordy += 1
                                else:
                                    if len(line) > j:
                                        lineFin += line[j]
                                    else:
                                        lineFin += ' '
                            else:
                                lineFin += ' '
                    chordsL = False
                    lineFin = lineFin + '\\brk'
                elif 'Verse' in line:
                    if playingNow != False:
                        if playingNow == 'verse':
                            lineFin = '\\endverse\n\\beginverse'
                        elif playingNow == 'chorus':
                            lineFin = '\\endchorus\n\\beginverse'
                        else:
                            lineFin = '}\\endverse\n\\beginverse'
                    else:
                        lineFin = '\\beginverse'
                    playingNow = 'verse'
                
                elif 'Chorus' in line:
                    if playingNow != False:
                        if playingNow == 'verse':
                            lineFin = '\\endverse\n\\beginchorus'
                        elif playingNow == 'chorus':
                            lineFin = '\\endchorus\n\\beginchorus'
                        else:
                            lineFin = '}\\endverse\n\\beginchorus'
                    else:
                        lineFin = '\\beginchorus'
                    playingNow = 'chorus'
                
                else:
                    for posI in range(len(listOfPosibilities)):
                        if listOfPosibilities[posI] in line:
                            if playingNow != False:
                                if playingNow == 'verse':
                                    lineFin = '\\endverse\n\\beginverse*{\\nolyrics [%s]: '%listOfPosibilities[posI]
                                elif playingNow == 'chorus':
                                    lineFin = '\\endchorus\n\\beginverse*{\\nolyrics [%s]: '%listOfPosibilities[posI]
                                else:
                                    lineFin = '}\\endverse\n\\beginverse*{\\nolyrics [%s]: '%listOfPosibilities[posI]
                            else:
                                lineFin = '\\beginverse*{\\nolyrics %s: '%listOfPosibilities[posI]
                            playingNow = listOfPosibilities[posI]
                finLst.append(lineFin)
           
            # now control the chords
            finLst2 = []
            i = 0
            while i < len(finLst):
                # print(i)
                line = finLst[i].replace('&','')
                if line == '' or line == ' ' or line == 'n' or line == '\n':
                    i = i+1
                elif 'Intro' in finLst[i]:
                    buffer = ''
                    for j in range(len(finLst)-i-1):
                        if not '}' in finLst[j+i+1]:
                            buffer += finLst[j+i]
                        else:
                            break
                    finLst2.append(buffer.replace('rsquo;',"'"))
                    i = i + j
                else:
                    finLst2.append(line.replace('rsquo;',"'"))
                    i = i + 1
        

            finLst = finLst2

            charLst = ['ě','š','č','ř','ž','ý','á','í','é','ú','ů','Ě','Š','Č','Ř','Ž','Ý','Á','Í','É','Ů','Ú']
            unicodeLst = []
            for chari in range(len(charLst)):
                # unicodeLst.append([charLst[chari], ord(charLst[chari]),u'%s'%ord(charLst[chari]).encode('utf-8')])
                # unicodeLst.append([charLst[chari], str(charLst[chari].encode('unicode_escape')).replace("b'\\\\",'\\').replace("'",'')])
                # print(str(charLst[chari]),str(charLst[chari].encode('unicode_escape')).replace("b'\\\\",'\\').replace("'",'').replace('x','u00'))
                jak = str(charLst[chari])
                co = str(charLst[chari].encode('unicode_escape')).replace("b'\\\\",'\\').replace("'",'').replace('x','u00')
                artist = artist.replace(co,jak)
                name = name.replace(co,jak)
                nameF = name.replace(co,jak)


                
                # artist = artist.replace(str(charLst[chari].encode('unicode_escape')).replace("b'\\\\",'\\').replace("'",''),)
            #     artist = artist.replace('%'%uni,unichr(i))
            #     name = name.replace('\\u00ed','í').replace('\\u00e1','á').replace('\\u00fa','ů').replace('\\u0159','ř').replace('\\u0161','š')
            #     nameF = name.replace('\\u00ed','i').replace('\\u00e1','a').replace('\\u00fa','u').replace('\\u0159','r').replace('\\u0161','s')

            # artist = str(artist.replace('\\\\','\\'))
            # artist = str(artist.decode('utf-8'))
            # artist = artist.replace('\\u00ed','í').replace('\\u00e1','á').replace('\\u00fa','ů').replace('\\u0159','ř').replace('\\u0161','š')
            # name = name.replace('\\u00ed','í').replace('\\u00e1','á').replace('\\u00fa','ů').replace('\\u0159','ř').replace('\\u0161','š')
            # nameF = name.replace('\\u00ed','i').replace('\\u00e1','a').replace('\\u00fa','u').replace('\\u0159','r').replace('\\u0161','s')
            
            print('\nI have prepared song %s by %s, capo %s'%(name,artist,capo))
            print('First line = %s\nPre-Last line = %s\nLast line = %s\nowner = %s'%(finLst[0],finLst[-2],finLst[-1],owner))
            
            if not runFromWeb:
                wTD = input('Do you want to change:'  
                                + '\n\t["1"]. word' 
                                + '\n\t["l"]. (last) word' 
                                + '\n\t["s"] name of the song' 
                                + '\n\t["i"] name of the author/interpret' 
                                + '\n\t["c"] capo'
                                + '\n\t["t"] transpose'
                                + '\n\t["o"] owner'
                                + '\nor ["n"] nothing?')
                if wTD == 'n':
                    songPath = Path(self.songsDir).joinpath(owner,nameF.replace(' ','_')+".tex")
                    with open(songPath,'w') as fl:
                        fl.writelines('\\sclearpage')
                        fl.writelines('\\beginsong{%s}[by={%s}]\n'%(name,artist))
                        if playingNow == False:
                            fl.writelines('\\beginverse')
                            playingNow = 'verse'
                        if not capo == '':
                            fl.writelines('\\capo{%s}\n'%capo)
                        if not transpose == 0:
                            fl.writelines('\\transpose{%d}\n'%transpose)
                        for i in range(len(finLst)):
                            fl.writelines(finLst[i]+'\n')
                        if playingNow == 'verse' or playingNow == 'chorus':
                            fl.writelines('\\end%s'%playingNow)
                        else:
                            fl.writelines('}\\endverse')
                        fl.writelines('\\endsong')

                        songInfo = pd.DataFrame({"name":[name],"path":[songPath],"owner":[owner],"author":[artist],'capo':[capo]})
                        self.songsLst=pd.concat([self.songsLst,songInfo],ignore_index = True)
                        self.saveDB()


                    songAdded = True
                else:
                    if '1' in wTD:
                        firstWord = input('Write the first word: ')
                    if 'l' in wTD:
                        lastWord = input('Write the last word: ')
                    if 's' in wTD:
                        name = input('Write name of the song: ')
                    if 'i' in wTD:
                        artist = input('Write interpret/author of the song: ')
                    if 'c' in wTD:
                        capo = input('Write capo: ')
                    if 't' in wTD:
                        transpose = int(input('Write transposition: '))
                    if 'o' in wTD:
                        ownS = (input('Write owner ("H"onzik, "D"omca or "L"ucka): '))
                        if 'H' in ownS:
                            owner = 'ŽŽ_HonzikSongs/' 
                        elif 'D' in ownS:
                            owner = 'ŽŽ_DomcaSongs/' 
                        elif 'K' in ownS:
                            owner = 'ŽŽ_KikiSongs/'
                        elif 'L' in ownS:
                            owner = 'ŽŽ_LuckaSongs/'
            else:
                owner = 'T'
                songPath = Path('songs/').joinpath(nameF.replace(' ','_')+".tex")
                with open(Path(self.songsDir).joinpath(nameF.replace(' ','_')+".tex"),'w') as fl:
                    fl.writelines('\\sclearpage')
                    fl.writelines('\\beginsong{%s}[by={%s}]\n'%(name,artist))
                    if playingNow == False:
                        fl.writelines('\\beginverse')
                        playingNow = 'verse'
                    if not capo == '':
                        fl.writelines('\\capo{%s}\n'%capo)
                    else:
                        capo = 0
                    if not transpose == 0:
                        fl.writelines('\\transpose{%d}\n'%transpose)
                    for i in range(len(finLst)):
                        fl.writelines(finLst[i]+'\n')
                    if playingNow == 'verse' or playingNow == 'chorus':
                        fl.writelines('\\end%s'%playingNow)
                    else:
                        fl.writelines('}\\endverse')
                    fl.writelines('\\endsong')
                songAdded = True
                
                songInfo = pd.DataFrame({"name":[name.replace(' ','_')],"path":[songPath],"owner":[owner],"author":[artist],'capo':[capo]})
                self.songsLst=pd.concat([self.songsLst,songInfo],ignore_index = True)
                self.saveDB()

                
                return nameF.replace(' ','_')

    def getSongHeader(songName,author,capo,django=False):
        if django:
            style1 = "{% static './style.css' %}"
            headerLine = "{% load static %} "
            transpose = "{% static './transpose.js' %}"
            editSong = '<div id ="edit"><a href="../editSong.html?song=%s" ><span class="back_span">Edit</span></a></div>' % songName
        else:
            style1="../style.css"
            headerLine=""
            transpose = "../transpose.js"
            editSong = ''

        htmlHead = f'''<!DOCTYPE html>
            <html lang="en">
            <head>
            <title>{songName}</title>
            <meta charset="UTF-8">
            {headerLine}
            <link rel="stylesheet" href="{style1}">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="{transpose}"></script>
            </head>
            <body>
            <div class="song">
            <div id="control">
            <div >
            <a href="../index.html" id ="return"><span class="back_span">⮌</span></a>
            </div>
            <div id="trans_control">
            {editSong}
            <div>
            <button onclick="transpose(+1)" class="control_button trans_button">Transpose +1</button><br>
            <div class="trans" id="trans" style="text-align:center">0</div><br>
            <button onclick="transpose(-1)" class="control_button trans_button">Transpose -1</button>
            </div>
            <div>
            <button onclick="scrollpage()" class="control_button scroll_button">Scroll<br>down</button>
            </div>
            </div>
            </div>
            <h1 id="song_name">{songName.replace("_"," ")}</h1>
            <h3 id="author">{author}</h3>
            <div class="songtext">
            <div class="song_container">
            {'' if capo == 0 else '<div id="capo">CAPO ' + str(capo)+'</div>'}
            '''
        return htmlHead

    def getIndexHeader(django = False):
        if django:
            style1 = "{% static './style.css' %}"
            style2 = "{% static './dropdown.css' %}"
            headerLine = "{% load static %} "
            songList = "{% static './songList.js' %}"
        else:
            style1="./style.css"
            style2="./dropdown.css"
            headerLine=""
            songList = "./songList.js"

        htmlHead=f'''<!DOCTYPE html>
            <html lang="en">
            <head>
            {headerLine}
            <script src="{songList}"></script>
            <link rel="stylesheet" href="{style1}">
            <link rel="stylesheet" href="{style2}">
            <title>Tomíkův zpěvník</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            </head>
            <body>
            <div id="control">
            <div>
                <a href="https://github.com/hlavatytomas/tomikuvZpevnik/raw/master/Songbook.pdf">
                <div class="control_button pdf_button">
                    PDF
                </div>
                </a>
            </div>
            <div id="list1" class="dropdown-check-list" tabindex="100">
                <span class="anchor">Select Owners</span>
                <ul class="items">
                <li><input type="checkbox" checked/>All </li>
                </ul>
            </div>
            </div>
            <h2 style="text-align:center">Tomíkův zpěvník</h3>
            <h3 style="text-align:center">&#127925; Seznam písniček &#127925;</h3>
            <div class="list_container">
            <div class="song_list">
            '''
        return htmlHead
    
    def songToHtml(content):
        #converts .tex documents to html syntax
        content = re.sub(r'\\beginverse', '<p class="verse"><br>', content)
        content = re.sub(r'\\endverse', '</p>', content)
        
        content = re.sub(r'\\capo{([^}]*)}', r'', content)

        content = re.sub(r'\\sclearpage\\beginsong{(.*)}\[by={(.*)}\]',"", content,1)

        transpose = re.search(r'\\transpose{([^}]*)}',content)
        if transpose is None:
            transpose=0
        else:
            transpose = int(transpose.group(1))
        content = re.sub(r'\\transpose{([^}]*)}', r'', content)
        
        transposer = SongBook.__getTransposer(transpose)
        content = re.sub(r'\\\[(.#*)([^\]]*)\]',lambda x: f'<span class="chord" tone="{transposer(x.group(1))}" type="{x.group(2)}"><span class="innerchord">{transposer(x.group(1))}{x.group(2)}</span></span>',content)

        content = re.sub(r'\\brk',r'<br>',content)
        content += "</div></div></div></body></html>"
        content = re.sub(r'\\beginchorus', '<p class="chorus"><br>', content)
        content = re.sub(r'\\endchorus', '</p class ="chorus">', content)
        content = re.sub(r'{\\nolyrics([^}]*)}', r'<span class="nolyrics">\1</span>', content)
        content = re.sub(r'\\endsong', '', content)
        return content

    def createHTML(self,htmlDir):
        htmlDir = Path(htmlDir)
        print(htmlDir.absolute)

        if not htmlDir.joinpath("songs").exists():
            print(f"Creating new directory: {htmlDir}")
            os.makedirs(htmlDir.joinpath("songs"),exist_ok=True)

        with open(htmlDir.joinpath("index.html"),"w", encoding='utf-8') as index:
            index.write(SongBook.getIndexHeader())
            #Convert all songs to html 
            songCount = 0
            print("Converting songs...")
            for _,row in self.songsLst.iterrows():
                songName = row["name"]
                songPath = Path(row["path"])
                songOwner = row["owner"]
                songAuthor = row["author"]
                songCapo = row["capo"]
                try:
                    with open(songPath,"r", encoding='utf-8') as tex:
                        content=tex.read()

                    content = SongBook.getSongHeader(songName,songAuthor,songCapo)+SongBook.songToHtml(content)

                    with open(htmlDir.joinpath("songs",f"{songName}.html"),"w", encoding='utf-8') as html:
                        html.write(content)

                    index.write(f'<div class="song_item" owner="{songOwner}"><a href="./songs/{songName}.html"><div class="song_ref"><span class="song_name">{re.sub("_"," ",songName)}</span><span class="owner">{songOwner}</span></div></a></div>\n')

                    songCount +=1
                except FileNotFoundError:
                    print(f"Song not found: {songName}")

            index.write("</div></div></body></html>")

            print(f"{songCount} songs converted to html")
    
    def createHTMLForDjango(self,htmlDir,sngDir=''):
        htmlDir = Path(htmlDir)

        if not htmlDir.joinpath("songs").exists():
            print(f"Creating new directory: {htmlDir}")
            os.makedirs(htmlDir.joinpath("songs"),exist_ok=True)

        with open(htmlDir.joinpath("index.html"),"w", encoding='utf-8') as index:
            index.write(SongBook.getIndexHeader(django=True))
            #Convert all songs to html 
            songCount = 0
            print("Converting songs...")
            for _,row in self.songsLst.iterrows():
                songName = row["name"]
                songPath = Path(row["path"])
                songOwner = row["owner"]
                songAuthor = row["author"]
                songCapo = row["capo"]
                try:
                    with open(Path(sngDir).joinpath(songPath),"r", encoding='utf-8') as tex:
                        content=tex.read()

                    content = SongBook.getSongHeader(songName,songAuthor,songCapo,django=True)+SongBook.songToHtml(content)

                    # with open(htmlDir.joinpath("songs",f"{songName}.html"),"w", encoding='utf-8') as html:
                    #     html.write(content)

                    index.write(f'<div class="song_item" owner="{songOwner}"><a href="./song.html?song={songName}"><div class="song_ref"><span class="song_name">{re.sub("_"," ",songName)}</span><span class="owner">{songOwner}</span></div></a></div>\n')

                    songCount +=1
                except FileNotFoundError:
                    print(f"Song not found: {songName}")

            index.write("</div></div></body></html>")

            print(f"{songCount} songs converted to html")

            # print("Creating django files...")
            # with open(htmlDir.joinpath('../project/urlsTmpl.py'), 'r') as urls:
            #     urlsLns = urls.readlines()
            # newUrlLns = []
            # uz = False
            # for i in range(len(urlsLns)):
            #     if "urlpatterns" in urlsLns[i]:
            #         uz = True
            #     elif "]" in urlsLns[i] and uz:
            #         uz = False
            #         for songInd,song in self.songsLst["name"].items():
            #             newUrlLns.append("\tpath('docs/songs/%s.html', views.p%d, name='%s'),\n" % (song, songInd, song))
            #     newUrlLns.append(urlsLns[i])
            # with open(htmlDir.joinpath('../project/urls.py'), 'w') as urls:
            #     urls.writelines(newUrlLns)
            
            # with open(htmlDir.joinpath('../pisnicky/viewsTmpl.py'), 'r') as views:
            #     viewsLst = views.readlines()
            # for songInd,song in self.songsLst["name"].items():
            #     viewsLst.append("\ndef p%d(request):\n\treturn render(request, '%s.html')\n" % (songInd, song))
            # with open(htmlDir.joinpath('../pisnicky/views.py'), 'w') as views:
            #     views.writelines(viewsLst)
                


    def __getTransposer(by):
        if by==0:
            return lambda x: x
        else:
            chords = ["C","C#","D","D#","E","F","F#","G","G#","A","B","H"]
            chordMap = {chords[i]:chords[(i+by) % len(chords)] for i in range(len(chords))}
            return lambda x: chordMap[x]

# if ran separately, launch songbook
if __name__ == "__main__":
    songsDir = './songs/'
    songBookTex = 'Songbook'

    # create song book
    songBook = SongBook(songsDir,songBookTex)

    # introduction
    songBook.giveIntro()
    while True:
        if songBook.askIfQuit():
            break
    
    songBook.createHTML("docs")
    # songBook.createHTMLForDjango("django/docs")
    # with open('songbook.pkl', 'wb') as f:
    #     pickle.dump(songBook, f)
    # songBook.createSongBook()
    # songBook.addSong()