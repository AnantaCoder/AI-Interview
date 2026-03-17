import streamlit as st
import subprocess
import sys
import nlp

st.set_page_config(page_title="Interview Cheat Detection", page_icon="👀", layout="wide")

def main():
    st.sidebar.title("Navigation 👀🚫")
    st.sidebar.write("Welcome to the Interview Cheat Detection System.")
    page = st.sidebar.radio("Go to:", ["Audio Interview (NLP)", "Vision Settings & Launch"])

    if page == "Audio Interview (NLP)":
        # Run the Streamlit app defined in nlp.py
        nlp.main()

    elif page == "Vision Settings & Launch":
        st.title("Real-Time Gaze & Cheat Tracking 📸")
        st.write("This module monitors eye movements and detects suspicious behavior like looking away from the screen.")
        st.write("Because it requires real-time video processing, it runs in a dedicated native window.")
        
        if st.button("Launch Anti-Cheating Webcam Monitor", type="primary"):
            # Launch computer_vision.py in the background using the current Python environment
            subprocess.Popen([sys.executable, "computer_vision.py"])
            st.success("Webcam monitor launched! Please look for the newly opened Video window.")
            st.info("Tip: Press **'q'** inside the video window to close it when you are done.")

if __name__ == "__main__":
    main()
