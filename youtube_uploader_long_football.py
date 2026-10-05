# youtube_uploader_long_football.py - Futbol normal video yukleyici
import os, sys, json, pickle
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SCOPES         = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS = Path("client_secrets.json")
TOKEN_FILE     = Path("data/youtube_token.pickle")
SCRIPTS_FILE   = Path("data/video_scripts_football.json")
UPLOADED_FILE  = Path("data/uploaded_videos_long_football.json")
VIDEOS_DIR     = Path("data/videos")


def get_authenticated_service():
    creds = None
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow  = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return build("youtube", "v3", credentials=creds)


def load_uploaded():
    if UPLOADED_FILE.exists():
        with open(UPLOADED_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def save_uploaded(entry):
    uploaded = load_uploaded()
    uploaded.append(entry)
    with open(UPLOADED_FILE, "w", encoding="utf-8") as f:
        json.dump(uploaded, f, ensure_ascii=False, indent=2)


def get_latest_video():
    videos   = list(VIDEOS_DIR.glob("football_video_*.mp4"))
    uploaded = {u["video_path"] for u in load_uploaded()}
    fresh    = [v for v in videos if str(v) not in uploaded]
    if not fresh:
        print("Yuklenmemis video bulunamadi.")
        return None
    return str(sorted(fresh, key=lambda x: x.stat().st_mtime, reverse=True)[0])


def get_script_info():
    if not SCRIPTS_FILE.exists():
        return "⚽ Futbol", "", []
    with open(SCRIPTS_FILE, encoding="utf-8") as f:
        scripts = json.load(f)
    if not scripts:
        return "⚽ Futbol", "", []

    script = scripts[-1]
    hook   = script.get("hook", "")
    giris  = script.get("giris", "")

    hook_sentences = hook.split(".")
    title = hook_sentences[0].strip() if hook_sentences else "Futbol"
    title = f"⚽ {title}"

    description = (
        f"{hook}\n\n"
        f"{giris[:300]}\n\n"
        f"#futbol #football #soccer #premierleague #championsleague\n\n"
        f"Kanalimiza abone olun, bir sonraki videoyu kacirmayin!"
    )

    tags = ["futbol","football","soccer","premierleague","championsleague","laliga","transfer","gol"]
    return title, description, tags


def upload_video(youtube, video_path, title, description, tags):
    print(f"Yukleniyor: {video_path}")
    body = {
        "snippet": {
            "title":           title[:100],
            "description":     description[:5000],
            "tags":            tags,
            "categoryId":      "17",
            "defaultLanguage": "tr",
        },
        "status": {
            "privacyStatus":           "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    media    = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=1024*1024*5)
    request  = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  %{int(status.progress()*100)} tamamlandi...")
    video_id  = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"Yuklendi! -> {video_url}")
    return video_id, video_url


def run():
    video_path = get_latest_video()
    if not video_path:
        return None

    title, description, tags = get_script_info()
    print(f"Baslik: {title}")

    youtube = get_authenticated_service()
    video_id, video_url = upload_video(youtube, video_path, title, description, tags)

    save_uploaded({
        "video_path":  video_path,
        "video_id":    video_id,
        "video_url":   video_url,
        "title":       title,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    })

    print(f"\nTamamlandi! -> {video_url}")
    return video_url


if __name__ == "__main__":
    run()
