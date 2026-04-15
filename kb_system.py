"""
占卜知识库系统 - Knowledge Base for Fortune Telling
支持文件类型: PDF, TXT, DOCX, MD
向量模型: sentence-transformers
向量数据库: ChromaDB
"""
import os, json, hashlib
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
try:
    from langchain_community.document_loaders import Docx2txtLoader
    HAS_DOCX = True
except:
    HAS_DOCX = False

KB_DIR = os.path.expanduser("~/knowledge-base")
UPLOAD_DIR = os.path.expanduser("~/uploads/knowledge-base")
CHROMA_DIR = os.path.join(KB_DIR, "chroma_db")
METADATA_FILE = os.path.join(KB_DIR, "indexed_files.json")
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
COLLECTION_NAME = "fortune_telling"

def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_DIR)

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_metadata(meta):
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def file_hash(filepath):
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == ".pdf":
            loader = PyPDFLoader(filepath)
            docs = loader.load()
            return "\n\n".join([d.page_content for d in docs])
        elif ext in (".txt", ".md"):
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif ext == ".docx" and HAS_DOCX:
            loader = Docx2txtLoader(filepath)
            docs = loader.load()
            return "\n\n".join([d.page_content for d in docs])
    except Exception as e:
        print(f"    Error reading {filepath}: {e}")
    return None

def split_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )
    return splitter.split_text(text)

def index_files(force=False):
    print("Scanning upload directory...")
    meta = load_metadata() if not force else {}
    new_files = []
    for root, dirs, files in os.walk(UPLOAD_DIR):
        for fname in files:
            fpath = os.path.join(root, fname)
            ext = os.path.splitext(fname)[1].lower()
            if ext not in (".pdf", ".txt", ".md", ".docx"):
                continue
            fhash = file_hash(fpath)
            key = os.path.relpath(fpath, UPLOAD_DIR)
            if not force and meta.get(key) == fhash:
                continue
            new_files.append((fpath, key, fhash))
    if not new_files:
        print("No new files to index.")
        return 0
    print(f"Found {len(new_files)} files to index...")
    client = get_chroma_client()
    collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space":"cosine"})
    total = 0
    for fpath, key, fhash in new_files:
        fname = os.path.basename(fpath)
        print(f"  Processing: {fname}")
        text = load_file(fpath)
        if not text or not text.strip():
            continue
        chunks = split_text(text)
        if not chunks:
            continue
        ids = [f"{key}__chunk_{i}" for i in range(len(chunks))]
        metas = [{"source": fname, "file_key": key} for _ in chunks]
        collection.add(ids=ids, documents=chunks, metadatas=metas)
        meta[key] = fhash
        total += len(chunks)
        print(f"    {len(chunks)} chunks indexed.")
    save_metadata(meta)
    print(f"Done! {len(new_files)} files, {total} chunks total.")
    return total

def search(query, top_k=5):
    client = get_chroma_client()
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    count = collection.count()
    if count == 0:
        return []
    results = collection.query(query_texts=[query], n_results=min(top_k, count))
    items = []
    for i in range(len(results["ids"][0])):
        items.append({
            "content": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "distance": results["distances"][0][i] if "distances" in results else None
        })
    return items

def get_stats():
    meta = load_metadata()
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        chunks = collection.count()
    except:
        chunks = 0
    return {"indexed_files": len(meta), "total_chunks": chunks, "files": list(meta.keys())}

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python kb_system.py [index|search|stats]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "index":
        index_files("--force" in sys.argv)
    elif cmd == "search":
        q = " ".join(sys.argv[2:])
        for i, r in enumerate(search(q), 1):
            print(f"\n---[{i}] {r['source']}---\n{r['content'][:300]}")
    elif cmd == "stats":
        s = get_stats()
        print(f"Files: {s['indexed_files']}, Chunks: {s['total_chunks']}")
