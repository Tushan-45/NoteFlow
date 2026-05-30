import re
import glob
import os

import whisper
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# Load Whisper model once at startup (used only as fallback)
model = whisper.load_model("base")


def get_video_id(youtube_url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", youtube_url)
    if not match:
        raise ValueError("Invalid YouTube URL")
    return match.group(1)


def get_captions(video_id):
    """Try to fetch captions via youtube-transcript-api."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript_list
    except (TranscriptsDisabled, NoTranscriptFound):
        # Try any available language
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcripts.find_generated_transcript(['en', 'hi', 'en-IN'])
            return transcript.fetch()
        except Exception:
            return None
    except Exception:
        return None


def format_captions(transcript_list):
    """Format caption entries into timestamped text."""
    formatted = ""
    for entry in transcript_list:
        start = int(entry["start"])
        minutes = start // 60
        seconds = start % 60
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        formatted += f"{timestamp} {entry['text']}\n"
    return formatted


def download_audio(youtube_url):
    """Download audio using yt-dlp as fallback."""
    old_files = glob.glob("audio.*")
    for file in old_files:
        try:
            os.remove(file)
        except:
            pass

        ydl_opts = {
    'format': '140',
    'outtmpl': 'audio.%(ext)s',
    'quiet': False,
    'noplaylist': True,
    'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0'
    },
}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    audio_files = glob.glob("audio.*")
    if not audio_files:
        raise Exception("Audio download failed")
    return audio_files[0]


def transcribe_audio(audio_path):
    """Transcribe audio using Whisper."""
    try:
        result = model.transcribe(
            audio_path,
            fp16=False,
            verbose=False,
            language="en"
        )
    except Exception as e:
        print("Whisper Error:", e)
        return "Transcript could not be generated properly."

    if "segments" not in result:
        return "No transcript segments found."

    formatted = ""
    for segment in result["segments"]:
        start = int(segment["start"])
        minutes = start // 60
        seconds = start % 60
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        formatted += f"{timestamp} {segment['text']}\n"
    return formatted


def transcribe_video(youtube_url):
    """
    Primary: fetch captions via youtube-transcript-api (fast, no bot issues).
    Fallback: download audio via yt-dlp and transcribe with Whisper.
    """
    video_id = get_video_id(youtube_url)

    # Primary: captions
    print("Trying captions first...")
    captions = get_captions(video_id)

    if captions:
        print("Captions found — using youtube-transcript-api")
        return format_captions(captions)

    # Fallback: yt-dlp + Whisper
    print("No captions found — falling back to Whisper transcription")
    audio_path = download_audio(youtube_url)
    print("Audio downloaded:", audio_path)
    return transcribe_audio(audio_path)