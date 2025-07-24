# 🤝 Pre-Networking Assistant

This is my first end-to-end coding project, built as part of an *Introduction to Programming* course. The **Pre-Networking Assistant App** is designed to help users prepare for professional networking calls by automating the research process, summarizing relevant content, and storing past connections for future reference.

---

## 🚀 Features

- 🧠 **Memory Storage**  
  Save names, roles, LinkedIn profiles, company websites, and conversation summaries in a structured and searchable way.

- 🔍 **Auto Research**  
  Scrapes recent news and insights about the contact’s company and industry using APIs like NewsAPI and BeautifulSoup.

- ✍️ **Call Summary Integration**  
  Upload a Word or Google Doc with your post-call notes. The app will extract key points and organize them for easy future reference.

- 🤖 **Gemini AI Integration**  
  Leverages Google Gemini to summarize input text and enhance insights from documents and webpages.

- 📚 **Networking History Tracker**  
  Maintain a growing list of who you’ve connected with and what was discussed.

---

## 🧑‍💻 Tech Stack

- **Python 3**
- **BeautifulSoup** – Web scraping
- **NewsAPI** – Real-time news fetch
- **Gemini Pro API** – AI summarization
- **JSON** – Data storage
- *(Optional future frontend: Streamlit)*

---

## 🗂️ Folder Structure

```bash
Grayson-Malone_Capstone-Project/
├── data/
│   └── contacts.json          # Stores networking memory
├── utils/
│   ├── scraper.py             # Web scraping logic
│   ├── news.py                # Fetch news from NewsAPI
│   └── summarizer.py          # Summarize text using Gemini
├── test.py                    # Test file for running modules
├── config.py                  # API keys (not tracked)
├── .venv/                     # Python virtual environment
└── README.md                  # Project overview (this file)
