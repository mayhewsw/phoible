from collections import defaultdict

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


def getHRLanguages(fname, hrthreshold=1000):
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

            code2name[langcode] = sline[3]

            if sline[4] != "1":
                continue

            p = Phoneme(*sline[-6:])

            #langs[int(inventoryid)].add(p)
            langs[langcode].add(p)
            
    return langs,code2name
    
    

def langsim(query, langs, only_hr=False):

    orig = langs[query]


    import os
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    hrlangs = getHRLanguages(os.path.join(__location__, "langsizes.txt"))

    dists = []

    for langid in langs.keys():
        if langid == query:
            continue
        if not only_hr or langid in hrlangs:
            d = len(langs[langid].intersection(orig))
            dists.append((d, langid))
            
    topk = 100
    ret = sorted(dists, reverse=True)[:topk]

    return ret

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("lang")
    #parser.add_argument("threshold", type=float)
    
    #parser.add_argument("--topk", help="show top k results", type=int, default=10)
    parser.add_argument("--highresource", help="only compare with high resource", action="store_true")
    
    args = parser.parse_args()

    print "lang: ", args.lang
    #print "threshold: ", args.threshold

    #print langsim("language.csv", args.lang, args.threshold, phon=args.phon, topk=args.topk, only_hr=args.highresource)

    langs,code2name = loadLangs("../gold-standard/phoible-phonemes.tsv")
    print langsim(args.lang, langs, only_hr=args.highresource)
