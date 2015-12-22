#!/usr/bin/python
from os import listdir
from os.path import isfile, join
import re
from collections import defaultdict
import math
import string
import argparse
import pickle

def simdist(d1,d2):
    """
    d1 and d2 are each dictionaries as {char:freq, ...}
    This gives a similarity score between them.
    """
    d1sum = sum(d1.values())
    d2sum = sum(d2.values())
    for k in d1:
        d1[k] /= float(d1sum)
    for k in d2:
        d2[k] /= float(d2sum)

    
    d1chars = set(d1.keys())
    d2chars = set(d2.keys())

    common = d1chars.intersection(d2chars)

    dot = 0
    for char in common:
        v = math.log(d1[char]) + math.log(d2[char])
        dot += math.exp(v)
        
    return dot

def countscripts(sizes,langdists):
    # a list of dictionaries
    scripts = []

    dsizes = dict(sizes)

    # this reverses sizes and makes it a dictionary
    # new format: {lang:size, lang:size...}
    dictsizes = dict([(p[1],p[0]) for p in sizes])
    
    for fname in langdists.keys():
        bestscript = None
        bestscore = -1

        d1 = langdists[fname]
        
        if dictsizes[fname] < 100:
            continue
        
        # script is a dictionary
        for script in scripts:

            fname2 = script.keys()[0]
            d2 = langdists[fname2]
            
            score = simdist(d1,d2)
            if score > bestscore:
                bestscore = score
                bestscript = script
        threshold = 0.004
        
        if bestscore > threshold:
            bestscript[fname] = langdists[fname]
        else:
            scripts.append({fname : langdists[fname]})


    for s in scripts:
        keys = s.keys()
        keysizepairs = map(lambda k: (dictsizes[k],k), keys)
        print sorted(keysizepairs)
    print "There are {0} scripts represented.".format(len(scripts))
            


def makedump(mypath):
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

    def filtering(f):
        return f.startswith("wikidata") and len(f.split(".")) == 2
    
    onlyfiles = filter(filtering, onlyfiles)

    print "There are {0} data files in this directory.".format(len(onlyfiles))

    sizes = []
    langdists = {}

    
    ignore = set(string.punctuation + string.whitespace + string.digits)
    
    for fname in onlyfiles:
        with open(fname) as f:
            lines = f.readlines()
            sizes.append((len(lines),fname))

            charfreqs = defaultdict(int)

            for line in lines:
                sline = line.split("\t")
                foreign = sline[0].decode("utf8")
                for char in foreign:
                    if char not in ignore:
                        char = char.lower()
                        charfreqs[char] += 1
                    
            langdists[fname] = charfreqs
                        
    return sorted(sizes,reverse=True),langdists


def loaddump(fname):

    langdists = pickle.load(fname)
    return langdists

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--listsizes", help="Print a sorted list of file sizes", action="store_true")
    g.add_argument("--getclosest", help="Compare LANG against all others", nargs=1)
    g.add_argument("--compare", help="Compare LANG1 against LANG2", nargs=2)
    g.add_argument("--countscripts", help="Get a grouping of scripts", action="store_true")
    g.add_argument("--dumpdists", help="Dump the script distributions", action="store_true")
    
    args = parser.parse_args()

    #sizes,langdists = getstats(".")
    langdists = loaddump("langdists.pkl")
    
    if args.getclosest:
        lang = args.getclosest[0]
        d1 = langdists["wikidata." + lang]
        
        chardists = []
        for fname in langdists:
            if fname == "wikidata." + lang:
                continue
            chardists.append((simdist(d1, langdists[fname]), fname))

        st = sorted(chardists, reverse=True)
        topk = 20
        for p in st[:topk]:
            print p
    elif args.countscripts:        
        countscripts(sizes,langdists)
    elif args.listsizes:
        for p in sizes:
            print p[1],p[0]
    elif args.compare:
        print args.compare
        # why are first and second
        d1 = langdists["wikidata." + args.compare[0]]
        d2 = langdists["wikidata." + args.compare[1]]
        
    # my own little copy of simdist.
        d1sum = sum(d1.values())
        d2sum = sum(d2.values())
        for k in d1:
            d1[k] /= float(d1sum)
        for k in d2:
            d2[k] /= float(d2sum)


        d1chars = set(d1.keys())
        d2chars = set(d2.keys())
        
        common = d1chars.intersection(d2chars)
        
        dot = 0
        ddd = []
        for char in common:
            v = math.log(d1[char]) + math.log(d2[char])
            dot += math.exp(v)
            ddd.append((char,math.exp(v)))
        

        for p in sorted(ddd):
            print p[0],p[1]
        print "Score: ", dot
    elif args.dumpdists:
        print "WOOOO"
        with open("langdists.pkl","w") as f:
            pickle.dump(langdists, f)
    else:
        print "Whoops... argparse shouldn't let you get here"
        
        


    
