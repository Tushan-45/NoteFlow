from youtube_transcript_api import YouTubeTranscriptApi
import re


def extract_video_id(url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)

    return match.group(1) if match else None


def get_transcript(video_url):

    video_id = extract_video_id(video_url)

    transcript_list = YouTubeTranscriptApi().fetch(video_id)

    full_text = ""

    for item in transcript_list:

        minutes = int(item.start // 60)
        seconds = int(item.start % 60)

        timestamp = f"[{minutes:02}:{seconds:02}]"

        full_text += f"{timestamp} {item.text}\n"

    return full_text