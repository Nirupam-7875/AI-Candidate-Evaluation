import { generateContentWithFallback, parseJSON } from './geminiClient.js';

// Define the 4 specialized AI Personas
const agentsConfig = [
    {
        name: "Technical Agent",
        emoji: "🔧",
        focusAreas: "Evaluate technical depth, coding ability, system design knowledge, project complexity.",
        systemPrompt: "You are the Technical Agent, a senior technical interviewer. Your job is to strictly evaluate technical depth..."
    },
    {
        name: "HR/Culture Agent",
        emoji: "🤝",
        focusAreas: "Evaluate communication skills, teamwork, honesty, cultural fit, emotional intelligence.",
        systemPrompt: "You are the HR/Culture Agent, an HR specialist..."
    },
    {
        name: "Hiring Manager Agent",
        emoji: "📋",
        focusAreas: "Evaluate ROI, role fit, growth potential, leadership potential.",
        systemPrompt: "You are the Hiring Manager Agent, a hiring manager..."
    },
    {
        name: "Skeptic Agent",
        emoji: "🔍",
        focusAreas: "Find contradictions between resume and transcript, exaggerations, unrealistic claims, red flags.",
        systemPrompt: "You are the Skeptic Agent, a critical analyst. Rate 1-10 (where 10 = very trustworthy, no red flags)..."
    }
];

export async function runAgentEvaluation(profile, resumeText, transcriptText, apiKey) {
    // Map over each agent to create 4 simultaneous asynchronous tasks
    const evaluationPromises = agentsConfig.map(async (agent) => {
        const prompt = `
            Candidate Profile Summary:
            ${JSON.stringify(profile, null, 2)}
            
            Resume: ${resumeText}
            Interview Transcript: ${transcriptText}
            
            Focus Areas: ${agent.focusAreas}
            
            Based on the above, provide your evaluation. You MUST return EXACTLY and ONLY a JSON object...
        `;

        try {
            // Send prompt to Gemini
            const responseText = await generateContentWithFallback(apiKey, agent.systemPrompt, prompt);
            return parseJSON(responseText);
        } catch (err) {
            console.error(`Agent evaluation failed for ${agent.name}:`, err.message);
        }
    });

    // Execute all 4 Gemini API calls in parallel!
    return await Promise.all(evaluationPromises);
}