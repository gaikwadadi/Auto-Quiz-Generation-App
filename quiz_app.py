import os
import sys
import json
import random
from difflib import SequenceMatcher
import streamlit as st
import google.generativeai as genai

# ------------------ UTF-8 Encoding ------------------ #
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# ------------------ PROMPT CREATION ------------------ #
def create_quiz_prompt_json(num_questions, quiz_type, quiz_context):
    """
    Generate a prompt for Google Gemini that returns quiz in JSON format.
    JSON format ensures robust parsing.
    """
    return f"""
You are an expert quiz creator. Generate {num_questions} {quiz_type} questions
about the following topic: "{quiz_context}".

Output ONLY a valid JSON with keys:
{{
  "questions": [
    {{
      "text": "Question text",
      "options": ["Option1", "Option2", "Option3", "Option4"]  # Only for multiple-choice
    }},
    ...
  ],
  "answers": ["a","b","c", ...]  # Use letters for MCQ, True/False, or full answer for open-ended
}}

IMPORTANT:
- No extra text outside JSON.
- MCQ answers must be lowercase letters.
- True/False answers must be exactly "True" or "False".
- Open-ended answers: string only.
"""

# ------------------ GEMINI QUIZ GENERATION ------------------ #
def generate_quiz_with_gemini(api_key, num_questions, quiz_type, quiz_context, retries=2):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = create_quiz_prompt_json(num_questions, quiz_type, quiz_context)

    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            raw_text = response.text.strip()

            # Extract JSON block from any extra text
            import re
            match = re.search(r'\{.*\}', raw_text, flags=re.DOTALL)
            if not match:
                st.warning("Could not find JSON in the model output. Retrying...")
                continue

            quiz_json = match.group(0)
            data = json.loads(quiz_json)

            # Validate structure
            if "questions" not in data or "answers" not in data:
                st.warning("JSON missing 'questions' or 'answers'. Retrying...")
                continue

            # Ensure all questions have text and MCQ options if needed
            for q in data["questions"]:
                if "text" not in q:
                    raise ValueError("A question is missing 'text'")
                if quiz_type == "multiple-choice" and "options" not in q:
                    raise ValueError("MCQ question missing 'options'")

            return data

        except Exception as e:
            if attempt == retries - 1:
                st.error(f"Failed to generate quiz: {e}")
                st.expander("Raw API Response").write(response.text if 'response' in locals() else "")
                return None

# ------------------ ANSWER NORMALIZATION ------------------ #
def normalize_answer(ans):
    if not ans:
        return ""
    ans = ans.strip()
    if len(ans) > 0 and ans[0].lower() in [chr(i) for i in range(97, 123)]:  # a-z
        return ans[0].lower()
    return ans.lower()

def fuzzy_match(ans1, ans2):
    return SequenceMatcher(None, ans1.lower(), ans2.lower()).ratio() > 0.8

# ------------------ FORMAT QUIZ FOR EXPORT ------------------ #
def format_quiz_as_text(questions, answers):
    lines = []
    for idx, q in enumerate(questions, 1):
        lines.append(f"Q{idx}. {q['text']}")
        if "options" in q:
            for opt_idx, opt in enumerate(q["options"]):
                letter = chr(97 + opt_idx)  # a, b, c, ...
                lines.append(f"{letter}. {opt}")
        lines.append(f"Answer: {answers[str(idx)] if str(idx) in answers else 'N/A'}")
        lines.append("")
    return "\n".join(lines)

# ------------------ STREAMLIT APP ------------------ #
def main():
    st.title("Quiz Generator App 📝")
    st.write("Generate quizzes (MCQ, True/False, Open-ended) from any concept using Google Gemini.")

    # Sidebar: API key input
    google_api_key = st.sidebar.text_input("Enter your Google Gemini API key", type="password")
    if not google_api_key:
        st.warning("Please enter your API key in the sidebar to continue.")
        return

    # User inputs
    context = st.text_area("Enter the concept/context for the quiz")
    num_questions = st.number_input("Number of questions", min_value=1, max_value=30, value=3)
    quiz_type = st.selectbox("Select quiz type", ["multiple-choice", "true-false", "open-ended"])

    # Generate quiz
    if st.button("Generate Quiz"):
        data = generate_quiz_with_gemini(google_api_key, num_questions, quiz_type, context)
        if not data:
            return

        structured_questions = data["questions"]
        structured_answers = {str(i + 1): ans for i, ans in enumerate(data["answers"])}

        # Shuffle MCQ options
        if quiz_type == "multiple-choice":
            for q in structured_questions:
                paired = list(zip([chr(97+i) for i in range(len(q["options"]))], q["options"]))
                random.shuffle(paired)
                letters, options = zip(*paired)
                q["options"] = options
                # Update correct answer mapping
                original_letter = structured_answers[str(structured_questions.index(q)+1)]
                for new_letter, option_text in zip(letters, options):
                    if option_text == q["options"][ord(original_letter)-97]:
                        structured_answers[str(structured_questions.index(q)+1)] = new_letter

        st.session_state.update({
            "structured_questions": structured_questions,
            "correct_answers": structured_answers,
            "quiz_type": quiz_type,
            "user_answers": {}
        })
        st.success("Quiz generated! Scroll down to attempt it.")

    # Render quiz
    if "structured_questions" in st.session_state:
        st.subheader("Quiz Questions")
        user_answers = {}
        for idx, q in enumerate(st.session_state["structured_questions"], 1):
            st.write(f"Q{idx}. {q['text']}")
            if st.session_state["quiz_type"] == "multiple-choice":
                options = ["--Select--"] + [f"{chr(97+i)}. {opt}" for i, opt in enumerate(q["options"])]
                pick = st.radio("Choose one:", options, key=f"q{idx}")
                user_answers[str(idx)] = None if pick == "--Select--" else pick[0].lower()
            elif st.session_state["quiz_type"] == "true-false":
                pick = st.radio("Choose:", ["--Select--", "True", "False"], key=f"q{idx}")
                user_answers[str(idx)] = pick if pick != "--Select--" else None
            elif st.session_state["quiz_type"] == "open-ended":
                answer = st.text_area("Your answer:", key=f"q{idx}")
                user_answers[str(idx)] = answer

        st.session_state["user_answers"] = user_answers

        if st.button("Reset Quiz"):
            st.session_state.clear()
            st.experimental_rerun()

    # Check answers
    if st.button("Check Answers") and "correct_answers" in st.session_state:
        st.subheader("Results ✅")
        score = 0
        total = len(st.session_state["correct_answers"])
        for q_num, correct in st.session_state["correct_answers"].items():
            user_ans = st.session_state["user_answers"].get(q_num)
            is_correct = False
            if st.session_state["quiz_type"] == "open-ended":
                if user_ans and fuzzy_match(user_ans, correct):
                    is_correct = True
            else:
                if normalize_answer(user_ans) == normalize_answer(correct):
                    is_correct = True
            if is_correct:
                score += 1
                st.write(f"Q{q_num}: ✅ Correct (Your: {user_ans})")
            else:
                st.write(f"Q{q_num}: ❌ Incorrect (Your: {user_ans} | Correct: {correct})")
        st.success(f"Your score: {score}/{total}")

    # Export quiz
    if "structured_questions" in st.session_state:
        st.subheader("Export Options")
        quiz_text = format_quiz_as_text(st.session_state["structured_questions"], st.session_state["correct_answers"])
        st.download_button("📥 Download Quiz", quiz_text, "quiz.txt", "text/plain")


if __name__ == "__main__":
    main()
