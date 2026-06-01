# AI Health Coach — Product Spec (Approved)

**Component:** AI Continuity Loop — Component 1 of 3  
**Status:** APPROVED FOR PLANNING  
**Date:** 2026-06-01  
**Spec version:** v3 (final, 3-round debate loop)  

---

## Debate Loop Summary

| Round | Technical Advisor | Project Manager | Key issues resolved |
|---|---|---|---|
| 1 | 5.58 | 5.55 | Draft only — 4 critical + 14 hidden gaps |
| 2 | 7.81 | 8.33 | 4 critical + 4 high resolved; 6 conditions remaining |
| 3 | **8.8** | **8.73** | All conditions resolved; both agents issued APPROVED |

---

## Goal

Enable every Elfie user to ask natural-language questions about their own health data and receive personalized, contextual answers that help them understand — not diagnose — their condition, while meeting all applicable regulatory framing, data privacy, and safety requirements for the Vietnam and Thailand launch markets.

---

## Scope

### In (MVP)

1. Conversational Q&A interface against the user's own Elfie data: vitals, medication logs, wearable data, lab results, symptom logs, and user-set goals
2. Tiered context retrieval pipeline (Tier 1: last 7 days; Tier 2: semantic pgvector search up to 90 days; Tier 3: on-demand full history for explicit temporal queries)
3. **2-stage safety layer:** Stage 1 rule-based keyword/pattern check (≤50ms) + Stage 2 fine-tuned lightweight classifier (DistilBERT-class, ≤300M parameters); combined ≤400ms P95; primary LLM NOT used in safety layer
4. **Buffer-then-validate response architecture:** full response buffered, safety-checked, then delivered; no partial streaming
5. **NLP-based PII scrubber on user messages AND context builder output** (two-point scrubbing)
6. **Timezone normalization:** all timestamps in responses and context resolved to user's registered timezone
7. **SEA geo-gate enforcement:** API layer + app layer; allow-list: Vietnam (VN), Thailand (TH); server-side flag
8. Explicit opt-in consent flow before first use (separate from Elfie ToS)
9. **Consent revocation pipeline:** full deletion across all stores within 72-hour SLA; audit log tombstoned (not deleted)
10. Gamification: Elfie Coins awarded at conversation milestones
11. Rate limiting: 10 messages/user/day (free tier)
12. Languages: Vietnamese and English
13. LLM provider: Claude 3.5 Sonnet or GPT-4o with signed HIPAA BAA

### Mobile UI Deliverables (iOS + Android)

The following 9 mobile surfaces are in scope:

1. **Chat UI** — new screen with AI Coach entry point from home dashboard
2. **Consent modal** — health AI data use consent; copy reviewed by Medical Affairs + Legal before implementation
3. **AI transparency badge** — persistent indicator displayed throughout active AI Coach session
4. **Conversation history screen** — History tab; swipe-to-delete on individual conversations
5. **Settings → Privacy → AI Coach Data section** — retention override, delete all, export
6. **Coin events integration** — milestone achievement notifications + coin history entries
7. **Rate limit counter** — "X of 10 messages remaining today" inline in chat UI
8. **Geo-gate "not available" state** — shown to non-SEA users with "coming soon" CTA
9. **Timezone-based reset display** — rate limit counter shows local-time reset clock

### Explicitly Out (v2+)

| Item | Reason deferred |
|---|---|
| SSE streaming responses | Incompatible with post-LLM safety layer — SSE requires separate safety architecture review before enabling |
| Fine-tuned custom LLM | Requires PMF validation at MVP scale first |
| EU / US market rollout | Blocked pending EU AI Act conformity assessment and FDA legal review |
| ElfieCare doctor-set targets in context | Acceptable fallback defined (AC 1.4); v2 when ElfieCare integration confirmed |
| Multimodal inputs (voice, images) | Separate engineering track |
| Self-hosted Llama | Requires infrastructure assessment |

---

## Acceptance Criteria

### Section 1 — Core Conversational Functionality

**AC 1.1 — Supported query types**

Handles these categories; test suite covers ≥50 representative queries per category:

| Category | Example |
|---|---|
| Vitals status | "How is my blood pressure this week?" |
| Trend analysis | "Is my blood sugar improving compared to last month?" |
| Medication adherence | "Have I been taking my medication on time?" |
| Goal progress | "Am I on track with my weight goal?" |
| Comparative analysis | "How does this month compare to last month?" |
| Contextual education | "What does a HbA1c of 7.2 mean for someone managing Type 2 diabetes?" |

For queries outside these categories: *"I can only answer questions about your own health data recorded in Elfie. For general medical questions, please consult a healthcare professional."*

*Verification:* Automated regression test suite ≥300 test cases (50 per category); manual QA of 20 edge-case conversations.

---

**AC 1.2 — Tiered context retrieval**

- **Tier 1 (always included):** Last 7 days of vitals, medication adherence rate, step count trend
- **Tier 2 (semantic retrieval):** Historical patterns via pgvector cosine similarity, top-5 results, threshold ≥0.75
- **Tier 3 (on-demand):** Full longitudinal history; triggered only by explicit temporal queries ("compare with 6 months ago")

Tier 3 is never triggered automatically.

*Verification:* Unit tests confirming tier activation rules; integration test confirming Tier 3 requires explicit temporal framing.

---

**AC 1.3 — Timezone normalization (R8)**

- All date/time references in AI responses expressed in user's registered timezone (not UTC, not server timezone)
- Context builder converts all data timestamps from UTC to user timezone before inserting into LLM prompt
- User timezone is a required field; defaults to device-reported timezone at registration
- If timezone is absent: fall back to UTC with visible notice in response: *"Times are shown in UTC. Update your timezone in Profile → Settings."*

*Verification:* Unit tests with synthetic users in UTC+7 (VN), UTC+8 (TH), UTC−5 (US regression), UTC (fallback); assert timestamps match expected local time. Regression test for DST transitions.

---

**AC 1.4 — ElfieCare targets fallback (resolves OQ-3)**

Context builder applies this priority order for goal/target values:

1. **Doctor-set targets from ElfieCare** — only when: user has active linked ElfieCare relationship AND doctor has set targets AND user opted-in to ElfieCare sharing
2. **User-set goals from Elfie App** — when ElfieCare targets unavailable
3. **Clinical guideline defaults** — when neither exists; referenced with source attribution

Response explicitly attributes source:
- *"Based on the target your care team has set (130/80 mmHg)..."*
- *"Based on your personal goal (140/90 mmHg)..."*
- *"According to ISH hypertension guidelines (target <140/90 mmHg)..."*

AI NEVER synthesizes or infers a clinical target where none exists.

*Verification:* Test matrix: 4 states × 3 biomarker types. Assert correct target source and attribution string.

---

**AC 1.5 — Rate limiting**

- Free tier: maximum 10 messages per user per day
- On limit: *"You've reached your daily conversation limit. Come back tomorrow — streaks earn bonus coins!"*
- Counter resets at midnight in user's registered timezone (AC 1.3)
- Enforcement at API gateway before safety layer or LLM call

*Verification:* Integration test confirming 11th message rejected with correct message; counter resets at midnight in user's local timezone.

---

**AC 1.6 — Citation requirement on clinical claims**

- Clinical guideline values must cite the guideline inline (e.g., *"According to ISH 2020 guidelines..."*)
- No numerical clinical reference without citation

*Verification:* Automated citation-presence check across test suite; manual review of 20 guideline-referencing responses.

---

### Section 2 — Safety & Guardrails

**AC 2.1 — 2-Stage Safety Classifier (revised from R1 + R5)**

Operates on the **complete buffered LLM response**. Combined latency budget: ≤400ms P95.

**Stage 1 — Rule-based keyword/pattern check (≤50ms)**

Deterministic pattern matching against versioned prohibited patterns:
- Diagnostic claims: "you have", "you may have", "this indicates", "this suggests you have", "consistent with a diagnosis of"
- Medication directives: "increase your dose", "decrease your dose", "stop taking", "you should take more/less"
- Symptom dismissal: "nothing to worry about", "this is probably nothing", "you don't need to see a doctor"

Pattern list is version-controlled; changes require PR with medical reviewer approval.

On Stage 1 match: response blocked/rewritten immediately; Stage 2 NOT invoked.

**Stage 2 — Lightweight ML classifier (≤350ms; Stage 1 + Stage 2 combined ≤400ms P95)**

- Model: DistilBERT-class, ≤300M parameters, hosted on Elfie's own inference infrastructure
- Invoked only when Stage 1 passes
- Task: binary classification (safe / unsafe) for paraphrased diagnostic framing, medication directives, symptom dismissal
- On "unsafe": response rewritten or regenerated; raw unsafe response NEVER delivered to user

**Validation dataset requirements (R5):**

| Requirement | Value |
|---|---|
| Total labeled examples | ≥ 1,000 |
| Positive examples (diagnostic/unsafe framing) | ≥ 200 |
| Independent annotators | ≥ 2 with healthcare background |
| Inter-annotator agreement (Cohen's kappa) | ≥ 0.80 |
| If kappa < 0.80 | Arbitration round required |
| Performance thresholds | Precision ≥ 95%, Recall ≥ 90% |
| Validation required before | Any real user sees the feature |
| Re-validation | After any classifier update + quarterly |

*Verification:* Automated benchmark against locked, independently-annotated test set; archived after every model update.

---

**AC 2.2 — Hard escalation triggers**

Evaluated against user message AND Tier 1 context. When matched: AI response suppressed; replaced by hardcoded safety message only.

| Trigger condition | Safety message |
|---|---|
| BP > 180/120 in Tier 1 context | *"Your most recent blood pressure reading is very high. Please contact your doctor or emergency services today. Do not wait."* |
| Glucose < 60 or > 400 mg/dL in Tier 1 | *"Your most recent blood sugar reading is outside a safe range. Please contact your doctor or emergency services immediately."* |
| Chest pain AND shortness of breath (co-occurrence) | *"If you are currently experiencing chest pain and difficulty breathing, call emergency services now."* |
| Suicidal ideation keyword match | Existing Elfie mental health crisis flow |

Escalation thresholds are **immutable constants** — not configurable by LLM, user input, or feature flags. Changes require code deployment reviewed by a qualified medical professional.

*Verification:* Integration tests with synthetic Tier 1 data for each trigger; assert correct safety message returned, AI response body empty.

---

**AC 2.3 — Diagnostic language prohibition**

AI responses must never contain:
- Disease attribution: "you have X", "you may have X", "consistent with X"
- "normal" or "abnormal" as standalone assessments (comparative framing required instead)
- Medication dosage change recommendations

*Verification:* Adversarial test suite ≥100 red-line prompts; zero failures permitted. Expanded quarterly when new evasion patterns identified.

---

**AC 2.4 — Treatment-adjacent disclaimer**

Any response that explains clinical significance of a biomarker value, references a medication by name, or describes a symptom pattern must include:

> *"This information is for your awareness only. For medical advice, diagnosis, or treatment decisions, please consult your healthcare provider."*

Rendered as a separate UI block below the response body — not inline text.

*Verification:* Automated disclaimer-presence detection across all treatment-adjacent test cases; UX review confirming separate visual block on iOS, Android, web.

---

### Section 3 — Regulatory Framing

**AC 3.1 — Non-device CDS framing**

AI Coach is positioned exclusively as a data understanding tool:
- System prompt: explicitly instructs LLM "health data understanding assistant, not a diagnostic tool"
- Onboarding copy: "AI Coach helps you understand your Elfie data. It does not provide medical diagnoses, prescriptions, or clinical recommendations."
- In-app header: "Understanding your health data · Not a medical diagnosis"
- Marketing copy: reviewed against FDA Non-device CDS guidance; must not use "AI doctor", "medical AI", or "diagnosis"

*Verification:* Legal sign-off on all user-facing copy before launch.

---

**AC 3.2 — AI identity disclosure (EU AI Act Art. 52)**

Three mandatory disclosure locations:
1. Onboarding consent screen: *"You are about to interact with an AI system. This AI is not a doctor."*
2. Chat interface header (persistent throughout session)
3. Footer of every AI response: *"Generated by Elfie AI Coach · Not medical advice"*

*Verification:* UX audit checklist on iOS, Android, web.

---

**AC 3.3 — SEA geo-gate enforcement (revised delivery gap)**

API layer:
- All `/ai-coach/*` endpoints check user's registered country code against allow-list `["VN", "TH"]`
- Country code from registration record (server-side); NOT from IP address
- Outside allow-list: HTTP 403 with localized message

App layer:
- AI Coach entry point hidden via server-side feature flag for non-SEA users

Allow-list expansion: requires (a) legal review, (b) server config update, (c) localized copy in release.

*Verification:* Integration tests: VN → allow; TH → allow; US → 403; FR → 403; both API and app-layer per case.

---

### Section 4 — Data Privacy & Security

> **Processing pipeline order:** AC 4.10 PII scrubber (user message) → context builder → AC 4.10 PII scrubber (assembled prompt) → AC 4.2 session token → LLM API (receives anonymized, PII-scrubbed context only)

---

**AC 4.1 — BAA in place before any PHI processing**

- Signed HIPAA BAA with LLM API provider required before any user health data is sent to provider
- BAA must specify: no training on Elfie data; API log retention ≤30 days or zero-day retention
- If BAA lapses, feature flag disabled immediately

*Verification:* Legal sign-off; BAA on file in legal repository. Launch Gate #1.

---

**AC 4.2 — Session token anonymization**

- User identity represented by per-session random token in all LLM API calls
- New token generated per conversation (not per user)
- Token ↔ user mapping stored only in Elfie's Redis (short TTL)
- Token does not contain, encode, or derive from any stable user identifier (no hashing of user ID)

*Verification:* Code review confirming cryptographically random token; unit test confirming two conversations from same user produce different tokens; entropy ≥128 bits.

---

**AC 4.3 — Encryption**

- Conversation history in Postgres: AES-256 at rest
- pgvector embeddings: same encryption-at-rest policy as Postgres
- All data in transit: TLS 1.3 minimum

*Verification:* Security configuration audit; TLS scan.

---

**AC 4.4 — Audit trail**

Every conversation generates audit log entry containing:
- Anonymized user token
- Conversation timestamp (UTC)
- Query intent classification
- Safety classifier outcome (Stage 1 result, Stage 2 result, overall)
- Escalation trigger fired (if any)
- Response delivered: yes/no
- Model version and safety classifier version

Audit logs do NOT contain raw text of user messages or AI responses. Retained per SOC2 Type 2 (minimum 1 year).

*Verification:* SOC2 audit; access control penetration test; confirm raw message text absent from log entries.

---

**AC 4.5 — Auto-deletion default**

- Conversation history deleted 90 days after conversation date by default
- Users can shorten to 30 days in Privacy Settings
- Users can trigger immediate deletion via Privacy Settings → Delete AI Conversation History

*Verification:* Integration test confirming scheduled deletion processes records ≥90 days old; manual test of immediate deletion.

---

**AC 4.6 — Data minimization**

- Context builder retrieves only data types relevant to user's query topic
- A question about sleep does not pull medication adherence data unless explicitly connected

*Verification:* Code review; unit tests asserting out-of-topic data types excluded from context per query category.

---

**AC 4.7 — Access controls**

- Conversation data accessible only to user + authorized Elfie backend services (AI Coach, audit)
- No ElfieCare clinician access to AI Coach conversation text (out of scope for MVP)
- RBAC at API layer; unauthorized role access returns 403

*Verification:* Authorization bypass penetration test; RBAC configuration review.

---

**AC 4.8 — Deletion scope (revised R4)**

When conversation history is deleted, Elfie's own systems execute:

| Store | Action | SLA |
|---|---|---|
| Postgres conversation records | Soft-delete → hard-delete | Hard-delete within 72 hours |
| pgvector embeddings | Deleted | Within 72 hours |
| Redis session context | Purged | Within 1 hour |
| Audit log linkage fields | Tombstoned (see AC 6.2 Step 6) | Within 72 hours |

**Elfie does NOT represent to users that LLM provider API logs are deleted on demand.**

LLM provider API log retention governed exclusively by BAA terms (≤30 days). Elfie has no API endpoint to delete provider-side logs.

User-facing copy (legal-reviewed):
> *"Your AI Coach conversation history has been deleted from Elfie. Under our data processing agreement, your AI provider may retain anonymized API interaction logs for up to 30 days before they are automatically deleted."*

*Verification:* Integration test confirming each store clears within SLA; legal review of user-facing copy.

---

**AC 4.9 — No PII in LLM API payload**

Context builder enforces: no user full name, email, phone number, physical address, or national ID in assembled LLM prompt.

*Verification:* PII-scanning of 500 assembled prompts; zero PII occurrences.

---

**AC 4.10 — NLP-based PII scrubber — TWO points (revised R3 + C1)**

Scrubber runs at **two distinct points**:

**(a) User message input** — before intent classifier or context builder  
**(b) Assembled context builder output** — before LLM API call; covers ElfieCare notes, lab result text, doctor comment fields

**Detected and redacted:**

| PII type | Examples |
|---|---|
| Personal names (NER) | "I'm Nguyễn Văn A", "My name is John" |
| Phone numbers | Vietnamese, Thai, international formats |
| Email addresses | Any valid email pattern |
| Physical addresses | Street, district, city patterns |
| National IDs | Vietnamese CCCD (12-digit), Thai national ID (13-digit) |

Redaction: replace with type placeholder before forwarding.

**Failure handling — fail-fast:**
- Scrubber error or timeout → message REJECTED (not silently forwarded)
- User receives: *"We couldn't process your message right now. Please try again."*
- Failure logged; original message text NOT stored in error log

Scrubber supports Vietnamese and English. Hosted on Elfie infrastructure.

*Verification:*
- Unit tests: ≥20 cases per PII category in Vietnamese + English (≥200 total)
- Integration test: scrubber-fail path rejects message, not forwarded to context builder
- Stage (b) test: crafted prompt with doctor note containing full name and clinic address; verify neither appears in LLM API payload
- Lab upload path included in test coverage (PDFs commonly embed patient demographics)

---

### Section 5 — Performance & Scalability

**AC 5.1 — End-to-end response latency (revised R2)**

Measured from user message submission to **complete response delivery** (buffer-then-validate; SSE streaming not used in MVP).

| Percentile | Target |
|---|---|
| P50 | ≤ 2,000 ms |
| P95 | ≤ 4,000 ms |

Loading indicator appears within 200ms of message submission.

*Verification:* Load test with realistic query corpus; latency measured at API gateway.

---

**AC 5.2 — Safety layer latency budget**

| Stage | Target |
|---|---|
| Stage 1 (rule-based) | ≤ 50ms |
| Stage 1 + Stage 2 combined | ≤ 400ms P95 |

Measured in isolation from LLM API call.

*Verification:* Isolated performance test on 1,000 pre-generated LLM response samples.

---

**AC 5.3 — Context retrieval latency**

| Tier | P95 target |
|---|---|
| Tier 1 (last 7 days, direct DB) | ≤ 100 ms |
| Tier 2 (pgvector semantic) | ≤ 200 ms |
| Tier 3 (full history, on-demand) | ≤ 800 ms |

---

**AC 5.4 — Rate limiting overhead**

Rate limit middleware adds ≤10ms P95 per request.

---

**AC 5.5 — Load test (revised R7; replaces former placeholder)**

- **Load test target:** 1,000 concurrent requests sustained 5 minutes
- **Success criteria:** P95 ≤ 4,000ms; zero HTTP 5xx errors throughout test window
- **LLM component:** mocked/cached layer (NOT production LLM endpoints)
- **Safety layer:** real classifier (no mock) to validate latency under load
- **50K concurrent:** documented as scaling design exercise (not a launch requirement)
- **Pre-launch:** LLM provider contractual throughput tier confirmed and documented before launch (Launch Gate #17)

*Verification:* Load test report reviewed and signed by Technical Advisor before feature flag enabled.

---

**AC 5.6 — Availability**

- Target: 99.5% monthly uptime
- If LLM API unavailable: *"AI Coach is temporarily unavailable. Please try again in a few minutes."*
- No coin rewards during degraded mode

---

### Section 6 — User Consent & Control

**AC 6.1 — Explicit opt-in consent**

Required consent screen elements:
1. What data is used (vitals, medications, wearable data, lab results, health goals)
2. That an AI processes the data
3. Responses are not medical advice
4. Data shared with AI provider under HIPAA BAA
5. Link to Privacy Policy and BAA summary

Consent stored with: user ID, consent version, timestamp, consent text hash. Re-consent required on material changes (new AI provider, new data types, new retention period).

*Verification:* UX test flow; consent record audited for required fields; re-consent triggered by version increment tested.

---

**AC 6.2 — Consent revocation (revised R6 + C2)**

Steps execute in order; each with defined SLA and per-step audit record:

| Step | Action | SLA |
|---|---|---|
| 1 | New message processing blocked | Immediate (synchronous) |
| 2 | In-flight Celery tasks cancelled | Within 1 minute (best-effort; failures logged) |
| 3 | Redis session context purged | Within 1 hour (guaranteed) |
| 4 | pgvector embeddings deleted | Within 72 hours (guaranteed) |
| 5 | Postgres records soft-deleted → hard-deleted | Hard-delete within 72 hours (guaranteed) |
| 6 | **Audit log tombstoned:** user_id replaced with permanent tombstone; token-to-user mapping severed; audit event itself RETAINED for 6 years per HIPAA | Within 72 hours (guaranteed) |
| 7 | Audit record written with completion timestamp for each of Steps 1–6 | Upon completion of each step (required) |

**Step 6 detail:** Audit log entries are NOT deleted. Deletion of audit entries violates HIPAA 6-year retention requirement. The tombstone operation is irreversible — no system may re-link the audit record to a real user identity after tombstoning.

SLA breach: if Steps 3–6 not confirmed within 72h → alert operations team → notify user.

*Verification:* Integration test: revoke consent for user with active session + queued Celery task + stored Postgres + pgvector + Redis data. Assert each step completes within SLA. Assert audit record has completion timestamp per step. Assert tombstone: entries exist, user_id = tombstone value, zero rows on user table join, total entry count unchanged.

---

**AC 6.3 — Right to explanation**

Users may request explanation of why AI gave a specific response:
- Data context used (which Tier, data types)
- Query classification (intent category)

Delivery: JSON export in Privacy Settings → My AI Coach Data within 48 hours of request.

---

**AC 6.4 — Conversation history management**

- View conversation history (History tab)
- Delete individual conversations (swipe-to-delete)
- Delete all conversation history (Privacy Settings)
- All deletion paths trigger store-wide deletion in AC 4.8 within stated SLAs

---

**AC 6.5 — Under-18 restriction**

- Under-18 users (by account date of birth) must not have AI Health Coach enabled
- AI Coach hidden and consent gate not presented for under-18 users
- If date of birth absent: AI Coach disabled until age confirmed

*Verification:* Test with synthetic under-18 account; confirm feature hidden.

---

### Section 7 — Gamification

**AC 7.1 — Coin milestones**

| Milestone | Coins |
|---|---|
| First AI Coach conversation completed | 50 coins |
| 7-day conversation streak | 100 coins |
| 10th conversation (cumulative) | 75 coins |

Coin events via existing Elfie coin pipeline. Milestone awards are idempotent (same milestone twice = no-op at coin service layer).

*Verification:* Integration test confirming coin events fire at each milestone; double-award idempotency test.

---

**AC 7.2 — No coins for over-use**

- Milestone-based only; no per-message coin rewards
- No coins during safety events (escalation triggered or safety layer blocked)

*Verification:* Code review of coin-trigger logic; confirm per-message awards absent.

---

## Pre-Launch Programmes

**These are external dependency tracks that must begin immediately upon spec approval. No feature launch until all gates are passed.**

### P1 — Safety Classifier Annotation Programme

**Duration:** 10–12 weeks (realistic; 8-week floor requires pre-contracted annotators on Day 1)  
**Owners:** ML Engineering + Medical Affairs  
**Blocks:** AC 2.1 validation; Launch Gates #3, #4, #5

| Gate | Deliverable | Exit criteria | Target week |
|---|---|---|---|
| P1-G1 | Annotation schema | Taxonomy approved by ≥2 healthcare professionals | Week 2 |
| P1-G2 | Labeled dataset | ≥1,000 examples, ≥200 positive, ≥2 healthcare-background annotators | Week 8 |
| P1-G3 | Inter-annotator agreement | Cohen's kappa ≥0.80; if <0.80, arbitration round + recalculation | Week 9 |
| P1-G4 | Model trained | DistilBERT-class model trained on P1-G3-approved dataset | Week 10 |
| P1-G5 | Classifier validated | Precision ≥95%, Recall ≥90% on held-out test split | Week 11 |
| P1-G6 | Latency validated | Stage 1 + Stage 2 ≤400ms P95 at 1,000 req/min | Week 12 |

---

### P2 — Medical Audit Workflow

**Duration:** 6–8 weeks (can partially overlap P1 after P1-G1)  
**Owners:** Medical Affairs + Engineering  
**Must be OPERATIONAL before launch** — not a post-launch backfill  
**Blocks:** Launch Gates #7, #11, #12, #13

| Deliverable | Exit criteria |
|---|---|
| P2-D1: Sampling pipeline | Stratified sampling pipeline running in staging; Medical Affairs reviewed |
| P2-D2: Reviewer interface | Tool deployed; Medical Affairs reviewer onboarded |
| P2-D3: Report template | Standardized monthly report; Medical Affairs lead approved |
| P2-D4: **Dry-run using synthetic conversation dataset** | ≥100 synthetic conversations (full AC 1.1 category distribution); ≥10 escalation scenarios; ≥10 safety classifier scenarios; ≥20 edge cases. Generated by ML Engineering, reviewed by Medical Affairs for clinical realism before dry-run. Medical Affairs lead sign-off on dry-run report required. Synthetic dataset kept as permanent regression test resource. |

---

### Medical Affairs bandwidth — top delivery risk

P1 and P2 both require Medical Affairs as named approver in overlapping time windows.

**Required at Week 0 planning kickoff:**
- Medical Affairs lead must confirm dedicated capacity for both P1 and P2 simultaneously, or provide a written sequencing plan
- A single Medical Affairs resource may not hold P1-G3 and P2-D4 sign-off in the same calendar week
- If capacity cannot be confirmed at Week 0 → escalate to product sponsor immediately; launch date cannot be committed until resolved

---

## Launch Gate Checklist

All 19 items must be marked PASS before feature flag is enabled for any real user. Technical Advisor signs off on complete checklist.

| # | Gate | Owner | Verification method |
|---|---|---|---|
| 1 | BAA signed with LLM API provider; terms: no training on Elfie data, log retention ≤30 days | Legal | BAA on file; reviewed by Legal lead |
| 2 | HIPAA BAA valid for MVP launch markets (VN, TH) | Legal | Written confirmation + provider acknowledgment |
| 3 | Safety Classifier P1 all 6 gates passed | ML + Medical | P1 gate completion report, signed by both owners |
| 4 | Classifier: Precision ≥95%, Recall ≥90% on locked test set | ML Engineering | Benchmark report with confusion matrix |
| 5 | Inter-annotator agreement: Cohen's kappa ≥0.80 | Medical Affairs | IAA calculation documented |
| 6 | Safety layer: Stage 1 + Stage 2 ≤400ms P95 at 1,000 req/min | Engineering | Safety layer isolated performance test report |
| 7 | Medical Audit Workflow P2 operational: P2-D1 through P2-D4 complete; dry-run signed off | Medical Affairs | P2-D4 sign-off from Medical Affairs lead |
| 8 | NLP PII scrubber deployed; ≥20 cases/category Vietnamese + English; both scrubbing points; fail-fast path confirmed | Engineering | Test report + integration test log |
| 9 | SEA geo-gate: VN → allow; TH → allow; US → 403; FR → 403; both API and app layer | Engineering | Integration test report |
| 10 | Consent revocation pipeline tested; 72h SLA verified all stores; tombstone verified; per-step audit record confirmed | Engineering | Integration test report with per-step timing |
| 11 | P50 ≤2,000ms and P95 ≤4,000ms under realistic load | Engineering | Load test report |
| 12 | Load test: 1,000 concurrent / 5 min; P95 ≤4,000ms; zero 5xx; LLM mocked | Engineering | Load test report reviewed by Technical Advisor |
| 13 | Buffer-then-validate confirmed: no streaming path, no safety bypass path | Engineering | Code review sign-off + integration test |
| 14 | All 4 hard escalation patterns validated; correct safety message; empty AI body | Engineering + Medical | Integration test report; medical reviewer confirms message copy |
| 15 | Timezone normalization: UTC+7 (VN), UTC+8 (TH), UTC−5 (US regression), UTC fallback | Engineering | Unit test report |
| 16 | Diagnostic language red-line: ≥100 adversarial prompts; zero unsafe outputs | ML + QA | Adversarial test report; zero-failure result |
| 17 | LLM provider contractual throughput tier confirmed for MVP launch volume | Engineering + Legal | Written confirmation from provider |
| 18 | All user-facing copy legal-reviewed: disclaimers, AI disclosures, consent screens, deletion confirmation, safety messages | Legal | Legal sign-off document |
| **19** | **AI-specific adversarial test suite: zero critical failures** covering (a) prompt injection, (b) multi-turn jailbreak, (c) medical claim extraction under rephrasing, (d) data exfiltration. Basis: OWASP LLM Top 10 (LLM01, LLM02) + EU AI Act Annex III cybersecurity | ML + Security | Signed red-team report with per-category pass/fail breakdown |

---

## Open Questions

| # | Question | Status |
|---|---|---|
| OQ-1 | LLM provider selected? BAA/DPA executed? | **Open — ⛔ blocks all LLM work.** Start procurement immediately. |
| OQ-2 | Self-hosted Llama feasibility for Vietnam PDPD data residency? | **Open — legal input needed.** If Vietnam PDPD requires in-country processing, Llama becomes a requirement. |
| OQ-3 | ElfieCare doctor-set targets fallback | **RESOLVED.** AC 1.4 defines 3-level priority. |
| OQ-4 | PDPA (Thailand) + PDPD (Vietnam) consent wording constraints? | **Open — country-specific legal review.** May result in AC 6.1 copy amendments before launch. |
| OQ-5 | NLP PII scrubber precision/recall threshold? (false-negative rate acceptable for forwarded missed PII?) | **Open — Legal/Privacy risk acceptance decision.** May add quantified scrubber accuracy AC in a future revision. |

---

*This spec is APPROVED FOR PLANNING. Product Owner, Technical Advisor (rounds 1–3), and Project Manager (rounds 1–3) have reviewed. All Critical and High risks are resolved. Medium items are tracked as engineering/UX tickets. Planning document goes in `docs/plans/01-ai-health-coach.md`.*
