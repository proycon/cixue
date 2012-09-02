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
import os

CHOICES = ((5*60, '5 minutes'), (3600, 'one hour'), (24*3600, 'one day'),(3*24*3600, 'three days'), (7*24*3600,'one week'),(31*24*3600, 'one month'), (365*24*3600,'one year'))
 
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

def red(s):
    CSI="\x1B["
    return CSI+"31m" + s + CSI + "0m"

class Mode:
    PASSIVE, ACTIVE = range(2)
    
class Word:
    def __init__(self, hanzi, pinyin, meanings, activedue = 0, passivedue = 0):
        self.hanzi = hanzi
        self.pinyin = pinyin        
        self.meanings = meanings #[Meaning]
        
        self.passivedue = passivedue
        self.activedue = activedue
        
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
                    passivedue = float(line[12:].strip())
                elif line[:11] == '<activedue>':   
                    activedue = float(line[11:].strip())
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
            if self.mode == Mode.PASSIVE and (word.passivedue <= t):
                pool.append(word)
            elif self.mode == Mode.ACTIVE and (word.activedue <= t):                
                pool.append(word)          
            else:          
                print "skipped already known word " + word.hanzi.encode('utf-8')
        random.shuffle(pool)
        for word in pool:
            yield word
    
    def all(self):
        for word in self.words:
            yield word
    
        

def printchoices():
    global CHOICES
    for i, (_, label) in enumerate(CHOICES):
        print magenta(str(i+1) + ") " + label + "  "),
    print
        

#this function makes the pinyin nicer, it strips the tone numbers and instead inserts proper diacritic marks (unicode). It converts for example "zhong1" into "zhōng". I go by the following rules (source: wikipedia):
# 	 The rules for determining on which vowel the tone mark appears when there are multiple vowels are as follows:
# 		  1. First, look for an "a" or an "e". If either vowel appears, it takes the tone mark. There are no possible pinyin syllables that contain both an "a" and an "e".
#   		  2. If there is no "a" or "e", look for an "ou". If "ou" appears, then the "o" takes the tone mark.
#   		  3. If none of the above cases hold, then the last vowel in the syllable takes the tone mark.
def pinyin_diacritics(pinyin):
    if ' ' in pinyin:
        return "".join(  [ pinyin_diacritics(x.strip()) for x in pinyin.split(' ') if x.strip() ] )
    
    pinyin = pinyin.lower();
    pinyin = pinyin.replace('u:',u"ü")
    
    if pinyin[-1].isdigit():
        tone = int(pinyin[-1])
        pinyin = pinyin[:-1]
        if tone == 5: #toneless tone, no diacritic, nothing to do
            return pinyin
    else:      
        #no tone, nothing to do
        return pinyin


    #set diacritic
    if pinyin.find('a') != -1:
        if tone == 1:
            return pinyin.replace('a',u"ā")
        elif tone == 2:
            return pinyin.replace('a',u"á")
        elif tone == 3:
            return pinyin.replace('a',u"ǎ")
        elif tone == 4:
            return pinyin.replace('a',u"à")
    elif pinyin.find('e') != -1:
        if tone == 1:
            return pinyin.replace('e',u"ē")
        elif tone == 2:
            return pinyin.replace('e',u"é")
        elif tone == 3:
            return pinyin.replace('e',u"ě")
        elif tone == 4:
            return pinyin.replace('e',u"è")
    elif pinyin.find('ou') != -1:
        if tone == 1:
            return pinyin.replace('ou',u"ōu")
        elif tone == 2:
            return pinyin.replace('ou',u"óu")
        elif tone == 3:
            return pinyin.replace('ou',u"ǒu")
        elif tone == 4:
            return pinyin.replace('ou',u"òu")
    else:
        #grab the last vowel and change it
        for i, c in enumerate(reversed(pinyin)):
            pre = pinyin[:-i-1]
            if -i < 0:
                post = pinyin[-i:]
            else:
                post = ""
            if c == 'a':
                if tone == 1: return pre + u"ā" + post
                elif tone == 2: return pre + u"á" + post
                elif tone == 3: return pre + u"ǎ" + post
                elif tone == 4: return pre + u"à" + post
            elif c == 'e':
                if tone == 1: return pre + u"ē" + post
                elif tone == 2: return pre + u"é" + post
                elif tone == 3: return pre + u"ě" + post
                elif tone == 4: return pre + u"è" + post
            elif c == 'u':
                if tone == 1: return pre + u"ū" + post
                elif tone == 2: return pre + u"ú" + post
                elif tone == 3: return pre + u"ǔ" + post
                elif tone == 4: return pre + u"ù" + post
            elif c == 'o':
                if tone == 1: return pre + u"ō" + post
                elif tone == 2: return pre + u"ó" + post
                elif tone == 3: return pre + u"ǒ" + post
                elif tone == 4: return pre + u"ò" + post
            elif c == 'i':
                if tone == 1: return pre + u"ī" + post
                elif tone == 2: return pre + u"í" + post
                elif tone == 3: return pre + u"ǐ" + post
                elif tone == 4: return pre + u"ì" + post
            elif c == u'ü':
                if tone == 1: return pre + u"ǖ" + post
                elif tone == 2: return pre + u"ǘ" + post
                elif tone == 3: return pre + u"ǚ" + post
                elif tone == 4: return pre + u"ǜ" + post
        return pinyin #nothing found


class Cedict(object):
    
    def __init__(self,filename):
        self.dict = {}
        self.initials = {}
        self.finals = {}
        f = codecs.open(filename,'r','utf-8')
        for line in f:        
            if line[0] != '#':
                zht,zhs,other = line.split(' ',2)
                assert other[0] == '['
                end = other.find(']')
                pinyin = pinyin_diacritics(other[1:end])
                translations = [ x.strip() for x in other[end+1:].split('/') if x.strip() ]
                self.dict[zhs] = (pinyin, translations) 
                                                            
                if zhs != zht:
                    self.dict[zht] = (pinyin, translations)
                    #add traditional chinese if different from simplified
                    
                if len(zhs) == 2:                    
                    if not zhs[0] in self.initials:
                        self.initials[zhs[0]] = []    
                    self.initials[zhs[0]].append(zhs)
                                    
                    if not zhs[-1] in self.finals:
                        self.finals[zhs[-1]] = []    
                    self.finals[zhs[-1]].append(zhs)
                    
        f.close()
       
    def __getitem__(self, key):
        return self.dict[key]
    
    def __contains__(self, key):
        return key in self.dict
    
    def lookup(self, key):
        if key in self:
            pinyin, translations = self[key]
            print green(key) + "\t" + yellow(pinyin) + "\t" + ";".join(translations) 
        if key in self.initials:
            print "Initial:"
            for initial in self.initials[key]:
                print green(initial) + "\t" + yellow(self[initial][0]) + "\t" + ";".join(self[initial][1])
        if key in self.finals:
            print "Trailing:"
            for final in self.finals[key]:
                print green(final) + "\t" + yellow(self[final][0]) + "\t" + ";".join(self[final][1])
            
    
    
if __name__ == "__main__":        
    mode = Mode.PASSIVE
    try:
        mode = sys.argv[2]
        if mode.lower() == 'a':
            mode = Mode.ACTIVE
    except:
        pass
                    
    db = DB(sys.argv[1], mode)
    if os.path.exists('cedict_ts.u8'):
        cedict = Cedict('cedict_ts.u8')
    else:
        cedict = None
    side = 0
    words = list(iter(db))
    if mode == Mode.ACTIVE:
        showpinyin = True
    else:
        showpinyin = False
    quit = False
    for i, word in enumerate(words):
        print blue("====================================================")
        print blue("Word " + str(i+1) + " of " + str(len(words)) + ":")
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
            elif c == 'z':
                random.shuffle(words)
                for w in words:
                    if w.hanzi in cedict: 
                        print w.hanzi + "   ",
                print
            elif c == 'l' or c == 'ls':
                random.shuffle(words)
                for w in words:
                    if w.hanzi in cedict: 
                        print green(w.hanzi) + "\t" + yellow(cedict[w.hanzi][0]) + "\t" + ";".join(cedict[w.hanzi][1])
            elif c == 'a':
                for w in db.all():
                    if w.hanzi in cedict: 
                        print green(w.hanzi) + "\t" + yellow(cedict[w.hanzi][0]) + "\t" + ";".join(cedict[w.hanzi][1])                    
            elif c == 'p':
                showpinyin = not showpinyin
                if showpinyin:
                    print "Showing pinyin"
                    word.front(showpinyin)
                else:
                    print "Hiding pinyin"
                    word.front(showpinyin)
                side = 1
            elif c == 'h':                    
                print "ENTER - Flip card"
                print "p - Show/hide pinyin"
                print "d - Dictionary lookup of individual hanzi in the word"
                print "a - list all words in the database"
                print "l - list all remaining words" 
                print "n - Next (no further action)"
                print "x - Show examples"
                print "q - Save and quit"
            elif c == 'q':
                db.save()
                sys.exit(0)
            elif c == 'n':
                if mode == Mode.PASSIVE: 
                    showpinyin = False
                else:
                    showpinyin = True
                done = True        
            elif c == 'd':        
                if cedict:
                    if word.hanzi in cedict and len(word.hanzi) > 1:
                        print green(word.hanzi) + "\t" + yellow(cedict[word.hanzi][0]) + "\t" + ";".join(cedict[word.hanzi][1])
                    for i, hanzi in enumerate(word.hanzi): 
                        print str(i+1) + ")"
                        cedict.lookup(hanzi)
            elif c.isdigit():
                showpinyin = False
                for j, (t,label) in enumerate(CHOICES):
                    if int(c) == j+1:           
                        print "Moving stack: ", label
                        if mode == Mode.ACTIVE:
                            word.activedue = time.time() + t
                        else:
                            word.passivedue = time.time() + t
                        done = True
                        break
            else:
                inp = unicode(c, 'utf-8')
                if mode == Mode.ACTIVE and (len(inp) >= 2 or (len(inp) == 1 and ord(inp[0]) > 128) ): 
                   if inp == word.hanzi:
                        print >>sys.stderr, green("Correct!")
                        word.front(True)
                        side = 1
                   else:
                        partial = False
                        for c2 in word.hanzi:
                            if c2 in inp: 
                                partial = True
                        if partial:    
                            print >>sys.stderr, yellow("Incorrect, but partial match")
                        else:                            
                            print >>sys.stderr, red("Incorrect")
                elif mode == Mode.PASSIVE and (len(inp) >= 2):
                    correct = False
                    for m in word.meanings:
                        if inp.lower() == m.text.lower():
                            correct = True
                    if correct:
                        print >>sys.stderr, green("Correct!")
                        word.front(True)
                        word.back()
                        side = 0
                    else:
                        print >>sys.stderr, red("Incorrect")                        
                else:
                    print >>sys.stderr, "Invalid command (type 'h' for help)" 
            if quit:
                break
    

print "All done!"
db.save()               
         
    
    
    
