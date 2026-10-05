# ⚔️ StudyBuddy: Level Up

### Gamified AI Study Planner powered by Google Gemma

StudyBuddy is a **gamified study planner and AI learning companion** designed to make studying feel less like a boring checklist and more like an RPG progression system.

Instead of simply asking students to complete tasks, StudyBuddy turns studying into a system of:

**Quests → XP → Levels → Ranks → Achievements → New Abilities**

The application combines study planning, AI assistance, revision, focus sessions, quizzes, progress tracking, and an original hunter-dungeon interface in one local-first application.

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

StudyBuddy includes an AI assistant powered through **Google Gemma (hosted via the Gemini API)**.

The AI System Assistant can:

### Generate Today's Quests

Tell the AI:

- What subjects you need to study
- Your available study time
- Your preferred workload

The AI generates suggested study missions that can then be added to the Quest Schedule.

### Shadow Mentor

Use the hosted Gemma AI as a study mentor.

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

StudyBuddy uses Google's hosted Gemma models through the Gemini API — **no local model installation is required**.

The Gemma Study Lab allows users to:

- Run learning tasks using hosted Gemma
- Test different hosted Gemma variants
- Compare output and timing between two hosted Gemma models side-by-side
- Compare response timing

Get your free API key from:

```text
https://aistudio.google.com/app/apikey
```

Paste the key into the sidebar once (or set it via environment / Streamlit secrets), and every AI feature works immediately — no downloads, no local server.

---

# 👥 Shadow Army

StudyBuddy turns AI study companions into RPG-style shadow soldiers.

Shadow characters are unlocked as the player's level increases.

Current companions include:

- ⚔️ **Crimson Warden** — Discipline Protocol
- 🐻 **Frostmaw** — Memory Guard
- 🛡️ **Ironclad** — Focus Shield
- 🔮 **Arcane Brute** — Knowledge Spell
- 👑 **Royal Mantis** — Royal Tutor

Each companion has its own personality and learning role.

For example:

**Crimson Warden** focuses on discipline and breaking large goals into manageable missions.

**Frostmaw** focuses on memory techniques and recall.

**Ironclad** helps overcome distractions and procrastination.

**Arcane Brute** creates practice questions and explains difficult concepts.

**Royal Mantis** acts as an enthusiastic personal tutor.

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
- 🛡️ Night Sentinel
- 🕷️ Void Weaver
- ❄️ Glacial Colossus

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

- **Google Gemini API** (Google GenAI SDK)
- **Gemma** — hosted Gemma variants (gemma-3-4b-it and family)
- Fully configurable model name — no model is hardcoded into features

## Data Storage

- **SQLite**
- Local filesystem storage

## PDF

- **pypdf**

## Secrets & Config

- **Streamlit st.secrets** (for Streamlit Cloud)
- **Environment variables**
- **.env** file support via python-dotenv

## Python Standard Library

The project also uses Python's standard library for:

- JSON processing
- File management
- Hashing
- Dates and time
- Regular expressions
- Randomization
- HTTP communication (remote image assets only)
- Local application paths

---

# 🧠 How the AI Architecture Works

StudyBuddy uses a **hosted Gemma AI architecture**.

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
                │ (keeps all prompts)│
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │  Google GenAI SDK  │
                │  (Gemma · Gemini)  │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Hosted Gemma Model │
                │  gemma-3-4b-it …   │
                └────────────────────┘
```

AI requests are sent to Google's hosted Gemma API using a free API key from Google AI Studio.

---

# 🔐 Privacy & Security

StudyBuddy is designed around local storage for your study data.

Study data is stored in:

```text
study_data/
```

The application uses a local SQLite database:

```text
study_data/studybuddy.db
```

The project does not require a cloud database for its core functionality.

**API key handling:**

- API keys are **never** hardcoded, logged, displayed (except masked input), or written to the database.
- Priority order for key resolution:
  1. `st.secrets["GEMINI_API_KEY"]` — Streamlit Cloud secrets (recommended for deployment)
  2. `GEMINI_API_KEY` environment variable
  3. `.env` file (loaded automatically if present)
  4. In-browser session input via the sidebar (ephemeral; cleared when you close the tab)
- `.env`, `.env.local`, and `.secrets.toml` are protected in `.gitignore`.

---

# 💻 Requirements

You need:

- Windows, Linux, or macOS
- Python 3.10+
- Git
- A free Google AI API key (from https://aistudio.google.com/app/apikey)
- Internet connection for AI requests and loading remote web assets used by the interface

Local model installation (Ollama) is **not required anymore**.

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

Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

You should now see something similar to:

```text
(venv) C:\...\STUDYBUDDY-LEVEL-UP-gamified-study-planner>
```

---

## 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` — the app UI
- `pypdf` — PDF upload support
- `google-generativeai` — official Google GenAI SDK for hosted Gemma
- `python-dotenv` — optional `.env` file support

---

## 4. Configure your Google AI API key

### Option A — Local `.env` file (recommended for development)

Create a file named `.env` in the project root (beside `app.py`) with the following content:

```env
GEMINI_API_KEY=your_google_ai_api_key_here
# Optional override for the default hosted Gemma model:
# STUDYBUDDY_MODEL=gemma-3-4b-it
```

Save and close the file. `.env` is already in `.gitignore`, so it will never be committed.

### Option B — System environment variable

Windows (CMD):
```cmd
set GEMINI_API_KEY=your_google_ai_api_key_here
```

Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY = "your_google_ai_api_key_here"
```

Linux / macOS:
```bash
export GEMINI_API_KEY=your_google_ai_api_key_here
```

### Option C — In-app first-run connection (no file edits)

Just start the app (see step 5), and in the sidebar under **Gemma AI · Google Cloud**:
1. Click **🔑 Get Google AI API Key** (opens aistudio.google.com/app/apikey)
2. Copy your new key
3. Paste it into the **Connect StudyBuddy AI** input (it's masked)
4. Click **Connect AI**

The key stays in your browser session only and is cleared when you close the tab.

---

## 5. Deploy to Streamlit Cloud

When deploying to https://streamlit.io/cloud :

1. Push your fork to GitHub.
2. Create a new Streamlit app pointing to the repo and `app.py`.
3. In the Streamlit Cloud dashboard, open **⚙️ Settings → Secrets** and paste:

   ```toml
   GEMINI_API_KEY = "your_google_ai_api_key_here"
   ```

   *(Optional)*
   ```toml
   STUDYBUDDY_MODEL = "gemma-3-4b-it"
   ```

4. Save and reboot the app. The app will auto-connect "Gemma AI: Connected" via Streamlit secrets with zero in-app setup needed.

---

## 6. Start StudyBuddy

Make sure you are inside the project folder.

Activate the virtual environment if needed:

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
2. Check the sidebar header — if everything is configured correctly you'll see **✓ Gemma AI: Connected**.
3. If the status says **✕ Gemma AI: Not connected**, open **🔗 Connect StudyBuddy AI** in the sidebar, click **🔑 Get Google AI API Key**, paste the key, then **Connect AI**.
4. Use any AI feature — AI System Assistant, Gemma Study Lab, Shadow Army chat, AI flashcard forge, weekly AI Hunter Report, or AI-generated dungeon quizzes.

All prompts, output formats, quiz JSON schemas, XP flow, and RPG mechanics are identical to the original local-AI design — only the inference backend changed.

---

# 🗂️ Project Structure

```text
StudyBuddy/
│
├── app.py
├── README.md
├── .gitignore
├── requirements.txt
│
└── study_data/
    ├── studybuddy.db
    └── important_pdfs/
```

### `app.py`

Main Streamlit application containing:

- UI
- AI integration (hosted Gemma via Google GenAI SDK)
- RPG systems
- Quest system
- Dungeon system
- Revision system
- Focus system
- Achievements
- Reports
- PDF library
- Guild system

### `study_data/`

Local runtime data.

This directory should not be committed to GitHub because it contains personal study data.

---

# 🧪 AI Fallback System

StudyBuddy is designed so that the application can still provide practice questions even when AI generation is unavailable (no API key, rate limit, network issue, etc.).

For supported subjects, the application contains built-in question banks.

If the hosted Gemma API cannot generate the requested quiz successfully, StudyBuddy can fall back to its local practice-question bank.

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

# ⚠️ Important Notes

- A free Google AI API key is required for AI features. Get one from https://aistudio.google.com/app/apikey
- No local Ollama server is needed, and `localhost:11434` is never contacted.
- You can override the default hosted Gemma model using the `STUDYBUDDY_MODEL` environment variable or the sidebar AI Model selector.
- Larger hosted models may have different quota tiers in Google AI Studio.
- The application is primarily designed as a local-first project.
- `study_data/` contains local user data and should not be uploaded.
- AI-generated answers should still be reviewed for accuracy.
- Never commit your `.env` or share your API key in screenshots, logs, or code.

---

# 🛠️ Future Improvements

Possible future development includes:

- PDF-to-AI study assistance
- More advanced document understanding
- Better personalized learning paths
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
