from collections import defaultdict
from scipy.spatial.distance import cosine

class Phoneme:

    def __init__(self, PhonemeID, GlyphID,Phoneme,Class,CombinedClass,NumOfCombinedGlyphs):
        self.PhonemeID = PhonemeID
        self.GlyphID = GlyphID
        self.Phoneme = Phoneme
        self.Class = Class
        self.CombinedClass = CombinedClass
        self.NumOfCombinedGlyphs = NumOfCombinedGlyphs

    def __repr__(self):
        return "Phoneme:[" + self.Phoneme + "]"

    def __eq__(self, other):
        return other.GlyphID == self.GlyphID

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.GlyphID.__hash__()


def getHRLanguages(fname, hrthreshold=0):
    """
    :param fname: the name of the file containing filesizes. Created using wc -l in the wikidata folder
    :param hrthreshold: how big a set of transliteration pairs needs to be considered high resource
    :return: a list of language names (in ISO 639-3 format?)
    """

    hrlangs = set()
    with open(fname) as fs:
        for line in fs:
            long,iso639_3,iso639_1,size = line.strip().split()
            if int(size) > hrthreshold:
                hrlangs.add(iso639_3)
    return hrlangs

    
def loadLangs(fname):
    langs = defaultdict(set)

    langsseen = set()

    code2name = {}

    with open(fname) as p:

        lines = p.readlines()

        for line in lines[1:]:

            sline = line.split("\t")
            inventoryid = sline[0]
            langcode = sline[2]

            if sline[4] != "1":
                continue
            
            code2name[langcode] = sline[3]

            p = Phoneme(*sline[-6:])

            #langs[int(inventoryid)].add(p)
            langs[langcode].add(p)
            
    return langs,code2name

def loadLangData(fname):
    with open(fname) as p:
        lines = p.readlines()
        header = lines[0].split("\t")
        outdct = {}
        for line in lines[1:]:
            sline = line.split("\t")
            code = sline[2]
            ldict = dict(zip(header, sline))
            outdct[code] = ldict

    return outdct
                

def langsim(query, langs, only_hr=False):

    orig = langs[query]

    import os
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    hrlangs = getHRLanguages(os.path.join(__location__, "langsizes.txt"))

    dists = []

    for langid in sorted(langs.keys(), reverse=True):
        if langid == query:
            continue
        if not only_hr or langid in hrlangs:
            # try getting F1 here instead of just intersection.
            #d = len(langs[langid].intersection(orig))
            tgt = langs[langid]
            #score = getF1(orig, tgt)
            score = getDistinctiveFeatures(orig,tgt)

            dists.append((score, langid))

            
    topk = 500
    ret = sorted(dists, reverse=True)[:topk]

    return ret



def comparePhonemes(fname, l1, l2):
    langs, code2name = loadLangs(fname)

    l1set = langs[l1]
    l2set = langs[l2]

    for p in l1set:
        u = p.Phoneme.decode("utf8")
        print u
        print list(u)

    print "intersection: ", l1set.intersection(l2set)
    print "unique to {0}:".format(l1), l1set.difference(l2set)
    print "unique to {0}:".format(l2), l2set.difference(l1set)


def getF1(lang1, lang2):
    """
    Instead of getting all language similarities, just get these two.
    lang1 and lang2 are phoneme sets.
    """

    tp = len(lang2.intersection(lang1))
    fp = len(lang2.difference(lang1))
    fn = len(lang1.difference(lang2))
    prec = tp / float(tp + fp) # this is also len(tgt)
    recall = tp / float(tp + fn) # this is also len(orig)
    f1 = 2 * prec * recall / (prec + recall)
    return f1


def readFeatureFile():

    import os
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    fname = os.path.join(__location__, "../raw-data/FEATURES/phoible-segments-features.tsv")

    with open(fname) as f:
        phonememap = {}
        for line in f:
            sline = line.split("\t")
            phoneme = sline[0]
            feats = map(lambda v: 1 if v == "+" else 0, sline[1:])  # FIXME: currently treats unknowns as 0
            phonememap[phoneme] = feats
    return phonememap


def getDistinctiveFeatures(lang1, lang2):
    """
    Again, lang1 and lang2 are phoneme sets
    :param lang1:
    :param lang2:
    :return:
    """
    if len(lang1) == 0:
        print "couldn't find " + str(lang1)
        return -1
    if len(lang2) == 0:
        print "couldn't find " + str(lang2)
        return -1

    pmap = readFeatureFile()

    total = 0
    for p in lang1:
        # get closest in lang2
        maxsim = 0  # just a small number...
        for p2 in lang2:
            sim = 1-cosine(pmap[p.Phoneme], pmap[p2.Phoneme])
            #print dist
            if sim > maxsim:
                maxsim = sim
        print p,maxsim
        total += maxsim

    print total



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--langsim", nargs = 1)
    group.add_argument("--langdata", nargs = 1)
    group.add_argument("--compare", nargs = 2)
    group.add_argument("--comp", help="compare with this lang", nargs=2)
    #parser.add_argument("threshold", type=float)
    
    #parser.add_argument("--topk", help="show top k results", type=int, default=10)
    parser.add_argument("--highresource", help="only compare with high resource", action="store_true")
    
    args = parser.parse_args()

    #print "threshold: ", args.threshold

    #print langsim("language.csv", args.lang, args.threshold, phon=args.phon, topk=args.topk, only_hr=args.highresource)
    if args.langsim:
        print "lang: ", args.langsim
        langs,code2name = loadLangs("../gold-standard/phoible-phonemes.tsv")
        print langsim(args.langsim[0], langs, only_hr=args.highresource)
    elif args.compare:
        print "langs: ", args.compare
        langs,code2name = loadLangs("../gold-standard/phoible-phonemes.tsv")
        print getF1(langs[args.compare[0]], langs[args.compare[1]])
    elif args.comp:
        print args.comp
        #comparePhonemes("../gold-standard/phoible-phonemes.tsv", args.lang, args.comp)
        langs,code2name = loadLangs("../gold-standard/phoible-phonemes.tsv")
        getDistinctiveFeatures(langs[args.comp[0]], langs[args.comp[1]])
    elif args.langdata:
        print "getting langdata... for", args.langdata
        d = loadLangData("../gold-standard/phoible-aggregated.tsv")
        print d[args.langdata[0]]

