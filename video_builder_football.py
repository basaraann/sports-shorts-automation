# video_builder_football.py - Futbol Shorts (1080x1920 dikey)
import json, os, requests, random
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from moviepy import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from tts_helper import generate_audio_file

load_dotenv()

SCRIPTS_FILE   = Path("data/shorts_scripts_football.json")
OUTPUT_DIR     = Path("data/videos")
STOCK_DIR      = Path("data/stock_football")
AUDIO_DIR      = Path("data/audio")
USED_CLIPS_FILE= Path("data/used_clips_football.json")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

VIDEO_W, VIDEO_H = 1080, 1920
FONT_SIZE        = 80
NUM_CLIPS        = 4


def load_used_clips():
    if USED_CLIPS_FILE.exists():
        with open(USED_CLIPS_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_used_clips(paths):
    used = load_used_clips()
    for p in paths:
        used.add(str(p))
    with open(USED_CLIPS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(used), f)


def generate_audio(script):
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    timestamp  = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    audio_path = AUDIO_DIR / f"football_shorts_{timestamp}.mp3"
    generate_audio_file(script["full_text"], audio_path, rate="+25%")
    return audio_path


def get_search_queries(script):
    title = script.get("source_title", "").lower()
    mapping = [
        ("messi",       ["messi goal football","argentina football","barcelona football","messi dribble","football genius","argentina fans"]),
        ("ronaldo",     ["ronaldo goal football","real madrid football","portugal football","ronaldo celebration","football free kick","madrid stadium"]),
        ("haaland",     ["manchester city football","haaland goal","premier league goal","city football","football striker","etihad stadium"]),
        ("mbappe",      ["mbappe speed football","paris football","france football","mbappe goal","football attack","ligue 1 football"]),
        ("champions",   ["champions league football","ucl goal","european football","stadium crowd","ucl night","football drama"]),
        ("premier",     ["premier league football","england football","wembley stadium","pl goal","football tackle","english football"]),
        ("laliga",      ["laliga football","spain football","bernabeu stadium","barcelona stadium","spanish football","la liga goal"]),
        ("serie",       ["serie a football","italy football","milan football","juventus football","italian football","serie a goal"]),
        ("transfer",    ["football transfer","player signing","stadium crowd","football training","press conference","football contract"]),
        ("goal",        ["football goal celebration","stadium crowd cheering","football match","goal scored","football net","goalkeeper"]),
        ("galatasaray", ["turkey football","istanbul stadium","turkish football","football crowd","turkish league","istanbul night"]),
        ("fenerbahce",  ["turkey football","istanbul derby","turkish league","football atmosphere","istanbul football","turkey fans"]),
    ]
    for kw, qs in mapping:
        if kw in title:
            return qs
    return ["football goal celebration","soccer match action","football stadium crowd","football player running","football tackle","football corner kick"]


def download_multiple_videos(queries, count=4):
    STOCK_DIR.mkdir(parents=True, exist_ok=True)
    used_clips  = load_used_clips()
    all_local   = list(STOCK_DIR.glob("*.mp4"))
    fresh_local = [v for v in all_local if str(v) not in used_clips]

    if PEXELS_API_KEY:
        headers = {"Authorization": PEXELS_API_KEY}
        random.shuffle(queries)
        for query in queries[:count*2]:
            params = {"query": query, "per_page": 8, "orientation": "portrait"}
            try:
                r = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=10)
                r.raise_for_status()
                videos = r.json().get("videos", [])
                random.shuffle(videos)
                for v in videos:
                    files = sorted(v["video_files"], key=lambda x: x.get("width", 0), reverse=True)
                    url   = files[0]["link"]
                    fname = STOCK_DIR / f"football_{v['id']}.mp4"
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

    print(f"Secilen {len(selected)} klip:")
    for s in selected:
        print(f"  {Path(s).name}")
    return selected


def prepare_clip(path, duration):
    clip = VideoFileClip(str(path), audio=False)
    r    = clip.w / clip.h
    tr   = VIDEO_W / VIDEO_H
    if r > tr:
        clip = clip.cropped(x_center=clip.w/2, width=int(clip.h*tr))
    else:
        clip = clip.cropped(y_center=clip.h/2, height=int(clip.w/tr))
    clip = clip.resized((VIDEO_W, VIDEO_H))
    if clip.duration < duration:
        loops = int(duration / clip.duration) + 1
        clip  = concatenate_videoclips([clip] * loops)
    return clip.subclipped(0, duration)


def make_subtitle_frame(word, highlight=True, size=(VIDEO_W, VIDEO_H)):
    img  = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_paths = ["C:/Windows/Fonts/arialbd.ttf","C:/Windows/Fonts/Impact.ttf","C:/Windows/Fonts/Arial.ttf"]
    font = None
    for fp in font_paths:
        if Path(fp).exists():
            font = ImageFont.truetype(fp, FONT_SIZE)
            break
    if font is None:
        font = ImageFont.load_default()

    word_upper = word.upper()
    bbox = draw.textbbox((0, 0), word_upper, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    x = (size[0] - tw) // 2
    y = int(size[1] * 0.72)

    draw.rounded_rectangle([x-20, y-20, x+tw+20, y+th+20], radius=12, fill=(0,0,0,180))
    for ox, oy in [(-4,-4),(4,-4),(-4,4),(4,4),(-4,0),(4,0),(0,-4),(0,4)]:
        draw.text((x+ox, y+oy), word_upper, font=font, fill=(0,0,0,255))
    text_color = (0, 230, 80, 255) if highlight else (255, 255, 255, 255)
    draw.text((x, y), word_upper, font=font, fill=text_color)
    return np.array(img)

def build_subtitle_clips(full_text, audio_duration):
    words = full_text.split()
    chunk_dur = audio_duration / len(words)
    clips = []
    for i, word in enumerate(words):
        frame = make_subtitle_frame(word, highlight=(i % 3 == 0))
        clips.append(ImageClip(frame, duration=chunk_dur).with_start(i * chunk_dur))
    return clips


def make_hook_flash(duration=1.5):
    frames = []
    total  = int(duration * 30)
    for i in range(total):
        img  = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        alpha = max(0, 160 - int((i/total)*160))
        draw.rectangle([0,0,VIDEO_W,VIDEO_H], fill=(0,180,60,alpha))
        frames.append(np.array(img))
    return ImageSequenceClip(frames, fps=30).with_duration(duration)

def make_vignette():
    img  = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    for i in range(300):
        alpha = int((1-i/300)**2 * 180)
        draw.rectangle([i,i,VIDEO_W-i,VIDEO_H-i], outline=(0,0,0,alpha))
    return ImageClip(np.array(img))


def build_video(script, video_paths, audio_path):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"football_shorts_{timestamp}.mp4"

    audio     = AudioFileClip(str(audio_path))
    total_dur = audio.duration
    clip_dur  = total_dur / len(video_paths)

    print(f"Toplam: {total_dur:.1f}s | {len(video_paths)} klip")

    prepared = []
    for i, path in enumerate(video_paths):
        print(f"  Klip {i+1}/{len(video_paths)}: {Path(path).name}")
        prepared.append(prepare_clip(path, clip_dur))
    bg = concatenate_videoclips(prepared).subclipped(0, total_dur)

    vignette   = make_vignette().with_duration(total_dur)
    hook_flash = make_hook_flash(duration=1.5)

    print("Altyazilar olusturuluyor...")
    subtitles = build_subtitle_clips(script["full_text"], total_dur)

    final = CompositeVideoClip([bg, vignette, hook_flash] + subtitles, size=(VIDEO_W, VIDEO_H)).with_audio(audio)

    print(f"Render -> {output_path}")
    final.write_videofile(str(output_path), fps=30, codec="libx264", audio_codec="aac",
                          temp_audiofile="temp_audio.m4a", remove_temp=True, logger="bar")
    print(f"Video hazir: {output_path}")
    return output_path


def run():
    with open(SCRIPTS_FILE, encoding="utf-8") as f:
        scripts = json.load(f)

    script = scripts[-1]
    print(f"Script: {script['source_title'][:60]}")

    audio_path           = generate_audio(script)
    script["audio_file"] = str(audio_path)

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
