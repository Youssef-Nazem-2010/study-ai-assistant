# --- 1. Import libraries ---
import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import time
import random
import json
import re

# --- 2. Setup App ---
st.set_page_config(page_title="🎓 Studying AI Assistant", layout="centered")
st.title('🎓 Studying AI Assistant')

subjects = ['Biology', 'Physics', 'Math', 'Chemistry', 'History', 'Geography', 'Combined Sciences', "Literature", 'General Culture']
details_options = ['Brief', 'Medium', 'Super Detailed']
tone_options = ['Friendly', 'Pro']
edu_level_options = ['Elementary', 'Junior', 'Senior']

# --- 3. Initialize session state ---
def init_session():
    defaults = {
        'quiz_count': 0,
        'show_answer': False,
        'current_card': None,
        'quiz_data': None,
        'start_timer': False,
        'score': 0,
        'submitted': {},
        'user_query': "",
        'start_pomodoro': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# --- 4. Voice Recognizer and TTS ---
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# --- 5. API Key Input ---
st.text('[Get your key from Google AI Studio]')
api_key = st.text_input('🔑 Enter your Gemini API key:', type='password')

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-8b')

# --- 6. Settings Rows ---
col1, col2 = st.columns(2)
subject = col1.selectbox('📖 Choose Subject:', subjects)
details = col2.selectbox('🔍 Level of Detailing:', details_options)

col3, col4 = st.columns(2)
tone = col3.selectbox('🗣️ Tone of Answer:', tone_options)
edu_level = col4.selectbox('🏫 Education Level:', edu_level_options)

# --- 7. Functions ---
def voice_input():
    with sr.Microphone() as source:
        st.write("🎤 Listening...")
        audio = recognizer.listen(source)
        try:
            query = recognizer.recognize_google(audio)
            st.success(f"✅ You said: {query}")
            return query
        except sr.UnknownValueError:
            st.error("❌ Could not understand. Try again.")
            return ""
        except sr.RequestError:
            st.error("❌ Speech recognition service unavailable.")
            return ""

def speak_text(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except:
        pass

def generate_quiz(subject, difficulty, edu_level):
    prompt = f"""
    Create 5 multiple-choice questions for a {edu_level} student studying {subject}.
    Difficulty should be {difficulty} and make the questions different every time.
    Format ONLY in this JSON:
    [
      {{
        "question": "Example question?",
        "choices": ["A", "B", "C"],
        "correct": "Correct answer"
      }},
      ...
    ]
    No extra text. Only JSON array.
    """
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        json_match = re.search(r'\[\s*{.*?}\s*\]', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            st.error("⚠️ Could not find valid JSON in the model response.")
            st.write("🔎 Raw Response:", response_text)
    except Exception as e:
        st.error("❌ Error generating quiz.")
        st.write("Details:", e)


def show_flashcards(subject):
    flashcards = {
        'Math': [("What is 2 + 2?", "4"), ("What is 5 * 3?", "15")],
        'Physics': [("What is Speed formula?", "Distance ÷ Time"), ("Gravity on Earth?", "9.8 m/s²")],
        'History': [("First US president?", "George Washington"), ("WW2 End Year?", "1945")],
        'Biology': [("What is DNA?", "Genetic Material"), ("Energy Organelle?", "Mitochondria")]
    }
    cards = flashcards.get(subject, [])
    if st.button("🎫 Show Flashcard"):
        if cards:
            st.session_state.current_card = random.choice(cards)
            st.session_state.show_answer = False
        else:
            st.warning(f"No flashcards available yet for **{subject}**.")

    if st.session_state.current_card:
        q, a = st.session_state.current_card
        st.write(f"🧐 **Question:** {q}")
        if not st.session_state.show_answer:
            if st.button("👀 Reveal Answer"):
                st.session_state.show_answer = True
        else:
            st.success(f"💡 Answer: {a}")

# --- 8. User Input Section ---
st.subheader("💬 Ask a Question")
input_method = st.radio("Select Input Method:", ['Text', 'Voice'])

if input_method == 'Text':
    st.session_state.user_query = st.text_area('✍️ Type your question here:', value=st.session_state.user_query)
else:
    if st.button('🎙️ Record Voice'):
        st.session_state.user_query = voice_input()

if st.button('Answer 👇'):
    if not api_key:
        st.warning("🔑 Please enter your API key first.")
    elif not st.session_state.user_query.strip():
        st.warning("💬 Please provide a question first.")
    else:
        prompt = f"""
        You are a {tone.lower()} AI tutor helping a {edu_level} student with {subject}.
        Provide a {details.lower()} explanation to this question in the same Language:
        {st.session_state.user_query}
        """
        try:
            response = model.generate_content(prompt)
            st.success(response.text)
            speak_text(response.text)
        except Exception as e:
            st.error("❌ Error generating answer.")
            st.write("Details:", e)

# --- 9. Extra Study Tools ---
st.divider()
st.header("✨ More Study Tools")

col5, col6, col7 = st.columns(3)

with col5:
    if st.button('📚 Start Quiz'):
        if not api_key:
            st.warning("🔑 Please enter your API key first.")
        else:
            with st.spinner('⏳ Generating Quiz...'):
                st.session_state.quiz_data = generate_quiz(subject, 'Medium', edu_level)
                if st.session_state.quiz_data:
                    st.success("🎉 Quiz Ready!")
                    st.session_state.start_timer = True
                    st.session_state.score = 0
                    st.session_state.submitted = {}
                    st.session_state.quiz_start_time = time.time()
                    st.session_state.quiz_count += 1
                else:
                    st.error("❌ Could not generate quiz.")

with col6:
    show_flashcards(subject)

with col7:
    if st.button('🍅 Start Pomodoro'):
        st.session_state.start_pomodoro = True

# --- Pomodoro Functions ---
def run_timer(minutes, label):
    countdown = minutes * 60
    timer_placeholder = st.empty()
    st.subheader(f"{label} ({minutes} min)")
    for remaining in range(countdown, 0, -1):
        mins, secs = divmod(remaining, 60)
        timer_placeholder.markdown(f"⏳ **{label}** remained: {mins:02d}:{secs:02d}")
        time.sleep(1)
    timer_placeholder.markdown(f"✅ **{label} Done!**")

def start_pomodoro_cycle(work_minutes=25, break_minutes=5, total_hours=1):
    total_minutes = total_hours * 60
    cycle_duration = work_minutes + break_minutes
    max_cycles = total_minutes // cycle_duration

    cycle = 1
    while cycle <= max_cycles:
        st.info(f"🔁 Starting Cycle {cycle} of {max_cycles}")
        run_timer(work_minutes, "🍅 Work Time")
        st.balloons( run_timer(break_minutes, "☕ Break Time"))

        if cycle < max_cycles:
            cont = st.radio("Continue to next Pomodoro?", ["Yes", "Stop"], key=f"pomodoro_{cycle}_{int(time.time())}")
            if cont == "Stop":
                st.success("✅ Pomodoro session ended.")
                break
        else:
            st.success("✅ All Pomodoro cycles completed.")
        cycle += 1

# --- Streamlit App UI ---
st.title("Pomodoro Timer")

# Slider to choose hours
pomodoro_hours = st.slider("⏱️ How many hours do you want to study?", 1, 8, 2)

if "start_pomodoro" not in st.session_state:
    st.session_state.start_pomodoro = False

if st.session_state.start_pomodoro:
    start_pomodoro_cycle(total_hours=pomodoro_hours)
    st.session_state.start_pomodoro = False

# --- 10. Quiz Display ---
if st.session_state.quiz_data:
    elapsed = int(time.time() - st.session_state.quiz_start_time)
    remaining = max(0, 300 - elapsed)
    m, s = divmod(remaining, 60)
    st.markdown(f"## ⏳ Time Left: {m:02d}:{s:02d}")

    if remaining == 0:
        st.error("⏰ Time's up!")
        st.session_state.quiz_data = None
        st.stop()

    st.header("📝 Your Quiz")
    for idx, item in enumerate(st.session_state.quiz_data):
        st.subheader(f"Q{idx+1}: {item['question']}")
        answer = st.radio(f"Answer for Q{idx+1}:", item['choices'], key=f"quiz_q{idx}")
        if st.button(f"✅ Submit Answer {idx+1}", key=f"submit_q{idx}"):
            if idx not in st.session_state.submitted:
                correct = item['correct']
                if answer == correct:
                    st.success("✅ Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"❌ Wrong. Correct Answer: {correct}")
                st.session_state.submitted[idx] = True

    if len(st.session_state.submitted) == len(st.session_state.quiz_data):
        st.success(f"🏆 Final Score: {st.session_state.score} / {len(st.session_state.quiz_data)}")

# --- 11. Sidebar Progress ---
st.sidebar.header("📊 Progress Tracker")
st.sidebar.write(f"Quizzes Taken: {st.session_state.quiz_count}")
