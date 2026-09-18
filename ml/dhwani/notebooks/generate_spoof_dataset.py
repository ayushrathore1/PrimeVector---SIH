"""
Dhwani Spoof Dataset Generator — Sarvam AI + ElevenLabs
=======================================================

Generates AI-synthesized voice samples using Sarvam AI (Indian languages)
and ElevenLabs (multilingual) to build a real spoof dataset for training
the Dhwani deepfake detector.

WHY THIS IS BETTER THAN ASVspoof:
  - Uses the EXACT TTS systems you want to detect in production
  - Indian language coverage (Hindi, Marathi, Gujarati) via Sarvam
  - High-quality neural TTS via ElevenLabs
  - Full control over voice diversity, text content, and volume

SETUP:
  1. pip install sarvamai elevenlabs soundfile librosa
  2. Set your API keys:
     - SARVAM_API_KEY=your_key  (get from dashboard.sarvam.ai)
     - ELEVENLABS_API_KEY=your_key  (get from elevenlabs.io)
  3. Run this script locally (NOT on Colab — saves API credits)
  4. Upload the output folder to Colab

OUTPUT:
  spoof_generated/
  ├── sarvam/
  │   ├── hi/  (Hindi samples)
  │   ├── en/  (English samples)
  │   ├── mr/  (Marathi samples)
  │   └── gu/  (Gujarati samples)
  ├── elevenlabs/
  │   ├── en/
  │   └── hi/
  └── manifest.csv

USAGE:
  python generate_spoof_dataset.py --sarvam-key YOUR_KEY --elevenlabs-key YOUR_KEY
  python generate_spoof_dataset.py --sarvam-only --sarvam-key YOUR_KEY
  python generate_spoof_dataset.py --elevenlabs-only --elevenlabs-key YOUR_KEY
"""

import os
import sys
import csv
import time
import hashlib
import argparse
import json
from pathlib import Path
from typing import Optional

# Audio processing
import numpy as np

try:
    import soundfile as sf
except ImportError:
    print("Install soundfile: pip install soundfile")
    sys.exit(1)

try:
    import librosa
except ImportError:
    print("Install librosa: pip install librosa")
    sys.exit(1)

# ============================================================
# Configuration
# ============================================================

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "spoof_generated")
SAMPLE_RATE = 16000  # Must match Dhwani pipeline
SAMPLES_PER_VOICE = 25  # Samples per voice variant

# ============================================================
# Text Prompts — Diverse Indian Language Content
# ============================================================

PROMPTS = {
    "hi-IN": [
        "भारत एक विविधताओं से भरा देश है जहाँ अनेक भाषाएँ बोली जाती हैं।",
        "आज मौसम बहुत अच्छा है, बाहर घूमने का मन कर रहा है।",
        "क्या आप मुझे बता सकते हैं कि नज़दीकी अस्पताल कहाँ है?",
        "मेरा नाम राहुल है और मैं दिल्ली में रहता हूँ।",
        "इस साल की फसल बहुत अच्छी हुई है, किसान खुश हैं।",
        "बच्चों को स्कूल में अच्छी शिक्षा मिलनी चाहिए।",
        "ट्रेन का समय बदल गया है, कृपया नया समय देखें।",
        "भारतीय खाना पूरी दुनिया में मशहूर है।",
        "नमस्ते, मैं अपने बैंक खाते की जानकारी चाहता हूँ।",
        "कल रात बारिश हुई थी और सड़कें भीगी हुई थीं।",
        "हमारे गाँव में एक नई सड़क बन रही है।",
        "मुझे एक गिलास पानी चाहिए, कृपया दे दीजिए।",
        "आपका फोन नंबर क्या है? मुझे बाद में कॉल करना है।",
        "दीपावली भारत का सबसे बड़ा त्योहार है।",
        "मैं कल सुबह छह बजे उठा और योग किया।",
        "सरकार ने नई योजना की घोषणा की है।",
        "पिछले हफ्ते मैं मुंबई गया था, वहाँ बहुत गर्मी थी।",
        "कृपया अपना आधार कार्ड दिखाएँ।",
        "इस महीने बिजली का बिल बहुत ज्यादा आया है।",
        "मेरे परिवार में पाँच सदस्य हैं।",
        "आज बाजार में सब्जियाँ बहुत सस्ती मिल रही हैं।",
        "क्या आप हिंदी में बात कर सकते हैं?",
        "मुझे एक टिकट चाहिए, दिल्ली से जयपुर तक।",
        "यह किताब बहुत रोचक है, मैंने इसे एक दिन में पढ़ लिया।",
        "भारत की जनसंख्या एक सौ चालीस करोड़ से अधिक है।",
    ],
    "en-IN": [
        "Good morning, I would like to check my account balance please.",
        "The weather in Bangalore is pleasant throughout the year.",
        "Can you please transfer five thousand rupees to my savings account?",
        "India has a rich cultural heritage spanning thousands of years.",
        "I need to book a flight ticket from Delhi to Mumbai for tomorrow.",
        "The new government policy will benefit millions of farmers.",
        "Please verify my identity before processing the transaction.",
        "Technology is transforming the way we live and work in India.",
        "I would like to report a suspicious transaction on my credit card.",
        "The cricket match between India and Australia starts at four PM.",
        "Education is the most powerful weapon to change the world.",
        "Can you send me the documents by email before five o'clock?",
        "The traffic on the highway was terrible during rush hour today.",
        "My name is Priya Sharma and I am calling from Hyderabad.",
        "The hospital is located near the railway station on Main Road.",
        "Please confirm my appointment for tomorrow at ten thirty AM.",
        "The stock market showed significant growth this quarter.",
        "I have been living in this city for the past fifteen years.",
        "Water conservation is very important for our future generations.",
        "The train from Chennai to Kolkata departs at six in the evening.",
        "Could you please repeat that? I could not hear you properly.",
        "The annual report shows a twenty percent increase in revenue.",
        "My daughter is studying engineering at IIT Bombay.",
        "Please update my mobile number in your records.",
        "The monsoon season brings relief from the scorching summer heat.",
    ],
    "mr-IN": [
        "महाराष्ट्र हे भारतातील एक प्रमुख राज्य आहे.",
        "मुंबई ही भारताची आर्थिक राजधानी आहे.",
        "आज पावसाची शक्यता आहे, छत्री घेऊन जा.",
        "माझं नाव अमित आहे आणि मी पुण्यात राहतो.",
        "शाळेत मुलांना चांगलं शिक्षण मिळालं पाहिजे.",
        "कृपया तुमचं आधार कार्ड दाखवा.",
        "या महिन्यात वीज बिल खूप जास्त आलं आहे.",
        "माझ्या कुटुंबात पाच सदस्य आहेत.",
        "आज बाजारात भाज्या खूप स्वस्त मिळत आहेत.",
        "गणपती बाप्पा मोरया, पुढच्या वर्षी लवकर या.",
        "तुम्ही मराठीत बोलू शकता का?",
        "मला एक तिकीट हवं आहे, पुणे ते मुंबई.",
        "हे पुस्तक खूप रोचक आहे.",
        "आमच्या गावात एक नवीन रस्ता बनत आहे.",
        "सकाळी लवकर उठणं आरोग्यासाठी चांगलं असतं.",
        "कृपया माझा फोन नंबर नोंदवा.",
        "शेतकऱ्यांना चांगला पाऊस हवा असतो.",
        "मी काल संध्याकाळी बागेत फिरायला गेलो.",
        "तुमच्या मदतीबद्दल खूप खूप धन्यवाद.",
        "या वर्षी दिवाळी खूप छान साजरी झाली.",
        "माझ्या मुलाला अभियांत्रिकीत रस आहे.",
        "कृपया पाणी आणा, मला खूप तहान लागली आहे.",
        "रेल्वे स्थानक इथून दोन किलोमीटर अंतरावर आहे.",
        "आज सकाळपासून खूप थंडी आहे.",
        "भारतीय संविधान हे जगातील सर्वात मोठं लिखित संविधान आहे.",
    ],
    "gu-IN": [
        "ગુજરાત ભારતનું એક સમૃદ્ધ રાજ્ય છે.",
        "અમદાવાદ ગુજરાતનું સૌથી મોટું શહેર છે.",
        "આજે હવામાન ખૂબ સારું છે, બહાર ફરવા જઈએ.",
        "મારું નામ વિજય છે અને હું સુરતમાં રહું છું.",
        "નવરાત્રી ગુજરાતનો સૌથી મોટો તહેવાર છે.",
        "ગુજરાતી ભોજન આખી દુનિયામાં પ્રખ્યાત છે.",
        "કૃપા કરીને તમારું આધાર કાર્ડ બતાવો.",
        "આ મહિનાનું વીજ બિલ ખૂબ વધારે આવ્યું છે.",
        "મારા પરિવારમાં પાંચ સભ્યો છે.",
        "આજે બજારમાં શાકભાજી ખૂબ સસ્તા મળી રહ્યા છે.",
        "ગાંધીજીનો જન્મ ગુજરાતના પોરબંદરમાં થયો હતો.",
        "તમે ગુજરાતીમાં વાત કરી શકો છો?",
        "મને એક ટિકિટ જોઈએ છે, અમદાવાદથી મુંબઈ.",
        "આ પુસ્તક ખૂબ રસપ્રદ છે.",
        "અમારા ગામમાં એક નવો રસ્તો બની રહ્યો છે.",
        "સવારે વહેલા ઉઠવું સ્વાસ્થ્ય માટે સારું છે.",
        "ખેડૂતોને સારા વરસાદની જરૂર છે.",
        "હું ગઈકાલે સાંજે બગીચામાં ફરવા ગયો હતો.",
        "તમારી મદદ માટે ખૂબ ખૂબ આભાર.",
        "આ વર્ષે દિવાળી ખૂબ સરસ ઉજવાઈ.",
        "મારા દીકરાને એન્જિનિયરિંગમાં રસ છે.",
        "કૃપા કરીને પાણી લાવો, મને ખૂબ તરસ લાગી છે.",
        "રેલવે સ્ટેશન અહીંથી બે કિલોમીટર દૂર છે.",
        "આજે સવારથી ખૂબ ઠંડી છે.",
        "ભારતનું બંધારણ દુનિયાનું સૌથી મોટું લખાયેલું બંધારણ છે.",
    ],
}

# ============================================================
# Sarvam AI Voices (Bulbul v3)
# ============================================================

SARVAM_VOICES = {
    "hi-IN": ["shubh", "ananya", "arjun", "manisha", "kunal"],
    "en-IN": ["shubh", "ananya", "arjun", "manisha", "kunal"],
    "mr-IN": ["shubh", "ananya", "arjun"],
    "gu-IN": ["shubh", "ananya", "arjun"],
}

# ============================================================
# ElevenLabs Voices
# ============================================================

ELEVENLABS_VOICES = [
    "Rachel", "Domi", "Bella", "Antoni", "Elli",
    "Josh", "Arnold", "Adam", "Sam",
]

# ============================================================
# Generator Functions
# ============================================================

def generate_sarvam(api_key: str, output_dir: str, max_per_lang: int = 50):
    """Generate spoof samples using Sarvam AI TTS (Bulbul v3)."""
    try:
        from sarvamai import SarvamAI
        import base64
    except ImportError:
        print("  Install sarvamai: pip install sarvamai")
        return []

    client = SarvamAI(api_subscription_key=api_key)
    metadata = []
    
    print("=" * 60)
    print("  🔊 GENERATING SARVAM AI TTS SAMPLES")
    print("=" * 60)

    for lang_code, prompts in PROMPTS.items():
        lang_short = lang_code.split("-")[0]
        lang_dir = os.path.join(output_dir, "sarvam", lang_short)
        os.makedirs(lang_dir, exist_ok=True)

        voices = SARVAM_VOICES.get(lang_code, ["shubh"])
        count = 0

        print(f"\n  Language: {lang_code} ({len(voices)} voices × {len(prompts)} prompts)")

        for prompt_idx, prompt in enumerate(prompts):
            if count >= max_per_lang:
                break

            for voice in voices:
                if count >= max_per_lang:
                    break

                try:
                    # Vary pace slightly for diversity
                    pace = np.random.choice([0.9, 1.0, 1.0, 1.1])

                    response = client.text_to_speech.convert(
                        text=prompt,
                        language_code=lang_code,
                        speaker=voice,
                        pace=pace,
                    )

                    audio_bytes = base64.b64decode(response.audio)

                    # Save raw then convert to 16kHz mono WAV
                    temp_path = os.path.join(lang_dir, f"_temp_{count}.wav")
                    with open(temp_path, "wb") as f:
                        f.write(audio_bytes)

                    # Load and resample to 16kHz mono
                    y, sr = librosa.load(temp_path, sr=SAMPLE_RATE, mono=True)
                    os.remove(temp_path)

                    if len(y) < SAMPLE_RATE * 0.5:  # Skip < 0.5s
                        continue

                    sample_id = hashlib.md5(
                        f"sarvam_{lang_code}_{voice}_{prompt_idx}".encode()
                    ).hexdigest()[:12]

                    filename = f"{sample_id}.wav"
                    filepath = os.path.join(lang_dir, filename)
                    sf.write(filepath, y, SAMPLE_RATE)

                    metadata.append({
                        "sample_id": sample_id,
                        "speaker_id": f"sarvam_{voice}",
                        "language": lang_short,
                        "duration": round(len(y) / SAMPLE_RATE, 2),
                        "source": "sarvam",
                        "generator": f"sarvam_bulbul_v3_{voice}",
                        "voice": voice,
                        "pace": pace,
                        "label": "spoof",
                        "attack_type": "tts",
                        "file_path": filepath,
                    })
                    count += 1

                    if count % 10 == 0:
                        print(f"    Generated {count}/{max_per_lang} for {lang_code}")

                    # Rate limiting — be respectful to the API
                    time.sleep(0.5)

                except Exception as e:
                    print(f"    ⚠️  Sarvam error ({voice}, prompt {prompt_idx}): {e}")
                    time.sleep(1)
                    continue

        print(f"  ✅ {lang_code}: {count} samples generated")

    return metadata


def generate_elevenlabs(api_key: str, output_dir: str, max_per_lang: int = 50):
    """Generate spoof samples using ElevenLabs TTS."""
    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        print("  Install elevenlabs: pip install elevenlabs")
        return []

    client = ElevenLabs(api_key=api_key)
    metadata = []

    print("=" * 60)
    print("  🔊 GENERATING ELEVENLABS TTS SAMPLES")
    print("=" * 60)

    # ElevenLabs primarily English + Hindi
    el_langs = {
        "en-IN": PROMPTS["en-IN"],
        "hi-IN": PROMPTS["hi-IN"],
    }

    for lang_code, prompts in el_langs.items():
        lang_short = lang_code.split("-")[0]
        lang_dir = os.path.join(output_dir, "elevenlabs", lang_short)
        os.makedirs(lang_dir, exist_ok=True)

        count = 0

        print(f"\n  Language: {lang_code} ({len(ELEVENLABS_VOICES)} voices)")

        for prompt_idx, prompt in enumerate(prompts):
            if count >= max_per_lang:
                break

            for voice in ELEVENLABS_VOICES:
                if count >= max_per_lang:
                    break

                try:
                    audio_gen = client.generate(
                        text=prompt,
                        voice=voice,
                        model="eleven_multilingual_v2",
                    )

                    # Collect audio chunks
                    audio_chunks = b""
                    for chunk in audio_gen:
                        audio_chunks += chunk

                    # Save as temp mp3 then convert
                    temp_path = os.path.join(lang_dir, f"_temp_{count}.mp3")
                    with open(temp_path, "wb") as f:
                        f.write(audio_chunks)

                    # Load and resample to 16kHz mono WAV
                    y, sr = librosa.load(temp_path, sr=SAMPLE_RATE, mono=True)
                    os.remove(temp_path)

                    if len(y) < SAMPLE_RATE * 0.5:
                        continue

                    sample_id = hashlib.md5(
                        f"elevenlabs_{lang_code}_{voice}_{prompt_idx}".encode()
                    ).hexdigest()[:12]

                    filename = f"{sample_id}.wav"
                    filepath = os.path.join(lang_dir, filename)
                    sf.write(filepath, y, SAMPLE_RATE)

                    metadata.append({
                        "sample_id": sample_id,
                        "speaker_id": f"elevenlabs_{voice.lower()}",
                        "language": lang_short,
                        "duration": round(len(y) / SAMPLE_RATE, 2),
                        "source": "elevenlabs",
                        "generator": f"elevenlabs_v2_{voice.lower()}",
                        "voice": voice,
                        "pace": 1.0,
                        "label": "spoof",
                        "attack_type": "tts",
                        "file_path": filepath,
                    })
                    count += 1

                    if count % 10 == 0:
                        print(f"    Generated {count}/{max_per_lang} for {lang_code}")

                    time.sleep(0.3)

                except Exception as e:
                    print(f"    ⚠️  ElevenLabs error ({voice}, prompt {prompt_idx}): {e}")
                    time.sleep(1)
                    continue

        print(f"  ✅ {lang_code}: {count} samples generated")

    return metadata


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate spoof voice dataset using Sarvam AI and ElevenLabs"
    )
    parser.add_argument("--sarvam-key", type=str, default=os.getenv("SARVAM_API_KEY"),
                        help="Sarvam AI API key")
    parser.add_argument("--elevenlabs-key", type=str, default=os.getenv("ELEVENLABS_API_KEY"),
                        help="ElevenLabs API key")
    parser.add_argument("--sarvam-only", action="store_true",
                        help="Only generate Sarvam samples")
    parser.add_argument("--elevenlabs-only", action="store_true",
                        help="Only generate ElevenLabs samples")
    parser.add_argument("--max-per-lang", type=int, default=50,
                        help="Max samples per language per source (default: 50)")
    parser.add_argument("--output-dir", type=str, default=OUTPUT_DIR,
                        help="Output directory")

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 60)
    print("  🎭 DHWANI SPOOF DATASET GENERATOR")
    print("=" * 60)
    print(f"  Output: {args.output_dir}")
    print(f"  Max samples per language per source: {args.max_per_lang}")

    all_metadata = []

    # Sarvam AI
    if not args.elevenlabs_only:
        if args.sarvam_key:
            sarvam_meta = generate_sarvam(args.sarvam_key, args.output_dir, args.max_per_lang)
            all_metadata.extend(sarvam_meta)
            print(f"\n  Sarvam total: {len(sarvam_meta)} samples")
        else:
            print("\n  ⚠️  No Sarvam API key. Skipping. Set --sarvam-key or SARVAM_API_KEY env var.")

    # ElevenLabs
    if not args.sarvam_only:
        if args.elevenlabs_key:
            el_meta = generate_elevenlabs(args.elevenlabs_key, args.output_dir, args.max_per_lang)
            all_metadata.extend(el_meta)
            print(f"\n  ElevenLabs total: {len(el_meta)} samples")
        else:
            print("\n  ⚠️  No ElevenLabs API key. Skipping. Set --elevenlabs-key or ELEVENLABS_API_KEY env var.")

    # Save manifest
    manifest_path = os.path.join(args.output_dir, "manifest.csv")
    if all_metadata:
        keys = all_metadata[0].keys()
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_metadata)

    # Summary
    total_duration = sum(m["duration"] for m in all_metadata)
    unique_voices = len(set(m["speaker_id"] for m in all_metadata))

    print("\n" + "=" * 60)
    print("  📊 GENERATION COMPLETE")
    print("=" * 60)
    print(f"  Total samples:  {len(all_metadata)}")
    print(f"  Total duration: {total_duration / 60:.1f} minutes")
    print(f"  Unique voices:  {unique_voices}")
    print(f"  Languages:      {sorted(set(m['language'] for m in all_metadata))}")
    print(f"  Manifest:       {manifest_path}")
    print(f"\n  Next steps:")
    print(f"    1. Upload '{args.output_dir}' folder to Google Colab")
    print(f"    2. Run Dhwani_Training_V2.ipynb — Cell 9 will auto-detect it")
    print("=" * 60)


if __name__ == "__main__":
    main()
