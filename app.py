# ======================================================
#  Flask App – Network Security Tutor & Quiz Agent
# ======================================================

from flask import Flask, render_template, request
from app.qa_tutor_agent import ask
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
        if "📚 Sources:" in response:
            answer, sources = response.split("📚 Sources:", 1)
        else:
            answer, sources = response, "No sources available."

        # Debugging: Print the sources obtained from the QA tutor
        print("📚 Sources Obtained:", sources)
        # Separate the sources and print them in a different part of the app
        print("📚 Sources:")
        print(sources.strip())
        return render_template("tutor.html", question=question, answer=answer.strip(), sources=sources.strip())
    return render_template("tutor.html")


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
                result, pts = grade_answer(user, correct, context, question_text)
                total_score += pts
                results.append((i, user, correct, result, question_text))


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


