# PrimeVector Design Rationale & Architectural Transparency Document

---

## 🎯 Executive Summary
This document presents the explicit engineering and aesthetic rationale behind the **PrimeVector Voice Integrity Demo & Marketing Platform**. The website was designed to break away from generic AI-generated SaaS landing templates (purple-to-blue gradients, rounded glassmorphism, Inter/Poppins fonts, fake testimonials) and present a bespoke, hand-crafted forensic security surface built for technical judges and enterprise auditors.

---

## 1. 🔤 Typography & Font Pairings

| Font Family | Font Type | Exact Role / Elements | Rationale & Aesthetic Purpose |
|---|---|---|---|
| **Fraunces** | Editorial Serif | `h1`, `h2`, `h3`, Card Titles | Chosen for its sharp, authoritative, bespoke editorial weight. Conveys forensic rigor, high-stakes financial security, and institutional trust, avoiding standard AI sans-serif defaults. |
| **Space Grotesk** | Geometric Sans | Body text, feature descriptions, navigation | A clean, modern sans-serif with subtle technical quirks. Replaces generic Inter/Poppins defaults while preserving maximum legibility across dense technical copy. |
| **JetBrains Mono** | Monospace | Latency metrics (ms), JSON payloads, risk scores, code snippets, status badges | Reinforces the real engineering product feel. High legibility for technical data and audited mathematical formulas. |

---

## 2. 🎨 Color Palette & Functional Token System

| Token Name | Hex Code | Role & Usage | Design Justification |
|---|---|---|---|
| **Obsidian Ink** | `#07090E` / `#0B0F17` | Base Page Backgrounds | Deep paper-dark obsidian creates an immersive forensic dark mode without grey washing or pure `#000000` harshness. |
| **Slate Card** | `#141C2E` / `#1E293B` | Card Containers & Borders | Defined high-contrast structural borders (`#334155`) with deep slate fill for clean section hierarchy. |
| **Forensic Amber** | `#F59E0B` / `#D97706` | Primary Brand Accent, Glows, Active Indicators | Warm signal amber evoking radar scans, acoustic spectrum vectors, and security analysis. Intentionally avoids overused purple-to-blue SaaS gradients. |
| **Emerald (Low Risk)** | `#10B981` | Functional Risk Score `[0.0 - 0.39]`, Health Checks | Strict functional color reserved for clean voice identity, healthy HTTP 200 responses, and proceed recommendations. |
| **Amber (Medium Risk)** | `#F59E0B` | Functional Risk Score `[0.40 - 0.69]`, Degraded Status | Reserved for callback verification recommendations and degraded service warnings. |
| **Crimson (High Risk)** | `#EF4444` / `#DC2626` | Functional Risk Score `[0.70 - 1.00]`, Alerts | Reserved for supervisor escalation alerts and synthetic voice clone detection. |

---

## 3. 🎬 Motion Design Strategy

1. **Framer Motion**:
   - **Interactive 3-Signal Pipeline Visualizer**: Smooth state updates when dragging acoustic, speaker match, content risk, and context sliders. Recalculates Noisy-OR probability math in real time.
   - **Scroll-Triggered Reveal**: Staggered step-by-step entry animations for pipeline mechanics, preventing layout shifts and maintaining visual momentum.
   - **Live Stream Animations**: New incoming call log events animate in from the top with `AnimatePresence`.

2. **Barba.js**:
   - **Page Transitions**: Custom `security-scan-transition` line wipe overlay between pages, simulating a top-to-bottom security vector scan when switching navigation tabs.

---

## 4. 📊 Explicit Audit of Data Sources & Sample Data Flags

Per strict honesty rules, all site sections are categorized into **Real Live Backend Connections** vs **Clearly Flagged Sample Data**:

| Page / Component | Data Source | Status / Flag | Integration Plan for Real Data |
|---|---|---|---|
| **Page 1: Overview & Pipeline** | Interactive Noisy-OR formula math | **LIVE MATH** | Real-time JS formulation of actual python `risk-fusion-engine` equations. |
| **Page 2: System Status** | Live `/healthz` pings to all 8 microservices via `/api/:port/healthz` proxy | **100% REAL LIVE BACKEND** | Pings live Docker microservices. Displays actual HTTP response codes and latency ms. |
| **Page 3: Live Demo Feed** | POST requests to `/v1/pipeline/process` on Orchestrator (:8080) | **100% REAL LIVE BACKEND** | Sends PCM audio + transcript to real backend. Displays actual computed risk score and execution latency (ms). |
| **Page 4: API Docs** | Python & Node SDK source code + FastAPI JSON schemas | **100% REAL REPO CODE** | Directly mirrors `proto/risk_assessment.proto`, `sdk/python`, and `sdk/node`. |
| **Page 5: API Usage Tracking** | Simulated 24-hour request histogram and metric totals | **SAMPLE DATA (FLAGGED)** | Prominently labeled with a **"SAMPLE DATA / DEMO PREVIEW"** badge. Will connect to TimescaleDB/Prometheus telemetry exporter in production. |
| **Page 6: Android Showcase** | Generated high-resolution app UI screenshots & Gradle build scripts | **AUTHENTIC ASSETS** | Real screenshots of mic-capture app interface and Sarvam STT stream. |
| **Page 7: About / Team** | Real SIH hackathon team roles & architecture invariants | **100% ACCURATE** | Reflects actual hackathon team members and system invariants. |

---

## 5. 📱 Mobile Responsiveness Verification
Tested down to 375px mobile viewport width. All tables feature horizontal scroll containers, navigation collapses to an accessible mobile icon bar, and typography scales fluidly.
