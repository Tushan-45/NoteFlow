import subprocess

ffmpeg_path = r"C:\Users\ASUS\Downloads\ffmpeg-8.1.1-essentials_build\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe"

result = subprocess.run(
    [ffmpeg_path, "-version"],
    capture_output=True,
    text=True
)

print(result.stdout)
