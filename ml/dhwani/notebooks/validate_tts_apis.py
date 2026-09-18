"""
Quick validation script for Sarvam AI and ElevenLabs TTS APIs.
Reads API keys from .env and tests each with a single short request.
"""
import os
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

SARVAM_KEY = os.getenv("SARVAM_API_KEY", "")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY", "")

print("=" * 60)
print("  TTS API VALIDATION")
print("=" * 60)

# --- Sarvam AI ---
print("\n  [1/2] Sarvam AI (Bulbul v3)...")
if not SARVAM_KEY or SARVAM_KEY == "your-sarvam-api-key-here":
    print("  [SKIP] SARVAM_API_KEY not set in .env")
else:
    try:
        from sarvamai import SarvamAI
        client = SarvamAI(api_subscription_key=SARVAM_KEY)
        resp = client.text_to_speech.convert(
            text="Hello, this is a test of the Sarvam API.",
            language_code="en-IN",
            speaker="shubh",
            model="bulbul:v3",
        )
        audio_count = len(resp.audios) if resp.audios else 0
        audio_len = len(resp.audios[0]) if audio_count > 0 else 0
        print(f"  [OK] Sarvam API working!")
        print(f"       Response: {audio_count} audio(s), first={audio_len:,} chars (base64)")
        print(f"       Voices: shubh, ananya, arjun, manisha, kunal + many more")
        print(f"       Languages: hi-IN, en-IN, mr-IN, gu-IN, bn-IN, ta-IN, te-IN, kn-IN, ml-IN, pa-IN, od-IN")
    except Exception as e:
        print(f"  [FAIL] Sarvam API error: {e}")

# --- ElevenLabs ---
print("\n  [2/2] ElevenLabs (v3)...")
if not ELEVENLABS_KEY or "your-" in ELEVENLABS_KEY:
    print("  [SKIP] ELEVENLABS_API_KEY not set in .env")
    print("         Get a free key at https://elevenlabs.io (10K chars/month)")
else:
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=ELEVENLABS_KEY)

        # Test TTS directly with a known voice ID (George)
        audio = client.text_to_speech.convert(
            text="Hello, this is a test of the ElevenLabs API.",
            voice_id="JBFqnCBsd6RMkjVDRZzb",  # George
            model_id="eleven_v3",
            output_format="mp3_44100_128",
        )
        audio_bytes = b""
        for chunk in audio:
            audio_bytes += chunk
        print(f"  [OK] ElevenLabs API working! Audio: {len(audio_bytes):,} bytes")
        print(f"       Model: eleven_v3")
        print(f"       Test voice: George (JBFqnCBsd6RMkjVDRZzb)")

    except Exception as e:
        print(f"  [FAIL] ElevenLabs API error: {e}")

print("\n" + "=" * 60)
print("  NEXT STEPS")
print("=" * 60)
print("  To generate the full spoof dataset, run:")
print("    python ml/dhwani/notebooks/generate_spoof_dataset.py --max-per-lang 50")
print("=" * 60)
