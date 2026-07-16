# Voice AI Worker

Real-time worker for active AI voice calls.

Planned responsibilities:

- Join LiveKit call sessions.
- Coordinate Deepgram Flux STT.
- Retrieve tenant knowledge.
- Call Groq `llama-3.3-70b-versatile`.
- Coordinate Sarvam AI TTS.
- Manage per-call conversation state.
- Emit call events, transcripts, classifications, callback intent, and knowledge gaps.

This worker should receive only the call context needed for one active call. It should not become a general-purpose backend.

