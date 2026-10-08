"""
Sample demo data for showcasing the AI Video Assistant UI/UX
without requiring long video downloads or API queries.
"""

DEMO_RESULT = {
    "title": "Quarterly Product Strategy & Q3 Roadmap Alignment",
    "source_name": "Product_Roadmap_Q3_Sync.mp4",
    "duration_str": "42m 15s",
    "word_count": 3480,
    "summary": """The cross-functional engineering and product leadership convened to finalize the Q3 product roadmap, focusing on scaling the real-time AI transcription infrastructure, addressing enterprise compliance requirements, and accelerating mobile client release.

Key highlights from the session:
• Cloud vs. Local Hybrid Inference: The team agreed to maintain local Whisper models for desktop enterprise clients while introducing hosted cloud fallback for web users.
• Timeline Commitments: Sprint 14 will prioritize database index optimization and latency reduction for retrieval pipelines.
• Security & SOC2 Compliance: Audit logging is now mandatory across all vector store operations to clear SOC2 Type II compliance by late Q3.
• Resource Reallocation: Two senior platform engineers will be temporarily shifted to the LangChain RAG pipeline optimization team for the next three weeks.""",
    
    "action_items": """1. Task: Benchmark Whisper small vs medium latency on consumer GPUs
   Owner: Alex Chen
   Deadline: Friday, July 18
   Priority: High

2. Task: Finalize SOC2 audit log schema for vector retrieval queries
   Owner: Priya Sharma
   Deadline: Next Tuesday
   Priority: High

3. Task: Implement fallback retry logic for YouTube video downloader failures
   Owner: Marcus Vance
   Deadline: July 24
   Priority: Medium

4. Task: Prepare developer documentation for Hinglish speech-to-text pipeline
   Owner: Rahul Verma
   Deadline: End of Month
   Priority: Medium

5. Task: Conduct user research interviews on meeting summarization templates
   Owner: Sarah Jenkins
   Deadline: August 5
   Priority: Low""",

    "key_decisions": """1. Adopt Hybrid Storage: ChromaDB will remain the default local vector database for on-premise users, while PostgreSQL pgvector will be evaluated for enterprise cloud tiers.
2. Standardize Chunking Strategy: Audio chunks will strictly remain at 10-minute intervals for Whisper and 25-second windows for Sarvam AI to avoid memory spikes and API payload limits.
3. Model Selection: Groq LPU (Llama-3.3-70B-versatile) was approved as the primary reasoning LLM due to ultra-fast 500+ tok/s execution, superior context adherence, and low latency.
4. Hindi/Hinglish Default: Hindi and mixed Hinglish audio will automatically route to the Sarvam Saaras translation engine with no user toggling required.""",

    "open_questions": """1. What is the maximum acceptable memory footprint for local Whisper execution on low-spec 8GB RAM laptops?
2. How will we handle video meetings that exceed 3 hours in continuous duration without exhausting local disk cache?
3. Should we support direct calendar integrations (Google Meet / Zoom bots) in the Q4 milestone or keep it file-and-URL focused?""",

    "transcript": """[00:00 - Alex Chen]: Good morning team. Today's agenda is finalizing our Q3 product roadmap, specifically focusing on our AI meeting intelligence engine.
[00:45 - Priya Sharma]: Thanks Alex. From the infrastructure side, we've observed that users are testing both local files and YouTube streams. Our audio pipeline is holding up well, but we need to discuss model selection and memory footprints.
[02:10 - Marcus Vance]: The Groq LPU integration has been a game-changer. Llama 3.3 70B summarizes 40 minutes of audio in under 2 seconds. For Hindi and Hinglish meetings, the Sarvam API bridge converts natural spoken Hinglish directly into coherent English text.
[05:30 - Alex Chen]: That's huge. Marcus, can you ensure benchmark results for Whisper small versus medium on consumer GPUs are finalized by Friday?
[06:05 - Marcus Vance]: Absolutely. I'll have the benchmarks ready by July 18.
[08:20 - Priya Sharma]: On compliance: SOC2 audit logging is required for any vector store queries that retrieve transcript segments. I'll lock down that schema by next Tuesday.
[12:15 - Sarah Jenkins]: Regarding summaries, the feedback from beta testers has been overwhelming. They love the structured breakdown—especially having action items clearly split with owners and deadlines.
[16:40 - Rahul Verma]: What about our Hinglish documentation? I can draft the developer guides by the end of the month so third-party teams understand the Sarvam translation flow.
[21:10 - Alex Chen]: Let's lock that in. To summarize: hybrid inference is approved, Groq LPU Llama-3.3-70B is our primary reasoning LLM, and we'll keep audio chunks strictly at 10 minutes. Thanks everyone, great session!""",

    "qa_samples": {
        "What are the main decisions made?": "The team made four primary decisions: 1) Adopt hybrid vector storage (ChromaDB local, pgvector for cloud); 2) Enforce strict 10-minute audio chunking; 3) Standardize on Groq LPU (Llama-3.3-70B) for reasoning; and 4) Automatically route Hindi/Hinglish to Sarvam Saaras.",
        "Who is responsible for the SOC2 audit log schema?": "Priya Sharma is responsible for finalizing the SOC2 audit log schema for vector retrieval queries, with a deadline of next Tuesday.",
        "What model is used for speech-to-text?": "English audio uses OpenAI's Whisper model running locally on the computer, while Hindi and Hinglish audio are processed via Sarvam AI's speech-to-text translate API."
    }
}
