# main.py
import subprocess
import sys

print("=== 1/3 Haberler cekiliyor ===")
subprocess.run([sys.executable, "rss_scraper.py"], check=True)

print("\n=== 2/3 Script uretiliyor ===")
subprocess.run([sys.executable, "shorts_generator.py"], check=True)

print("\n=== 3/3 Video olusturuluyor ===")
subprocess.run([sys.executable, "video_builder.py"], check=True)

print("\nTamamlandi!")