"""Tiny RAG layer: Ollama embeddings + Chroma. Intentionally has NO access control."""
import math, os, uuid
import chromadb, ollama

EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
MAX_DIST = float(os.getenv("RAG_MAX_DIST", "0.9"))   # lower = stricter relevance filter
col = chromadb.PersistentClient(path="chroma_db").get_or_create_collection("acme_kb")

def embed(texts, kind="search_document"):
    # nomic-embed-text expects a task prefix; vectors are normalised so distance behaves like cosine
    vecs = ollama.embed(model=EMBED_MODEL, input=[f"{kind}: {t}" for t in texts])["embeddings"]
    return [[x / (math.sqrt(sum(y * y for y in v)) or 1) for x in v] for v in vecs]

def chunk(text, size=700):
    out, cur = [], ""
    for p in text.split("\n\n"):
        if len(cur) + len(p) > size and cur:
            out.append(cur.strip()); cur = ""
        cur += p + "\n\n"
    if cur.strip():
        out.append(cur.strip())
    return out

def add_doc(title, text, meta):
    parts = chunk(text)
    col.add(ids=[str(uuid.uuid4()) for _ in parts],
            documents=parts,
            embeddings=embed(parts),
            metadatas=[{**meta, "title": title} for _ in parts])
    return len(parts)

def retrieve(query, k=3):
    # VULN: no filtering by user, owner or classification (only a relevance cut-off)
    res = col.query(query_embeddings=embed([query], "search_query"), n_results=k)
    docs = []
    for d, dist, meta in zip(res["documents"][0], res["distances"][0], res["metadatas"][0]):
        keep = dist <= MAX_DIST
        print(f"[rag] dist={dist:.2f} {'KEEP' if keep else 'drop'} {meta.get('title')}")
        if keep:
            docs.append(d)
    return docs