import asyncio
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Add orchestrator app directory to python sys.path
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "services", "orchestrator", "app"))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from content_risk import assess_content_risk  # type: ignore # noqa: E402

async def run_tests():
    multilingual_tests = [
        ("Gujarati (ઓટીપી આપો & પૈસા ટ્રાન્સફર)", "તમારું SBI એકાઉન્ટ બ્લોક થઈ જશે, તરત જ ઓટીપી આપો અને પૈસા ટ્રાન્સફર કરો."),
        ("Gujish (Romanized Gujarati)", "Tamaru khata block thai jashe, turant otp aapo ane paisa transfer karo hamna j."),
        ("Marathi (ओटीपी सांगा & पैसे पाठवा)", "तुमचे बँक खाते फ्रीज होईल, पोलिसांची केस होईल, ताबडतोब ओटीपी सांगा आणि पैसे पाठवा."),
        ("Marathiglish (Romanized Marathi)", "Tumche khata freeze hoil, police case hoil, tabadtob otp sanga ani paise pathva."),
        ("Hindi (ओटीपी बताओ & डिजिटल अरेस्ट)", "मैं सीबीआई ऑफिसर बोल रहा हूँ, आपके नाम डिजिटल अरेस्ट वारंट है। तुरंत ओटीपी बताओ और पैसे भेजो।"),
        ("Hinglish (Romanized Hindi)", "Main CBI officer bol raha hoon, aapka account freeze ho jayega. Immediate 50000 rupees transfer karo aur OTP batao."),
        ("Tamil (Tanglish)", "Ungal account block aayidum, police case hoil, udane otp sollunga ane money transfer pannunga."),
        ("Telugu (Tenglish)", "Mee account block avutundi, ventane otp cheppandi and money transfer cheyandi."),
        ("Bengali (Banglish)", "Apnar account block hoye jabe, ekhoni otp bolun ebong taka transfer korun."),
        ("Gujarati Safe Chat", "કાલે બપોરે જમવા માટે ક્યાં મળવું છે? ચાલો નવી હોટેલમાં જઈએ."),
        ("Marathi Safe Chat", "उद्या दुपारी जेवायला कुठे भेटायचे? आपण नवीन हॉटेलमध्ये जाऊया."),
    ]

    print("\n======================================================================")
    print("  MULTILINGUAL INDIAN LANGUAGE FRAUD CLASSIFIER TEST SUITE")
    print("======================================================================")

    for title, text in multilingual_tests:
        res = await assess_content_risk(text)
        print(f"\n[TEST] {title}:")
        print(f"   Transcript: \"{text}\"")
        print(f"   Score     : {res.score} (Confidence: {res.confidence})")
        print(f"   Detail    : {res.detail}")

if __name__ == "__main__":
    asyncio.run(run_tests())
