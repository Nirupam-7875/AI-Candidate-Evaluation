import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import multer from 'multer';
import pdfParse from 'pdf-parse';
import { buildProfile } from './services/profileBuilder.js';
import { runAgentEvaluation } from './services/agents.js';
import { runDebate } from './services/debate.js';
import { makeFinalDecision } from './services/finalDecision.js';
import { generateReport } from './services/reportGenerator.js';

const app = express();
const port = process.env.PORT || 3001;

// Middleware
app.use(cors({ origin: 'http://localhost:5173' }));
app.use(express.json({ limit: '50mb' }));

// Multer for memory storage (doesn't clutter hard drive)
const upload = multer({ storage: multer.memoryStorage() });

// Endpoint 1: PDF Parsing
app.post('/api/parse-pdf', upload.single('resume'), async (req, res) => {
    try {
        if (!req.file) return res.status(400).json({ error: 'No PDF file uploaded' });
        const data = await pdfParse(req.file.buffer);
        res.json({ text: data.text });
    } catch (error) {
        console.error('Error parsing PDF:', error);
        res.status(500).json({ error: 'Failed to parse PDF' });
    }
});

// Endpoint 2: Evaluation Engine with Server-Sent Events (SSE)
app.post('/api/evaluate', async (req, res) => {
    const { resumeText, transcriptText, apiKey, jobRole } = req.body;

    // Keep the HTTP connection open for live streaming
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders();

    const sendEvent = (type, data) => res.write(`data: ${JSON.stringify({ type, data })}\n\n`);

    try {
        // Step 1: Profile Building
        const profile = await buildProfile(resumeText, transcriptText, apiKey);
        sendEvent('profile', profile);

        // Step 2: Agent Evaluation (agents run in parallel)
        const agentEvaluations = await runAgentEvaluation(profile, resumeText, transcriptText, apiKey);
        for (const evalResult of agentEvaluations) {
            sendEvent('agent_evaluation', evalResult);
        }

        // Step 3: Debate Protocol
        const debateResult = await runDebate(agentEvaluations, profile, apiKey);
        sendEvent('debate', debateResult);

        // Step 4 & 5: Final Decision & Report
        const finalDecision = await makeFinalDecision(agentEvaluations, debateResult, profile, apiKey);
        const finalReport = generateReport(profile, agentEvaluations, debateResult, finalDecision);
        sendEvent('final_decision', finalReport);

        sendEvent('done', {});

    } catch (error) {
        console.error('Evaluation Error:', error);
        sendEvent('error', { message: error.message || 'An error occurred during evaluation' });
    } finally {
        res.end();
    }
});

app.listen(port, () => console.log(`Server running on port ${port}`));