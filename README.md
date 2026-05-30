#  NoteFlow – AI YouTube Notes Generator

NoteFlow is an AI-powered web application that converts YouTube videos into smart, structured study notes.

##  Features

*  Convert YouTube videos into AI-generated notes
*  Multiple language support

  * English
  * Hindi
  * Hinglish
*  Important timestamps
*  Smart summaries
*  Key takeaways
*  Definitions & terminology
*  Quick revision flashcards
*  PDF download support
*  Dark / Light mode UI

---

##  Tech Stack

### Frontend

* React.js
* Axios
* Framer Motion
* React Icons

### Backend

* Flask
* Groq API
* Whisper
* yt-dlp
* youtube-transcript-api
* ReportLab

---

##  Project Structure

```text
yt/
├── frontend/
├── backend/
├── README.md
└── .gitignore
```

---

##  Installation

### Backend

Go to backend folder:

```bash
cd backend
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run backend:

```bash
py -3.11 app.py
```

Backend runs on:

```text
http://127.0.0.1:5000
```

---

### Frontend

Go to frontend folder:

```bash
cd frontend
```

Install packages:

```bash
npm install
```

Run frontend:

```bash
npm start
```

Frontend runs on:

```text
http://localhost:3000
```

---

##  Environment Variables

Create `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
```

---

##  Screenshots

Add screenshots here later.

---

##  Author

**Tushan Kumar Sinha**

Built with ❤️ using AI + Full Stack Development.
