from collections import defaultdict
from scipy.spatial.distance import cosine
import os
import codecs
import stats
import math

class Phoneme:
    """
    This represents a phoneme, and is used when reading the language file.
    """

    def __init__(self, PhonemeID, GlyphID,Phoneme,Class,CombinedClass,NumOfCombinedGlyphs):
        self.PhonemeID = PhonemeID
        self.GlyphID = GlyphID
        self.Phoneme = Phoneme
        self.Class = Class
        self.CombinedClass = CombinedClass
        self.NumOfCombinedGlyphs = NumOfCombinedGlyphs

        # this is a printable version of Phoneme
        self.p = Phoneme.encode("utf8")

    def __repr__(self):
        return "Phoneme:[" + self.p + "]"

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
    :return: a map of language names (in ISO 639-3 format?)
    """

    hrlangs = {}
    with open(fname) as fs:
        for line in fs:
            longname,iso639_3,iso639_1,size = line.strip().split()
            if int(size) > hrthreshold:
                hrlangs[iso639_3] = longname
    return hrlangs

    
def loadLangs(fname):
    """
    This takes the filename of the phoible data and reads it into useful structures.
    :param fname: the name of the phoible file, typically gold-standard/phoible-phonemes.tsv
    :return: a map of {langcode : set(phonemes), ...}, a map of {langcode : langname, ...}
    """

    # This maps: {langcode : set(Phonemes...), ...}
    langs = defaultdict(set)

    # This maps {langcode : langname, ...}
    # For example, kor : Korean
    code2name = {}

    with codecs.open(fname, "r", "utf-8") as p:

        i = 1

        for line in p:
            # skip header somehow?
            if i == 1:
                i += 1
                continue

            i += 1

            sline = line.split("\t")
            inventoryid = sline[0]
            langcode = sline[2]

            # trump decides between different versions
            # of the same language. 1 trumps all others.
            # FIXME: can we validate that every language has a 1? Do any start at 2?
            trump = sline[4]
            if trump != "1":
                continue
            
            code2name[langcode] = sline[3]

            p = Phoneme(*sline[-6:])

            langs[langcode].add(p)
            
    return langs, code2name


def loadLangData(fname):
    """
    This loads the file called phoible-aggregated.tsv. This has language data on each language.
    Use the code2name structure to map langcode back to langname.
    :param fname: this is the file typically called gold-standard/phoible-aggregated.tsv
    :return: a map from {langcode : {lang features}, ...}
    """
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
                

def langsim(query, langs, code2name, only_hr=False, script_rerank=False, topk=100000):
    """

    :param query: a langcode
    :param langs: the result coming from loadLangs
    :param only_hr: include only high resource languages?
    :return: a sorted list of languages sorted by similarity to the query. Format is [(highest score, langcode), (next highest, langcode), ...]
    """

    # this is a set of phonemes
    orig = langs[query]

    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    hrlangs = getHRLanguages(os.path.join(__location__, "langsizes.txt"))

    pmap = readFeatureFile()

    ss = stats.StaticStats()

    dists = []

    for langid in sorted(langs.keys(), reverse=True):

        if langid == query:
            continue
        if not only_hr or langid in hrlangs:
            # try getting F1 here instead of just intersection.
            tgt = langs[langid]

            score = getF1(orig, tgt)
            #score = getDistinctiveFeatures(orig, tgt, pmap)
            #score = getOV(tgt, orig, langs["eng"])

            langdct = {"phonscore" : score, "langid":langid}
            
            if script_rerank:
                if langid not in hrlangs:
                    scriptdist = -1
                else:
                    scriptdist = stats.compare(hrlangs[query], hrlangs[langid], ss.langdists)
                if scriptdist == -1:
                    langdct["scriptdist"] = None
                else:
                    langdct["scriptdist"] = scriptdist
                
            dists.append(langdct)

            
    ret = sorted(dists, key=lambda p: p["phonscore"], reverse=True)[:topk]

    return ret



def comparePhonemes(fname, l1, l2):
    """
    Given the phoible-phonemes file, and two langnames, this will print
    the common and unique phonemes between these languages.
    :param fname: phoible-phonemes.tsv file
    :param l1: langcode
    :param l2: langcode
    :return: None
    """

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
    Get the F1 score between two sets of phonemes. This ranges from 0 to 1.
    If lang1 and lang2 are identical, the F1 is 1.
    lang1 and lang2 are phoneme sets, previously loaded by loadLangs

    :param lang1: a set of phonemes
    :param lang2: a set of phonemes
    :return: F1 score
    """

    if len(lang1) == 0:
        print "ERROR: first lang is empty or doesn't exist"
        return -1
    if len(lang2) == 0:
        print "ERROR: second lang is empty or doesn't exist"
        return -1

    tp = len(lang2.intersection(lang1))
    fp = len(lang2.difference(lang1))
    fn = len(lang1.difference(lang2))

    print lang1
    print lang2
    
    print tp,fp,fn
    
    prec = tp / float(tp + fp) # this is also len(tgt)
    recall = tp / float(tp + fn) # this is also len(orig)
    f1 = 2 * prec * recall / (prec + recall)
    return f1


def readFeatureFile():
    """
    This loads the distinctive features file in phoible, typically
    called raw-data/FEATURES/phoible-segments-features.tsv
    :return: a map of {phoneme : {df : val, df : val, ...}, ...}
    """

    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    fname = os.path.join(__location__, "../raw-data/FEATURES/phoible-segments-features.tsv")

    i = 1
    with codecs.open(fname, "r", "utf-8") as f:
        phonememap = {}
        for line in f:

            i += 1
            sline = line.split("\t")
            phoneme = sline[0]
            feats = map(lambda v: 1 if v == "+" else 0, sline[1:])  # FIXME: currently treats unknowns as 0
            phonememap[phoneme] = feats

    return phonememap

# used for memoization.
phonedist = {}


def getDistinctiveFeatures(lang1, lang2, phonemeMap):
    """
    Contrast this with getF1.

    I can't get this to work correctly.

    :param lang1: a set of Phonemes
    :param lang2: a set of Phonemes
    :return: the Distinctive Features score for these languages.
    """

    if len(lang1) == 0:
        print "ERROR: first lang is empty or doesn't exist"
        return -1
    if len(lang2) == 0:
        print "ERROR: second lang is empty or doesn't exist"
        return -1

    # loop over all pairs.
    scores = {}

    total = 0

    for p in lang1:
        # get closest in lang2
        maxsim = 0  # just a small number...
        maxp = None  # max phoneme associate with maxsim
        for p2 in lang2:
            pu1 = p.Phoneme
            pu2 = p2.Phoneme
            if pu1 in phonemeMap and pu2 in phonemeMap:

                ps = tuple(sorted([pu1, pu2]))
                if ps in phonedist:
                    sim = phonedist[ps]
                else:
                    sim = 1-cosine(phonemeMap[pu1], phonemeMap[pu2])
                    phonedist[ps] = sim
            else:
                # not there...?
                #print "SHOULD NEVER HAPPEN!",
                #if pu1 not in phonemeMap:
                #    print "missing ", pu1
                #if pu2 not in phonemeMap:
                    #print "missing ", pu2

                sim = 0
            scores[(pu1,pu2)] = sim
            total += sim

    total /= float(len(lang1) * len(lang2))

    return total

def getOV(bridge, target, eng):
    """
    This is another measure of transliterability based on overlap and
    having a richer inventory.

    :param lang1: a set of Phonemes
    :param lang2: a set of Phonemes
    :param eng: the set of Phonemes for English.
    :return: a score, larger is better.
    """
    if len(bridge) == 0:
        print "ERROR: bridge lang is empty or doesn't exist"
        return -1
    if len(target) == 0:
        print "ERROR: target lang is empty or doesn't exist"
        return -1

    common = bridge.intersection(target)
    commoneng = bridge.intersection(eng)

    bridgeonly = bridge.difference(target)
    targetonly = target.difference(bridge)

    return len(common) - len(targetonly)
    #return len(common)/float(len(target)) + len(bridgeonly) / float(len(bridge)) - len(targetonly) / float(len(target))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Interact with the Phoible database.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--langsim", help="Get languages ordered by similarity to query", metavar="query", nargs=1)
    group.add_argument("--langdata", nargs=1)
    group.add_argument("--getF1", help="Get the F1 score between lang1 and lang2", metavar=('lang1', 'lang2'), nargs=2)
    group.add_argument("--getDF", help="Get the Distinctive Feature score between lang1 and lang2", metavar=('lang1', 'lang2'), nargs=2)
    group.add_argument("--getOV", help="Get the Overlap score between lang1 and lang2", metavar=('bridge', 'target'), nargs=2)
    parser.add_argument("--highresource", "-hr", help="only compare with high resource", action="store_true")
    
    args = parser.parse_args()

    phonfile = "../gold-standard/phoible-phonemes.tsv"
    langfile = "../gold-standard/phoible-aggregated.tsv"


    if args.langsim:
        print "lang: ", args.langsim
        langs, code2name = loadLangs(phonfile)
        print langsim(args.langsim[0], langs, code2name, only_hr=args.highresource, script_rerank=True)
    elif args.getF1:
        print "langs: ", args.getF1
        langs, code2name = loadLangs(phonfile)
        print getF1(langs[args.getF1[0]], langs[args.getF1[1]])
    elif args.getDF:
        print "langs: ", args.getDF
        langs, code2name = loadLangs(phonfile)
        pmap = readFeatureFile()
        print getDistinctiveFeatures(langs[args.getDF[0]], langs[args.getDF[1]], pmap)
    elif args.getOV:
        print "langs: ", args.getOV
        langs, code2name = loadLangs(phonfile)
        print getOV(langs[args.getOV[0]], langs[args.getOV[1]], langs["eng"])
    elif args.langdata:
        print "getting langdata... for", args.langdata
        d = loadLangData(langfile)
        print d[args.langdata[0]]

