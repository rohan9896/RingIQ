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

## Call artifacts

Final Deepgram/LiveKit conversation turns are persisted to the RingIQ API for
campaign calls when `RINGIQ_INTERNAL_API_KEY` is configured. Recording is
optional and does not participate in call readiness. Set
`LIVEKIT_RECORDING_ENABLED=true` together with the `LIVEKIT_RECORDING_S3_*`
settings to start an audio-only, dual-channel LiveKit Egress recording after the
SIP participant connects. `LIVEKIT_RECORDING_PUBLIC_BASE_URL` should point to a
readable CDN or bucket origin only as a fallback; RingIQ normally generates a
short-lived signed URL from the private S3 location for the Calls screen.

Connected calls have two deterministic lifecycle guards. With the default
settings, 15 seconds without customer, agent, transcript, or recovered pipeline
activity ends the room. At three minutes, the agent plays a callback assurance
in the customer's last detected language and then ends the call. Configure these
with `LIVEKIT_CALL_IDLE_TIMEOUT_SECONDS` and
`LIVEKIT_CALL_MAX_DURATION_SECONDS`.

This worker should receive only the call context needed for one active call. It should not become a general-purpose backend.

## Demo command

```bash
uv run python -m apps.voice_worker.agent dev
```
