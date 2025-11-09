import os
import re
import pdfplumber
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
import torch

# model + chroma client
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="embeddings")
collection = client.get_or_create_collection("network_security")

# Device / batching options
# If you have a CUDA GPU, set the model to cuda. By default this will try CUDA then fall back to CPU.
try:
    if torch.cuda.is_available():
        model.to("cuda")
        print("Using CUDA for embeddings")
except Exception:
    # ignore device move errors (MPS may be used on macs but encode(..., convert_to_numpy=True) will return CPU numpy)
    pass

# Tune this depending on memory; larger batches = higher throughput
EMBED_BATCH = int(os.environ.get("EMBED_BATCH", "64"))

def extract_text(path):
    """Extract clean text from PDF or TXT with layout cleanup."""
    text = ""
    if path.endswith(".pdf"):
        with pdfplumber.open(path) as pdf:
            for p in pdf.pages:
                t = p.extract_text() or ""
                t = re.sub(r"•|·|▪|▶|►|–|-", " ", t)  # remove bullet symbols
                t = re.sub(r"\s{2,}", " ", t)         # collapse spaces
                t = re.sub(r"Page\s*\d+", "", t)      # remove page labels
                text += " " + t
    else:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()

    # remove figure captions, lecture titles, slide headers
    text = re.sub(r"Figure\s*\d+.*", "", text)
    text = re.sub(r"Lecture\s*\d+.*", "", text)
    text = re.sub(r"Outline.*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_text(text, size=120):
    """Split clean text into smaller sentences or topic chunks."""
    sentences = re.split(r'(?<=[.?!])\s+', text)
    chunks, current = [], []
    count = 0
    for s in sentences:
        current.append(s)
        count += len(s.split())
        if count > size:
            chunks.append(" ".join(current))
            current, count = [], 0
    if current:
        chunks.append(" ".join(current))
    return chunks


def embed_folder(folder, source_type):
    if not os.path.exists(folder):
        print(f"⚠️ Folder not found: {folder}")
        return

    docs_batch, ids_batch, metas_batch = [], [], []
    total = 0

    def flush_batch():
        nonlocal docs_batch, ids_batch, metas_batch, total
        if not docs_batch:
            return
        # encode -> return numpy array on CPU
        embeddings = model.encode(docs_batch, batch_size=EMBED_BATCH, convert_to_numpy=True, show_progress_bar=False)
        # ensure list-of-lists (chromadb accepts numpy arrays too, but .tolist() is safe)
        try:
            emb_for_add = embeddings.tolist()
        except Exception:
            emb_for_add = embeddings

        collection.add(
            documents=docs_batch,
            embeddings=emb_for_add,
            ids=ids_batch,
            metadatas=metas_batch,
        )
        total += len(docs_batch)
        docs_batch, ids_batch, metas_batch = [], [], []

    for file in os.listdir(folder):
        fpath = os.path.join(folder, file)
        if not os.path.isfile(fpath):
            continue
        print(f"🔹 Preparing: {source_type}/{file}")

        # If PDF, embed each page's raw extracted text directly (no regex cleanup / no chunking)
        if fpath.lower().endswith(".pdf"):
            with pdfplumber.open(fpath) as pdf:
                for i, p in enumerate(pdf.pages):
                    page_text = p.extract_text() or ""
                    page_text = page_text.strip()
                    if not page_text:
                        continue
                    docs_batch.append(page_text)
                    ids_batch.append(f"{source_type}_{file}_page_{i}")
                    metas_batch.append({"source_type": source_type, "filename": file, "page": i})
                    if len(docs_batch) >= EMBED_BATCH:
                        flush_batch()
        else:
            text = extract_text(fpath)
            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                docs_batch.append(chunk)
                ids_batch.append(f"{source_type}_{file}_{i}")
                # Ensure metadata includes all required fields
                if not file or not source_type:
                    print(f"⚠️ Skipping file due to missing metadata: {file}")
                    continue

                # Add detailed logging for debugging
                print(f"🔹 Adding document: {file}, Source Type: {source_type}, Page: {i if fpath.lower().endswith('.pdf') else 'N/A'}")

                # Ensure metadata consistency
                meta = {"source_type": source_type, "filename": file}
                if fpath.lower().endswith(".pdf"):
                    meta["page"] = i
                metas_batch.append(meta)
                if len(docs_batch) >= EMBED_BATCH:
                    flush_batch()

    # final flush
    flush_batch()
    print(f"✅ Embedded {total} documents from {source_type}")

if __name__ == "__main__":
    # resolve project root relative to this file so data paths work
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(repo_root, "data")

    folders = [
        ("Lectures", "lecture_slide"),
        ("Lectures_text", "lecture_slide_Formatted"),
        ("textbooks", "textbook"),
        ("internet_sources", "internet_source"),
        ("Assignments", "assignment"),
        ("Quizzes", "quiz"),
    ]

    for subfolder, source_type in folders:
        path = os.path.join(data_dir, subfolder)
        embed_folder(path, source_type)

    print("🎉 All data embedded successfully!")
    print("📊 Total documents:", collection.count())
