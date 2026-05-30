import traceback
import os
import time
import logging
import yt_dlp

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq

from whisper_utils import transcribe_video
from pdf_generator import create_pdf

# ─────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

log = logging.getLogger(__name__)

groq_api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=groq_api_key)

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# Translation Prompts
#
# Strategy: always generate notes in English first
# (models do this reliably), then translate in a
# second call. This is far more reliable than asking
# the model to generate + follow language rules at once.
# ─────────────────────────────────────────────

TRANSLATION_CONFIG = {

    "english": None,  # No translation needed

    "hindi": {
        "system": (
            "You are a professional Hindi translator. "
            "Translate the given English text into pure Hindi using Devanagari script. "
            "Keep all section headings, bullet points, timestamps and formatting exactly the same. "
            "Only translate the text content — do not add or remove any sections."
        ),
        "prompt": (
            "Translate the following English notes into Hindi (Devanagari script). "
            "Keep all formatting, bullet points, timestamps, and section headings intact.\n\n"
            "{notes}"
        )
    },

    "hinglish": {
        "system": (
            "You are an expert at writing in Indian Hinglish — "
            "a natural mix of Hindi words (written in Roman/English letters) and English. "
            "You will be given English notes. Rewrite them in Hinglish. "
            "Rules: "
            "1. EVERY sentence must contain Hindi words mixed in. "
            "2. Never write a full sentence in pure English. "
            "3. Never use Devanagari script — only Roman letters for Hindi words. "
            "4. Use natural Hindi words like: toh, kyunki, matlab, lekin, aur, samjho, "
            "dekho, ab, yaar, bohot, achha, theek hai, bilkul, haan, nahi, phir, "
            "karna hai, iske baad, suno, woh, uska, isliye, jab, tab, seedha, "
            "pata chala, hua, tha, thi, hai, hain, kar, raha, rahi. "
            "5. Keep all section headings, bullet points, timestamps and formatting the same. "
            "Example of CORRECT Hinglish: "
            "'Toh samjho, Jigsaw ek aisa banda tha jisne apna khud ka justice system banaya tha, "
            "kyunki woh sochta tha ki log apni galtiyon ki saza khud uthayein.' "
            "Example of WRONG output (pure English — never do this): "
            "'Jigsaw was a person who created his own justice system.'"
        ),
        "prompt": (
            "Rewrite the following English notes in Hinglish "
            "(Hindi words in Roman letters mixed with English). "
            "Every sentence must have Hindi words. Keep all formatting intact.\n\n"
            "{notes}"
        )
    },
}

# ─────────────────────────────────────────────
# Deduplicate Lines
# ─────────────────────────────────────────────

def deduplicate_lines(text: str) -> str:
    lines = text.split('\n')
    seen = set()
    cleaned = []

    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.endswith(':'):
            cleaned.append(line)
            continue

        if stripped not in seen:
            seen.add(stripped)
            cleaned.append(line)

    return '\n'.join(cleaned)

# ─────────────────────────────────────────────
# Get YouTube Video Info
# ─────────────────────────────────────────────

def get_video_info(youtube_url: str) -> dict:

    ydl_opts = {
        'quiet': True,
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return {
            "title": info.get("title"),
            "channel": info.get("uploader"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration", 0)
        }

# ─────────────────────────────────────────────
# Step 1: Generate English Notes
# ─────────────────────────────────────────────

def chunk_text(text: str, max_words: int = 1500) -> list:
    """Split transcript into smaller chunks to stay under token limits."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunks.append(' '.join(words[i:i + max_words]))
    return chunks


def generate_english_notes(transcript: str) -> str:

    chunks = chunk_text(transcript, max_words=1500)
    all_notes = []

    for i, chunk in enumerate(chunks):
        log.info(f"Generating notes for chunk {i + 1}/{len(chunks)}...")

        # Wait 65 seconds between chunks to reset TPM limit
        if i > 0:
            log.info("Waiting 65s for rate limit reset...")
            time.sleep(65)

        prompt = f"""
You are an expert educational notes generator.
Generate comprehensive notes in clear English from the transcript below.
This is part {i + 1} of {len(chunks)} of the full transcript.

TIMESTAMP RULES:
- Extract ONLY real timestamps that exist in the transcript
- Each timestamp must cover a MEANINGFUL moment — not every sentence
- Group nearby related sentences into ONE timestamp
- Minimum 30 seconds gap between timestamps
- Maximum 10 timestamps per chunk
- NEVER repeat the same description
- Format: MM:SS - One clear sentence describing what happens

Generate ALL 15 sections:

1. Important Timestamps (max 10, unique, min 30s gap)
2. Topics Covered
3. Easy Notes
4. Important Points
5. Summary
6. Key Takeaways
7. Definitions & Terminology
8. Real-world Examples & Use Cases
9. Common Mistakes to Avoid
10. Prerequisites
11. Related Topics
12. Quick Revision Flashcards (Q&A)
13. Mind Map Outline
14. Difficulty Level (Easy / Medium / Hard)
15. Estimated Study Time

Transcript:
{chunk}
"""

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educational notes generator. Write clear, structured notes in English."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=4096
        )

        all_notes.append(response.choices[0].message.content)

    return "\n\n---\n\n".join(all_notes)

# ─────────────────────────────────────────────
# Step 2: Translate Notes (if needed)
# ─────────────────────────────────────────────

def translate_notes(english_notes: str, language: str) -> str:

    config = TRANSLATION_CONFIG.get(language)

    # English needs no translation
    if config is None:
        return english_notes

    log.info(f"Translating notes to {language}...")

    prompt = config["prompt"].format(notes=english_notes)

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": config["system"]
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=8192
    )

    translated = response.choices[0].message.content
    log.info(f"Translation done ({len(translated)} chars)")

    return translated

# ─────────────────────────────────────────────
# Generate Notes Route
# ─────────────────────────────────────────────

@app.route('/generate-notes', methods=['POST'])
def generate_notes():

    data = request.json

    if not data:
        return jsonify({"success": False, "error": "No JSON data received"}), 400

    youtube_url = data.get('url', '').strip()
    language = data.get('language', 'hinglish').strip().lower()

    log.info(f"Request — language: '{language}', url: '{youtube_url}'")

    if not youtube_url:
        return jsonify({"success": False, "error": "YouTube URL is required"}), 400

    if language not in TRANSLATION_CONFIG:
        return jsonify({
            "success": False,
            "error": f"Invalid language. Choose from: {', '.join(TRANSLATION_CONFIG.keys())}"
        }), 400

    try:

        # ── Video Info ────────────────────────
        log.info("Fetching video info...")
        video_info = get_video_info(youtube_url)
        log.info(f"Video: {video_info.get('title')}")

        # ── Transcript ────────────────────────
        log.info("Transcribing video...")
        start_time = time.time()

        transcript = transcribe_video(youtube_url)

        if not transcript or not transcript.strip():
            return jsonify({"success": False, "error": "Transcript could not be generated"}), 500

        log.info(f"Transcript ready in {time.time() - start_time:.1f}s ({len(transcript)} chars)")

        # ── Step 1: Generate English Notes ────
        log.info("Generating English notes...")
        english_notes = generate_english_notes(transcript)
        english_notes = deduplicate_lines(english_notes)
        log.info(f"English notes done ({len(english_notes)} chars)")

        # ── Step 2: Translate if needed ───────
        final_notes = translate_notes(english_notes, language)
        final_notes = deduplicate_lines(final_notes)

        # ── Create PDF ────────────────────────
        create_pdf(final_notes)
        log.info("PDF created: notes.pdf")

        return jsonify({
            "success": True,
            "notes": final_notes,
            "video_info": video_info
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ─────────────────────────────────────────────
# Download PDF
# ─────────────────────────────────────────────

@app.route('/download-pdf')
def download_pdf():

    pdf_path = "notes.pdf"

    if not os.path.exists(pdf_path):
        return jsonify({"success": False, "error": "PDF not found. Generate notes first."}), 404

    return send_file(pdf_path, as_attachment=True)

# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "languages": list(TRANSLATION_CONFIG.keys())
    })

# ─────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)