# tts_helper.py - Tum scriptler bunu import eder
# pip install elevenlabs edge-tts
import os, asyncio, re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY  = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "")
EDGE_VOICE          = "tr-TR-AhmetNeural"


def clean_text(text):
    """Bozuk karakterleri temizle."""
    replacements = {
        "\t": " ",
        "\r": " ",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n+', ' ', text)
    return text.strip()


def generate_audio_file(text, output_path, rate="+25%"):
    text = clean_text(text)
    if ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID:
        print("ElevenLabs TTS kullaniliyor...")
        return _elevenlabs_tts(text, Path(output_path))
    else:
        print("Edge TTS kullaniliyor...")
        return _edge_tts(text, Path(output_path), rate)


def _elevenlabs_tts(text, output_path):
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import save
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio  = client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            text=text,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        save(audio, str(output_path))
        print(f"Ses (ElevenLabs): {output_path}")
        return output_path
    except Exception as e:
        print(f"ElevenLabs hatasi: {e}, Edge TTS'e geciliyor...")
        return _edge_tts(text, output_path, "+25%")


async def _edge_tts_async(text, output_path, rate):
    import edge_tts
    communicate = edge_tts.Communicate(text, EDGE_VOICE, rate=rate)
    await communicate.save(str(output_path))

def _edge_tts(text, output_path, rate="+25%"):
    asyncio.run(_edge_tts_async(text, str(output_path), rate))
    print(f"Ses (Edge TTS): {output_path}")
    return output_path
