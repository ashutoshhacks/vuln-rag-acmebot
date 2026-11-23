"""Load data/docs/*.md into the vector store. Header lines (owner:, classification:) end at first blank line."""
import glob, os
from kb import add_doc

for path in sorted(glob.glob("data/docs/*.md")):
    raw = open(path, encoding="utf-8").read()
    head, _, body = raw.partition("\n\n")
    meta = dict(l.split(":", 1) for l in head.splitlines() if ":" in l)
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    n = add_doc(os.path.basename(path), body, meta)
    print(f"ingested {path}: {n} chunk(s) {meta}")
