# Sports Shorts Automation

Spor haberlerinden otomatik YouTube videosu üreten Python pipeline'ı. RSS kaynaklarından güncel haberleri çeker, yapay zekayla Türkçe video metni yazar, seslendirir, stok görüntülerle altyazılı video oluşturur ve YouTube'a yükler. Motor sporları ve futbol için hem Shorts (dikey) hem normal (yatay) video üretir.

## Nasıl çalışır

```
RSS haberleri  →  Groq (Llama 3.3 70B) ile Türkçe metin  →  Seslendirme  →  Pexels stok video + altyazı  →  YouTube API ile yükleme
```

1. **Haber toplama:** Autosport, Motorsport.com, BBC Sport, The Race, Sky Sports, The Guardian, ESPN, TRT Spor gibi RSS kaynaklarından son haberler çekilir; daha önce kullanılan haberler atlanır.
2. **Metin üretimi:** Groq API üzerinden Llama 3.3 70B ile kanca cümlesi, gövde ve kapanıştan oluşan Türkçe video metni yazılır.
3. **Seslendirme:** ElevenLabs anahtarı varsa ElevenLabs, yoksa ücretsiz Microsoft Edge TTS (`tr-TR-AhmetNeural`) kullanılır.
4. **Video kurgusu:** Haberin konusuna göre Pexels'tan stok görüntüler indirilir, ses süresine göre kesilip birleştirilir, altyazılar eklenir. Shorts 1080×1920, normal videolar 1920×1080.
5. **Yükleme:** YouTube Data API v3 ile başlık, açıklama ve etiketlerle yüklenir; yüklenen videolar tekrar yüklenmemek için kaydedilir.

## Pipeline'lar

| Komut | Kategori | Format | Adımlar |
| --- | --- | --- | --- |
| `python main_motorsport_shorts.py` | Motor sporları | Shorts | `rss_scraper` → `shorts_generator` → `video_builder` → `youtube_uploader` |
| `python main_motorsport_long.py` | Motor sporları | Normal | `rss_scraper` → `video_generator` → `video_builder_long` → `youtube_uploader_long` |
| `python main_football_shorts.py` | Futbol | Shorts | `rss_scraper_football` → `shorts_generator_football` → `video_builder_football` → `youtube_uploader_football` |
| `python main_football_long.py` | Futbol | Normal | `rss_scraper_football` → `video_generator_football` → `video_builder_long_football` → `youtube_uploader_long_football` |

`main.py` yükleme yapmadan sadece motor sporları Shorts videosunu üretir, denemek için kullanılabilir.

Her pipeline adımları ayrı süreç olarak çalıştırır, zaman aşımı ve hata durumlarını `data/logs/` altına kaydeder ve sonunda `N8N_OUTPUT:` önekli bir JSON basar; böylece n8n gibi bir otomasyon aracıyla zamanlanabilir.

## Kurulum

**Gereksinimler:** Python 3.10+, PATH'te [FFmpeg](https://ffmpeg.org/download.html) (`ffprobe` kullanılıyor)

```bash
pip install -r requirements.txt
```

`.env.example` dosyasını `.env` olarak kopyalayıp anahtarları gir:

| Değişken | Zorunlu | Nereden alınır |
| --- | --- | --- |
| `GROQ_API_KEY` | Evet | console.groq.com |
| `PEXELS_API_KEY` | Evet | pexels.com/api |
| `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` | Hayır | elevenlabs.io (boşsa Edge TTS kullanılır) |

**YouTube yüklemesi için:** Google Cloud Console'da bir proje aç, YouTube Data API v3'ü etkinleştir, "Masaüstü uygulaması" tipinde OAuth istemcisi oluştur ve indirdiğin JSON'u proje klasörüne `client_secrets.json` adıyla koy. İlk yüklemede tarayıcı açılır, kanal hesabınla giriş yaptıktan sonra oturum `data/youtube_token.pickle` dosyasına kaydedilir.

## Proje yapısı

```
├── main_*.py               # Pipeline'ları uçtan uca çalıştıran giriş noktaları
├── rss_scraper*.py         # Haber toplama
├── shorts_generator*.py    # Shorts metni üretimi
├── video_generator*.py     # Normal video metni üretimi
├── tts_helper.py           # ElevenLabs / Edge TTS seslendirme
├── video_builder*.py       # Stok görüntü + ses + altyazı ile video kurgusu
├── youtube_uploader*.py    # YouTube yüklemesi
└── data/                   # Çalışırken oluşur: haberler, metinler, videolar, loglar (repoya dahil değil)
```

## Notlar

- `.env`, `client_secrets.json` ve `data/youtube_token.pickle` gizli bilgiler içerdiği için `.gitignore` ile repoya dahil edilmez.
- Haber içerikleri ilgili yayıncılara aittir; üretilen metinler özet niteliğindedir.
