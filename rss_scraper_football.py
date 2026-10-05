# rss_scraper_football.py
# pip install feedparser

import feedparser
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

RSS_SOURCES = {
    # ── Premier Lig ────────────────────────────────────────
    "bbc_football":       "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "skysports_pl":       "https://www.skysports.com/rss/12040",
    "guardian_football":  "https://www.theguardian.com/football/rss",

    # ── Champions League ───────────────────────────────────
    "skysports_ucl":      "https://www.skysports.com/rss/12691",

    # ── La Liga ────────────────────────────────────────────
    "skysports_laliga":   "https://www.skysports.com/rss/12691",
    "marca":              "https://e00-marca.uecdn.es/rss/futbol/primera-division.xml",

    # ── Serie A ────────────────────────────────────────────
    "skysports_seriea":   "https://www.skysports.com/rss/12078",

    # ── Bundesliga ─────────────────────────────────────────
    "skysports_bundes":   "https://www.skysports.com/rss/12098",

    # ── Turkiye Supra Lig ──────────────────────────────────
    "trt_spor":           "https://www.trthaber.com/rss/spor.rss",
    "fanatik":            "https://www.fanatik.com.tr/rss",

    # ── Genel Futbol ───────────────────────────────────────
    "espn_football":      "https://www.espn.com/espn/rss/soccer/news",
    "goal_com":           "https://www.goal.com/feeds/en/news",
    "fourfourtwo":        "https://www.fourfourtwo.com/rss",
}

OUTPUT_FILE    = Path("data/raw_articles_football.json")
MAX_PER_SOURCE = 8


def scrape_rss():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    all_articles = []
    failed       = []

    for name, url in RSS_SOURCES.items():
        try:
            print(f"[{name}] cekiliyor...")
            feed = feedparser.parse(url)

            if feed.bozo and not feed.entries:
                print(f"  HATA: {feed.bozo_exception}")
                failed.append(name)
                continue

            count = 0
            for entry in feed.entries[:MAX_PER_SOURCE]:
                title   = entry.get("title", "").strip()
                link    = entry.get("link", "").strip()
                summary = entry.get("summary", "").strip()[:1500]
                date    = entry.get("published", "")

                if not title or not link:
                    continue

                all_articles.append({
                    "source":     name,
                    "category":   "football",
                    "title":      title,
                    "url":        link,
                    "summary":    summary,
                    "date":       date,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })
                count += 1

            print(f"  {count} makale bulundu.")

        except Exception as e:
            print(f"  HATA: {e}")
            failed.append(name)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)

    print(f"\nToplam {len(all_articles)} makale -> {OUTPUT_FILE}")
    if failed:
        print(f"Basarisiz: {', '.join(failed)}")

    return all_articles


if __name__ == "__main__":
    scrape_rss()
