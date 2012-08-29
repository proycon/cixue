#!/usr/bin/env python
# -*- coding: utf8 -*-

# 词学
#   by Maarten van Gompel (proycon)
#   Licensed under GPLv3

#   Works with files exported from www.nciku.com: 
#   - Content downloaded from the nciku website is only for personal use and must not be used for commercial purposes.
#   - Mass copying or downloading from the nciku website is strictly prohibited.

import sys
import time
import codecs
import random
from datetime import datetime

CHOICES = ((5*60, '5 minutes'), (3600, 'one hour'), (24*3600, 'one day'),(7*24*3600,'seven days'),(31*24*3600, 'one month'), (365*24*3600,'one year'))
 
def magenta(s):
    CSI="\x1B["
    return CSI+"35m" + s + CSI + "0m"   

def green(s):
    CSI="\x1B["
    return CSI+"32m" + s + CSI + "0m"   


def yellow(s):
    CSI="\x1B["
    return CSI+"33m" + s + CSI + "0m"   


def blue(s):
    CSI="\x1B["
    return CSI+"34m" + s + CSI + "0m"   



class Mode:
    PASSIVE, ACTIVE = range(2)
    
class Word:
    def __init__(self, hanzi, pinyin, meanings, examples, activedue = 0, passivedue = 0):
        self.hanzi = hanzi
        self.pinyin = pinyin        
        self.meanings = meanings #[Meaning]
        
        self.passivedue = 0
        self.activedue = 0
        
    def front(self, dopinyin=True):
        print "----------------------------------------------------------------------------------------"
        print green(self.hanzi.encode('utf-8')), 
        if dopinyin: 
            print "\t\t\t" + yellow(self.pinyin.encode('utf-8'))
        else:
            print
        print "----------------------------------------------------------------------------------------"
        
    def back(self):
        print "----------------------------------------------------------------------------------------"
        for i, meaning in enumerate(self.meanings):
            print '\t' + str(i+1) + ') ' + meaning.text.encode('utf-8') + "\t\t\t[" + meaning.type.encode('utf-8') + "]"
        print "----------------------------------------------------------------------------------------"
        
    def showexamples(self):
        print "----------------------------------------------------------------------------------------"
        for i, meaning in enumerate(self.meanings):
            if meaning.examples:
                print '\t' + str(i+1) + ')'
                for chinese, english in meaning.examples: 
                    print '\t\t' + chinese.encode('utf-8')
                    print '\t\t' + english.encode('utf-8')
                    print                 
        print "----------------------------------------------------------------------------------------"                

class Meaning:
    def __init__(self, text, type, examples= None):
        self.text = text
        self.type = type
        if not examples:
            self.examples = []
        else:
            self.examples = examples #[(chinese, english)]
                
class DB:    


    def __init__(self, filename, mode):
        self.words = []
        self.mode = mode
        self.filename = filename
        hanzi = ""
        pinyin = ""
        mode = None
        passivedue = time.time()
        activedue = time.time()
        type = ""
        meanings = []
        meaningcursor = 0
        for line in codecs.open(filename,'r','utf-8'):
            line = line.strip()
            if line:
                if line[:6] == '<Word>':
                    if hanzi:
                        self.words.append( self.make(hanzi,pinyin, meanings, activedue, passivedue) )
                        meanings = [] 
                    hanzi = line[6:]
                elif line[:6] == '<Pron>':
                    pinyin = line[6:]
                elif line[:9] == '<meaning>':
                    mode = 'meaning'
                elif line[:9] == '<example>':
                    mode = 'example'
                elif line[:12] == '<passivedue>':                    
                    passivedue = datetime.fromtimestamp(float(line[12:].strip()))
                elif line[:11] == '<activedue>':   
                    activedue = datetime.fromtimestamp(float(line[11:].strip()))
                elif line[:11] == '<StudyInfo>':    
                    pass
                else:                
                    if mode == 'meaning':
                        gt = line.find('>')
                        if line[0] == '<': line = line[gt+1:]
                        brackr = line.find(']')
                        if line[0] == '[':                                                    
                            text = line[brackr+1:].strip()
                            type = line[1:brackr].strip()
                            meanings.append( Meaning(text,type) )
                        else:   
                            text = line.strip()
                            meanings.append( Meaning(text,"") )                                                  
                    elif mode == 'example':
                        if line[0] == '<' and line[-1] == '>':
                            meaningcursor = int(line[1:-1]) - 1
                        else:     
                            raw = line.split(':',1)
                            if len(raw) == 1: raw.append("")
                            try:
                                meanings[meaningcursor].examples.append( (raw[0].strip(), raw[1].strip()) )
                            except:
                                print >>sys.stderr, "MEANINGCURSOR OUT OF RANGE: ", meaningcursor   
        if hanzi:
            self.words.append( self.make(hanzi,pinyin, meanings, activedue, passivedue) )
        
    def make(self, hanzi,pinyin, meanings, activedue, passivedue):
        return Word(hanzi,pinyin, meanings, activedue, passivedue)
                
    
    def save(self):
        f = codecs.open(self.filename,'w','utf-8')
        for word in self.words:
            f.write("<Word>" + word.hanzi + "\n")
            f.write("<Pron>" + word.pinyin + "\n")
            f.write("<meaning>\n")
            for i, meaning in enumerate(word.meanings):  
                if meaning.type:
                    f.write("<" + str(i+1) + ">[" + meaning.type + "] " + meaning.text + "\n")
                else:
                    f.write("<" + str(i+1) + ">" + meaning.text + "\n")
            f.write('<example>\n')                    
            for i, meaning in enumerate(word.meanings):                
                f.write('<' + str(i+1) + '>\n')
                for chinese, english in meaning.examples:
                    f.write("\t\t\t" + chinese + ' : ' + english + "\n")       
            f.write('<activedue>' + str(word.activedue) + "\n")
            f.write('<passivedue>' + str(word.passivedue) + "\n")
                     
        f.close()
    
    def __iter__(self):
        pool = []
        t = time.time()
        for word in self.words:
            if self.mode == Mode.PASSIVE and (word.passivedue >= t or not word.passivedue):
                pool.append(word)
            elif self.mode == Mode.ACTIVE and (word.activedue >= t or not word.activedue):                
                pool.append(word)                    
        random.shuffle(pool)
        for word in pool:
            yield word
        

def printchoices():
    global CHOICES
    for i, (_, label) in enumerate(CHOICES):
        print magenta(str(i) + ") " + label + "  "),
    print
        

if __name__ == "__main__":        
    mode = Mode.PASSIVE
    try:
        mode = sys.argv[2]
        if mode.lower() == 'a':
            mode = Mode.ACTIVE
    except:
        pass
                    
    db = DB(sys.argv[1], mode)
    side = 0
    words = list(iter(db))
    showpinyin = False
    quit = False
    for i, word in enumerate(words):
        print blue("====================================================")
        print "Word " + str(i+1) + " of " + str(len(words)) + ":"
        if mode == Mode.ACTIVE:
            side = 0
            word.back()
        else:
            side = 1
            word.front(showpinyin)
                   
        done = False
        while not done:
            printchoices()
            print ">>> ",
            c = sys.stdin.readline().strip()
            if not c:
                if side == 0:
                    side = 1
                    word.front(showpinyin)
                else:
                    side = 0
                    word.back()
            elif c == 'x':
                word.showexamples()
            elif c == 'p':
                showpinyin = not showpinyin
                if showpinyin:
                    print "Showing pinyin"
                    side = 0
                    word.front(showpinyin)
                else:
                    print "Hiding pinyin"
                    side = 0
                    word.front(showpinyin)
            elif c == 'h':                    
                print "ENTER - Flip card"
                print "p - Show/hide pinyin"
                print "n - Next (no further action)"
                print "x - Show examples"
                print "q - Save and quit"
            elif c == 'q':
                db.save()
                sys.exit(0)
            elif c == 'n':
                done = True                
            elif c.isdigit():
                for j, (t,label) in enumerate(CHOICES):
                    print "Moving to next stack"
                    if int(c) == j+1:           
                        if mode == Mode.ACTIVE:
                            word.activedue = time.time() + t
                        else:
                            word.passivedue = time.time() + t
                        done = True
                        break
            else:
                print >>sys.stderr, "Invalid command (type 'h' for help)" 
            if quit:
                break
    
print "All done!"
    
               
         
    
    
    
