# Interview Cheat Detection System 👀🚫

![Project Logo](https://via.placeholder.com/150) <!-- Add a logo or banner image here if you have one -->

Welcome to the **Interview Cheat Detection System**! This project is designed to monitor and detect suspicious behavior during online interviews or exams using **AI-powered gaze tracking** and **behavioral analysis**. Whether you're conducting remote interviews or online assessments, this tool ensures fairness and integrity by identifying potential cheating attempts.

---

## 🌟 Features

- **Real-Time Gaze Tracking**: Monitors the user's eye movements to detect suspicious patterns.
- **Cheating Detection**: Flags behaviors like looking away from the screen, rapid eye movements, or prolonged focus on specific areas.
- **AI-Powered Feedback**: Uses OpenAI's GPT models to provide nuanced feedback on user responses.
- **Speech-to-Text Integration**: Converts spoken answers into text for analysis.
- **Semantic Similarity Scoring**: Compares user answers with correct answers using advanced NLP techniques.
- **User-Friendly Interface**: Built with **Streamlit** for an intuitive and interactive experience.

---

## 🛠️ How It Works

1. **Gaze Tracking**: The system uses facial landmarks to track the user's gaze in real-time.
2. **Behavior Analysis**: It analyzes gaze patterns to detect suspicious behavior (e.g., looking away, rapid eye movements).
3. **Speech-to-Text**: Converts recorded audio responses into text for further analysis.
4. **AI Feedback**: Uses OpenAI's GPT models to evaluate the quality of user responses.
5. **Semantic Similarity**: Compares user answers with correct answers using cosine similarity and sentence embeddings.

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- [OpenAI API Key](https://platform.openai.com/signup/) (for AI feedback)
- [Google Speech Recognition](https://pypi.org/project/SpeechRecognition/) (for speech-to-text)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/interview-cheat-detection.git
   cd interview-cheat-detection
