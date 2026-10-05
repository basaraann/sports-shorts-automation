# main_motorsport_shorts.py
import subprocess, sys, json, os, time
from pathlib import Path
from datetime import datetime, timezone

LOG_FILE = Path("data/logs/motorsport_shorts.log")

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

def log(msg):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    try:
        print(line)
    except Exception:
        print(line.encode('ascii', errors='replace').decode())
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def run_step(script_name, step_no, total, timeout=600):
    log(f"ADIM {step_no}/{total}: {script_name}")
    result = subprocess.run(
        [sys.executable, "-u", script_name],
        capture_output=True,
        encoding='utf-8',
        errors='replace',
        timeout=timeout,
        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
    )
    if result.returncode != 0:
        err = result.stderr[-500:] if result.stderr else "bilinmeyen hata"
        log(f"HATA: {err}")
        raise RuntimeError(f"{script_name} basarisiz")
    log(f"ADIM {step_no}/{total}: tamamlandi")
    if result.stdout:
        log(result.stdout[-300:])
    return result.stdout

def get_latest_video():
    videos = list(Path("data/videos").glob("shorts_*.mp4"))
    if not videos:
        return None
    return str(sorted(videos, key=lambda x: x.stat().st_mtime, reverse=True)[0])

def main():
    log("=" * 50)
    log("MOTOR SPORLARI SHORTS PIPELINE BASLADI")
    log("=" * 50)

    # Adim 1: Haber cek (hizli)
    run_step("rss_scraper.py", 1, 4, timeout=120)

    # Adim 2: Script uret (hizli)
    run_step("shorts_generator.py", 2, 4, timeout=120)

    # Adim 3: Video olustur (en uzun - 600 saniye)
    run_step("video_builder.py", 3, 4, timeout=1200)

    # Adim 4: YouTube'a yukle (orta)
    run_step("youtube_uploader.py", 4, 4, timeout=600)

    video_path = get_latest_video()
    log(f"TAMAMLANDI: {video_path}")

    result = {
        "success":    True,
        "video_path": video_path,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
    }
    print("N8N_OUTPUT:" + json.dumps(result))
    return result

if __name__ == "__main__":
    main()
