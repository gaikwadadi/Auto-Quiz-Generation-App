import os
import sys
import re
import streamlit as st
import google.generativeai as genai

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


# ------------------ PROMPT CREATION ------------------ #
def create_the_quiz_prompt(num_questions, quiz_type, quiz_context):
    return f"""
    You are an expert quiz maker for technical fields. Let's think step by step and
    create a quiz with {num_questions} {quiz_type} questions about the following concept/content: {quiz_context}.

    Strictly follow this output format:
    - Questions:
        <Q1 text> : <a. Option1>, <b. Option2>, <c. Option3>, <d. Option4>   (for multiple-choice)
        <Q1 text> : <True|False>                                            (for true-false)
        <Q1 text>                                                           (for open-ended)
        ...
    - Answers:
        1. <correct option/True/False/correct answer>
        2. <correct option/True/False/correct answer>
        ...
    """


# ------------------ QUIZ GENERATION ------------------ #
def generate_quiz_with_gemini(google_api_key, num_questions, quiz_type, quiz_context):
    genai.configure(api_key=google_api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = create_the_quiz_prompt(num_questions, quiz_type, quiz_context)
    response = model.generate_content(prompt)
    return response.text


# ------------------ HELPERS: CLEANERS/PARSERS ------------------ #
def clean_question_text(q_text: str, quiz_type: str) -> str:
    s = q_text.strip()
    if quiz_type == "true-false":
        # Remove suffix like ": True|False" or " - True/False"
        s = re.sub(r'\s*[:\-]\s*(true\s*[\|/]\s*false|false\s*[\|/]\s*true)\s*$', '', s, flags=re.I)
    return s.strip()

def parse_tf_answer(a: str) -> str:
    s = a.strip()
    # Drop leading numbering and "Answer:" prefix
    s = re.sub(r'^\s*(\d+[\.\)]\s*)?(answer\s*:\s*)?', '', s, flags=re.I)
    m = re.search(r'\b(true|false)\b', s, flags=re.I)
    return m.group(1).capitalize() if m else s.strip().capitalize()

def parse_open_answer(a: str) -> str:
    s = a.strip()
    s = re.sub(r'^\s*(\d+[\.\)]\s*)?(answer\s*:\s*)?', '', s, flags=re.I)
    return s.strip()


# ------------------ QUIZ PARSER ------------------ #
def split_questions_answers(quiz_response, quiz_type):
    parts = quiz_response.split("- Answers:")
    if len(parts) < 2:
        return [], {}

    questions_raw = [q.strip() for q in parts[0].split("\n") if q.strip() and not q.strip().startswith("- Questions")]
    answers_raw = [a.strip() for a in parts[1].split("\n") if a.strip()]

    structured_questions = []
    structured_answers = {}

    if quiz_type == "multiple-choice":
        for q in questions_raw:
            if ":" in q:
                q_text, q_options = q.split(":", 1)
                q_text = clean_question_text(q_text, quiz_type)
                options = [opt.strip() for opt in q_options.split(",") if opt.strip()]
                structured_questions.append({"question": q_text, "options": options})
        for a in answers_raw:
            if "." in a:
                q_num, correct = a.split(".", 1)
                structured_answers[q_num.strip()] = correct.strip()
            else:
                # fallback: sequential mapping if no numbering
                idx = str(len(structured_answers) + 1)
                structured_answers[idx] = a.strip()

    elif quiz_type == "true-false":
        for q in questions_raw:
            structured_questions.append({"question": clean_question_text(q, quiz_type)})
        for a in answers_raw:
            idx = str(len(structured_answers) + 1)
            structured_answers[idx] = parse_tf_answer(a)

    elif quiz_type == "open-ended":
        for q in questions_raw:
            structured_questions.append({"question": clean_question_text(q, quiz_type)})
        for a in answers_raw:
            idx = str(len(structured_answers) + 1)
            structured_answers[idx] = parse_open_answer(a)

    return structured_questions, structured_answers


# ------------------ ANSWER NORMALIZATION ------------------ #
def normalize_answer(ans):
    if not ans:
        return ""
    ans = ans.strip()
    # If multiple choice, keep only option letter
    if len(ans) > 0 and ans[0].lower() in ["a", "b", "c", "d"]:
        return ans[0].lower()
    # true/false or open text
    return ans.lower()


# ------------------ FORMAT QUIZ TO TEXT ------------------ #
def format_quiz_as_text(structured_questions, structured_answers):
    lines = []
    for idx, q in enumerate(structured_questions, 1):
        q_text = q["question"]
        if q_text and q_text[0].isdigit():
            lines.append(q_text)
        else:
            lines.append(f"Q{idx}. {q_text}")

        if "options" in q:  # MCQ options
            for opt in q["options"]:
                lines.append(opt)

        answer = structured_answers.get(str(idx), "N/A")
        lines.append(f"Answer: {answer}")
        lines.append("")  # blank line between questions
    return "\n".join(lines)


# ------------------ STREAMLIT APP ------------------ #
def main():
    st.title("Quiz Generator App 📝")
    st.write("Generate quizzes (MCQ, True/False, Open-ended) from any concept using Google Gemini.")

    # API key
    google_api_key = st.sidebar.text_input("Enter your Google Gemini API key", type="password")
    if google_api_key == "":
        st.error("Please enter your Google Gemini API key")
        return

    # User inputs
    context = st.text_area("Enter the concept/context for the quiz")
    num_questions = st.number_input("Enter the number of questions", min_value=1, max_value=10, value=3)
    quiz_type = st.selectbox("Select the quiz type", ["multiple-choice", "true-false", "open-ended"])

    # Generate Quiz
    if st.button("Generate Quiz"):
        quiz_response = generate_quiz_with_gemini(google_api_key, num_questions, quiz_type, context)
        structured_questions, structured_answers = split_questions_answers(quiz_response, quiz_type)

        if not structured_questions:
            st.error("Failed to generate quiz. Try again with a different prompt.")
            return

        st.session_state["structured_questions"] = structured_questions
        st.session_state["correct_answers"] = structured_answers
        st.session_state["quiz_type"] = quiz_type
        st.session_state["user_answers"] = {}

        st.success("Quiz generated! Scroll down to attempt it.")

    # Display Quiz
    if "structured_questions" in st.session_state:
        st.subheader("Quiz Questions")
        user_answers = {}

        for idx, q in enumerate(st.session_state["structured_questions"], 1):
            q_text = q["question"]

            # Avoid double numbering if Gemini already added it
            if q_text and q_text[0].isdigit():
                st.write(q_text)
            else:
                st.write(f"Q{idx}. {q_text}")

            if st.session_state["quiz_type"] == "multiple-choice":
                user_answer = st.radio("Choose one:", q["options"], key=f"q{idx}")
                user_answers[str(idx)] = user_answer

            elif st.session_state["quiz_type"] == "true-false":
                user_answer = st.radio("Choose:", ["True", "False"], key=f"q{idx}")
                user_answers[str(idx)] = user_answer

            elif st.session_state["quiz_type"] == "open-ended":
                user_answer = st.text_area("Your answer:", key=f"q{idx}")
                user_answers[str(idx)] = user_answer

        st.session_state["user_answers"] = user_answers

    # Check Answers
    if st.button("Check Answers") and "correct_answers" in st.session_state:
        st.subheader("Results ✅")
        score = 0
        total = len(st.session_state["correct_answers"])

        for q_num, correct in st.session_state["correct_answers"].items():
            user_ans = st.session_state["user_answers"].get(q_num, None)
            if normalize_answer(user_ans) == normalize_answer(correct):
                score += 1
                st.write(f"Q{q_num}: ✅ Correct (Your: {user_ans})")
            else:
                st.write(f"Q{q_num}: ❌ Incorrect (Your: {user_ans} | Correct: {correct})")

        st.success(f"Your score: {score}/{total}")

    # Download Option (formatted quiz text)
    if "structured_questions" in st.session_state:
        st.subheader("Export Options")
        quiz_text = format_quiz_as_text(
            st.session_state["structured_questions"],
            st.session_state["correct_answers"]
        )
        st.download_button("📥 Download Quiz", quiz_text, "quiz.txt", "text/plain")


if __name__ == "__main__":
    main()
