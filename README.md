# AI Candidate Evaluator (Multi-Agent Intelligence Network)

An advanced, multi-agent AI system designed to evaluate technical candidates by analyzing their resumes and interview transcripts. Instead of relying on a single LLM prompt, this system deploys **four distinct AI personas** that independently analyze the candidate and then enter a **debate protocol** to reach a consensus-driven final hiring decision.

## 🚀 Features

- **Multi-Agent Architecture:**
  - 🔧 **Technical Agent:** Evaluates system design, coding ability, and technical depth.
  - 🤝 **HR/Culture Agent:** Analyzes communication skills, teamwork, and cultural fit.
  - 📋 **Hiring Manager:** Assesses ROI, leadership potential, and business impact.
  - 🔍 **Skeptic Agent:** Actively looks for exaggerations, red flags, and contradictions.
- **Debate Protocol:** Agents review each other's findings and debate conflicting viewpoints before the final score is calculated.
- **Server-Sent Events (SSE):** Real-time, step-by-step streaming of the evaluation process to the frontend.
- **PDF Parsing:** Native support for uploading PDF resumes.
- **Sleek UI/UX:** Built with React & Tailwind CSS for a professional, hackathon-ready presentation.

## 🛠️ Tech Stack

- **Frontend:** React (Vite), Tailwind CSS
- **Backend:** Node.js, Express.js, Multer (Memory Storage), `pdf-parse`
- **AI Integration:** Google Gemini API (`gemini-2.5-flash` / `gemini-3.1-pro`) via `@google/genai` SDK

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/ai-candidate-evaluator.git
   cd ai-candidate-evaluator
   ```

2. **Install dependencies:**
   ```bash
   npm run install:all
   ```

3. **Get a Gemini API Key:**
   - Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and generate a free API key.
   - You can enter this key directly into the Web UI when you launch the app.

4. **Run the Application:**
   ```bash
   npm run dev
   ```
   *This uses `concurrently` to start the Node.js backend on port 3001 and the Vite React frontend on port 5173.*

5. **Open your browser:**
   Navigate to [http://localhost:5173](http://localhost:5173)

## 🎯 How to Use (Hackathon Demo)
If you are presenting this to a jury, simply click the **"HACKATHON QUICK DEMO"** button on the Upload screen. This will auto-fill a sample resume and a sample technical interview transcript, allowing you to instantly demonstrate the multi-agent debate and final consensus report.
