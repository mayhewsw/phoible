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


def phoible(query):

    langs = defaultdict(set)

    langsseen = set()

    id2name = {}

    with open("../gold-standard/phoible-phonemes.tsv") as p:

        lines = p.readlines()

        for line in lines[1:]:

            sline = line.split("\t")
            inventoryid = sline[0]
            langcode = sline[2]

            id2name[int(inventoryid)] = langcode

            if sline[4] != "1":
                continue

            p = Phoneme(*sline[-6:])

            langs[int(inventoryid)].add(p)

    orig = langs[query]

    dists = []

    for langid in langs.keys():
        if langid == query:
            continue
        d = len(langs[langid].intersection(orig))
        dists.append((d, id2name[langid]))

    topk = 100
    ret = sorted(dists, reverse=True)[:topk]

    return ret

if __name__ == "__main__":
    print phoible(45)