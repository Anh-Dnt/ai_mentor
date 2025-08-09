# AI Mentor 🧠

AI Mentor is a proactive, conversational learning assistant designed to help students stay organized, find study materials, and actively learn new concepts. Built with Python and powered by Google's Gemini and LangChain, this agent combines multiple tools to create a truly helpful study companion.

This project was built as part of the `PANDA Hacks 2025` hackathon challenge.

## ✨ Features

  * 📅 **Dynamic Calendar Integration:** Connects directly to your Google Calendar to know about upcoming exams, tests, and deadlines.
  * 🌐 **Smart Web Search:** Actively finds relevant study materials, articles, and videos from the web based on your upcoming schedule.
  * 🗂️ **Interactive Flashcard Management:** Allows you to create, review, and manage flashcards on various topics directly through conversation.
  * ⏰ **Proactive Reminders:** A background scheduler automatically checks your calendar and sends you helpful reminders and study suggestions for upcoming tests without you having to ask.

## 🚀 Getting Started

Follow these steps to set up and run AI Mentor on your local machine.

### Prerequisites

  * Python 3.8+
  * `pip` package installer

### Setup Instructions

**1. Clone the Repository**

```bash
git clone https://github.com/your-username/ai-mentor.git
cd ai-mentor
```

**2. API & Credentials Setup**

This project requires credentials for several Google services.

**A. Google Gemini API Key**

1.  Go to **[Google AI Studio](https://aistudio.google.com/)**.
2.  Click on **"Get API key"** and create a new key.
3.  Copy this key.

**B. Google Cloud Project (for Calendar & Search APIs)**

1.  Go to the **[Google Cloud Console](https://console.cloud.google.com/)** and create a new project.
2.  **Enable APIs:**
      * In the navigation menu (☰), go to **APIs & Services \> Library**.
      * Search for and enable both of the following APIs:
          * **Google Calendar API**
          * **Custom Search API**
3.  **Create OAuth 2.0 Credentials (for Calendar):**
      * Go to **APIs & Services \> Credentials**.
      * Click **+ CREATE CREDENTIALS** \> **OAuth 2.0 Client ID**.
      * Select **"Desktop app"** as the application type and give it a name.
      * Click **CREATE**. A window will pop up. Click **DOWNLOAD JSON**.
      * Rename the downloaded file to `credentials.json` and place it in your project folder.
4.  **Create Custom Search Engine (for Search):**
      * Go to the **[Programmable Search Engine control panel](https://programmablesearchengine.google.com/controlpanel/all)**.
      * Click **"Add"** to create a new search engine.
      * Give it a name, and in the "What to search?" section, select **"Search the entire web"**.
      * After creating, find and copy the **"Search engine ID"**.

**C. Set up Environment File**

1.  Create a file named `.env` in the root of your project directory.
2.  Add the credentials you just obtained to this file:

<!-- end list -->

```.env
# From Google AI Studio
GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"

# From Google Cloud Console (may be the same as GOOGLE_API_KEY)
CUSTOM_SEARCH_API_KEY="YOUR_CUSTOM_SEARCH_API_KEY_HERE"

# From Programmable Search Engine
SEARCH_ENGINE_ID="YOUR_SEARCH_ENGINE_ID_HERE"
```

**3. Install Dependencies**

It is highly recommended to use a virtual environment.

```bash
# Create a virtual environment
python -m venv .venv

# Activate it
# On Windows:
# .\.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

# Install the required packages
pip install langchain langchain-google-genai google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv apscheduler
```

**4. Run the Application**

Now you are ready to start the AI Mentor\!

```bash
python main.py
```

**First-Time Authentication:**
The very first time you run the script, a new tab will open in your web browser asking you to log in with your Google account and grant permission for the app to view your calendar. After you approve, a `token.json` file will be created in your project folder, and you won't need to log in again.

## 🧪 Sample Prompts

Once the agent is running, try these prompts to test its capabilities:

1.  **Tool Chaining (Calendar + Search):**

    > "Check if I have any exams in the next 30 days, and if so, find review videos for that subject."

2.  **Complex Tool Input (Flashcards):**

    > "Create a new flashcard topic called 'Chemistry', then add a card to it. Front: 'What is the chemical formula for water?'. Back: 'H₂O'."

3.  **Proactive Feature Test:**

    > First, add an event named "Final Physics Exam" to your Google Calendar for tomorrow. Then, run the application and just wait for a minute or two. The agent should automatically print a reminder about your upcoming exam.

4.  **Multi-Tool Combination (Calendar + Flashcards):**

    > "Do I have a History exam this week? If so, let me review all my flashcards for the 'History' topic."

5.  **Multi-Step "Stress Test":**

    > "Find study materials about 'Newton's Laws of Motion'. Afterward, create a new flashcard under the 'Physics' topic. Front: 'What is Newton's First Law also known as?'. Back: 'The Law of Inertia'."
