import streamlit as st
from audio_recorder_streamlit import audio_recorder
import os
import json
import speech_recognition as sr
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Create the recordings directory if it doesn't exist
if not os.path.exists("recordings"):
    os.makedirs("recordings")

# Load questions and answers from a JSON file
def load_questions():
    with open("questions.json", "r") as f:
        return json.load(f)

# Convert speech to text
def speech_to_text(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError:
        return "Could not request results"

# Calculate semantic similarity between two sentences
def calculate_similarity(user_answer, correct_answer):
    # Load a pre-trained sentence transformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Encode the sentences into embeddings
    embeddings = model.encode([user_answer, correct_answer])

    # Calculate cosine similarity between the embeddings
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    return similarity

# Save user data to Excel
def save_to_excel(user_name, user_answers, ratings, feedbacks, final_rating):
    # Create a dictionary to store the data
    data = {
        "Name": [user_name],
        "Voice Text": [" | ".join(user_answers)],  # Combine all answers into a single string
        "Feedback": [" | ".join(feedbacks)],  # Combine all feedbacks into a single string
        "Rating": [final_rating]
    }

    # Convert the dictionary to a DataFrame
    df = pd.DataFrame(data)

    # Save to Excel
    if not os.path.exists("user_responses.xlsx"):
        df.to_excel("user_responses.xlsx", index=False)
    else:
        # Append to the existing Excel file
        existing_df = pd.read_excel("user_responses.xlsx")
        updated_df = pd.concat([existing_df, df], ignore_index=True)
        updated_df.to_excel("user_responses.xlsx", index=False)

# Streamlit app
def main():
    st.title("Online Interview App")
    st.write("Answer the following questions by recording your responses.")

    # Load questions
    questions = load_questions()

    # Initialize session state to keep track of the current question
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0

    # Ask each question and record the response
    user_name = st.text_input("Enter your name:")
    ratings = []
    feedbacks = []
    user_answers = []

    if user_name:
        if st.session_state.current_question < len(questions):
            qa = questions[st.session_state.current_question]

            # Display the question in a beautiful frame
            st.markdown(
                f"""
                <div style="border: 2px solid #4CAF50; border-radius: 5px; padding: 10px; margin: 10px 0;">
                    <h3>Question {st.session_state.current_question + 1}</h3>
                    <p>{qa["question"]}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Record audio for the current question
            audio_bytes = audio_recorder(text=f"Record Answer for Q{st.session_state.current_question + 1}", pause_threshold=2.0)

            # If audio is recorded, save it and display it
            if audio_bytes:
                # Save the recording to a file
                filename = f"recordings/record_q{st.session_state.current_question + 1}.wav"
                with open(filename, "wb") as f:
                    f.write(audio_bytes)

                st.write(f"Recording saved as {filename}")
                st.audio(audio_bytes, format="audio/wav")

                # Convert speech to text
                user_answer = speech_to_text(filename)
                st.write(f"Your answer: {user_answer}")
                user_answers.append(user_answer)  # Store the user's answer

                # Calculate semantic similarity
                similarity_score = calculate_similarity(user_answer, qa["answer"])
                st.write(f"Similarity Score: {similarity_score:.2f}")

                # Rate the answer based on similarity
                if similarity_score >= 0.8:
                    rating = 10
                    feedback = "Excellent answer!"
                elif similarity_score >= 0.6:
                    rating = 8
                    feedback = "Good answer, but could be improved."
                elif similarity_score >= 0.4:
                    rating = 6
                    feedback = "Partially correct, but missing key points."
                else:
                    rating = 4
                    feedback = "Incorrect answer."

                st.write(f"Rating: {rating}/10")
                st.write(f"Feedback: {feedback}")

                # Save rating and feedback
                ratings.append(rating)
                feedbacks.append(feedback)

                # Add a button to move to the next question
                if st.button("Next Question"):
                    st.session_state.current_question += 1
                    st.rerun()  # Use st.rerun() instead of st.experimental_rerun()

        else:
            # Calculate final rating
            if ratings:
                final_rating = sum(ratings) / len(ratings)
                st.write(f"Your final rating is: {final_rating}/10")

                # Save all data to Excel
                save_to_excel(user_name, user_answers, ratings, feedbacks, final_rating)
                st.success("Your responses have been saved successfully!")

if __name__ == "__main__":
    main()