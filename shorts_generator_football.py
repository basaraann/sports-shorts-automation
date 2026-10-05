# shorts_generator_football.py
import json, os, sys
from pathlib import Path
from datetime import datetime, timezone
from groq import Groq
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL  = "llama-3.3-70b-versatile"

INPUT_FILE   = Path("data/raw_articles_football.json")
OUTPUT_FILE  = Path("data/shorts_scripts_football.json")
USED_FILE    = Path("data/used_articles_football.json")
MIN_WORDS    = 60
MAX_WORDS    = 75
MAX_TRIES    = 3


def load_used_urls():
    if USED_FILE.exists():
        with open(USED_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_used_url(url):
    used = load_used_urls()
    used.add(url)
    USED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(used), f, ensure_ascii=False, indent=2)


def pick_best_article(articles):
    used_urls = load_used_urls()
    fresh     = [a for a in articles if a["url"] not in used_urls]

    if not fresh:
        print("Tum haberler kullanildi, sifirlaniyor...")
        with open(USED_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        fresh = articles

    print(f"Kullanilmamis haber: {len(fresh)}/{len(articles)}")

    titles_block = "\n".join(
        f"{i+1}. [{a['source']}] {a['title']}"
        for i, a in enumerate(fresh)
    )
    r = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Futbol haberlerinden en dramatik olanin numarasini yaz. Sadece sayi."},
            {"role": "user",   "content": titles_block},
        ],
        max_tokens=5, temperature=0.3,
    )
    idx    = int(r.choices[0].message.content.strip()) - 1
    chosen = fresh[max(0, min(idx, len(fresh)-1))]
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
            {"role": "user", "content": f"Baslik: {title}\nOzet: {summary[:1200]}"},
        ],
        max_tokens=800, temperature=0.3,
        response_format={"type": "json_object"},
    )
    result = json.loads(r.choices[0].message.content)
    print(f"Turkce baslik: {result.get('baslik','')[:80]}")
    return result.get("baslik", title), result.get("ozet", summary)


def generate_script(tr_title, tr_summary, orig_title, orig_url, attempt=1):
    extra = f"\nBU SEFER {MIN_WORDS}-{MAX_WORDS} KELIME ARASI YAZ. FAZLA YAZMA." if attempt > 1 else ""

    r = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"""Sen bir futbol YouTube Shorts scriptwriterisin.
Asagida TAMAMEN TURKCE bir haber var. Bunu kullanarak Turkce script yaz.

ONEMLI: Toplam {MIN_WORDS}-{MAX_WORDS} kelime olmali. Ne fazla ne az.

HOOK (1-2 kisa cumle): Sok edici giris.
BODY (5-7 cumle): Dramatik anlatim, soru yok, her cumle max 10 kelime.
CTA: "Takip et, bir sonraki videoyu kacirma."{extra}

SADECE JSON: {{"hook":"...","body":"...","cta":"..."}}""",
            },
            {"role": "user", "content": f"Turkce Baslik: {tr_title}\nTurkce Ozet: {tr_summary}"},
        ],
        max_tokens=400, temperature=0.9,
        response_format={"type": "json_object"},
    )
    script = json.loads(r.choices[0].message.content)
    full   = f"{script['hook']} {script['body']} {script['cta']}"
    script.update({
        "full_text":    full,
        "source_title": orig_title,
        "source_url":   orig_url,
        "word_count":   len(full.split()),
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
        if MIN_WORDS <= script["word_count"] <= MAX_WORDS + 10:
            print("Yeterli!")
            break
        print("Aralikta degil, tekrar...")

    save_used_url(article["url"])

    print(f"\nHOOK: {script['hook']}")
    print(f"BODY: {script['body'][:100]}...")
    print(f"KELIME: {script['word_count']}\n")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = json.load(open(OUTPUT_FILE, encoding="utf-8")) if OUTPUT_FILE.exists() else []
    existing.append(script)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"Kaydedildi -> {OUTPUT_FILE}")
    return script

if __name__ == "__main__":
    run()
