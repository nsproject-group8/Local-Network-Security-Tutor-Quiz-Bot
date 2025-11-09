import re, random, subprocess, shutil
from sentence_transformers import SentenceTransformer
import chromadb
import os, subprocess

# ----------------------------
# Load Embedding Model + DB
# ----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="embeddings")
collection = client.get_or_create_collection("network_security")

# ----------------------------
# Helper: Query local Ollama Llama-3.2-3B
# ----------------------------
# Run a local Ollama model (offline). Prefer the Python 'ollama' package if available,
# otherwise look for an 'ollama' binary on PATH or via OLLAMA_PATH environment variable.
OLLAMA_PATH = os.environ.get("OLLAMA_PATH") or shutil.which("ollama")

def run_llama(prompt, model_name="llama3.2:3b"):
    """Runs prompt through local Ollama model (offline)."""

    # 1) Try Python package first
    try:
        import ollama
        try:
            r = ollama.generate(model=model_name, prompt=prompt)

            # Some Ollama versions return a dict, others a stream or string
            if isinstance(r, dict):
                # prefer .get("response") or .get("output") or .get("text")
                return r.get("response") or r.get("output") or r.get("text") or str(r)
            elif hasattr(r, "response"):
                return r.response
            elif isinstance(r, str):
                return r
            else:
                return str(r)
        except Exception as e:
            return f"⚠️ Ollama (python package) error: {e}"
    except Exception:
        pass

    # 2) Try subprocess with binary
    if not OLLAMA_PATH:
        return (
            "⚠️ Llama model unavailable: no `ollama` python package found and no `ollama` "
            "binary found on PATH. Install Ollama (https://ollama.com) or set OLLAMA_PATH env var."
        )

    try:
        result = subprocess.run(
            [OLLAMA_PATH, "run", model_name],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )
        # Get plain text from stdout only
        output = result.stdout.decode("utf-8").strip()
        # Strip structured metadata if present
        output = re.sub(r"model='[^']+'.*?response='(.*?)'", r"\1", output, flags=re.DOTALL)
        return output.strip()
    except FileNotFoundError:
        return f"⚠️ Llama model error: binary not found at {OLLAMA_PATH}"
    except Exception as e:
        return f"⚠️ Llama model error: {e}"


# ----------------------------
# Helper: Clean retrieved text
# ----------------------------
def clean_text(text):
    text = re.sub(r"Figure\s*\d+(\.\d+)?|Table\s*\d+(\.\d+)?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Page\s*\d+|Slide\s*\d+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"References?:.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

# ----------------------------
# Tutor main logic
# ----------------------------
def ask(question, top_k=3, source_type=None, page=None, include_sources=True):
    """Retrieves local context from Chroma and uses Llama-3.2 to generate a clear answer.

    Optional filters:
      - source_type: filter results by metadata 'source_type' (e.g. 'lecture_slide')
      - page: filter results by metadata 'page' (int or string)
      - include_sources: when False, do not append a Sources section to the reply

    Behavior:
    - If matching documents (by source_type/page) are found, they are used as context.
    - If no matching docs are found, the function falls back to the top general matches and
      (optionally) includes those as "Fallback sources" so you can see where the answer
      came from.
    """
    q_emb = model.encode(question).tolist()
    # request a few extra results so filtering doesn't reduce our context too much
    results = collection.query(query_embeddings=[q_emb], n_results=max(top_k * 3, 10))

    if not results["documents"] or not results["documents"][0]:
        return "⚠️ No relevant content found in local data. Please ask a course-related question."

    docs, metas = results["documents"][0], results["metadatas"][0]

    # Pair and filter by metadata if requested
    pairs = list(zip(docs, metas))
    def matches_meta(m):
        if source_type and m.get("source_type") != source_type:
            return False
        if page is not None:
            # allow numeric or string comparison
            mp = m.get("page")
            if mp is None:
                return False
            if str(mp) != str(page):
                return False
        return True

    matched_pairs = [ (d,m) for (d,m) in pairs if matches_meta(m) and len(str(d).split()) > 8 ]

    # Debugging: Log matched pairs and metadata
    print("🔍 Matched Pairs:", matched_pairs)

    used_pairs = matched_pairs
    used_as_fallback = False
    if not used_pairs:
        # No docs matched the requested filters; fall back to top general results
        used_as_fallback = True
        used_pairs = [ (d,m) for (d,m) in pairs if len(str(d).split()) > 8 ][:top_k]

    if not used_pairs:
        return "⚠️ Retrieved content too short to answer."

    context = "\n\n".join([ clean_text(d) for d,m in used_pairs[:top_k] ])

    # Build structured prompt for local Llama
    if source_type or page is not None:
        filter_note = "Use ONLY the requested source filters (source_type and/or page) when present."
    else:
        filter_note = "Use the context below to answer the question."

    prompt = f"""
You are a helpful Network Security Tutor.
{filter_note}
Answer in clear bullet points. If formulas appear, include them in simple readable form.
Avoid figure numbers, page labels, or unrelated noise.

Context:
{context[:1000]}
Question: {question}

Answer:
"""

    # Generate answer via local Llama
    raw = run_llama(prompt)

    # Remove model-internal arrays/metadata from returned text
    cleaned_output = re.sub(r"context\s*=\s*\[.*?\]", "", str(raw), flags=re.DOTALL)
    cleaned_output = re.sub(r"thinking\s*=\s*[^\n]*", "", cleaned_output)
    cleaned_output = re.sub(r"\n{3,}", "\n\n", cleaned_output.strip())

    # Ensure sources are properly retrieved and formatted
    if include_sources:
        if used_as_fallback:
            srcs = sorted({f"{m.get('source_type','?')} → {m.get('filename','?')}" for d,m in used_pairs})
            src_line = "\n".join(srcs)
            sources_block = f"\n\n📚 Fallback Sources:\n{src_line}"
        else:
            srcs = sorted({f"{m.get('source_type','?')} → {m.get('filename','?')}{(' (page '+str(m.get('page'))+')') if m.get('page') is not None else ''}" for d,m in used_pairs})
            src_line = "\n".join(srcs)
            sources_block = f"\n\n📚 Sources:\n{src_line}"
    else:
        sources_block = ""

    # Debugging: Log sources block
    print("📚 Sources Block:", sources_block)

    # Ensure only the proper answer is returned in text format
    formatted_output = cleaned_output.strip()

    return f"{formatted_output}{sources_block}"

# 🧩 Quick local test
if __name__ == "__main__":
    while True:
        q = input("\nAsk a question (or type 'exit'): ")
        if q.lower() == "exit":
            break
        ans = ask(q)
        print("\n🧠 Answer:\n", ans)