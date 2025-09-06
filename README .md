# 📘 Quiz Generator App

A Streamlit-based web application that uses **Google Gemini AI** to
generate quizzes (MCQ, True/False, Open-ended) from any concept.

## 🚀 Features

-   Generate quizzes instantly using Google Gemini API.\
-   Supports:
    -   Multiple-choice (MCQ)\
    -   True/False\
    -   Open-ended questions\
-   Shuffle MCQ options for fairness.\
-   Intelligent **fuzzy matching** for open-ended answers.\
-   Export quiz to a `.txt` file.\
-   Reset quiz and retake anytime.

------------------------------------------------------------------------

## 📂 Project Structure

    .
    ├── quiz_app.py          # Main Streamlit app
    ├── requirements.txt     # Dependencies
    └── README.md            # Documentation

------------------------------------------------------------------------

## 🛠️ Installation

### 1. Clone the repository

``` bash
git clone https://github.com/yourusername/quiz-generator.git
cd quiz-generator
```

### 2. Create virtual environment (recommended)

``` bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## 🔑 Setup API Key

This project requires a **Google Gemini API key**.

1.  Get your key from: [Google AI
    Studio](https://aistudio.google.com/app/apikey)\
2.  In the app sidebar, enter your API key when prompted.

*(Optional)*: To avoid typing it each time, create a `.env` file and
load it automatically:

``` env
GOOGLE_API_KEY=your_api_key_here
```

------------------------------------------------------------------------

## ▶️ Run the App

``` bash
streamlit run quiz_app.py
```

-   The app will open in your browser (default:
    <http://localhost:8501>).\
-   Enter a concept, number of questions, and quiz type → then generate
    your quiz!

------------------------------------------------------------------------

## 📤 Export Quiz

-   After generating a quiz, scroll down to **Export Options**.\
-   Click **📥 Download Quiz** to save it as a text file.

------------------------------------------------------------------------

## 📸 Screenshots

*(Add your own screenshots here!)*

------------------------------------------------------------------------

## ⚙️ Requirements

See [`requirements.txt`](requirements.txt):

    streamlit>=1.35.0
    google-generativeai>=0.7.0

------------------------------------------------------------------------

## 🙌 Contributing

Pull requests are welcome! If you'd like to add features (e.g., CSV
export, timed quizzes), feel free to open an issue.

------------------------------------------------------------------------

## 📜 License

MIT License -- feel free to use and modify.
