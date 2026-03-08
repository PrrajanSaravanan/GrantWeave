# GrantWeave

<div align="center">
  <img src="https://agent.tinyfish.ai/favicon.ico" alt="Logo" width="80" height="auto" />
  <h3>Autonomous Grant Hunting Platform</h3>
  <p>Powered by the <strong>AetherForge Kernel</strong> and the <strong>TinyFish Web Agent API</strong></p>
</div>

---

## 🚀 Overview

GrantWeave is a beautiful, real-world SaaS designed to help nonprofits and startups find, match, and prepare grant applications. Instead of manually scouring outdated portals, users simply describe their needs, and GrantWeave deploys parallel, autonomous web agents to hunt across actual government and foundation websites.

### The AetherForge Kernel
GrantWeave runs on **AetherForge**, a custom, state-of-the-art orchestration layer built specifically for web agents:

*   🧬 **EvoForge:** Self-healing agents. If a site changes its layout and an agent fails, EvoForge automatically mutates the original instructions, testing 3-5 variants simultaneously until one succeeds.
*   🧠 **Akasha Ledger:** Permanent memory. Once an EvoForge mutation bypasses a block, it is saved to local SQLite memory. Future agents encountering the same portal will utilize this known-good strategy instantly.
*   🕸️ **Weave Mesh:** Dynamic coordination. A single "Hunt" command spawns a Master Cell, which subsequently recruits specialized Sub-Cells for different portals, executing them concurrently within safe semaphore limits.
*   ⏳ **Temporal Fabric:** Session resilience. Agent states are checkpointed automatically, allowing interrupted hunts to be resumed flawlessly without losing data.

---

## 🛠 Tech Stack

*   **Backend:** Python `FastAPI` + `asyncio`
*   **Database:** Local `SQLite` (via `aiosqlite`)
*   **Real-time:** `SSE` (Server-Sent Events) for logs/streaming URLs, `WebSockets` for team handoff.
*   **Frontend:** React 18, `Vite`, TypeScript
*   **Styling:** Tailwind CSS (Dark Mode Glassmorphism)
*   **State Management:** `Zustand`
*   **Visualizations:** `@tldraw/tldraw` (Mind Maps)
*   **Agents:** [TinyFish Web Agent API](https://agent.tinyfish.ai)

---

## ⚙️ Setup & Installation

This project is entirely local-first. No cloud databases required.

### 1. Backend Setup

```bash
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the database seeder (crucial for the demo experience!)
python seed_db.py
```

### 2. Environment Variables

In the root directory, copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` and insert your **TinyFish API Key**.

### 3. Frontend Setup

```bash
cd frontend

# Install Node dependencies
npm install
```

---

## 🏃‍♂️ Running the Application

You will need two terminal windows.

**Terminal 1 (FastAPI Backend):**
```bash
cd backend
# Make sure your venv is active
uvicorn main:app --reload --port 8000
```

**Terminal 2 (React Frontend):**
```bash
cd frontend
npm run dev
```

The application will be available at: **http://localhost:5173**

---

## 🎬 Hackathon / Demo Script

Want to show off the system? Follow this flow:

1.  **Onboarding Box:** Because you ran `seed_db.py`, the system is already seeded. Click "Upload PDF" and pick any dummy PDF, or choose "Manual Entry" and click through.
2.  **The Dashboard:** You'll land on the gorgeous dark-mode dashboard.
3.  **Initiate the Hunt:** In the command bar, type: *"Find STEM education grants in California focused on high school robotics"* and hit Send.
4.  **Watch the Magic:**
    *   **Live Browsers:** The grid in the center will populate with up to 6 `iframe` windows showing the TinyFish agents actually driving web browsers in the cloud.
    *   **EvoLog:** The right panel will show the AetherForge kernel logging mutation attempts in real time.
    *   **Mind Map:** On the left, a `tldraw` canvas will automatically arrange categories, and as agents report `MATCH_FOUND` events via SSE, new grant nodes will pop into existence on the canvas.
5.  **Team Handoff (WebSockets):** Click the "Copy Link" button in the bottom left module. Open an Incognito window and paste the link. Watch the "viewing" counter instantly update via WebSockets.
6.  **Applications & Export:** Go to the "Applications" tab to see the final portfolio. Click **"Download Core PDFs"** to trigger `fpdf2` generating a styled, pre-filled application package using the organization's backend profile.
7.  **Wrapped:** Check out the "Wrapped" tab for a Spotify-style weekly summary.

---

## 🤝 Architecture Notes

*   **Why SSE?** Web agents are slow. Instead of blocking HTTP requests, the backend orchestrator yields a raw HTTP stream. The frontend interprets `STARTED`, `SCANNING`, `STREAMING_URL`, `MATCH`, and `EVO` events as they happen.
*   **Why SQLite?** To adhere to the strict local-only requirement, everything including the Akasha Ledger's vector-like memory is stored relationally in `aetherforge.db`.

---
<div align="center">
  <i>Built with Python, React, and an excessive amount of caffeine.</i>
</div>
