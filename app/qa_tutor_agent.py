import re, subprocess, shutil
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
RELEVANCE_THRESHOLD = float(os.environ.get("QA_RELEVANCE_THRESHOLD", "0.4"))

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


def _extract_stream_text(chunk):
    if isinstance(chunk, dict):
        text = chunk.get("response") or chunk.get("output") or chunk.get("text") or ""
    elif hasattr(chunk, "response"):
        text = getattr(chunk, "response", "")
    elif isinstance(chunk, str):
        text = chunk
    else:
        text = str(chunk)

    if text and "response='" in text and "model=" in text:
        match = re.search(r"response='(.*?)'", text)
        if match:
            text = match.group(1)
    return text


def stream_llama(prompt, model_name="llama3.2:3b"):
    """Yields incremental chunks from the local Ollama model."""

    python_error = None
    try:
        import ollama
        try:
            stream = ollama.generate(model=model_name, prompt=prompt, stream=True)
            for chunk in stream:
                text = _extract_stream_text(chunk)
                if text:
                    yield text
            return
        except Exception as e:
            python_error = f"⚠️ Ollama (python package) error: {e}"
    except Exception:
        python_error = None

    if not OLLAMA_PATH:
        yield python_error or (
            "⚠️ Llama model unavailable: no `ollama` python package found and no `ollama` "
            "binary found on PATH. Install Ollama (https://ollama.com) or set OLLAMA_PATH env var."
        )
        return

    try:
        process = subprocess.Popen(
            [OLLAMA_PATH, "run", model_name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        process.stdin.write(prompt)
        process.stdin.close()

        def _stream_stdout():
            while True:
                chunk = process.stdout.read(256)
                if not chunk:
                    break
                yield chunk

        for chunk in _stream_stdout():
            text = _extract_stream_text(chunk)
            if text:
                yield text

        process.wait()
        if process.returncode != 0:
            error_output = process.stderr.read()
            yield python_error or f"⚠️ Llama model error: {error_output.strip()}"
    except FileNotFoundError:
        yield f"⚠️ Llama model error: binary not found at {OLLAMA_PATH}"
    except Exception as e:
        yield f"⚠️ Llama model error: {e}"


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
# Tutor main logic helpers
# ----------------------------
def prepare_prompt(question, top_k=3, source_type=None, page=None, include_sources=True):
    q_emb = model.encode(question).tolist()
    results = collection.query(query_embeddings=[q_emb], n_results=max(top_k * 3, 10))

    if not results["documents"] or not results["documents"][0]:
        return {"error": "⚠️ No relevant content found in local data. Please ask a course-related question."}

    distances = results.get("distances")
    best_distance = None
    if distances and distances[0]:
        try:
            best_distance = float(distances[0][0])
        except (TypeError, ValueError):
            best_distance = None

    docs, metas = results["documents"][0], results["metadatas"][0]

    pairs = list(zip(docs, metas))

    def matches_meta(m):
        if source_type and m.get("source_type") != source_type:
            return False
        if page is not None:
            mp = m.get("page")
            if mp is None:
                return False
            if str(mp) != str(page):
                return False
        return True

    matched_pairs = [(d, m) for (d, m) in pairs if matches_meta(m) and len(str(d).split()) > 8]

    # Debugging: Log matched pairs and metadata
    print("🔍 Matched Pairs:", matched_pairs)

    used_pairs = matched_pairs
    used_as_fallback = False
    if not used_pairs:
        used_as_fallback = True
        used_pairs = [(d, m) for (d, m) in pairs if len(str(d).split()) > 8][:top_k]

    if not used_pairs:
        return {"error": "⚠️ Retrieved content too short to answer."}

    context = "\n\n".join([clean_text(d) for d, m in used_pairs[:top_k]])

    is_relevant = True
    if best_distance is not None:
        is_relevant = best_distance <= RELEVANCE_THRESHOLD
    if used_as_fallback:
        is_relevant = False

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

    show_sources = include_sources and is_relevant
    sources_text = ""
    sources_block = ""
    if show_sources:
        if used_as_fallback:
            srcs = sorted({f"{m.get('source_type','?')} → {m.get('filename','?')}" for d, m in used_pairs})
            header = "📚 Fallback Sources:"
        else:
            srcs = sorted({
                f"{m.get('source_type','?')} → {m.get('filename','?')}"
                f"{(' (page '+str(m.get('page'))+')') if m.get('page') is not None else ''}"
                for d, m in used_pairs
            })
            header = "📚 Sources:"
        src_line = "\n".join(srcs)
        sources_text = f"{header}\n{src_line}" if src_line else ""
        sources_block = f"\n\n{sources_text}" if sources_text else ""

    print("📚 Sources Block:", sources_block)

    return {
        "prompt": prompt,
        "sources_block": sources_block,
        "sources_text": sources_text,
        "show_sources": show_sources,
        "best_distance": best_distance,
    }


def ask(question, top_k=3, source_type=None, page=None, include_sources=True):
    """Retrieves local context from Chroma and uses Llama-3.2 to generate a clear answer."""

    prepared = prepare_prompt(question, top_k=top_k, source_type=source_type, page=page, include_sources=include_sources)
    if prepared.get("error"):
        return {
            "answer": prepared["error"],
            "sources": "",
            "show_sources": False,
            "best_distance": prepared.get("best_distance"),
        }

    prompt = prepared["prompt"]
    raw = run_llama(prompt)

    cleaned_output = re.sub(r"context\s*=\s*\[.*?\]", "", str(raw), flags=re.DOTALL)
    cleaned_output = re.sub(r"thinking\s*=\s*[^\n]*", "", cleaned_output)
    cleaned_output = re.sub(r"\n{3,}", "\n\n", cleaned_output.strip())

    formatted_output = cleaned_output.strip()
    return {
        "answer": formatted_output,
        "sources": prepared["sources_text"] if prepared.get("show_sources") else "",
        "show_sources": prepared.get("show_sources", False),
        "best_distance": prepared.get("best_distance"),
    }


def stream_answer(question, top_k=3, source_type=None, page=None, include_sources=True):
    """Generator that streams an answer and optional sources."""

    prepared = prepare_prompt(question, top_k=top_k, source_type=source_type, page=page, include_sources=include_sources)
    if prepared.get("error"):
        yield {"type": "error", "text": prepared["error"]}
        return

    prompt = prepared["prompt"]
    show_sources = prepared.get("show_sources", False)
    yield {"type": "meta", "show_sources": show_sources, "best_distance": prepared.get("best_distance")}
    for chunk in stream_llama(prompt):
        if chunk:
            yield {"type": "chunk", "text": chunk}

    if include_sources and show_sources and prepared.get("sources_text"):
        yield {"type": "sources", "text": prepared["sources_text"]}

# 🧩 Quick local test
if __name__ == "__main__":
    while True:
        q = input("\nAsk a question (or type 'exit'): ")
        if q.lower() == "exit":
            break
        ans = ask(q)
        if isinstance(ans, dict):
            print("\n🧠 Answer:\n", ans.get("answer", ""))
            if ans.get("show_sources") and ans.get("sources"):
                print("\n", ans.get("sources"))
        else:
            print("\n🧠 Answer:\n", ans)
