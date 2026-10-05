# video_builder_long_football.py - Futbol Normal Video (1920x1080 yatay, ~3 dakika)
import json, os, requests, random, subprocess
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from tts_helper import generate_audio_file

load_dotenv()

SCRIPTS_FILE    = Path("data/video_scripts_football.json")
OUTPUT_DIR      = Path("data/videos")
STOCK_DIR       = Path("data/stock_football")
AUDIO_DIR       = Path("data/audio")
TEMP_DIR        = Path("data/temp")
USED_CLIPS_FILE = Path("data/used_clips_long_football.json")
PEXELS_API_KEY  = os.environ.get("PEXELS_API_KEY", "")

VIDEO_W, VIDEO_H = 1920, 1080
NUM_CLIPS        = 8
WORDS_PER_SUB    = 5
FPS              = 30


def load_used_clips():
    if USED_CLIPS_FILE.exists():
        with open(USED_CLIPS_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_used_clips(paths):
    used = load_used_clips()
    for p in paths:
        used.add(str(p))
    with open(USED_CLIPS_FILE, "w") as f:
        json.dump(list(used), f)


def generate_audio(script):
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    timestamp  = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    audio_path = AUDIO_DIR / f"football_video_{timestamp}.mp3"
    generate_audio_file(script["full_text"], audio_path, rate="+15%")
    return audio_path


def get_audio_duration(audio_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def get_search_queries(script):
    title = script.get("source_title", "").lower()
    mapping = [
        ("messi",       ["messi football","argentina football","barcelona football","messi dribble","football genius","argentina fans","messi goal","football skill"]),
        ("ronaldo",     ["ronaldo football","real madrid football","portugal football","ronaldo goal","football free kick","madrid fans","ronaldo skill","football celebration"]),
        ("haaland",     ["manchester city football","haaland goal","premier league","city football","football striker","etihad stadium","football power","pl action"]),
        ("mbappe",      ["mbappe football","paris football","france football","mbappe goal","football speed","football attack","ligue 1","france squad"]),
        ("champions",   ["champions league","ucl football","european football","stadium crowd","ucl night","football drama","champions trophy","ucl final"]),
        ("premier",     ["premier league","england football","wembley","pl action","football tackle","english football","pl drama","football referee"]),
        ("transfer",    ["football training","player signing","stadium crowd","football contract","press conference","football handshake","new signing","football jersey"]),
        ("galatasaray", ["turkish football","istanbul stadium","turkey football","football crowd","turkish league","istanbul night","turkey league","football ultras"]),
        ("fenerbahce",  ["turkish football","istanbul derby","turkey football","football atmosphere","istanbul football","turkish league","football crowd","turkey fans"]),
    ]
    for kw, qs in mapping:
        if kw in title:
            return qs
    return ["football match","soccer goal","football stadium","football player","football tackle","football corner","football header","football atmosphere"]


def download_multiple_videos(queries, count=8):
    STOCK_DIR.mkdir(parents=True, exist_ok=True)
    used_clips  = load_used_clips()
    all_local   = list(STOCK_DIR.glob("*.mp4"))
    fresh_local = [v for v in all_local if str(v) not in used_clips]

    if PEXELS_API_KEY:
        headers = {"Authorization": PEXELS_API_KEY}
        random.shuffle(queries)
        for query in queries[:count*2]:
            params = {"query": query, "per_page": 5, "orientation": "landscape"}
            try:
                r = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=10)
                r.raise_for_status()
                videos = r.json().get("videos", [])
                random.shuffle(videos)
                for v in videos:
                    files = sorted(v["video_files"], key=lambda x: x.get("width", 0), reverse=True)
                    url   = files[0]["link"]
                    fname = STOCK_DIR / f"football_long_{v['id']}.mp4"
                    if not fname.exists():
                        print(f"  Indiriliyor [{query}]...")
                        with requests.get(url, stream=True, timeout=30) as resp:
                            with open(fname, "wb") as f:
                                f.write(resp.content)
                        fresh_local.append(fname)
                        break
            except Exception as e:
                print(f"  Atlanıyor [{query}]: {e}")

    if len(fresh_local) >= count:
        selected = random.sample(fresh_local, count)
    elif all_local:
        print("Sifirlaniyor...")
        with open(USED_CLIPS_FILE, "w") as f:
            json.dump([], f)
        selected = random.sample(all_local, min(count, len(all_local)))
    else:
        selected = []

    print(f"Secilen {len(selected)} klip")
    return selected


def make_subtitle_image(text):
    img  = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_paths = ["C:/Windows/Fonts/arialbd.ttf","C:/Windows/Fonts/Impact.ttf","C:/Windows/Fonts/Arial.ttf"]
    font = None
    for fp in font_paths:
        if Path(fp).exists():
            font = ImageFont.truetype(fp, 55)
            break
    if font is None:
        font = ImageFont.load_default()

    text_upper = text.upper()
    bbox = draw.textbbox((0, 0), text_upper, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x  = (VIDEO_W - tw) // 2
    y  = int(VIDEO_H * 0.85)

    pad = 16
    draw.rounded_rectangle([x-pad, y-pad, x+tw+pad, y+th+pad], radius=10, fill=(0,0,0,200))
    for ox, oy in [(-3,-3),(3,-3),(-3,3),(3,3)]:
        draw.text((x+ox, y+oy), text_upper, font=font, fill=(0,0,0,255))
    draw.text((x, y), text_upper, font=font, fill=(255, 255, 255, 255))

    return np.array(img)


def make_intro_card(title):
    img  = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 220))
    draw = ImageDraw.Draw(img)

    font_paths = ["C:/Windows/Fonts/arialbd.ttf","C:/Windows/Fonts/Impact.ttf"]
    font = None
    for fp in font_paths:
        if Path(fp).exists():
            font = ImageFont.truetype(fp, 72)
            break
    if font is None:
        font = ImageFont.load_default()

    draw.rectangle([0, 0, VIDEO_W, 12], fill=(0, 180, 60, 255))
    draw.rectangle([0, VIDEO_H-12, VIDEO_W, VIDEO_H], fill=(0, 180, 60, 255))

    words = title.upper().split()
    line1 = " ".join(words[:len(words)//2])
    line2 = " ".join(words[len(words)//2:])

    for i, line in enumerate([line1, line2]):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw   = bbox[2] - bbox[0]
        x    = (VIDEO_W - tw) // 2
        y    = VIDEO_H // 2 - 60 + i * 90
        draw.text((x+3, y+3), line, font=font, fill=(0,0,0,200))
        draw.text((x, y), line, font=font, fill=(0, 230, 80, 255))

    return np.array(img)


def build_video(script, video_paths, audio_path):
    from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"football_video_{timestamp}.mp4"

    audio    = AudioFileClip(str(audio_path))
    duration = audio.duration
    clip_dur = duration / len(video_paths)
    print(f"Ses: {duration:.1f}s | {len(video_paths)} klip x {clip_dur:.1f}s")

    bg_clips = []
    for i, path in enumerate(video_paths):
        clip = VideoFileClip(str(path), audio=False)
        r  = clip.w / clip.h
        tr = VIDEO_W / VIDEO_H
        if r > tr:
            clip = clip.cropped(x_center=clip.w/2, width=int(clip.h*tr))
        else:
            clip = clip.cropped(y_center=clip.h/2, height=int(clip.w/tr))
        clip = clip.resized((VIDEO_W, VIDEO_H))
        if clip.duration < clip_dur:
            loops = int(clip_dur / clip.duration) + 1
            clip  = concatenate_videoclips([clip] * loops)
        clip = clip.subclipped(0, clip_dur)
        bg_clips.append(clip)
        print(f"  Klip {i+1}/{len(video_paths)} hazir")

    bg = concatenate_videoclips(bg_clips)

    intro_frame = make_intro_card(script.get("source_title", "")[:80])
    intro = ImageClip(intro_frame, duration=3.0).with_start(0)

    words     = script["full_text"].split()
    chunks    = [" ".join(words[i:i+WORDS_PER_SUB]) for i in range(0, len(words), WORDS_PER_SUB)]
    chunk_dur = duration / len(chunks)
    sub_clips = []
    for i, chunk in enumerate(chunks):
        frame = make_subtitle_image(chunk)
        sc    = ImageClip(frame, duration=chunk_dur).with_start(i * chunk_dur)
        sub_clips.append(sc)
    print(f"Altyazi: {len(sub_clips)} frame hazir")

    final = CompositeVideoClip([bg, intro] + sub_clips, size=(VIDEO_W, VIDEO_H)).with_audio(audio)

    print(f"Render -> {output_path}")
    final.write_videofile(
        str(output_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=str(TEMP_DIR / "temp_audio_long_football.m4a"),
        remove_temp=True,
        logger=None,
    )

    print(f"Video hazir: {output_path}")
    return output_path


def run():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    with open(SCRIPTS_FILE, encoding="utf-8") as f:
        scripts = json.load(f)

    script = scripts[-1]
    print(f"Script: {script['source_title'][:60]}")

    audio_path  = generate_audio(script)
    queries     = get_search_queries(script)
    video_paths = download_multiple_videos(queries, count=NUM_CLIPS)

    if not video_paths:
        raise FileNotFoundError("Video bulunamadi.")

    save_used_clips([str(p) for p in video_paths])
    output = build_video(script, video_paths, audio_path)
    print(f"\nTamamlandi! -> {output}")
    return output

if __name__ == "__main__":
    run()
