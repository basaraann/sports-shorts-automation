# rss_scraper.py
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
    # ── Formula 1 ──────────────────────────────────────────
    "autosport_f1":       "https://www.autosport.com/rss/feed/f1",
    "motorsport_f1":      "https://www.motorsport.com/rss/f1/news/",
    "bbc_f1":             "https://feeds.bbci.co.uk/sport/formula1/rss.xml",
    "the_race":           "https://the-race.com/feed/",
    "racefans":           "https://www.racefans.net/feed/",

    # ── MotoGP ─────────────────────────────────────────────
    "motorsport_motogp":  "https://www.motorsport.com/rss/motogp/news/",
    "autosport_motogp":   "https://www.autosport.com/rss/feed/motogp",

    # ── NASCAR ─────────────────────────────────────────────
    "motorsport_nascar":  "https://www.motorsport.com/rss/nascar-cup/news/",

    # ── WRC Ralli ──────────────────────────────────────────
    "motorsport_wrc":     "https://www.motorsport.com/rss/wrc/news/",

    # ── Formula E ──────────────────────────────────────────
    "motorsport_fe":      "https://www.motorsport.com/rss/formula-e/news/",

    # ── IndyCar ────────────────────────────────────────────
    "motorsport_indycar": "https://www.motorsport.com/rss/indycar/news/",

    # ── Le Mans / Endurance ────────────────────────────────
    "motorsport_wec":     "https://www.motorsport.com/rss/le-mans/news/",

    # ── DTM / Touring Car ──────────────────────────────────
    "motorsport_dtm":     "https://www.motorsport.com/rss/dtm/news/",

    # ── Genel Motor Sporlari ───────────────────────────────
    "autosport_all":      "https://www.autosport.com/rss/feed/all",
    "motorsport_all":     "https://www.motorsport.com/rss/all/news/",
}

OUTPUT_FILE    = Path("data/raw_articles.json")
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

                # Kategori tag'i ekle
                tags = [t.term for t in entry.get("tags", [])] if entry.get("tags") else []

                all_articles.append({
                    "source":     name,
                    "category":   name.split("_")[1] if "_" in name else "motorsport",
                    "title":      title,
                    "url":        link,
                    "summary":    summary,
                    "date":       date,
                    "tags":       tags,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })
                count += 1

            print(f"  {count} makale bulundu.")

        except Exception as e:
            print(f"  BEKLENMEDIK HATA: {e}")
            failed.append(name)
            continue

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)

    print(f"\nToplam {len(all_articles)} makale -> {OUTPUT_FILE}")

    if failed:
        print(f"Basarisiz kaynaklar: {', '.join(failed)}")

    # Kategorilere gore ozet
    from collections import Counter
    cats = Counter(a["category"] for a in all_articles)
    print("\nKategori dagilimi:")
    for cat, count in cats.most_common():
        print(f"  {cat}: {count} makale")

    return all_articles


if __name__ == "__main__":
    scrape_rss()
