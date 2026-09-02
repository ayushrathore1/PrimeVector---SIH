# 🗣️ PrimeVector: Easy-Language SIH Briefing & Tech Breakdown
> **Voice Integrity & Impersonation Prevention Platform**  
> *Dual-Layer Guide: Non-Technical Analogies + Technical Terms & Architecture*

---

## 🏛️ PART 1: Why Do Banks, Enterprises & Telcos ACTUALLY Need PrimeVector?

### 1. The Real-World Crisis: Voice is No Longer Proof of Identity
For decades, when a customer called their bank and said *"Hello, I am Rajesh, my account number is X"*, the bank agent recognized their voice. 

**What changed?**
Today, Generative AI voice cloning software allows anyone to extract a 5-second audio clip of your voice from Instagram, YouTube, or WhatsApp, and create a **live AI voice clone**. A scammer can call your bank, speak into their microphone, and the AI converts their speech into **YOUR EXACT VOICE** in real-time.

---

### 2. Two Multi-Million Dollar Scenarios

#### 🔴 Scenario A: Bank Account Takeover (Retail Fraud)
- **What happens:** A fraudster calls customer service impersonating an account holder.
- **The trick:** The AI voice sounds 100% identical to the real customer. The scammer says, *"I lost my phone and net banking password, please transfer ₹5,00,000 to this new UPI ID immediately."*
- **The result:** Bank call center agents are human—they get duped by the emotional, identical-sounding voice and process the transfer. Millions of rupees are lost daily to this **vishing (voice phishing)** scam.

#### 🔴 Scenario B: Corporate CEO/CFO Wire Fraud (Enterprise Fraud)
- **What happens:** A scammer clones the voice of a company's CEO.
- **The trick:** The scammer calls the Finance Manager/CFO on a Friday evening: *"Hey, this is the CEO. We are closing an urgent secret acquisition deal. Wire $500,000 to this vendor account right now!"*
- **The result:** The CFO recognizes the CEO's voice and approves the wire transfer. (Real-world incidents like this have resulted in multi-million dollar corporate losses).

---

### 3. Why Traditional Security Fails
- **Human Ears:** Human ears **cannot** detect modern AI voice clones over telephone networks.
- **Security Questions:** Questions like *"What is your mother's maiden name?"* or *"What is your Date of Birth?"* are easily found by hackers on social media.
- **Old Voice Biometrics:** Traditional biometrics only matched voice identity, but couldn't detect if the voice was computer-generated or human!

### 🎯 Why PrimeVector is Mandatory
PrimeVector acts as a **Digital X-Ray Machine for Phone Calls**. While human ears hear a normal voice, PrimeVector looks at microscopic sound waves in real-time, spots AI computer glitches, verifies speaker identity, and alerts the bank **before** money leaves the account.

---

## 🔄 PART 2 & 3: End-to-End System Flow & Tech Stack

```
[Phone Call Arrives]
         ↓
1. Ingestion Gateway (Go / gRPC) ───► Fast reception guard taking the audio stream
         ↓
2. Feature Extraction (Python)  ───► Sound scan: turns audio into math, shreds raw audio
         ↓
3. Spoof Detector (Python/PyTorch) ─► Fake detector checking for AI synthesis glitches
         ↓
4. Enrollment Service (Python) ───► Passport checker comparing caller voiceprint
         ↓
5. Risk Fusion Engine (Python)  ───► Chief Security Officer calculating master risk score
         ↓
6. Policy Engine (Python)       ───► Rulebook decider (e.g., Recommend Callback vs Proceed)
         ↓
7. Alerting Service (Python)    ───► Alarms call center screen & logs hashed audit trail
```

---

### 1️⃣ `ingestion-gateway` (The Front Gate / Fast Receptionist)

* 🟢 **Non-Technical Analogy:** Imagine 10,000 people calling a bank at the exact same second. You need a super-fast security guard standing at the front door who can receive call streams instantly without crashing or creating long queues.
* 🔵 **Technical Breakdown & Terms:**
  * **Tech Stack:** **Go 1.22** (Golang) & **gRPC**.
  * **Term 1 — gRPC (Google Remote Procedure Call):** Unlike standard web APIs (HTTP REST) that send heavy text/JSON, gRPC sends compact **binary data streams**. It is up to 10x faster and designed for real-time streaming audio.
  * **Term 2 — Concurrency (Goroutines):** Go can process 10,000+ incoming audio streams simultaneously using lightweight background threads called Goroutines with minimal RAM usage.
  * **Term 3 — Rate Limiting & Backpressure:** If too many calls hit the server, it automatically controls the flow (rate limiting) so servers don't crash.
  * **Why we used it:** Python is great for AI, but too slow for handling 10,000 raw network streams at the edge. Go handles the heavy streaming traffic at the front door!

---

### 2️⃣ `feature-extraction-service` (The Sound Scanner / X-Ray Machine)

* 🟢 **Non-Technical Analogy:** The receptionist hands the voice clip to a scanner. The scanner converts the voice into mathematical graphs and sound fingerprints. Once the math is saved, it **immediately shreds the original audio recording** so nobody can steal or record your private telephone conversation.
* 🔵 **Technical Breakdown & Terms:**
  * **Tech Stack:** **Python 3.10**, **FastAPI**, **Librosa**, **NumPy**.
  * **Term 1 — PCM Audio (Pulse-Code Modulation):** Raw digital sound bytes sampled 16,000 times per second (16kHz).
  * **Term 2 — Log-Mel Spectrogram:** A 2D visual graph/heatmap of voice frequencies over time (80 mel bands). Humans hear words; AI models inspect this visual frequency graph!
  * **Term 3 — Prosody & $F_0$ Pitch Contours:** Analyzing speech rhythm, fundamental pitch frequency ($F_0$), micro-vibrations (jitter/shimmer), and natural speaking pauses. AI voices speak too perfectly without natural human breathing pauses!
  * **Term 4 — Speaker Embedding (192-dim vector):** A unique mathematical coordinate made of 192 numbers that represents the physical shape of a person's vocal cords.
  * **Why we used it:** `Librosa` and `NumPy` are industry-standard Python libraries for high-speed mathematical sound analysis.
  * **🔒 Hard Privacy Invariant:** Raw audio exists **only in RAM memory** for milliseconds during math conversion. **Zero raw audio is saved to disk or databases!**

---

### 3️⃣ `spoof-detection-service` (The Lie Detector / AI Fake Hunter)

* 🟢 **Non-Technical Analogy:** A forensic expert takes the sound graph and inspects it under a microscope, looking for tiny digital glitches and artificial patterns left behind by AI voice-generating software.
* 🔵 **Technical Breakdown & Terms:**
  * **Tech Stack:** **Python 3.10**, **FastAPI**, **PyTorch**, **ONNX Runtime**.
  * **Term 1 — AI Synthesis Probability Score:** The AI model outputs a score from `0.0` (100% natural human voice) to `1.0` (100% fake AI clone).
  * **Term 2 — Logits & Sigmoid Function:** Math formulas inside neural networks that convert complex acoustic features into a smooth percentage score.
  * **Term 3 — Regional Accent Routing (`hi-in`, `ta-in`, `te-in`, `bn-in`, `en-generic`):** India has hundreds of accents (Hindi, Tamil, Telugu, Bengali, etc.). If a person speaks English with a strong regional accent, a generic AI model might mistake it for a fake voice! Our accent router sends the sound to an accent-specific model to prevent false alarms.
  * **Why we used it:** PyTorch and ONNX Runtime allow deep neural networks to run inference in milliseconds.

---

### 4️⃣ `enrollment-service` (The Voice ID Verifier / Passport Vault)

* 🟢 **Non-Technical Analogy:** Comparing the caller's voice fingerprint against the customer's registered "Voice Passport" on file to answer: *"Is this caller actually Mr. Ramesh?"*
* 🔵 **Technical Breakdown & Terms:**
  * **Tech Stack:** **Python 3.10**, **FastAPI**, **SciPy**.
  * **Term 1 — Cosine Vector Similarity:** A mathematical formula that measures the geometric angle between two 192-number vectors. If the angle is very small, the voice belongs to the same person!
  * **Term 2 — Multi-Session Distinct Calendar Day Rule:** To register a voice passport, a customer must record their voice on **3 separate days** with random phrases (e.g. *"blue mountain running clock 847"*). This stops scammers from uploading a stolen 5-second audio clip to register a fake voice profile!

---

### 5️⃣ `risk-fusion-engine` (The Chief Security Officer / Master Brain)

* 🟢 **Non-Technical Analogy:** The Master Security Officer receives reports from all departments:
  - *Spoof Detector says:* 95% chance it's an AI fake voice.
  - *Voice ID Verifier says:* Voice match is doubtful.
  - *Bank Context says:* Caller is trying to transfer ₹10,000,000.
  The Master Brain runs advanced security math to calculate the final **Master Risk Score (0.0 to 1.0)**.
* 🔵 **Technical Breakdown & Terms:**
  * **Tech Stack:** **Python 3.10**, **FastAPI**, **Pydantic**.
  * **Term 1 — Noisy-OR Probabilistic Fusion Math:**
    $$P(\text{suspicious}) = 1 - (1 - \text{Score}_1) \times (1 - \text{Score}_2)$$
    *Why not simple averaging?* If you average 95% (fake score) and 0% (context score), you get 47.5% (Medium Risk), which lets the hacker slip through! **Noisy-OR math ensures that if ANY acoustic signal detects a high threat, the overall risk stays HIGH!**
  * **Term 2 — Bounded Contextual Multiplier ($0.85\times - 1.35\times$):** Context (like transaction amount) multiplies the acoustic risk score, but can never accuse a clean human voice of fraud on its own.

---

### 6️⃣ `policy-threshold-engine` (The Bank Rulebook & Auto-Block Gate)

* 🟢 **Non-Technical Analogy:** Taking the Master Risk Score and looking at the bank's rulebook to decide what action to recommend to the bank agent.
* 🔵 **Technical Breakdown & Terms:**
  * **Tech Stack:** **Python 3.10**, **FastAPI**.
  * **Term 1 — Action Recommendation Rules:**
    * Score $\ge 0.70 \implies$ `RECOMMEND_SUPERVISOR_ESCALATION` & `RECOMMEND_CALLBACK_VERIFICATION`
    * Score $\ge 0.40 \implies$ `RECOMMEND_CALLBACK_VERIFICATION` (Ask caller to call back from registered mobile)
    * Score $< 0.40 \implies$ `PROCEED`
  * **Term 2 — Opt-In Auto-Block Liability Gate:** Banks fear lawsuits if an automated system mistakenly blocks a genuine rich client. Therefore, `auto_block_enabled` defaults to `False`. The system gives clear recommendations to human agents and **never** blocks transactions automatically unless the bank explicitly turns auto-block ON.

---

### 7️⃣ `alerting-service` (The Alarm System & Auditor)

* 🟢 **Non-Technical Analogy:** Sending real-time warning pop-ups to the call center agent's screen and recording an unalterable, private log in the security ledger.
* 🔵 **Technical Breakdown & Terms:**
  * **Tech Stack:** **Python 3.10**, **FastAPI**.
  * **Term 1 — Idempotency Gate:** Prevents duplicate notification alerts if network packets retry.
  * **Term 2 — SHA-256 Hashing:** Hashing recipient phone numbers / account IDs into irreversible random text strings (`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`) for audit logs so customer privacy is 100% protected (DPDP Act & GDPR compliant).

---

## 💡 Quick Summary to Tell SIH Judges

> *"We built an end-to-end event-driven microservice platform. **Go and gRPC** handle streaming edge ingestion under 50ms without network delay. **Python microservices** perform spectral analysis, pitch contour extraction, and PyTorch deepfake detection, discarding raw audio immediately for 100% privacy. Finally, our **Risk Fusion Engine** uses Noisy-OR probability math to combine clues and trigger real-time policy alerts before fraudulent transfers occur."*
