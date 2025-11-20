# ======================================================
#  Flask App – Network Security Tutor & Quiz Agent
# ======================================================

import json
from flask import Flask, Response, jsonify, render_template, request, stream_with_context
from app.qa_tutor_agent import ask, stream_answer
from app.quiz_agent import generate_quiz, grade_answer

app = Flask(__name__)


# ------------------------------------------------------
#  HOME PAGE
# ------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# ------------------------------------------------------
#  TUTOR AGENT
# ------------------------------------------------------
@app.route("/tutor", methods=["GET", "POST"])
def tutor():
    if request.method == "POST":
        question = request.form["question"]
        response = ask(question)
        if isinstance(response, dict):
            answer = response.get("answer", "")
            sources = response.get("sources", "")
            show_sources = response.get("show_sources", False)
        else:
            answer = str(response)
            sources = ""
            show_sources = False

        # Debugging: Print the sources obtained from the QA tutor
        print("📚 Sources Obtained:", sources)
        # Separate the sources and print them in a different part of the app
        print("📚 Sources:")
        print(sources.strip())
        return render_template(
            "tutor.html",
            question=question,
            answer=answer.strip(),
            sources=sources.strip(),
            show_sources=show_sources,
        )
    return render_template("tutor.html")


@app.route("/tutor/stream", methods=["POST"])
def tutor_stream():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    include_sources = data.get("include_sources", True)

    if not question:
        return jsonify({"error": "Question is required."}), 400

    def generate():
        try:
            for payload in stream_answer(question, include_sources=include_sources):
                yield json.dumps(payload) + "\n"
        except Exception as exc:
            error_payload = {"type": "error", "text": f"⚠️ Streaming error: {exc}"}
            yield json.dumps(error_payload) + "\n"

    return Response(stream_with_context(generate()), mimetype="text/plain")


# ------------------------------------------------------
#  QUIZ AGENT
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if request.method == "POST":
        # CASE 1 – User submitted answers for grading
        if "answer_1" in request.form:  
            user_answers = request.form
            num_q = int(user_answers.get("num_questions", 5))
            total_score = 0
            results = []

            for i in range(1, num_q + 1):
                user = user_answers.get(f"answer_{i}", "").strip()
                correct = user_answers.get(f"correct_{i}", "")
                context = user_answers.get(f"context_{i}", "")
                question_text = user_answers.get(f"question_text_{i}", "")
                source = user_answers.get(f"source_{i}", "")
                result, pts = grade_answer(user, correct, context, question_text)
                total_score += pts
                results.append((i, user, correct, result, question_text, context, source))


            return render_template("quiz.html", results=results, score=total_score)

        # CASE 2 – User clicked "Generate Quiz"
        mode = request.form.get("mode", "random")
        topic = request.form.get("topic", "network security")
        num_q = int(request.form.get("num_questions", 5))
        questions = generate_quiz(mode, topic, num_q)
        return render_template("quiz.html", questions=questions, mode=mode, topic=topic, num_questions=num_q)

    # CASE 3 – First visit, show configuration form only
    return render_template("quiz.html", questions=None, results=None)
    



if __name__ == "__main__":
    app.run(debug=True)
