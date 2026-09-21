import asyncio
import os
import sys

# Add orchestrator app directory to python sys.path
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "services", "orchestrator", "app"))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from content_risk import assess_content_risk  # type: ignore # noqa: E402

async def run_tests():
    tests = [
        ("Digital Arrest Scam", "Digital arrest warrant issued by Cyber Crime Branch for illegal parcel containing MDMA. Pay 50000 rupees."),
        ("AnyDesk Remote Access Scam", "Download AnyDesk and QuickSupport app right now on your phone to update your KYC or your SBI card will be blocked."),
        ("OTP & Money Transfer Scam", "Please transfer 50000 rupees immediately to this account number and share the OTP you just received on your phone."),
        ("Educational Bank Warning (False Positive Shield)", "State Bank Warning: Never share your OTP or PIN with anyone claiming to be a bank official."),
        ("Normal Family / Lunch Chat", "Are we still meeting for lunch tomorrow at the usual place? I was thinking we could try that new restaurant."),
    ]

    print("\n======================================================================")
    print("  SMART LOCAL NLP FRAUD CLASSIFIER TEST SUITE")
    print("======================================================================")

    for title, text in tests:
        res = await assess_content_risk(text)
        print(f"\n[TEST] {title}:")
        print(f"   Transcript: \"{text}\"")
        print(f"   Score     : {res.score} (Confidence: {res.confidence})")
        print(f"   Detail    : {res.detail}")

if __name__ == "__main__":
    asyncio.run(run_tests())
