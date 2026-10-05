# video_generator_football.py
import json, os, sys
from pathlib import Path
from datetime import datetime, timezone
from groq import Groq
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL  = "llama-3.3-70b-versatile"

INPUT_FILE  = Path("data/raw_articles_football.json")
OUTPUT_FILE = Path("data/video_scripts_football.json")
MIN_WORDS   = 380
MAX_TRIES   = 3


def pick_best_article(articles):
    titles_block = "\n".join(
        f"{i+1}. [{a['source']}] {a['title']}"
        for i, a in enumerate(articles)
    )
    r = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Futbol haberlerinden en dramatik olanin numarasini yaz. Sadece sayi."},
            {"role": "user",   "content": titles_block},
        ],
        max_tokens=5, temperature=0.3,
    )
    idx = int(r.choices[0].message.content.strip()) - 1
    chosen = articles[max(0, min(idx, len(articles)-1))]
    print(f"Secilen: [{chosen['source']}] {chosen['title']}")
    return chosen


def translate_to_turkish(title, summary):
    r = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Sen bir cevirimensin. Ingilizce haber baslik ve ozetini "
                    "akici dogal Turkceye cevir. "
                    "JSON: {\"baslik\": \"...\", \"ozet\": \"...\"}"
                ),
            },
            {"role": "user", "content": f"Baslik: {title}\nOzet: {summary[:2000]}"},
        ],
        max_tokens=1200, temperature=0.3,
        response_format={"type": "json_object"},
    )
    result = json.loads(r.choices[0].message.content)
    print(f"Turkce baslik: {result.get('baslik','')[:80]}")
    return result.get("baslik", title), result.get("ozet", summary)


def generate_script(tr_title, tr_summary, orig_title, orig_url, attempt=1):
    extra = f"\nBU SEFER KESINLIKLE EN AZ {MIN_WORDS} KELIME YAZ." if attempt > 1 else ""

    r = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"""Sen profesyonel bir futbol YouTube scriptwriterisin.
Asagida TAMAMEN TURKCE bir haber var. Bunu kullanarak 3 dakikalik Turkce video scripti yaz.
TOPLAM EN AZ {MIN_WORDS} KELIME OLMALI.

YAPI:
HOOK (40-50 kelime): Sok edici giris.
GIRIS (50-60 kelime): Kim bu oyuncu/takim, neden onemli?
OLAY (100-120 kelime): Ne oldu adim adim, her detay.
ARKA_PLAN (60-70 kelime): Lig tablosu, sampiyonluk etkisi.
PERSPEKTIF (60-70 kelime): Oyuncu ve teknik direktor ne dedi?
ANALIZ (60-70 kelime): Bundan sonra ne olur?
KAPANIS (30-40 kelime): Son cumle: "Kanalimiza abone olun, bir sonraki videoyu kacirmayin."{extra}

SADECE JSON:
{{"hook":"...","giris":"...","olay":"...","arka_plan":"...","perspektif":"...","analiz":"...","kapanis":"..."}}""",
            },
            {
                "role": "user",
                "content": f"Turkce Baslik: {tr_title}\nTurkce Ozet: {tr_summary}",
            },
        ],
        max_tokens=2500, temperature=0.9,
        response_format={"type": "json_object"},
    )

    script    = json.loads(r.choices[0].message.content)
    full_text = " ".join([
        script.get("hook",""), script.get("giris",""),
        script.get("olay",""), script.get("arka_plan",""),
        script.get("perspektif",""), script.get("analiz",""),
        script.get("kapanis",""),
    ])
    script.update({
        "full_text":    full_text,
        "source_title": orig_title,
        "source_url":   orig_url,
        "word_count":   len(full_text.split()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })
    return script


def run():
    with open(INPUT_FILE, encoding="utf-8") as f:
        articles = json.load(f)

    article              = pick_best_article(articles)
    tr_title, tr_summary = translate_to_turkish(article["title"], article["summary"])

    script = None
    for attempt in range(1, MAX_TRIES+1):
        print(f"Script uretiliyor... ({attempt}/{MAX_TRIES})")
        script = generate_script(tr_title, tr_summary, article["title"], article["url"], attempt)
        print(f"Kelime: {script['word_count']}")
        if script["word_count"] >= MIN_WORDS:
            print("Yeterli!")
            break
        print(f"Yetersiz, tekrar...")

    print(f"\nHOOK      : {script.get('hook','')}")
    print(f"GIRIS     : {script.get('giris','')[:80]}...")
    print(f"OLAY      : {script.get('olay','')[:80]}...")
    print(f"KAPANIS   : {script.get('kapanis','')}")
    print(f"\nFINAL KELIME: {script['word_count']}\n")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = json.load(open(OUTPUT_FILE, encoding="utf-8")) if OUTPUT_FILE.exists() else []
    existing.append(script)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"Kaydedildi -> {OUTPUT_FILE}")
    return script

if __name__ == "__main__":
    run()
