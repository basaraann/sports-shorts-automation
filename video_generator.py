# video_generator.py - Normal YouTube video icin metin uretici
# pip install groq

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from groq import Groq
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL  = "llama-3.3-70b-versatile"

INPUT_FILE  = Path("data/raw_articles.json")
OUTPUT_FILE = Path("data/video_scripts.json")

MIN_WORDS = 250
MAX_TRIES = 3


def pick_best_article(articles):
    titles_block = "\n".join(
        f"{i+1}. [{a['source']}] {a['title']}"
        for i, a in enumerate(articles)
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Sen bir YouTube icerik stratejistisin. "
                    "Motor sporlari haberlerinden en dramatik, "
                    "merak uyandiran haberi sec. "
                    "Sadece haberin numarasini yaz."
                ),
            },
            {"role": "user", "content": titles_block},
        ],
        max_tokens=5,
        temperature=0.3,
    )
    idx = int(response.choices[0].message.content.strip()) - 1
    chosen = articles[max(0, min(idx, len(articles) - 1))]
    print(f"Secilen: [{chosen['source']}] {chosen['title']}")
    return chosen


def generate_script(article, attempt=1):
    extra = ""
    if attempt > 1:
        extra = f"\n\nONCEKI DENEMEDE YETERLI KELIME URETEMEDIN. BU SEFER KESINLIKLE HER BOLUMU DOLU YAZ. TOPLAM EN AZ {MIN_WORDS} KELIME OLMALI."

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"""Sen profesyonel bir motor sporlari YouTube scriptwriterisin.
3 dakikalik video icin script yaziyorsun. BU COK ONEMLI: toplam metin EN AZ {MIN_WORDS} kelime olmali.

ZORUNLU YAPI - HER BOLUMU DOLU YAZ:

HOOK (40-50 kelime):
Sok edici, merak uyandiran giris. Izleyiciyi ilk 5 saniyede yakala.

GIRIS (50-60 kelime):
Kim bu surucu? Bu takim nasil bir gecmise sahip? Neden bu haber onemli?

OLAY (100-120 kelime):
Ne oldu adim adim anlat. Kacinci turdu? Hava nasıldi? Surucu ne yapti?
Her detayi ver. Sinema gibi canlandir.

ARKA_PLAN (60-70 kelime):
Bu sezon nasil gidiyor? Sampiyonluk tablosu ne durumda?
Bu olay puan siralamasi icin ne anlama geliyor?

PERSPEKTIF (60-70 kelime):
Surucu ne hissetti? Takim ne dedi? Basin toplantisinda ne konustu?
Duygusal anlar, ozel sozler.

ANALIZ (60-70 kelime):
Bundan sonra ne olabilir? Hangi takim avantaj kazandi?
Bir uzman gozuyle degerlendirme yap.

KAPANIS (30-40 kelime):
Guclu kapaniş. Izleyiciyi dusundur. Abone olmaya tesvık et.
Son cumle: "Kanalimiza abone olun, bir sonraki videoyu kacirmayin."{extra}

SADECE JSON don:
{{"hook":"...","giris":"...","olay":"...","arka_plan":"...","perspektif":"...","analiz":"...","kapanis":"..."}}""",
            },
            {
                "role": "user",
                "content": (
                    f"Baslik: {article['title']}\n"
                    f"Ozet: {article['summary'][:2000]}"
                ),
            },
        ],
        max_tokens=2500,
        temperature=0.9,
        response_format={"type": "json_object"},
    )

    script = json.loads(response.choices[0].message.content)
    full_text = " ".join([
        script.get("hook", ""),
        script.get("giris", ""),
        script.get("olay", ""),
        script.get("arka_plan", ""),
        script.get("perspektif", ""),
        script.get("analiz", ""),
        script.get("kapanis", ""),
    ])

    script["full_text"]    = full_text
    script["source_title"] = article["title"]
    script["source_url"]   = article["url"]
    script["word_count"]   = len(full_text.split())
    script["generated_at"] = datetime.now(timezone.utc).isoformat()
    return script


def run():
    with open(INPUT_FILE, encoding="utf-8") as f:
        articles = json.load(f)

    article = pick_best_article(articles)
    script  = None

    for attempt in range(1, MAX_TRIES + 1):
        print(f"Script uretiliyor... (deneme {attempt}/{MAX_TRIES})")
        script = generate_script(article, attempt=attempt)
        print(f"Kelime sayisi: {script['word_count']}")

        if script["word_count"] >= MIN_WORDS:
            print("Kelime sayisi yeterli!")
            break
        else:
            print(f"Yetersiz ({script['word_count']} < {MIN_WORDS}), tekrar deneniyor...")

    print("\n-- URETILEN SCRIPT --")
    print(f"HOOK       : {script.get('hook', '')}")
    print(f"GIRIS      : {script.get('giris', '')[:80]}...")
    print(f"OLAY       : {script.get('olay', '')[:80]}...")
    print(f"ARKA PLAN  : {script.get('arka_plan', '')[:80]}...")
    print(f"PERSPEKTIF : {script.get('perspektif', '')[:80]}...")
    print(f"ANALIZ     : {script.get('analiz', '')[:80]}...")
    print(f"KAPANIS    : {script.get('kapanis', '')}")
    print(f"\nFINAL KELIME SAYISI: {script['word_count']}")
    print("---------------------\n")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            existing = json.load(f)
    existing.append(script)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"Script kaydedildi -> {OUTPUT_FILE}")
    return script


if __name__ == "__main__":
    run()
