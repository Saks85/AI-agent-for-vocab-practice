# Spanish Vocabulary Learning App 🇪🇸

An intelligent desktop application for learning Spanish vocabulary using spaced repetition and the Leitner system. The app adapts to your learning pace and automatically schedules review sessions based on your performance.

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📋 Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Project Architecture](#project-architecture)
- [Data Storage](#data-storage)
- [AI Decision Making](#ai-decision-making)
- [Learning Algorithm](#learning-algorithm)
- [Use Cases](#use-cases)
- [File Structure](#file-structure)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### 🧠 Intelligent Learning System
- **Adaptive Spaced Repetition**: Uses the Leitner system for optimal review timing
- **Session-Based Scheduling**: Reviews scheduled based on completed sessions, not time
- **Smart Word Selection**: AI chooses the most effective words for each session
- **Performance Tracking**: Detailed progress monitoring with mastery levels

### 🎯 User Experience
- **Clean GUI Interface**: Built with tkinter for cross-platform compatibility
- **Two Learning Modes**: 
  - New word learning (flashcard + quiz)
  - Review sessions (quiz only)
- **Visual Feedback**: Color-coded answers (green for correct, red for incorrect)
- **Progress Statistics**: Comprehensive session summaries and overall progress

### 📊 Data Management
- **Persistent Progress**: All learning data saved locally in JSON format
- **Session Tracking**: Maintains session counter for scheduling
- **Flexible Vocabulary**: Supports CSV vocabulary datasets

## 🛠 Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Language** | Python 3.7+ | Core application logic |
| **GUI Framework** | Tkinter + ttk | Cross-platform desktop interface |
| **Data Storage** | JSON | Progress and session data persistence |
| **Vocabulary Data** | CSV | Vocabulary dataset format |
| **Styling** | ttk.Style | Modern GUI appearance |

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- No additional packages required (uses built-in libraries)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/spanish-vocab-app.git
   cd spanish-vocab-app
   ```

2. **Prepare vocabulary dataset**
   - Create or download `english_spanish.csv` file
   - Ensure it has columns: `english`, `spanish` (or similar variants)
   - Example format:
     ```csv
     english,spanish
     hello,hola
     goodbye,adiós
     thank you,gracias
     ```

3. **Run the application**
   ```bash
   python vocab_gui.py
   ```

## 🚀 Usage

### First Time Setup
1. Launch the application
2. The system will create initial progress files
3. Start with a learning session to begin building your vocabulary

### Daily Workflow
1. **Welcome Screen**: Shows session number and available options
2. **Choose Session Type**:
   - **Learning Session**: Introduction of new words + review
   - **Revision Session**: Focus on words due for review (appears automatically when needed)
3. **Complete Session**: Work through flashcards and quizzes
4. **Review Summary**: Check your performance and progress

## 🏗 Project Architecture

### Core Components

```
VocabularyGUI (Main Class)
├── Data Management
│   ├── load_data()           # Load vocabulary and progress
│   ├── save_progress()       # Persist learning data
│   └── session counter      # Track completed sessions
├── Learning Logic
│   ├── select_session_words() # AI word selection
│   ├── Leitner System       # Spaced repetition algorithm
│   └── Progress tracking    # Mastery and performance data
├── User Interface
│   ├── Welcome page         # Session selection
│   ├── Flashcard display    # Word introduction
│   ├── Quiz interface       # Multiple choice testing
│   └── Summary reports      # Performance feedback
└── Session Management
    ├── Learning sessions    # New words + mixed review
    └── Revision sessions    # Focused review of due words
```

## 💾 Data Storage

### File Structure
```
project_folder/
├── vocab_gui.py              # Main application
├── english_spanish.csv       # Vocabulary dataset
├── vocab_progress.json       # Learning progress data
└── session_counter.json      # Session tracking
```

### Progress Data Schema
```json
{
  "word": {
    "mastery": 0-10,           # Mastery level (0=new, 10=mastered)
    "attempts": 0,             # Total quiz attempts
    "correct": 0,              # Correct answers
    "box": 0-5,                # Leitner box level
    "last_reviewed_session": 0  # Last session this word was reviewed
  }
}
```

### Session Counter Schema
```json
{
  "session_counter": 0         # Total completed sessions
}
```

## 🤖 AI Decision Making

### Intelligent Session Planning

#### Learning Session Word Selection
The AI selects 10 words per session with this distribution:
- **3 New Words**: Never seen before (prioritized by word length)
- **4 Low Mastery**: Words with mastery 1-2 (struggling words)
- **2 Medium Mastery**: Words with mastery 3-6 (developing words)
- **1 High Mastery**: Words with mastery 7+ (30% probability for reinforcement)

#### Revision Session Triggers
- **Automatic Detection**: Analyzes due words every session
- **Minimum Threshold**: Requires ≥5 words due for review
- **Smart Scheduling**: Uses Leitner intervals based on performance:

| Leitner Box | Sessions Until Review | Use Case |
|-------------|----------------------|----------|
| Box 1 | 1 session | New/difficult words |
| Box 2 | 2 sessions | Recently learned |
| Box 3 | 4 sessions | Developing mastery |
| Box 4 | 7 sessions | Well-known words |
| Box 5 | 15 sessions | Mastered words |

#### Word Progression Logic
```python
# Correct Answer
mastery += 1 (max 10)
box = min(box + 1, 5)  # Move to next Leitner box

# Incorrect Answer  
mastery -= 1 (min 0)
box = max(box - 1, 1)  # Move back in Leitner system
```

## 🧮 Learning Algorithm

### Spaced Repetition Implementation

The app implements a **session-based Leitner system** instead of traditional time-based spacing:

1. **Session Tracking**: Each completed session increments the global counter
2. **Individual Scheduling**: Words are scheduled based on their Leitner box level
3. **Performance Adaptation**: Box progression depends on quiz performance
4. **Intelligent Mixing**: Learning sessions blend new words with strategic reviews

### Quiz Generation
- **4 Multiple Choice Options**: 1 correct + 3 random distractors
- **Smart Distractors**: Selected from the same vocabulary pool
- **Randomized Order**: Options shuffled to prevent pattern memorization
- **Immediate Feedback**: Visual confirmation with color coding

## 📱 Use Cases

### 🎓 Students
**Scenario**: High school student learning Spanish
- Start with 10-word daily sessions
- Focus on curriculum vocabulary
- Track progress for assignments
- Use revision sessions before exams

### 🌍 Travelers
**Scenario**: Planning a trip to Spain
- Learn essential travel vocabulary
- Practice common phrases and words
- Build confidence with spaced repetition
- Focus on practical, everyday words

### 🧠 Language Enthusiasts
**Scenario**: Adult learner pursuing Spanish fluency
- Systematic vocabulary building
- Long-term retention through spaced repetition
- Track learning progress over months
- Supplement formal language courses

### 👩‍🏫 Educators
**Scenario**: Spanish teacher managing classroom vocabulary
- Assign specific vocabulary sets
- Monitor student progress
- Create custom vocabulary lists
- Supplement classroom instruction

### 🏢 Professional Development
**Scenario**: Business professional working with Spanish clients
- Learn business-specific vocabulary
- Maintain language skills with regular practice
- Flexible session timing around work schedule
- Focus on professional communication terms

## 📁 File Structure

```
spanish-vocab-app/
│
├── vocab_gui.py                 # Main application file
├── english_spanish.csv          # Vocabulary dataset (user-provided)
├── vocab_progress.json          # Generated: Learning progress
├── session_counter.json         # Generated: Session tracking
├── README.md                    # This file
├── requirements.txt             # Python dependencies (if any)
└── assets/                      # Optional: Screenshots, icons
    ├── screenshot1.png
    └── app_icon.ico
```

## 🔧 Configuration

### Customizable Parameters
You can modify these constants in the code:

```python
# File paths
PROGRESS_FILE = "vocab_progress.json"
DATASET_FILE = "english_spanish.csv"
SESSION_COUNTER_FILE = "session_counter.json"

# Leitner system intervals (in sessions)
LEITNER_SCHEDULE = {
    1: 1,    # Review after 1 session
    2: 2,    # Review after 2 sessions  
    3: 4,    # Review after 4 sessions
    4: 7,    # Review after 7 sessions
    5: 15    # Review after 15 sessions
}
```

### Vocabulary Dataset Format
Supported CSV column names (case-insensitive):
- English: `english`, `English`, `ENG`, `en`, `EN`
- Spanish: `spanish`, `Spanish`, `ESP`, `es`, `ES`

## 🚨 Troubleshooting

### Common Issues

**Dataset not found**
```
Error: Dataset file 'english_spanish.csv' not found
Solution: Ensure CSV file is in the same directory as the app
```

**Empty vocabulary**
```
Error: No valid vocabulary pairs found
Solution: Check CSV format and ensure data is present
```

**Progress file corruption**
```
Error: Failed to load progress
Solution: Delete vocab_progress.json to reset (progress will be lost)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add comments for complex logic
- Test with different vocabulary sizes
- Ensure cross-platform compatibility

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the Leitner system for spaced repetition
- Built with Python's built-in tkinter for maximum compatibility
- Designed for effective vocabulary acquisition and retention

---

**Happy Learning! 🎉**

For questions or support, please open an issue on GitHub or contact [your-email@example.com](mailto:your-email@example.com).