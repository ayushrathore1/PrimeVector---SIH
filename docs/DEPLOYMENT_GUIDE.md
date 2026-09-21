# 🚀 SatyaDhVani 2 (PrimeVector) — 100% Free Production Deployment Guide
> **Zero Credit Cards Required • 100% Free Forever • Fully Autonomous Cloud Stack**

This guide provides a step-by-step walkthrough to deploy the entire **SatyaDhVani 2** ecosystem online in under **5 minutes** without entering any payment details or credit cards.

---

## 🏗️ Deployment Architecture

| Tier | Provider | Plan | Cost | Credit Card Required? |
|---|---|---|---|---|
| **Backend & Microservices** | [Render.com](https://render.com) | Free Web Service (Docker) | $0.00 | ❌ **NO** |
| **Frontend Web App** | [Vercel](https://vercel.com) | Free Hobby Plan (Edge CDN) | $0.00 | ❌ **NO** |
| **ML Checkpoints & Math** | Self-Contained | In-Memory / Docker | $0.00 | ❌ **NO** |

---

## ⚡ Step 1: Deploy Backend Microservices on Render (3 Minutes)

Render builds and runs our multi-stage `Dockerfile` directly from GitHub. It hosts all 8 microservices, the Dhwani v2 neural model, policy threshold engine, and reverse proxy in one unified container.

1. **Sign in to Render**:
   - Go to [dashboard.render.com](https://dashboard.render.com).
   - Click **Sign in with GitHub** *(Zero credit card needed)*.

2. **Create a New Web Service**:
   - Click the blue **New +** button in the top right $\rightarrow$ select **Web Service**.
   - Select **Build and deploy from a Git repository** $\rightarrow$ click **Next**.
   - Select your repository: `ayushrathore1/PrimeVector---SIH`.

3. **Configure Service Settings**:
   - **Name**: `satyadhvani-api` *(or your preferred name)*.
   - **Region**: `Oregon (US West)` or `Frankfurt (EU)`.
   - **Branch**: `main`.
   - **Runtime**: `Docker`.
   - **Instance Type**: Select **Free** *(0.1 vCPU, 512 MB RAM, $0/month)*.

4. **Environment Variables**:
   Under **Environment Variables**, verify or add:
   - `PORT` = `10000`
   - `SPOOF_MODEL_REGISTRY_BACKEND` = `dhwani`

5. **Deploy**:
   - Click **Create Web Service**.
   - Render will build the Docker container and install audio dependencies.
   - Once the build finishes (~3-4 minutes), you will see:
     ```
     ==> Starting SatyaDhVani 2 Production Gateway on 0.0.0.0:10000
     ==> Launched spoof-detection-service (port :8002)
     ==> Launched api-gateway (port :8090)
     ==> Application is live at https://satyadhvani-api.onrender.com
     ```
   - **Copy your backend URL**: `https://<your-service-name>.onrender.com`

---

## 🌐 Step 2: Deploy Frontend on Vercel (2 Minutes)

1. **Sign in to Vercel**:
   - Go to [vercel.com/signup](https://vercel.com/signup).
   - Click **Continue with GitHub** *(Zero credit card needed)*.

2. **Import Project**:
   - On the Vercel dashboard, click **Add New...** $\rightarrow$ **Project**.
   - Select the `PrimeVector---SIH` repository $\rightarrow$ click **Import**.

3. **Configure Build Settings**:
   - **Framework Preset**: `Vite` *(auto-detected)*.
   - **Root Directory**: Click **Edit** and select `website`.

4. **Add Backend Environment Variable**:
   - Expand the **Environment Variables** accordion.
   - Add:
     - **Key**: `VITE_API_BASE`
     - **Value**: `https://<your-service-name>.onrender.com` *(the URL from Step 1)*
   - Click **Add**.

5. **Deploy**:
   - Click **Deploy**.
   - Vercel compiles the React 19 app in ~30 seconds and outputs your live URL:
     `https://primevector.vercel.app` *(or your custom project name)*.

---

## ✅ Step 3: Verification & Live Health Check

1. **Verify Backend Health**:
   Open in your browser:
   ```
   https://<your-render-app>.onrender.com/healthz
   ```
   Expected response:
   ```json
   {
     "status": "healthy",
     "gateway_port": 10000,
     "services": {
       "spoof-detection-service": "online",
       "api-gateway": "online",
       "policy-threshold-engine": "online",
       "risk-fusion-engine": "online",
       "alerting-service": "online",
       "orchestrator": "online"
     }
   }
   ```

2. **Verify Public API Detection**:
   Test a live cURL against your API Gateway:
   ```bash
   curl -X GET https://<your-render-app>.onrender.com/v1/health
   ```
   Expected:
   ```json
   {"status":"healthy","model_loaded":true,"version":"1.0.0"}
   ```

3. **Verify Interactive Frontend**:
   - Open your Vercel URL (`https://primevector.vercel.app`).
   - Navigate to the **Direct Dhwani Live Detection** panel.
   - Speak into your microphone $\rightarrow$ verify real-time voice classification and low latency!

---

## 💡 Important Free Tier Tips

* **Render Cold Starts**: Render's free tier spins down the container after 15 minutes of inactivity. When a request arrives, it wakes up automatically in ~30 seconds.
* **Keep-Alive (Optional)**: You can set up a free monitor at [cron-job.org](https://cron-job.org) or [uptimerobot.com](https://uptimerobot.com) to ping `https://<your-render-app>.onrender.com/healthz` once every 14 minutes to keep it warm 24/7!
* **No Colab / Ngrok Needed**: With this Docker deployment, all services execute autonomously in the cloud without needing browser tabs or ngrok tunnels.
