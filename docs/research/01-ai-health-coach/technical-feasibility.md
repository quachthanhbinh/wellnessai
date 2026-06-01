# AI Health Coach — Technical Feasibility Research

**Component:** AI Health Coach  
**Research date:** 2026-06-01

---

## Kiến trúc tổng thể đề xuất

```
User message
      │
      ▼
[Intent Classifier]
Phân loại: data-query / education / emotional / escalation-needed
      │
      ├──► [RAG Pipeline] ──► Health knowledge base (articles, guidelines)
      │
      ├──► [Personalized Context Builder]
      │         └─ Pulls: vitals history, medication log, wearable data, lab results
      │
      ▼
[LLM Response Generator]
Model: fine-tuned or prompted with strong system prompt + guardrails
      │
      ▼
[Safety & Compliance Layer]
- Medical claim detector
- Hallucination check (citation required for clinical claims)
- Escalation trigger (if symptoms flagged as urgent)
      │
      ▼
[Response Formatter]
Plain language, with cited sources, with "Ask your doctor" nudge when needed
```

---

## Lựa chọn model

### Option A — API-based (Recommended for MVP)

| Model | Provider | Strengths | Concerns |
|---|---|---|---|
| **Claude 3.5 Sonnet** | Anthropic | Strong safety alignment, follows instructions well, good at nuanced health conversations | Cost at scale; data residency |
| **GPT-4o** | OpenAI | Best general performance, multimodal (can read lab result images) | US data processing by default |
| **Gemini 1.5 Pro** | Google | Long context window (1M tokens — good for full patient history), Google Health integration | Less proven for clinical safety |
| **Llama 3.1 70B** | Meta (self-hosted) | No data leaves Elfie infrastructure | Requires GPU infra; more ops overhead |

**Recommendation MVP:** Claude 3.5 Sonnet or GPT-4o với Business Associate Agreement (BAA) cho HIPAA compliance. Evaluate self-hosted Llama for markets with strict data residency (e.g., Vietnam PDPA, EU GDPR).

### Option B — Fine-tuned (v2+)

Fine-tune trên:
- Elfie's 1,000+ medically-reviewed articles (proprietary)
- Anonymized Q&A patterns từ ElfieCare Evidence AI
- WHO/ISH/ADA/ESC clinical guidelines

Cost: ~$50–100K one-time + retraining quarterly. Chỉ nên đầu tư sau khi validate PMF với Option A.

---

## Personalized Context Builder

**Challenge:** Làm sao đưa "toàn bộ lịch sử bệnh nhân" vào một conversation mà không exceed context window?

**Solution — Tiered Context Retrieval:**

```
Tier 1 — Always included (last 7 days):
  - Recent vitals (BP, glucose, weight, SpO2)
  - Medication adherence rate
  - Step count trend

Tier 2 — Included by relevance (semantic search):
  - Lab results related to user question
  - Historical patterns matching query topic
  - Doctor notes from ElfieCare (if opted in)

Tier 3 — On-demand:
  - Full history for explicit "compare with X months ago" queries
```

**Implementation:** Vector embeddings (pgvector on existing PostgreSQL, or Pinecone) cho Tier 2 semantic retrieval.

---

## Safety & Guardrails (Critical)

### Red lines — AI Coach tuyệt đối không được làm

1. **Diagnose** — "Bạn có thể bị X" → Prohibited
2. **Change medication dosage** — "Bạn nên giảm liều thuốc" → Prohibited
3. **Dismiss urgent symptoms** — Nếu user báo đau ngực + khó thở → Hard escalation, không AI response
4. **Reference specific test values as "normal/abnormal"** mà không có patient's doctor-set targets

### Implementation approach

```python
# Simplified guardrail pipeline
def check_response(response: str, intent: str) -> SafetyResult:
    # 1. Keyword-based fast check (low latency)
    if any(term in response for term in DIAGNOSTIC_TERMS):
        return SafetyResult(action="rewrite", reason="diagnostic_claim")
    
    # 2. LLM-based safety classifier (for subtle cases)
    safety_score = safety_classifier.evaluate(response, context=intent)
    if safety_score.diagnosis_confidence > 0.7:
        return SafetyResult(action="append_disclaimer")
    
    # 3. Citation check for clinical claims
    if contains_clinical_claim(response) and not has_citation(response):
        return SafetyResult(action="require_citation")
    
    return SafetyResult(action="pass")
```

### Urgent escalation triggers

| Symptom pattern | Action |
|---|---|
| Chest pain + shortness of breath | Hard stop → "Gọi cấp cứu ngay" |
| BP > 180/120 | "Liên hệ bác sĩ ngay hôm nay" |
| Suicidal ideation keywords | Mental health crisis protocol |
| Glucose < 60 or > 400 | Immediate alert |

---

## Data Pipeline

### Inputs vào AI Coach

```
Elfie App data store
├── vitals_readings (BP, HR, glucose, weight, SpO2, temp)
├── medication_logs (drug, dose, taken/skipped, time)
├── wearable_sync (steps, sleep stages, HRV, calories)
├── lab_results (user-uploaded PDFs + parsed structured data)
├── symptom_logs (free-text + structured tags)
└── user_goals (target BP, target weight, etc. — set by doctor or user)
```

### Privacy-safe processing

- Không gửi PII sang LLM API — chỉ gửi **anonymized health context**
- User ID thay thế bằng session token trong mỗi API call
- Conversation history encrypted at rest, deleted after 90 days (configurable per region)

---

## Estimating latency & cost

| Operation | Est. latency | Est. cost per query |
|---|---|---|
| Context retrieval (Tier 1+2) | ~200ms | ~$0.001 |
| LLM call (Claude Sonnet) | ~1.5s | ~$0.003–0.008 |
| Safety check | ~300ms | ~$0.001 |
| **Total per message** | **~2s** | **~$0.005–0.01** |

At 1M users × 2 messages/day = **$10,000–20,000/day** at full scale. MVP at 50K active users: ~$500–1,000/day. Acceptable if capped at 10 messages/user/day (free tier).

---

## Tech stack gợi ý

| Layer | Technology |
|---|---|
| LLM API | Claude 3.5 / GPT-4o (BAA) |
| Vector store | pgvector (reuse existing Postgres) |
| Context builder | Python service (FastAPI) |
| Safety classifier | Fine-tuned DistilBERT or rule-based + LLM hybrid |
| Streaming responses | Server-sent events (SSE) |
| Rate limiting | Redis (existing) |
| Conversation history | Postgres + AES-256 encryption |

---

## Build vs. Buy

| Component | Decision | Rationale |
|---|---|---|
| LLM | **Buy (API)** MVP → evaluate self-host v2 | Time to market; cost manageable at MVP scale |
| Vector search | **Build on existing pgvector** | Already in stack; avoid new vendor |
| Safety classifier | **Build** | Medical-specific; no off-shelf solution good enough |
| Context retrieval | **Build** | Elfie-specific data schema |
| Conversation UI | **Build on existing chat** | Extend existing Elfie chat UI patterns |
