# ⚔️ StudyBuddy: Level Up

### Gamified AI Study Planner powered by Local AI, Ollama & Gemma

StudyBuddy is a **gamified study planner and AI learning companion** designed to make studying feel less like a boring checklist and more like an RPG progression system.

Instead of simply asking students to complete tasks, StudyBuddy turns studying into a system of:

**Quests → XP → Levels → Ranks → Achievements → New Abilities**

The application combines study planning, AI assistance, revision, focus sessions, quizzes, progress tracking, and an anime-inspired hunter interface in one local-first application.

---

## 🎯 Why StudyBuddy?

Students often know **what** they need to study but struggle with:

- Procrastination
- Staying consistent
- Organizing multiple subjects
- Revising regularly
- Maintaining motivation
- Knowing what to study next
- Turning study progress into something measurable

StudyBuddy addresses these problems by turning study activity into a progression system.

Every completed mission contributes to your progression, while AI tools help you plan, understand, practice, and stay focused.

---

# ✨ Main Features

## 🏠 Hunter Dashboard

The main dashboard provides a quick overview of your study progression.

It shows:

- Current level
- XP
- Hunter rank
- Study streak
- Completed quests
- Focus activity
- Progress information
- Recent achievements
- Level-up events

The dashboard acts as the central control panel for your study journey.

---

## 📅 Quest Schedule

Create and manage study missions.

Each quest can contain:

- Title
- Subject
- Due date
- Study duration
- Difficulty
- XP reward
- Completion status

Completing quests awards XP and contributes to your study progression.

The system can also apply configurable penalties for missed quests.

---

## 🤖 AI System Assistant

StudyBuddy includes a local AI assistant powered through **Ollama**.

The AI System Assistant can:

### Generate Today's Quests

Tell the AI:

- What subjects you need to study
- Your available study time
- Your preferred workload

The AI generates suggested study missions that can then be added to the Quest Schedule.

### Shadow Mentor

Use the local AI as a study mentor.

The mentor can:

- Help plan your study
- Suggest practical next steps
- Explain concepts
- Coach your progress
- Help with study discipline

The AI does not directly award XP or modify the progression system.

---

# ✨ Gemma Study Lab

One of the main AI features of StudyBuddy is the **Gemma Study Lab**.

StudyBuddy detects installed Gemma models through your local Ollama server.

The Gemma Study Lab allows users to:

- Detect installed Gemma models
- Run learning tasks using Gemma
- Test Gemma locally
- Compare Gemma output with another installed Ollama model
- Compare response timing
- Experiment with different local AI models

The project currently provides an option to install:

```bash
ollama pull gemma3:1b
```

Gemma runs locally through Ollama, so no Google API key is required for this local workflow.

---

# 👥 Shadow Army

StudyBuddy turns AI study companions into RPG-style shadow soldiers.

Shadow characters are unlocked as the player's level increases.

Current companions include:

- ⚔️ **Igris** — Discipline Protocol
- 🐻 **Tank** — Memory Guard
- 🛡️ **Iron** — Focus Shield
- 🔮 **Tusk** — Knowledge Spell
- 👑 **Beru** — Royal Tutor

Each companion has its own personality and learning role.

For example:

**Igris** focuses on discipline and breaking large goals into manageable missions.

**Tank** focuses on memory techniques and recall.

**Iron** helps overcome distractions and procrastination.

**Tusk** creates practice questions and explains difficult concepts.

**Beru** acts as an enthusiastic personal tutor.

---

# 🏰 Dungeon Battles

StudyBuddy includes RPG-style quiz battles.

Choose:

- Subject
- Difficulty
- Number of questions
- Dungeon boss

The player answers multiple-choice questions and fights the knowledge boss.

Correct answers contribute toward defeating the boss.

Completing a dungeon can award additional XP, with bonuses for difficulty and perfect runs.

Available dungeon themes include:

- 🐉 Infernal Dragon
- 🛡️ Shadow Monarch's Guardian
- 🕷️ Abyssal Spider
- ❄️ Frost Titan

---

# ⏱️ Focus Room

StudyBuddy includes a dedicated focus timer.

Available study modes include:

- Quick Focus — 15 minutes
- Classic Pomodoro — 25 minutes
- Deep Work — 50 minutes
- Long Session — 90 minutes

Completed focus sessions are stored locally and converted into progression XP.

---

# 🧠 Revision Lab

The Revision Lab provides a local flashcard system using spaced-review scheduling.

Users can:

- Create revision cards
- Review cards due today
- Rate cards as Again, Hard, Good, or Easy
- Track repetitions
- Track review intervals
- Schedule future reviews

This is designed to encourage repeated active recall instead of one-time memorization.

---

# 🏆 Achievements

StudyBuddy tracks milestones and unlocks achievements based on actual activity.

Examples include:

- First Awakening
- Quest Breaker
- Relentless Hunter
- Awakened
- Power Surge
- Seven-Day Shadow
- Focus Initiate
- Deep Focus
- Dungeon Runner
- Perfect Clear
- Memory Awakening
- S-Rank Scholar

Achievements are stored locally as permanent progress records.

---

# 📊 Hunter Report

The Hunter Report provides a weekly view of study activity.

It can show:

- Study effort
- Focus time
- Quest completion
- Dungeon activity
- Progress trends
- Areas requiring more attention
- Suggested training priorities

The report is based on the user's local StudyBuddy activity data.

---

# 🤝 Guild Hall

The Guild Hall provides a local study-party experience.

It includes:

- Guild name
- Guild motto
- Guild code
- Weekly XP goal
- Member list
- Weekly XP
- Focus minutes
- Local leaderboard

The current implementation is intentionally **local-first** and does not pretend to provide real-time cloud multiplayer.

---

# 📚 Important PDFs

StudyBuddy includes a local PDF library for storing important study material.

Users can upload:

- Notes
- Question papers
- Reference PDFs
- Study material

PDFs are stored locally and can be organized using:

- Display name
- Subject/category

The application also checks that an uploaded file is a readable PDF before storing it.

---

# 🧬 Character & Power

The player can customize their hunter profile.

Available character classes include:

- 🗡️ Shadow Hunter
- 🔮 Mage
- 🛡️ Knight
- 🏹 Archer

Character progression is connected to real study activity rather than combat.

---

# ⚙️ Settings

The settings section allows the user to customize their StudyBuddy profile and manage application behavior.

StudyBuddy also supports configurable missed-quest penalties.

---

# 🧩 Technology Stack

## Frontend / Application

- **Python**
- **Streamlit**
- HTML/CSS styling inside Streamlit

## AI

- **Ollama**
- **Gemma**
- Other locally installed Ollama models

## Data Storage

- **SQLite**
- Local filesystem storage

## PDF

- **pypdf**

## Python Standard Library

The project also uses Python's standard library for:

- JSON processing
- File management
- Hashing
- Dates and time
- Regular expressions
- Randomization
- HTTP communication
- Local application paths

---

# 🧠 How the AI Architecture Works

StudyBuddy uses a **local-first AI architecture**.

```text
                ┌────────────────────┐
                │    StudyBuddy UI   │
                │     Streamlit      │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │   StudyBuddy AI    │
                │   System Layer     │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │       Ollama       │
                │   Local AI Server  │
                └─────────┬──────────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
      ┌─────────────┐           ┌─────────────┐
      │    Gemma    │           │ Other Local │
      │    Models   │           │   Models    │
      └─────────────┘           └─────────────┘
```

This means the AI requests are sent to your **local Ollama server** instead of requiring a paid cloud API.

---

# 🔐 Local-First & Privacy

StudyBuddy is designed around local storage and local AI inference.

Study data is stored in:

```text
study_data/
```

The application uses a local SQLite database:

```text
study_data/studybuddy.db
```

The project does not require a cloud database for its core functionality.

The AI can also run locally through Ollama.

This makes StudyBuddy useful for students who want to experiment with AI without depending entirely on paid cloud APIs.

---

# 💻 Requirements

You need:

- Windows, Linux, or macOS
- Python
- Git
- Ollama
- An installed Ollama model
- Internet connection for downloading Ollama/models and loading remote web assets used by the interface

The application itself is designed to work with local AI once the required model has been downloaded.

---

# 🚀 Installation

## 1. Clone the repository

Open Command Prompt or PowerShell:

```bash
git clone https://github.com/shanaldo7/STUDYBUDDY-LEVEL-UP-gamified-study-planner.git
```

Enter the project:

```bash
cd STUDYBUDDY-LEVEL-UP-gamified-study-planner
```

---

## 2. Create a Python virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

You should now see something similar to:

```text
(venv) C:\...\STUDYBUDDY-LEVEL-UP-gamified-study-planner>
```

---

## 3. Install Python dependencies

Install Streamlit:

```bash
pip install streamlit
```

Install pypdf:

```bash
pip install pypdf
```

Or install both together:

```bash
pip install streamlit pypdf
```

---

# 🤖 Installing Ollama

Download and install Ollama from:

https://ollama.com/

After installation, verify it:

```bash
ollama --version
```

Then check whether the Ollama server is available:

```bash
ollama list
```

---

# 🧠 Install an AI model

StudyBuddy can use locally installed Ollama models.

For a lightweight general-purpose model:

```bash
ollama pull qwen2.5:0.5b
```

For the Gemma Study Lab:

```bash
ollama pull gemma3:1b
```

You can then verify your installed models:

```bash
ollama list
```

You should see your installed models in the list.

---

# ▶️ Start StudyBuddy

Make sure you are inside the project folder.

Activate the virtual environment:

```bash
venv\Scripts\activate
```

Then start Streamlit:

```bash
streamlit run app.py
```

Streamlit will normally open the application in your browser.

The local application will be available at:

```text
http://localhost:8501
```

---

# ✨ Using Gemma

After starting StudyBuddy:

1. Open the application.
2. Look at the sidebar.
3. Open **✨ Gemma Study Lab**.
4. StudyBuddy checks your locally installed Ollama models.
5. If Gemma is installed, select the available Gemma model.
6. Use the learning workflow.
7. Compare Gemma with your selected baseline model when the comparison option is available.

For a lightweight installation:

```bash
ollama pull gemma3:1b
```

---

# 🗂️ Project Structure

```text
StudyBuddy/
│
├── app.py
├── README.md
├── .gitignore
│
├── models/
│
└── study_data/
    ├── studybuddy.db
    └── important_pdfs/
```

### `app.py`

Main Streamlit application containing:

- UI
- AI integration
- RPG systems
- Quest system
- Dungeon system
- Revision system
- Focus system
- Achievements
- Reports
- PDF library
- Guild system

### `models/`

Project model-related files/resources.

### `study_data/`

Local runtime data.

This directory should not be committed to GitHub because it contains personal study data.

---

# 🧪 AI Fallback System

StudyBuddy is designed so that the application can still provide practice questions even when AI generation is unavailable.

For supported subjects, the application contains built-in question banks.

If Ollama cannot generate the requested quiz successfully, StudyBuddy can fall back to its local practice-question bank.

This makes the quiz system more resilient instead of depending entirely on an AI server.

---

# 📈 Progression System

StudyBuddy uses XP-based progression.

The basic concept is:

```text
Complete Study Activity
          ↓
        Earn XP
          ↓
       Gain Levels
          ↓
     Unlock Features
          ↓
      Unlock Shadows
          ↓
   Improve Study Progress
```

Ranks progress through:

```text
E-RANK
D-RANK
C-RANK
B-RANK
A-RANK
S-RANK
NATIONAL LEVEL
```

---

# 🎓 Who Is It For?

StudyBuddy is intended for:

- College students
- School students
- Self-learners
- Students preparing for exams
- Developers learning technical subjects
- Anyone who struggles with study consistency

It is especially useful for people who enjoy **gamification, RPG systems, AI assistants, and structured study routines**.

---

# 💡 What Problem Does It Solve?

StudyBuddy combines multiple study tools that are normally separated across different applications.

Instead of using:

```text
Planner + Timer + Flashcards + Quiz App + AI Chatbot + Progress Tracker
```

StudyBuddy attempts to bring these into one experience:

```text
             STUDYBUDDY
                  │
     ┌────────────┼────────────┐
     ▼            ▼            ▼
  Planning      AI Help      Focus
     │            │            │
     ├────────────┼────────────┤
     ▼            ▼            ▼
  Quests       Gemma        Timer
     │
     ▼
   XP / Levels
     │
     ▼
   Rewards
     │
     ├───────────┬────────────┐
     ▼           ▼            ▼
Revision      Dungeons    Achievements
```

---

# 🌟 Why Local AI?

Using local AI provides several benefits:

### Cost

No per-request cloud AI API is required for the local Ollama workflow.

### Privacy

Study prompts can remain on the user's machine.

### Experimentation

Users can install and compare different models.

### Control

The application controls the system prompts, workflows, and study-specific AI behavior.

### Offline-Friendly AI

After the model has been downloaded, AI inference can run locally without requiring every request to go through a cloud API.

---

# ⚠️ Important Notes

- Ollama must be installed and available for AI features.
- At least one Ollama model should be installed.
- Gemma features require a Gemma model to be installed.
- Larger AI models require more RAM and processing power.
- The application is primarily designed as a local-first project.
- `study_data/` contains local user data and should not be uploaded.
- AI-generated answers should still be reviewed for accuracy.

---

# 🛠️ Future Improvements

Possible future development includes:

- PDF-to-AI study assistance
- More advanced document understanding
- Better personalized learning paths
- More AI models
- Voice interaction
- Mobile support
- Cloud synchronization
- Real-time multiplayer guilds
- More advanced analytics
- Better adaptive quizzes
- Automated exam preparation plans

---

# 🤝 Contributing

Contributions are welcome.

Possible contribution areas include:

- UI improvements
- New study features
- New question banks
- AI integrations
- Better accessibility
- Performance improvements
- Testing
- Documentation
- Bug fixes

To contribute:

```bash
git clone https://github.com/shanaldo7/STUDYBUDDY-LEVEL-UP-gamified-study-planner.git
cd STUDYBUDDY-LEVEL-UP-gamified-study-planner
```

Create a branch:

```bash
git checkout -b feature/your-feature
```

Make your changes, commit them, and open a pull request.

---

# 📜 License

Add your preferred open-source license here.

Example:

```text
MIT License
```

> Replace this section with the actual license file once a license has been selected for the repository.

---

# 👨‍💻 Developer

**Shayan / shanaldo7**

GitHub:

https://github.com/shanaldo7/STUDYBUDDY-LEVEL-UP-gamified-study-planner

---

# ⚔️ Final Message

StudyBuddy is built around one simple idea:

> **Studying should feel like progress, not punishment.**

Complete the quest.

Earn the XP.

Build the streak.

Defeat the dungeon.

Unlock your shadows.

And keep leveling up.

## ⚔️ ARISE, HUNTER.

### LEVEL UP YOUR KNOWLEDGE.
