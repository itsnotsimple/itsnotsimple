"""Subset fonts to just the characters a banner uses and return them as base64 WOFF2,
so the SVGs render with the right typeface even inside GitHub's <img> sandbox."""
import base64, io, sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

FONT_DIR = sys.argv[1] if len(sys.argv) > 1 else "fonts"

def _load(path, axes=None):
    f = TTFont(path)
    if axes and "fvar" in f:
        f = instancer.instantiateVariableFont(f, axes)
    return f

class Font:
    def __init__(self, path, axes=None):
        self.path, self.axes = path, axes
        self.font = _load(path, axes)
        self.upm = self.font["head"].unitsPerEm
        self.cmap = self.font.getBestCmap()
        self.hmtx = self.font["hmtx"]
        self.used = set()

    def width(self, text, size, tracking=0.0):
        self.used.update(text)
        w = sum(self.hmtx[self.cmap.get(ord(c), self.cmap.get(32))][0] for c in text)
        return w * size / self.upm + tracking * size * max(len(text) - 1, 0)

    def use(self, text):
        self.used.update(text)
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def woff2(self):
        f = _load(self.path, self.axes)
        opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["kern", "liga"]
        opts.name_IDs = []; opts.notdef_outline = True
        s = subset.Subsetter(opts); s.populate(text="".join(sorted(self.used)) + " "); s.subset(f)
        f.flavor = "woff2"; buf = io.BytesIO(); f.save(buf)
        return base64.b64encode(buf.getvalue()).decode()

    def face(self, family, weight=400, style="normal"):
        return (f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:{style};"
                f"src:url(data:font/woff2;base64,{self.woff2()}) format('woff2');}}")
