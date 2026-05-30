import React, { useState, useRef } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import {
  FaYoutube,
  FaCopy,
  FaDownload,
  FaMagic
} from 'react-icons/fa';

const API_URL = "http://127.0.0.1:5000";

function App() {

  const [url, setUrl] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const [language, setLanguage] = useState('hinglish');
  const [videoInfo, setVideoInfo] = useState(null);
  const [usedLanguage, setUsedLanguage] = useState('hinglish');

  // ── useRef keeps language always in sync, no stale closure ──
  const languageRef = useRef('hinglish');

  const handleLanguageChange = (lang) => {
    setLanguage(lang);
    languageRef.current = lang;  // always fresh, even on first click
    console.log("Language selected:", lang);
  };

  const copyNotes = () => {
    navigator.clipboard.writeText(notes);
    alert('Notes copied!');
  };

  const generateNotes = async () => {

    if (!url) {
      alert('Please enter a YouTube URL');
      return;
    }

    // Read from ref — guaranteed to be current value
    const selectedLanguage = languageRef.current;

    console.log("Generating notes with language:", selectedLanguage);

    try {

      setLoading(true);
      setNotes('');
      setVideoInfo(null);

      const response = await axios.post(
        `${API_URL}/generate-notes`,
        {
          url: url,
          language: selectedLanguage   // always correct
        }
      );

      console.log("Response:", response.data);

      if (response.data.success) {

        setNotes(response.data.notes || "No notes generated");
        setVideoInfo(response.data.video_info);
        setUsedLanguage(selectedLanguage);  // track what was actually used

      } else {

        console.error(response.data.error);
        alert(response.data.error || "Something went wrong");

      }

    } catch (error) {

      console.error(error);
      alert('Something went wrong. Check console for details.');

    } finally {

      setLoading(false);

    }
  };

  const languageLabel = {
    english: "English",
    hindi: "हिंदी",
    hinglish: "Hinglish"
  };

  return (

    <div className={darkMode ? "app dark" : "app light"}>

      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="hero"
      >

        <h1 className="logo-title">
          <img
            src="/neww.png"
            alt="NoteFlow Logo"
            className="logo-img"
          />
          NoteFlow
        </h1>

        <p>Convert YouTube videos into Smart Notes with AI</p>

        <button
          className="theme-toggle"
          onClick={() => setDarkMode(!darkMode)}
        >
          {darkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
        </button>

        {/* ── Language selector with active highlight ── */}
        <div className="language-buttons">

          {['english', 'hinglish', 'hindi'].map((lang) => (
            <button
              key={lang}
              onClick={() => handleLanguageChange(lang)}
              className={language === lang ? 'lang-btn active' : 'lang-btn'}
              style={{
                // Inline fallback in case CSS class isn't set up yet
                fontWeight: language === lang ? 'bold' : 'normal',
                borderBottom: language === lang ? '2px solid #f97316' : '2px solid transparent',
                opacity: language === lang ? 1 : 0.6,
              }}
            >
              {lang === 'english' ? '🇬🇧 English' : lang === 'hinglish' ? '🇮🇳 Hinglish' : '🇮🇳 Hindi'}
            </button>
          ))}

        </div>

        {/* ── Show which language is currently selected ── */}
        <p style={{ fontSize: '0.85rem', opacity: 0.7, marginTop: '6px' }}>
          Selected: <strong>{languageLabel[language]}</strong>
        </p>

      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="card"
      >

        <div className="input-section">

          <input
            type="text"
            placeholder="Paste YouTube URL here..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />

          <button onClick={generateNotes} disabled={loading}>
            <FaMagic /> {loading ? 'Generating...' : 'Generate Notes'}
          </button>

        </div>

      </motion.div>

      {loading && (

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="loader-container"
        >

          <div className="spinner"></div>

          <p>AI is generating smart <strong>{languageLabel[language]}</strong> notes...</p>

        </motion.div>

      )}

      {videoInfo && (

        <div className="video-card">

          <img
            src={videoInfo.thumbnail}
            alt="thumbnail"
            className="thumbnail"
          />

          <div className="video-details">

            <h2>{videoInfo.title}</h2>

            <p>📺 {videoInfo.channel}</p>

            <p>⏱ Duration: {Math.floor(videoInfo.duration / 60)} min</p>

          </div>

        </div>

      )}

      {notes && (

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="notes-card"
        >

          <h2>Generated Notes</h2>

          <h3 className="language-label">
            Language : {languageLabel[usedLanguage]}
          </h3>

          <div
            className="formatted-notes"
            dangerouslySetInnerHTML={{
              __html: notes
                .replace(/^## (.*$)/gim, '<div class="heading">$1</div>')
                .replace(/\*\*(.*?)\*\*/g, '<div class="heading">$1</div>')
                .replace(/\[(\d{2}:\d{2})\]/g, '<span class="timestamp">[$1]</span>')
                .replace(/^- /gim, '• ')
                .replace(/\n/g, '<br/>')
            }}
          ></div>

          <div className="button-group">

            <button
              className="copy-btn"
              onClick={copyNotes}
            >
              <FaCopy /> Copy Notes
            </button>

            <a
              href={`${API_URL}/download-pdf`}
              target="_blank"
              rel="noreferrer"
            >
              <button className="download-btn">
                <FaDownload /> Download PDF
              </button>
            </a>

          </div>

        </motion.div>

      )}

    </div>
  );
}

export default App;