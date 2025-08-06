# gemma3n-emotion-plugin
> AI-powered emotion analysis and support system built for Google's Gemma 3n Impact Challenge

[![Demo Video](https://img.shields.io/badge/Demo-Video-red)](https://youtu.be/3ZsAurYd5Is)

## 🎯 Project Overview
This web application **Google’s Gemma 3n LLM** to provide **nuanced and scientifically grounded emotional analysis**.  It translates natural language into **Plutchik-based emotion insights**, offering Emotion classification, Intensity analysis, Reasoning and Visualization. 

Beyond analysis, the app features a **real-time conversation companion**.  Users can chat with the AI like a supportive friend, receiving **empathetic and personalized responses** that make emotional self-reflection engaging and comforting.

## 🚀 Quick Start
```python
# Clone the repository
git clone https://github.com/YOUR_USERNAME/gemma3n-emotion-companion.git
cd gemma3n-emotion-companion

# Install dependencies
pip install -r requirements.txt

# Start the backend server
cd backend
python main.py

# Open your browser to http://localhost:8888
```
Usage
- Enter your feelings in natural language (e.g., "I'm excited about my job interview but worried I'll mess up")
- Get instant analysis - see your emotions mapped to Plutchik's framework
- Visualize emotions with interactive emotion wheels
- Chat with AI companion - get personalized emotional support

## 🏗️ System Architecture

**User Input**  
→ **Gemma 3n Analysis**  
→ **Plutchik Mapping**  
→ **Visualization**  
→ **AI Companion**

---

Natural Language → Emotion Vectors → 8D Scoring → Wheel Chart → Personalized Chat

---

## Core Components

- 🤖 **Emotion Analyzer**  
  Gemma 3n-powered natural language emotion analysis

- 📊 **Plutchik Mapper**  
  Scientific emotion classification and intensity scoring

- 🎨 **Visualization Engine**  
  Real-time emotion wheel generation with matplotlib

- 💬 **AI Companion**  
  Dynamic conversational roles tailored to individual users


## 📁 Project Structure
```pgsql
gemma3n-emotion-plugin/
├── backend/
│   ├── main.py                 # FastAPI server
│   ├── core/
│   │   ├── emotion_analyzer_enhanced.py
│   │   └── emotional_chat_function.py
│   ├── utils/
│   │   ├── dynamic_prompt_builder.py
│   │   ├── role_creator_builder.py
│   │   └── multi_plutchik_plotter.py
│   └── prompts/
│       └── emotion_analysis_config.json
├── frontend/
│   ├── index.html
│   └── style.css
├── requirements.txt
└── README.md
```

## 🤝 Reference:
Cameron, G., Sanseviero, O., Martins, G., Ballantyne, I., Black, K., Sherwood, M., Ferev, M., Zhu, R., Chauhan, N., Bhuwalka, P., Kosa, E., & Howard, A. (2025). Google - The Gemma 3n Impact Challenge. https://kaggle.com/competitions/google-gemma-3n-hackathon. https://kaggle.com/competitions/google-gemma-3n-hackathon
