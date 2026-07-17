# RingIQ Voice Pipeline Cost Analysis

**Date:** 2026-07-17  
**Purpose:** Estimate the per-minute cost of RingIQ's current demo voice AI pipeline after the latency-optimized provider configuration.

## Current Pipeline

The current demo pipeline is:

```text
Vobiz SIP -> LiveKit SIP + Agent Runtime -> Deepgram Flux Multilingual STT
-> Groq openai/gpt-oss-20b LLM -> Sarvam Bulbul v3 TTS
```

## Pricing Inputs

| Component | Current Choice | Public Pricing Input | INR Estimate |
|---|---|---:|---:|
| Telephony | Vobiz SIP channel | Rs. 0.45 per minute | Rs. 0.45/min |
| SIP platform | LiveKit third-party SIP | $0.004 per minute | ~Rs. 0.39/min |
| STT | Deepgram Flux Multilingual | $0.47 per hour | ~Rs. 0.76/min |
| LLM | Groq `openai/gpt-oss-20b` | $0.075 / 1M input tokens, $0.30 / 1M output tokens | ~Rs. 0.02 to Rs. 0.09/min |
| TTS | Sarvam Bulbul v3 | Rs. 30 per 10,000 characters | ~Rs. 0.90 to Rs. 2.40/min |

**FX assumption:** 1 USD = Rs. 96.4. Actual invoice cost will vary with exchange rate, taxes, plan discounts, and provider billing terms.

## Baseline Per-Minute Estimate

Assumption for a normal lead qualification call:

- Connected call duration: 1 minute
- AI-generated speech: ~450 characters per connected minute
- LLM usage: ~2,000 input tokens and ~200 output tokens per connected minute
- Worker is self-hosted, not deployed on LiveKit Cloud Agents
- Recording, storage, analytics, and server compute are excluded

| Component | Calculation | Cost / Connected Minute |
|---|---:|---:|
| Vobiz SIP | Fixed per-minute channel rate | Rs. 0.45 |
| LiveKit third-party SIP | $0.004 * 96.4 | Rs. 0.39 |
| Deepgram Flux Multilingual | ($0.47 / 60) * 96.4 | Rs. 0.76 |
| Groq `openai/gpt-oss-20b` | ((2,000 * $0.075 + 200 * $0.30) / 1,000,000) * 96.4 | Rs. 0.02 |
| Sarvam Bulbul v3 | 450 * Rs. 30 / 10,000 | Rs. 1.35 |
| **Total** |  | **~Rs. 2.96/min** |

## Practical Call-Level Estimate

| Connected Call Duration | Estimated Cost |
|---:|---:|
| 1 minute | ~Rs. 2.96 |
| 2 minutes | ~Rs. 5.92 |
| 3 minutes | ~Rs. 8.88 |
| 5 minutes | ~Rs. 14.80 |

## Cost Range by Assistant Talk Time

Sarvam TTS is the biggest variable because it is billed by generated characters. Keeping the assistant concise improves both latency and cost.

| AI Speech Characters / Minute | Sarvam TTS Cost / Minute | Total Pipeline Cost / Minute |
|---:|---:|---:|
| 300 chars/min | Rs. 0.90 | ~Rs. 2.51 |
| 450 chars/min | Rs. 1.35 | ~Rs. 2.96 |
| 600 chars/min | Rs. 1.80 | ~Rs. 3.41 |
| 800 chars/min | Rs. 2.40 | ~Rs. 4.01 |

## LLM Cost Sensitivity

Groq is not the main cost driver for the current short-call flow, but it matters more once RAG context grows.

| LLM Usage / Minute | `openai/gpt-oss-20b` Cost / Minute | Previous `llama-3.3-70b-versatile` Approx. Cost / Minute |
|---:|---:|---:|
| 2,000 input + 200 output tokens | ~Rs. 0.02 | ~Rs. 0.13 |
| 5,000 input + 300 output tokens | ~Rs. 0.04 | ~Rs. 0.31 |
| 10,000 input + 500 output tokens | ~Rs. 0.09 | ~Rs. 0.61 |

For the current demo, the model switch mostly improves latency and future cost headroom. For production calls with larger tenant knowledge-base context, `openai/gpt-oss-20b` is materially cheaper than the previous 70B model.

## Optional LiveKit Cloud Agent Runtime

The estimate above assumes the LiveKit agent worker runs on RingIQ-managed infrastructure. If the worker is deployed on LiveKit Cloud Agents, add:

```text
$0.0100/min * 96.4 = ~Rs. 0.96/min
```

That would move the baseline estimate from:

```text
~Rs. 2.96/min -> ~Rs. 3.92/min
```

## Excluded Costs

These costs are not included in the per-minute estimate:

- Vobiz DID rental: Rs. 500/month per active number
- GST, payment fees, and currency conversion spread
- FastAPI / voice worker hosting
- Database, object storage, and recording retention
- Monitoring, logs, analytics, and alerting
- Failed call attempts where billing behavior may differ by provider
- Future compliance infrastructure such as DND scrubbing, consent tracking, and audit exports

## Optimization Levers

1. Keep assistant responses short.
   - Biggest immediate cost lever because Sarvam TTS is charged per generated character.

2. Keep RAG context compact.
   - Helps Groq token cost and first-token latency.

3. Measure real call logs.
   - Use actual generated TTS characters, LLM input/output tokens, connected seconds, and retry rates once demo calls are running.

4. Revisit WebSocket transport at scale.
   - Vobiz WebSocket streaming avoids LiveKit SIP/platform overhead, but increases engineering ownership for turn-taking, interruption, audio transport, and debugging.

5. Separate answered vs unanswered economics.
   - Sales-call unit economics should track cost per connected call, cost per qualified lead, and retry cost per lead.

## Source Links

- Vobiz SIP pricing: https://docs.vobiz.ai/concepts/sip-vs-websockets
- LiveKit pricing: https://livekit.com/pricing
- Deepgram pricing: https://deepgram.com/pricing
- Groq pricing: https://groq.com/pricing
- Sarvam API pricing: https://www.sarvam.ai/api-pricing
- USD/INR reference used for estimate: https://www.investing.com/currencies/usd-inr-historical-data

