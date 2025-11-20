'''import os, json, random, re
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer
import chromadb
import ollama

# ---------- Load local models ----------
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="embeddings")
collection = client.get_or_create_collection("network_security")


# ---------- Grading ----------
def grade_answer(user_ans, correct_ans, context_text=None, question_text=None):
    """
    Compare user answer vs correct answer, return result + score.
    Uses Ollama locally for a short reasoning if available.
    """

    from difflib import SequenceMatcher
    sim = SequenceMatcher(None, user_ans.lower().strip(), correct_ans.lower().strip()).ratio()

    # Assign base grade
    if sim > 0.8:
        result, pts = "Excellent ✅", 1
    elif sim > 0.5:
        result, pts = "Partially correct ⚠️", 0.5
    else:
        result, pts = "Incorrect ❌", 0

    # Generate reasoning (only if context is available)
    reason = ""
    if context_text:
        try:
            prompt = f"""
            You are a Network Security Tutor.
            Question: {question_text}
            Correct Answer: {correct_ans}
            User Answer: {user_ans}

            Context: {context_text[:400]}

            In one short line, explain why the correct answer is right.
            """
            import ollama
            r = ollama.generate(model="llama3.2", prompt=prompt)
            reason = r.get("response", "").strip()
        except Exception as e:
            reason = f"⚠️ Reasoning unavailable (Ollama error: {e})"
    else:
        reason = "Explanation unavailable due to missing context."

    return f"{result} — {reason}", pts


# ---------- Use Ollama to generate question dynamically ----------

def llama_generate_question(context, qtype="MCQ"):
    """Generate a structured question (MCQ, True/False, FillBlank) using Ollama locally."""
    if qtype == "MCQ":
        instruction = """
        Create ONE multiple-choice question (MCQ) based ONLY on the given text.
        Give 4 unique, realistic options and mark the correct one.
        Return JSON in this exact format:
        {
          "type": "MCQ",
          "question": "...",
          "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
          "answer": "...",
          "explanation": "..."
        }
        """
    elif qtype == "TrueFalse":
        instruction = """
        Create ONE True/False question based on the text.
        Return JSON:
        {
          "type": "TrueFalse",
          "question": "...",
          "options": ["True", "False"],
          "answer": "True" or "False",
          "explanation": "..."
        }
        """
    else:  # FillBlank
        instruction = """
        Create ONE Fill-in-the-Blank question based on the text.
        Replace one key word with '____' and provide the correct answer.
        Return JSON:
        {
          "type": "FillBlank",
          "question": "...",
          "options": [],
          "answer": "...",
          "explanation": "..."
        }
        """

    # --- Build prompt ---
    prompt = f"""
You are a professional Network Security quiz generator.
Generate a {qtype} question using ONLY the following context.
Avoid figure numbers, lecture numbers, or irrelevant details.

Context:
{context[:1200]}

{instruction}
"""

    try:
        r = ollama.generate(model="llama3.2", prompt=prompt)
        text = r.get("response", "").strip()

        # --- Attempt to isolate JSON ---
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            # try fallback if markdown fences are used
            match = re.search(r"\{[\s\S]*\}", text.replace("```json", "").replace("```", ""))
        if not match:
            raise ValueError(f"No valid JSON found in response:\n{text[:200]}")

        json_str = match.group().strip()

        # --- Clean up minor formatting issues ---
        json_str = json_str.replace("True or False", "TrueFalse")
        json_str = re.sub(r"[\r\n]+", " ", json_str)

        data = json.loads(json_str)
        return data

    except Exception as e:
        # Fallback if JSON fails
        return {
            "type": qtype,
            "question": f"⚠️ Fallback question (Ollama error: {e})",
            "options": (
                ["Encryption", "Authentication", "Integrity", "Firewalls"]
                if qtype == "MCQ"
                else ["True", "False"] if qtype == "TrueFalse" else []
            ),
            "answer": (
                "Encryption" if qtype == "MCQ"
                else "True" if qtype == "TrueFalse"
                else "confidentiality"
            ),
            "explanation": "Fallback due to Ollama JSON parsing issue."
        }
# ---------- Retrieve clean context ----------
def get_context(topic="network security"):
    results = collection.query(query_texts=[topic], n_results=5)
    if not results["documents"] or not results["documents"][0]:
        return "⚠️ No local data found.", "system"

    docs, metas = results["documents"][0], results["metadatas"][0]
    text, meta = random.choice(list(zip(docs, metas)))
    src = f"{meta.get('source_type','unknown')} → {meta.get('filename','unknown')}"
    text = re.sub(r"Lecture\s*\d+.*?:", "", text)
    text = re.sub(r"•|–|-|—", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip(), src


# ---------- Generate a balanced quiz ----------
def generate_quiz(mode="mixed", topic=None, num_questions=6):
    """
    Generate a balanced quiz with 3 types of questions:
    - MCQ
    - True/False
    - Fill-in-the-Blank
    """
    topic = topic or "network security"
    num_questions = max(3, min(int(num_questions), 15))

    # ensure distribution
    types = ["MCQ", "TrueFalse", "FillBlank"]
    quiz = []

    for i in range(num_questions):
        qtype = types[i % 3]  # cycle through the three types
        context, src = get_context(topic)
        qdata = llama_generate_question(context, qtype)
        qdata["source"] = src
        quiz.append(qdata)

    return quiz'''
'''import os, json, random, re
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer
import chromadb
import ollama

# ---------- Load local models ----------
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="embeddings")
collection = client.get_or_create_collection("network_security")

# ---------- Grading ----------
def grade_answer(user_ans, correct_ans, context_text=None, question_text=None):
    """Compare user answer vs correct answer, return result + score."""
    sim = SequenceMatcher(None, user_ans.lower().strip(), correct_ans.lower().strip()).ratio()

    if sim > 0.8:
        result, pts = "Excellent ✅", 1
    elif sim > 0.5:
        result, pts = "Partially correct ⚠️", 0.5
    else:
        result, pts = "Incorrect ❌", 0

    reason = ""
    if context_text:
        try:
            prompt = f"""
            You are a Network Security Tutor.
            Question: {question_text}
            Correct Answer: {correct_ans}
            User Answer: {user_ans}

            Context: {context_text[:128]}

            In one short line, explain why the correct answer is right.
            """
            r = ollama.generate(
                model="llama3.2",
                prompt=prompt,
                options={"num_predict": 150, "temperature": 0.7}
            )
            reason = r.get("response", "").strip()
        except Exception as e:
            reason = f"⚠️ Reasoning unavailable (Ollama error: {e})"
    else:
        reason = "Explanation unavailable due to missing context."

    return f"{result} — {reason}", pts


# ---------- JSON Repair & Extraction ----------
def safe_extract_json(raw_text: str):
    """
    Extracts and repairs JSON from model output (handles incomplete arrays, unclosed braces, and streaming cutoffs).
    """
    # Cleanup markdown, smart quotes, etc.
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    cleaned = cleaned.replace("\\n", " ").replace('\\"', '"').replace("’", "'").replace("“", '"').replace("”", '"')

    # Find first '{' occurrence and start parsing from there
    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in text: {raw_text[:200]}")

    candidate = cleaned[start:]

    # --- Bracket balancing ---
    open_braces = 0
    balanced_json = ""
    for ch in candidate:
        balanced_json += ch
        if ch == "{":
            open_braces += 1
        elif ch == "}":
            open_braces -= 1
            if open_braces == 0:
                break

    # If not balanced, close remaining braces/brackets
    if open_braces > 0:
        # Try to close arrays first if last open was '['
        if balanced_json.count("[") > balanced_json.count("]"):
            balanced_json += "]"
        balanced_json += "}" * open_braces

    # --- Remove stray trailing commas ---
    balanced_json = re.sub(r",\s*([}\]])", r"\1", balanced_json)

    try:
        return json.loads(balanced_json)
    except Exception as e:
        # Last resort: attempt minimal fixes
        try:
            fixed = balanced_json.rstrip(",") + "}"
            return json.loads(fixed)
        except Exception:
            raise ValueError(f"Failed to repair JSON: {e}\nRaw snippet:\n{balanced_json[:400]}")
# ---------- Question Generation ----------
def llama_generate_question(context, qtype="MCQ"):
    """Generate one question (MCQ, TrueFalse, or FillBlank) using Ollama."""
    if qtype == "MCQ":
        instruction = """
        Create ONE conceptual multiple-choice question (MCQ) based ONLY on the given text.
        Focus on understanding (what/why/how) rather than asking about section numbers or page references.
        Give 4 unique, realistic options and mark the correct one.
        Return JSON:
        {
          "type": "MCQ",
          "question": "...",
          "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
          "answer": "...",
          "explanation": "..."
        }
        """
    elif qtype == "TrueFalse":
        instruction = """
        Create ONE conceptual True/False question based on the text that tests comprehension instead of referencing sections/figures.
        Return JSON:
        {
          "type": "TrueFalse",
          "question": "...",
          "options": ["True", "False"],
          "answer": "True" or "False",
          "explanation": "..."
        }
        """
    else:  # FillBlank
        instruction = """
        Create ONE Fill-in-the-Blank question based on the text.
        Replace one key word with '____' and provide the correct answer.
        Return JSON:
        {
          "type": "FillBlank",
          "question": "...",
          "options": [],
          "answer": "...",
          "explanation": "..."
        }
        """

    prompt = f"""
You are a professional Network Security quiz generator.
Generate a {qtype} question using ONLY the following context.
Avoid figure numbers, lecture numbers, or irrelevant details.

Context:
{context[:128]}

{instruction}
"""

    try:
        r = ollama.generate(
            model="llama3.2",
            prompt=prompt,
            options={"num_predict": 150, "temperature": 0.7}
        )
        text = r.get("response", "").strip()
        data = safe_extract_json(text)
        return data

    except Exception as e:
        # Retry once with stricter instruction
        try:
            strict_prompt = prompt + "\nReturn ONLY valid JSON, no explanation, no prose."
            r2 = ollama.generate(
                model="llama3.2",
                prompt=strict_prompt,
                options={"num_predict": 150, "temperature": 0.7}
            )
            text2 = r2.get("response", "").strip()
            data2 = safe_extract_json(text2)
            return data2
        except Exception as e2:
            print(f"⚠️ Ollama failed twice: {e2}")
            # Fallback
            return {
                "type": qtype,
                "question": f"⚠️ Fallback question (Ollama error: {e2})",
                "options": (
                    ["Encryption", "Authentication", "Integrity", "Firewalls"]
                    if qtype == "MCQ"
                    else ["True", "False"] if qtype == "TrueFalse" else []
                ),
                "answer": (
                    "Encryption" if qtype == "MCQ"
                    else "True" if qtype == "TrueFalse"
                    else "confidentiality"
                ),
                "explanation": "Fallback due to Ollama parsing error."
            }


# ---------- Retrieve clean context ----------
def get_context(topic="network security"):
    results = collection.query(query_texts=[topic], n_results=5)
    if not results["documents"] or not results["documents"][0]:
        return "⚠️ No local data found.", "system"

    docs, metas = results["documents"][0], results["metadatas"][0]
    text, meta = random.choice(list(zip(docs, metas)))
    src = f"{meta.get('source_type', 'unknown')} → {meta.get('filename', 'unknown')}"
    text = re.sub(r"Lecture\s*\d+.*?:", "", text)
    text = re.sub(r"•|–|-|—", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip(), src


# ---------- Generate a balanced quiz ----------
def generate_quiz(mode="mixed", topic=None, num_questions=6):
    """
    Generate a balanced quiz with MCQ, True/False, and Fill-in-the-Blank.
    """
    topic = topic or "network security"
    num_questions = max(3, min(int(num_questions), 15))

    types = ["MCQ", "TrueFalse", "FillBlank"]
    quiz = []

    for i in range(num_questions):
        qtype = types[i % 3]
        context, src = get_context(topic)
        qdata = llama_generate_question(context, qtype)
        qdata["source"] = src
        quiz.append(qdata)

    return quiz
'''
'''import os, json, random, re
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer
import chromadb
import ollama

# ---------- Load local models ----------
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="embeddings")
collection = client.get_or_create_collection("network_security")

# ---------- Grading ----------
def grade_answer(user_ans, correct_ans, context_text=None, question_text=None):
    """Compare user answer vs correct answer, return result + score."""
    sim = SequenceMatcher(None, user_ans.lower().strip(), correct_ans.lower().strip()).ratio()

    if sim > 0.8:
        result, pts = "Excellent ✅", 1
    elif sim > 0.5:
        result, pts = "Partially correct ⚠️", 0.5
    else:
        result, pts = "Incorrect ❌", 0

    reason = ""
    if context_text:
        try:
            prompt = f"""
            You are a Network Security Tutor.
            Question: {question_text}
            Correct Answer: {correct_ans}
            User Answer: {user_ans}

            Context: {context_text[:200]}

            In one short line, explain why the correct answer is right.
            """
            r = ollama.generate(
                model="mistral",
                prompt=prompt,
                options={"num_predict": 256, "temperature": 0.7}
            )
            reason = r.get("response", "").strip()
        except Exception as e:
            reason = f"⚠️ Reasoning unavailable (Ollama error: {e})"
    else:
        reason = "Explanation unavailable due to missing context."

    return f"{result} — {reason}", pts


# ---------- JSON Repair & Extraction ----------
def safe_extract_json(raw_text: str):
    """Extracts and repairs JSON from model output (handles incomplete arrays, unclosed braces, and streaming cutoffs)."""
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    cleaned = cleaned.replace("\\n", " ").replace('\\"', '"').replace("’", "'").replace("“", '"').replace("”", '"')
    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in text: {raw_text[:200]}")

    candidate = cleaned[start:]
    open_braces = 0
    balanced_json = ""
    for ch in candidate:
        balanced_json += ch
        if ch == "{":
            open_braces += 1
        elif ch == "}":
            open_braces -= 1
            if open_braces == 0:
                break

    if open_braces > 0:
        if balanced_json.count("[") > balanced_json.count("]"):
            balanced_json += "]"
        balanced_json += "}" * open_braces

    balanced_json = re.sub(r",\s*([}\]])", r"\1", balanced_json)

    try:
        return json.loads(balanced_json)
    except Exception as e:
        try:
            fixed = balanced_json.rstrip(",") + "}"
            return json.loads(fixed)
        except Exception:
            raise ValueError(f"Failed to repair JSON: {e}\nRaw snippet:\n{balanced_json[:400]}")


# ---------- Question Generation ----------
def llama_generate_question(context, qtype="MCQ"):
    """Generate one question (MCQ, TrueFalse, or FillBlank) using Ollama (Mistral model)."""
    if qtype == "MCQ":
        instruction = """
        Create ONE conceptual multiple-choice question (MCQ) based ONLY on the given text.
        Focus on concrete network security concepts (what/why/how) stated in the text rather than asking about section/page numbers, book structure, author intent, or learning styles.
        Ignore any course logistics or publishing metadata in the context unless it directly explains a security mechanism.
        Give 4 unique, realistic options and mark the correct one. The correct answer must be directly supported by the context.
        Return JSON:
        {
          "type": "MCQ",
          "question": "...",
          "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
          "answer": "...",
          "explanation": "..."
        }
        """
    elif qtype == "TrueFalse":
        instruction = """
        Create ONE conceptual True/False question based on the text that tests comprehension instead of referencing sections/figures, author intentions, book layouts, or website logistics.
        Ignore non-technical metadata. The statement must be directly verifiable from the provided context.
        Return JSON:
        {
          "type": "TrueFalse",
          "question": "...",
          "options": ["True", "False"],
          "answer": "True" or "False",
          "explanation": "..."
        }
        """
    else:  # FillBlank
        instruction = """
        Create ONE Fill-in-the-Blank question based on the text.
        Replace one key word with '____' and provide the correct answer.
        Return JSON:
        {
          "type": "FillBlank",
          "question": "...",
          "options": [],
          "answer": "...",
          "explanation": "..."
        }
        """

    prompt = f"""
You are a professional Network Security quiz generator.
Generate a {qtype} question using ONLY the following context.
Avoid figure numbers, lecture numbers, or irrelevant details.

Context:
{context[:1200]}

{instruction}
"""

    try:
        r = ollama.generate(
            model="mistral",
            prompt=prompt,
            options={"num_predict": 200, "temperature": 0.6}
        )
        text = r.get("response", "").strip()
        data = safe_extract_json(text)
        return data

    except Exception as e:
        try:
            strict_prompt = prompt + "\nReturn ONLY valid JSON, no explanation, no prose."
            r2 = ollama.generate(
                model="mistral",
                prompt=strict_prompt,
                options={"num_predict": 200, "temperature": 0.6}
            )
            text2 = r2.get("response", "").strip()
            data2 = safe_extract_json(text2)
            return data2
        except Exception as e2:
            print(f"⚠️ Ollama failed twice: {e2}")
            return {
                "type": qtype,
                "question": f"⚠️ Fallback question (Ollama error: {e2})",
                "options": (
                    ["Encryption", "Authentication", "Integrity", "Firewalls"]
                    if qtype == "MCQ"
                    else ["True", "False"] if qtype == "TrueFalse" else []
                ),
                "answer": (
                    "Encryption" if qtype == "MCQ"
                    else "True" if qtype == "TrueFalse"
                    else "confidentiality"
                ),
                "explanation": "Fallback due to Ollama parsing error."
            }


# ---------- Retrieve clean context ----------
def get_context(topic="network security"):
    results = collection.query(query_texts=[topic], n_results=5)
    if not results["documents"] or not results["documents"][0]:
        return "⚠️ No local data found.", "system"

    docs, metas = results["documents"][0], results["metadatas"][0]
    text, meta = random.choice(list(zip(docs, metas)))
    src = f"{meta.get('source_type', 'unknown')} → {meta.get('filename', 'unknown')}"
    text = re.sub(r"Lecture\s*\d+.*?:", "", text)
    text = re.sub(r"•|–|-|—", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip(), src


# ---------- Generate a balanced quiz ----------
def generate_quiz(mode="mixed", topic=None, num_questions=6):
    """Generate a balanced quiz with MCQ, True/False, and Fill-in-the-Blank."""
    topic = topic or "network security"
    num_questions = max(3, min(int(num_questions), 15))

    types = ["MCQ", "TrueFalse", "FillBlank"]
    quiz = []

    for i in range(num_questions):
        qtype = types[i % 3]
        context, src = get_context(topic)
        qdata = llama_generate_question(context, qtype)
        qdata["source"] = src
        quiz.append(qdata)

    return quiz'''
import os, json, random, re
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer
import chromadb
import ollama

# ---------- Load local models ----------
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="embeddings")
collection = client.get_or_create_collection("network_security")

# Use the same local Llama variant as the tutor unless overridden via env.
QUIZ_MODEL = os.environ.get("QUIZ_MODEL", "llama3.2:3b")

# ---------- Grading ----------
def grade_answer(user_ans, correct_ans, context_text=None, question_text=None):
    """Compare user answer vs correct answer, return result + score."""
    sim = SequenceMatcher(None, user_ans.lower().strip(), correct_ans.lower().strip()).ratio()

    if sim > 0.8:
        result, pts = "Excellent ✅", 1
    elif sim > 0.5:
        result, pts = "Partially correct ⚠️", 0.5
    else:
        result, pts = "Incorrect ❌", 0

    reason = ""
    if context_text:
        try:
            prompt = f"""
            You are a Network Security Tutor.
            Question: {question_text}
            Correct Answer: {correct_ans}
            User Answer: {user_ans}

            Context: {context_text[:256]}

            In one short line, explain why the correct answer is right.
            """
            r = ollama.generate(
                model=QUIZ_MODEL,
                prompt=prompt,
                options={"num_predict": 256, "temperature": 0.7}
            )
            reason = r.get("response", "").strip()
        except Exception as e:
            reason = f"⚠️ Reasoning unavailable (Ollama error: {e})"
    else:
        reason = "Explanation unavailable due to missing context."

    return f"{result} — {reason}", pts


# ---------- JSON Repair & Extraction ----------
def safe_extract_json(raw_text: str):
    """Extracts and repairs JSON from model output (handles incomplete arrays, unclosed braces, and streaming cutoffs)."""
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    cleaned = cleaned.replace("\\n", " ").replace('\\"', '"').replace("’", "'").replace("“", '"').replace("”", '"')

    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in text: {raw_text[:200]}")
    candidate = cleaned[start:]

    open_braces = 0
    balanced_json = ""
    for ch in candidate:
        balanced_json += ch
        if ch == "{":
            open_braces += 1
        elif ch == "}":
            open_braces -= 1
            if open_braces == 0:
                break

    if open_braces > 0:
        if balanced_json.count("[") > balanced_json.count("]"):
            balanced_json += "]"
        balanced_json += "}" * open_braces

    balanced_json = re.sub(r",\s*([}\]])", r"\1", balanced_json)
    try:
        return json.loads(balanced_json)
    except Exception as e:
        try:
            fixed = balanced_json.rstrip(",") + "}"
            return json.loads(fixed)
        except Exception:
            raise ValueError(f"Failed to repair JSON: {e}\nRaw snippet:\n{balanced_json[:400]}")


# ---------- Question Generation ----------
def llama_generate_question(context, qtype="MCQ"):
    """Generate one question (MCQ, TrueFalse, or OpenEnded) using Ollama."""
    if qtype == "MCQ":
        instruction = """
        Create ONE conceptual multiple-choice question (MCQ) based ONLY on the given text.
        Focus on understanding (what/why/how) rather than asking about section or page numbers.
        Give 4 unique, realistic options and mark the correct one.
        Return JSON:
        {
          "type": "MCQ",
          "question": "...",
          "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
          "answer": "...",
          "explanation": "..."
        }
        """
    elif qtype == "TrueFalse":
        instruction = """
        Create ONE conceptual True/False question based on the text that tests comprehension instead of referencing sections/figures.
        Return JSON:
        {
          "type": "TrueFalse",
          "question": "...",
          "options": ["True", "False"],
          "answer": "True" or "False",
          "explanation": "..."
        }
        """
    else:  # OpenEnded
        instruction = """
        Create ONE short open-ended question that asks the student to explain or describe a key network security concept from the text.
        The question must be answerable purely from the provided context and must not reference section/page numbers, author motivations, learning processes, or other publishing details.
        Return JSON:
        {
          "type": "OpenEnded",
          "question": "...",
          "options": [],
          "answer": "Provide a concise correct explanation or key points expected from the student.",
          "explanation": "..."
        }
        """

    prompt = f"""
You are a professional Network Security quiz generator.
Generate a {qtype} question using ONLY the following context.
Avoid figure numbers, lecture numbers, or irrelevant details.
Ask conceptual, explainable questions (what/why/how) that can be answered without referencing section numbers, slide numbers, or page locations.
Do NOT ask "what is in section X" style questions.
Ensure every question and answer pair is explicitly grounded in the supplied context. Do not ask about the author's intentions, teaching style, or anything not stated verbatim in the text.

Requirements:
- The answer must be deducible directly from the context snippet.
- Avoid meta-level, publisher, or study-guide questions (e.g., "How does the author approach teaching?", "What is covered in Part Two?").
- Ignore companion-website logistics unless the context explicitly ties them to a security concept.
- Keep wording concrete and specific to the technical ideas described (threats, mitigations, protocols, properties, trade-offs, etc.).

Context:
{context[:512]}

{instruction}
"""

    try:
        r = ollama.generate(
            model=QUIZ_MODEL,
            prompt=prompt,
            options={"num_predict":512, "temperature": 0.7}
        )
        text = r.get("response", "").strip()
        data = safe_extract_json(text)
        return data

    except Exception as e:
        try:
            strict_prompt = prompt + "\nReturn ONLY valid JSON, no explanation, no prose."
            r2 = ollama.generate(
                model=QUIZ_MODEL,
                prompt=strict_prompt,
                options={"num_predict": 512, "temperature": 0.7}
            )
            text2 = r2.get("response", "").strip()
            data2 = safe_extract_json(text2)
            return data2
        except Exception as e2:
            print(f"⚠️ Ollama failed twice: {e2}")
            return {
                "type": qtype,
                "question": f"⚠️ Fallback question (Ollama error: {e2})",
                "options": [],
                "answer": "Not available",
                "explanation": "Fallback due to Ollama parsing error."
            }


# ---------- Retrieve clean context ----------
def get_context(topic="network security"):
    results = collection.query(query_texts=[topic], n_results=5)
    if not results["documents"] or not results["documents"][0]:
        return "⚠️ No local data found.", "system"

    docs, metas = results["documents"][0], results["metadatas"][0]
    text, meta = random.choice(list(zip(docs, metas)))
    src = f"{meta.get('source_type', 'unknown')} → {meta.get('filename', 'unknown')}"
    text = re.sub(r"Lecture\s*\d+.*?:", "", text)
    text = re.sub(r"•|–|-|—", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip(), src


# ---------- Generate a balanced quiz ----------
def generate_quiz(mode="mixed", topic=None, num_questions=6):
    """Generate a balanced quiz with MCQ, True/False, and OpenEnded."""
    topic = topic or "network security"
    num_questions = max(3, min(int(num_questions), 15))

    types = ["MCQ", "TrueFalse", "OpenEnded"]
    quiz = []

    for i in range(num_questions):
        qtype = types[i % len(types)]
        context, src = get_context(topic)
        qdata = llama_generate_question(context, qtype)
        qdata["source"] = src
        quiz.append(qdata)

    return quiz
