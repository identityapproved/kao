class DB:
    # views over the generated blobs (see tools/build_data.py); only what is shown gets decoded
    def __init__(self, mod):
        self.faces = mod.FACES
        self.tag_lines = mod.TAGS
        self.widths = mod.WIDTHS
        self.cats = mod.CATS
        self.categories = mod.CATEGORIES
        self.count = mod.COUNT
        self.offs = memoryview(mod.OFFS).cast("I")
        self.toffs = memoryview(mod.TOFFS).cast("I")
        self.words_blob = mod.WORDS
        self.wpost = memoryview(mod.WPOST).cast("I")
        self.cpost = memoryview(mod.CPOST).cast("I")
        self.post = memoryview(mod.POST).cast("I")
        self._words = None

    def words(self):
        # the tag vocabulary (a few thousand words), split on the first query
        if self._words is None:
            self._words = self.words_blob.decode("utf-8").split("\n")
        return self._words

    def word_entries(self, w):
        return self.post[self.wpost[w] : self.wpost[w + 1]]

    def category_entries(self, c):
        return self.post[self.cpost[c] : self.cpost[c + 1]]

    def face(self, i):
        return self.faces[self.offs[i] : self.offs[i + 1] - 1].decode("utf-8")

    def width(self, i):
        return self.widths[i]

    def tags(self, i):
        line = self.tag_lines[self.toffs[i] : self.toffs[i + 1] - 1]
        return line[: line.index(b"\t")].decode("utf-8")

    def category(self, i):
        return self.categories[self.cats[i]]


def load():
    # data/local/*.json builds _data_local (gitignored); without it, the committed set
    try:
        from kao import _data_local as mod
    except ImportError:
        from kao import _data as mod
    return DB(mod)
