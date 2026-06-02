# Proactive RAG with Progressive Profiling — Product Spec

**Component:** AI Continuity Loop — Component 4 (Enhancement layer on Component 1)
**Status:** PENDING REVIEW
**Date:** 2026-06-02
**Spec version:** v2 (Product Owner decisions incorporated 2026-06-02)

---

## Goal

Enable the AI Health Coach to build a persistent, structured health profile from natural-language conversations over time — using NER-based entity extraction running in parallel with RAG retrieval — so that every response becomes progressively more personalized without requiring users to fill in a form, while embedding targeted follow-up questions that organically close the most relevant profile gaps for the current query.

---

## Platform Foundation (Existing Elfie Capabilities)

Component 4 is built on top of three deployed Elfie capabilities. These are assumed available as data sources and infrastructure — engineers do not need to build them from scratch.

| Capability | What it provides to Component 4 |
|---|---|
| **Hyper-Personalization engine** | Elfie already connects RAG to the user's "lifestyle cycle" — morning BP readings, last night's sleep data, meal patterns, tracked health metrics. These live in Elfie's structured stores and are fetched via Tier 1 RAG (not re-extracted by NER). Component 4's profile enriches this retrieval further with conversationally-extracted context. |
| **Medical Record Scanning (Quét chỉ số khám bệnh)** | AI-digitized data from health examination forms (lab values, health check results) flows into Elfie's structured data stores. Component 4 retrieves this via Tier 1 RAG; NER does not re-extract it. Scanned data can pre-populate or confirm profile fields (e.g., confirmed diagnoses, lab reference baselines). |
| **Clinical Decision Support knowledge base (ElfieCare)** | Elfie maintains a curated medical knowledge base with trusted-source rules and treatment protocols for diabetes, hypertension, and other conditions. This is the primary evidence base for OQ-2 (ICD-10 normalization dictionary) and the Gap Analyzer intent map (AC 1.3). Medical Affairs rules already govern what the AI is and is not permitted to recommend. |

**Inherited architectural principle:** AI reasons from existing knowledge and data — it does not generate medical knowledge. Component 4 extends this: NER extracts entities from conversation; all medical reasoning draws from Elfie's curated knowledge base and the user's own structured health data. The LLM is a reasoning engine, not a knowledge source.

---

```
User Message
     │
     ▼
[PII Scrubber (Point A)]                       ← Inherited from Component 1 AC 4.10
     │
     ├──────────────────────┬────────────────────────────────┐
     ▼                      ▼                                ▼
[Intent Classifier]   [NER Pipeline]              [Tier 1 RAG Retrieval]
[Component 1]         [GLiNER / SpaCy]             [Structured DB: vitals, meds]
     │                     │
     │                     ▼
     │              [Profile Store Update]
     │              [PostgreSQL append-only]
     │                     │
     ▼                     ▼
[Profile Gap Analyzer] ←──[Profile Snapshot]
     │
     ▼
[Agentic Orchestrator]          ← MVP: rule-based; v2: LangGraph state machine
     │
     ├──► [Vector RAG]           pgvector semantic search → profile-aware rerank
     ├──► [Structured Retriever] Elfie vitals/meds/lab DB
     └──► [GraphRAG]             ← v3: Medical Knowledge Graph (Neo4j / Apache AGE)
                  │
                  ▼
         [Agentic Reflector]     ← v2: "Sufficient context?" loop (max 3 iterations)
                  │
                  ▼
       [Context Assembler]
       System Prompt + Profile Summary (~200 tokens) +
       Tier 1 data + Retrieved chunks + Conversation buffer
                  │
[PII Scrubber (Point B)]                       ← Inherited from Component 1 AC 4.10
                  │
                  ▼
         [Reasoning LLM]
         Claude 3.5 Sonnet / GPT-4o + chain-of-thought
                  │
         [Post-gen Question Validation]        ← strips rule violations before safety
                  │
         [2-Stage Safety Layer]                ← Inherited from Component 1 AC 2.1
                  │
                  ▼
         [Response + embedded questions (0–2)]
```

---

## Scope

### In (MVP)

1. **Intent + Entity Extractor (NER pipeline):** GLiNER/SpaCy model running parallel to Tier 1 RAG retrieval on every user message, after the 2-point PII scrubber; extracts seven entity types: `CONDITION`, `MEDICATION`, `DEMOGRAPHIC`, `LIFESTYLE_FACTOR`, `SYMPTOM_CHRONIC`, `BIOMARKER_PREFERENCE`, `TEMPORAL_CONTEXT`; hosted on Elfie NER inference service (not LLM-based)
2. **User Health Profile Store:** PostgreSQL append-only schema scoped by `profile_id` (not `user_id`) covering six field groups — demographics, conditions, medications, lifestyle, biomarker preferences, chronic symptoms; every entry carries confidence score, source conversation reference, timestamp, and confirmation status
3. **Family Care profile isolation:** hard per-profile-id scoping at database, session, and context assembly layers; `active_profile_id` bound to session token at conversation start; context never crosses profile boundaries
4. **Profile Gap Analyzer:** rule-based component (no LLM, no ML) mapping detected query intent to required profile fields; identifies absent or low-confidence required fields; ranks by query relevance; outputs ≤ 2 gap fields
5. **Embedded follow-up questions:** up to 2 targeted questions embedded naturally in AI responses when Gap Analyzer detects missing high-priority fields; questions never re-ask known data; all questions pass the existing 2-stage safety classifier
6. **Low-confidence extraction confirmation flow:** extractions below confidence threshold 0.60 staged in a pending table; single confirmation prompt in a subsequent session; staged extractions expire after 30 days
7. **Context Assembler enhancement:** profile summary block (≤ 200 tokens) injected ahead of retrieved docs and conversation buffer; hedged language for unconfirmed fields
8. **Profile-aware RAG reranking:** pgvector Tier 2 chunks re-ranked using profile relevance signal after cosine similarity retrieval, before Context Assembler insertion
9. **User profile transparency UI:** Settings → Privacy → AI Health Profile — field view with confidence indicators, individual field correction/deletion, full profile deletion, JSON export, pending extractions view
10. **Separate consent gate for progressive profiling:** explicit opt-in after AI Health Coach consent; declining leaves AI Health Coach fully functional
11. **Profile deletion pipeline:** full deletion across PostgreSQL profile store and staging table within 72-hour SLA; integrated with Component 1 consent revocation pipeline
12. **Profile-building gamification:** Elfie Coins awarded at two milestones: (a) first profile field confirmed (any field group), (b) profile completeness ≥ 50% for the user's primary tracked condition; coin events integrated with existing Elfie gamification pipeline via the same coin event bus used by AI Health Coach (Component 1)

### Mobile UI Deliverables (iOS + Android — MVP)

1. **Profile selector UI** — shown at AI Coach entry when account has > 1 profile (Family Care); user selects who they are asking about before conversation starts; cannot change mid-conversation
2. **Combined consent modal (dual-checkbox)** — one modal with two independent checkboxes: Checkbox A (AI Health Coach, required) + Checkbox B (Progressive Profiling, optional, unchecked by default); copy reviewed by Medical Affairs + Legal before implementation
3. **Settings → Privacy → AI Health Profile section** — field-level view with confidence indicators, primary-condition completeness progress bar (%), individual field deletion, full profile deletion, JSON export, pending extractions view
4. **Profile-aware response indicator** — subtle badge ("Personalized for you") when profile context was used; tappable to show which **field groups** were used (CONDITIONS, MEDICATIONS, LIFESTYLE, etc.) — not individual field values
5. **Pending extraction confirmation prompt** — single inline conversational prompt in next session; not a form
6. **Profile milestone coin notification** — in-app notification and coin history entry when profile milestones are reached (first confirmed field, 50% completeness for primary condition); uses existing Elfie coin notification infrastructure

### Explicitly Out (v2+)

| Item | Reason deferred |
|---|---|
| **AgenticRAG (multi-hop iterative retrieval)** | LangGraph state machine; latency profiling required; see Technology Roadmap §v2 |
| **GraphRAG (Medical Knowledge Graph)** | Neo4j / Apache AGE infra; medical ontology pipeline; see Technology Roadmap §v3 |
| Profile data shared with ElfieCare or Pre-Visit Agent | Requires separate dual-consent flow; no doctor-side profile reading in MVP |
| Active profile-building UI (user manually fills form) | Defeats conversational extraction approach |
| Voice/multimodal profile extraction | Separate engineering track; NER pipeline currently text-only |
| Profile portability / export to EHR | Regulatory complexity; separate legal review required |
| Profile used by Predictive Adherence AI (Component 2) | Cross-component data sharing requires separate DPIA |
| EU / US market rollout | Same constraints as Component 1 |
| Autonomous profile repair (AI-initiated correction without user trigger) | Product ethics review required |
| Real-time NER on wearable / CGM data streams | Requires stream processing infrastructure |

---

## Acceptance Criteria

### Section 1 — Progressive Profiling & Entity Extraction

---

**AC 1.1 — Profile Store Schema**

The User Health Profile Store is an append-only PostgreSQL table: `user_health_profile_entries`.

**Schema:**

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | Entry identifier |
| `account_id` | UUID FK | Elfie account (may manage multiple profiles) |
| `profile_id` | UUID FK | Isolated per family member — primary isolation key |
| `field_group` | ENUM | `DEMOGRAPHICS`, `CONDITIONS`, `MEDICATIONS`, `LIFESTYLE`, `BIOMARKER_PREFERENCES`, `SYMPTOMS_CHRONIC` |
| `field_key` | VARCHAR(64) | Canonical field name (see Field Catalogue) |
| `field_value` | JSONB | Structured value; schema per `field_key` |
| `confidence_score` | FLOAT [0.0–1.0] | NER model calibrated confidence at extraction time |
| `confirmed` | BOOLEAN | True when user explicitly confirmed this value |
| `source_conversation_id` | UUID | References session token of source conversation (not user identity) |
| `source_turn_index` | INTEGER | Turn within source conversation |
| `extracted_at` | TIMESTAMPTZ | UTC extraction timestamp |
| `confirmed_at` | TIMESTAMPTZ NULL | UTC confirmation timestamp; NULL if unconfirmed |
| `version` | INTEGER | Monotonically increasing per `profile_id` + `field_key` |
| `superseded_by` | UUID NULL | ID of entry that supersedes this one; NULL = current |

> **Critical:** All queries on `user_health_profile_entries` MUST include `WHERE profile_id = :active_profile_id`. Application service role enforces this at query-builder level. Cross-profile reads are a P0 security violation.

**Field Catalogue (canonical `field_key` values for MVP):**

| `field_group` | `field_key` | Value type | Example |
|---|---|---|---|
| `DEMOGRAPHICS` | `age_years` | Integer | `45` |
| `DEMOGRAPHICS` | `biological_sex` | ENUM: `male`, `female`, `not_stated` | `"female"` |
| `DEMOGRAPHICS` | `height_cm` | Float | `162.5` |
| `DEMOGRAPHICS` | `weight_kg` | Float | `68.0` |
| `CONDITIONS` | `condition_name` | String (ICD-10 normalized) | `"hypertension"` |
| `MEDICATIONS` | `medication_name` | String (INN normalized) | `"metformin"` |
| `MEDICATIONS` | `medication_dose` | String | `"500mg twice daily"` |
| `LIFESTYLE` | `exercise_frequency_per_week` | Integer | `3` |
| `LIFESTYLE` | `smoking_status` | ENUM: `current`, `former`, `never` | `"never"` |
| `LIFESTYLE` | `alcohol_status` | ENUM: `none`, `occasional`, `regular` | `"occasional"` |
| `LIFESTYLE` | `sleep_hours_avg` | Float | `6.5` |
| `LIFESTYLE` | `diet_type` | String (free text, normalized) | `"low-sodium"` |
| `BIOMARKER_PREFERENCES` | `personal_target` | Object `{biomarker, target_value, unit}` | `{biomarker: "systolic_bp", target_value: 130, unit: "mmHg"}` |
| `SYMPTOMS_CHRONIC` | `symptom_name` | String (MedDRA PT normalized) | `"morning headache"` |
| `SYMPTOMS_CHRONIC` | `symptom_frequency` | ENUM: `daily`, `weekly`, `occasional` | `"daily"` |

**Active value resolution rule:** for a given `profile_id` + `field_key`, the active value is the most recent entry (by `extracted_at`) where `(confirmed = true) OR (confidence_score ≥ 0.85)`. Entries with `confirmed = false AND confidence_score < 0.85` are provisional. Entries with `confidence_score < 0.60` are not in this table (staged separately).

**Append-only constraint:** no `UPDATE` or `DELETE` on entry rows. Logical supersession recorded by setting `superseded_by` on the prior entry within a single transaction.

*Verification:* Schema migration reviewed by Technical Advisor; unit tests confirming append-only constraint; active value resolution for all 4 confidence/confirmation state combinations; cross-profile read rejection test (query with wrong `profile_id` returns empty result, not the other profile's data); automated schema validation in CI pipeline.

---

**AC 1.2 — NER Pipeline (Entity Extraction Rules)**

The NER pipeline runs **in parallel with Tier 1 RAG retrieval** on every user message. Executes after the 2-point PII scrubber (Component 1 AC 4.10). NER operates on scrubbed text only.

**Entity types and profile field group mapping:**

| Entity type | `field_group` target | Extraction examples |
|---|---|---|
| `CONDITION` | `CONDITIONS` | "Tôi bị tiểu đường type 2", "diagnosed with hypertension 3 years ago" |
| `MEDICATION` | `MEDICATIONS` | "Tôi đang uống Metformin 500mg", "I'm on amlodipine" |
| `DEMOGRAPHIC` | `DEMOGRAPHICS` | "Tôi 45 tuổi", "I'm a woman", "I weigh 68 kilos" |
| `LIFESTYLE_FACTOR` | `LIFESTYLE` | "Tôi chạy 3 lần một tuần", "I sleep about 6 hours" |
| `SYMPTOM_CHRONIC` | `SYMPTOMS_CHRONIC` | "Tôi hay đau đầu buổi sáng", "I feel tired most days" |
| `BIOMARKER_PREFERENCE` | `BIOMARKER_PREFERENCES` | "Tôi muốn giữ huyết áp dưới 130" |
| `TEMPORAL_CONTEXT` | metadata only | "từ năm ngoái", "for 5 years" — enriches other entities, not stored independently |

**Entity attribution rule:** extracted entities are always attributed to `active_profile_id` from the session token — never inferred from linguistic subject ("mẹ tôi", "my son"). NER does not attempt to identify who is being discussed from message content.

**Normalization rules:**
- Condition names: normalized to ICD-10 preferred term ("cao huyết áp" → `"hypertension"`); normalization dictionary version-controlled; Medical Affairs reviewed before initial deployment and on every update
- Medication names: normalized to INN with brand name retained as alias ("Glucophage" → normalized: `"metformin"`, alias: `"Glucophage"`)
- Demographic values: SI units (kg, cm, years)
- Symptom names: MedDRA Preferred Term where mapping exists; free text retained alongside normalized term

**Extraction exclusions:**
- Values already present in Elfie's structured data stores (vitals, medication log, lab results, **digitized health examination data from the Medical Record Scanning feature**) are NOT extracted by NER — fetched directly via Tier 1 RAG pipeline
- NER runs on user messages only; never on AI-generated turns

**Model requirements:**
- GLiNER or SpaCy NER, hosted on Elfie NER inference service; NOT the primary LLM
- Must support Vietnamese and English
- Model version pinned at deployment; any update requires re-validation and recalibration (AC 3.2)

**Vietnam v1 launch — English-only NER fallback (RESOLVED — OQ-1):**
- MVP Vietnam launch proceeds with English-only NER; profiling available in English only for Vietnamese-market users at v1 launch
- Vietnamese NER is a **v1.1 gate**: F1 ≥ 0.85 per entity type in Vietnamese is required before Vietnamese-language profiling is enabled
- Profile store and all downstream components are language-agnostic; only the NER model scope changes between v1 and v1.1
- UI indicator shown to Vietnamese users whose messages are processed in English: *"Tính năng cá nhân hóa hiện hỗ trợ tiếng Anh. Hỗ trợ tiếng Việt sẽ sớm ra mắt."*

*Verification:* NER test suite ≥ 200 labeled messages (English only for MVP launch gate; Vietnamese ≥ 20 per entity type per language added as v1.1 gate); F1 ≥ 0.85 per entity type in English before MVP deployment; normalization dictionary coverage test (≥ 50 common condition aliases); regression test confirming NER does not run on AI-generated turns; latency ≤ 150ms P95 on 200-token messages at 500 req/min.

---

**AC 1.3 — Profile Gap Analyzer**

Rule-based component (no LLM, no ML). Runs after NER extraction and before Context Assembler. Compares current query intent against active profile state to produce an ordered list of the most relevant missing fields.

**Intent → Required Profile Fields mapping (version-controlled; Medical Affairs reviewed):**

| Intent category | Required fields for full personalization |
|---|---|
| `blood_pressure_query` | `age_years`, `conditions`, `medications`, `lifestyle.smoking_status` |
| `glucose_query` | `conditions`, `medications`, `weight_kg`, `biological_sex` |
| `medication_adherence_query` | `medications`, `conditions` |
| `weight_goal_query` | `weight_kg`, `height_cm`, `age_years`, `biological_sex` |
| `sleep_query` | `lifestyle.sleep_hours_avg`, `conditions`, `lifestyle.exercise_frequency_per_week` |
| `exercise_query` | `lifestyle.exercise_frequency_per_week`, `age_years`, `conditions` |
| `general_trend_query` | `age_years`, `biological_sex`, `conditions` |
| `lab_result_query` | `conditions`, `medications`, `age_years`, `biological_sex` |
| `symptom_interpretation_query` | `conditions`, `medications`, `symptoms_chronic` |

**Gap priority ranking:** fields absent outrank fields with low-confidence provisional entries; fields most directly linked to the query's primary entity outrank peripheral fields.

**Output:** ordered list of ≤ 2 gap fields passed to Context Assembler. 0 gaps → empty list (no embedded questions).

*Verification:* Unit tests covering all 9 intent categories × 4 profile states (empty, partial, full, provisional-only); output list length ≤ 2 at all times; performance ≤ 20ms P95.

---

**AC 1.4 — Embedded Follow-Up Question Rules**

The Reasoning Engine (LLM) is instructed via system prompt to embed follow-up questions for gap fields identified by the Gap Analyzer. Hard rules are enforced by post-generation automated validation before safety classifier input.

**Hard rules:**

1. **Maximum 2 questions per response.** 0 gaps → 0 questions; 1 gap → ≤ 1 question; 2 gaps → ≤ 2 questions.
2. **Never re-ask known data.** If a field has any active profile entry (confidence ≥ 0.40 or confirmed): that field must not be questioned.
3. **No questions in escalation responses.** When a hard escalation trigger fires (Component 1 AC 2.2), no follow-up questions appear.
4. **No questions in safety-blocked responses.** If Stage 1 or Stage 2 rewrites the response, the rewritten response contains no embedded questions.
5. **All questions pass the 2-stage safety classifier.** Classifier treats embedded questions identically to any other response text.
6. **Maximum 1 question if response body > 200 words.**
7. **Questions must be conversational, not clinical-form-style.** Prohibited: "Please state your…", "Enter your…", "What is your [field name]?".
8. **Questions must not solicit acute or diagnostic information.** Questions may ask about chronic conditions but must not ask users to interpret current symptoms suggestive of emergencies, or to self-diagnose.

**Phrasing guidance in system prompt (examples):**

| Gap field | Acceptable embedded phrasing |
|---|---|
| `age_years` | "Bạn khoảng bao nhiêu tuổi? Điều đó giúp mình đưa ra bối cảnh phù hợp hơn." |
| `conditions` | "Bạn có mắc bệnh nào như tiểu đường hay cao huyết áp không?" |
| `medications` | "Bạn hiện đang dùng thuốc gì cho vấn đề này không?" |
| `lifestyle.sleep_hours_avg` | "Bạn thường ngủ khoảng mấy tiếng? Đó có thể là một yếu tố liên quan." |

**Post-generation validation (runs before safety classifier input):**
- Question count check: > 2 → strip excess
- Re-ask check: question targets field with active entry (confidence ≥ 0.40) → strip
- Prohibited phrasing check: pattern match → strip
- Escalation context check: if escalation flag set → strip all questions
- Acute symptom pattern check: "Are you currently feeling…", "Do you have chest pain…" → strip

*Verification:* Post-generation validation unit tests for all rule scenarios; adversarial test suite ≥ 50 cases; end-to-end conversation test ≥ 20 conversations.

---

**AC 1.5 — Low-Confidence Extraction Confirmation Flow**

Extractions with `confidence_score < 0.60` written to staging table `pending_profile_extractions`, NOT to `user_health_profile_entries` until confirmed.

**Staging table schema:**

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | Staging entry identifier |
| `account_id` | UUID FK | Account owner |
| `profile_id` | UUID FK | Target profile (Family Care safe) |
| `field_group` | ENUM | Same as profile store |
| `field_key` | VARCHAR(64) | Same as profile store |
| `field_value` | JSONB | Extracted value |
| `confidence_score` | FLOAT | NER confidence at extraction |
| `source_conversation_id` | UUID | Source session token |
| `extracted_at` | TIMESTAMPTZ | UTC extraction time |
| `expires_at` | TIMESTAMPTZ | `extracted_at + 30 days` |
| `confirmation_prompt_sent` | BOOLEAN | Whether prompt has been issued |
| `conflict_flag` | BOOLEAN | True if conflicts with an existing active entry |

**Flow rules:**
1. In the **next session** (different conversation), if pending extractions are relevant to current query intent, a single confirmation prompt may be embedded: *"Lần trước bạn có nhắc đến [giá trị] — mình hiểu đúng không?"*
2. **Maximum 1 confirmation prompt per session** regardless of pending count.
3. **User confirms:** staged entry moves to `user_health_profile_entries` with `confirmed = true`, `confidence_score = 0.90`.
4. **User denies:** staging entry deleted; audit record written.
5. **Expiry:** daily cleanup job hard-deletes entries where `NOW() > expires_at`; audit log event written.
6. Confirmation prompts subject to the same 2-stage safety classifier as all other AI responses.

*Verification:* Integration test for confirm path, deny path, expiry cleanup; confirmation prompt count per session ≤ 1 with 3 concurrent pending extractions; safety classifier invoked on confirmation prompt.

---

**AC 1.6 — Profile Usage Hedging Rules**

| Entry state | Representation in context | LLM instruction |
|---|---|---|
| `confirmed = true` OR `confidence_score ≥ 0.85` | Stated as fact: *"User has type 2 diabetes"* | Use directly in reasoning and personalization |
| `0.60 ≤ confidence_score < 0.85`, `confirmed = false` | Provisional: *"User mentioned having type 2 diabetes (unconfirmed)"* | Use with hedging: *"Based on what you've shared…"* |
| `confidence_score < 0.60` | Not included in context | Staged pending confirmation only |

System prompt permanent instruction: *"Profile data marked 'unconfirmed' represents what the user mentioned in conversation — treat it as self-reported context, not a verified medical record."*

*Verification:* Unit tests for Context Assembler confirming correct representation per all 3 states; adversarial test with provisional-only profile — assert LLM response uses hedged attribution.

---

**AC 1.7 — Profile Staleness**

| Condition | Effect |
|---|---|
| Entry age > 365 days (general fields) | Effective confidence reduced by 0.20 for context assembly |
| Entry age > 730 days (general fields) | `potentially_stale` flag in context: *"User mentioned [X] approximately [Y] ago — may have changed"* |
| `weight_kg`, `medication_*`, `lifestyle.*` entries > 180 days | `potentially_stale` flag applied |

Stored `confidence_score` is never mutated by staleness. Stale flags may trigger a new embedded question if the field is required for the current intent and staleness-adjusted effective confidence falls below the active threshold.

*Verification:* Unit tests for staleness calculation at 0, 90, 180, 181, 365, 366, 730 days; stored `confidence_score` not mutated (SELECT after staleness event returns original value).

---

**AC 1.8 — Profile-Building Gamification (Elfie Coins)**

Two profile milestone coin events are triggered by the Profile Store service and delivered to the Elfie coin event bus:

| Milestone | Trigger condition | Coin event type |
|---|---|---|
| First confirmation | First entry in `user_health_profile_entries` with `confirmed = true` for this `profile_id` | `PROFILE_FIRST_CONFIRMATION` |
| Primary condition completeness ≥ 50% | ≥ 50% of required fields for user's primary confirmed condition are active (per AC 1.1 active value resolution rule) | `PROFILE_COMPLETENESS_50` |

**Rules:**
- Each milestone event fires **at most once** per `profile_id` (idempotent; re-confirmed entries or re-completions do not re-fire)
- Coin amounts are configured in the Elfie gamification system, not in Component 4 code; Component 4 only emits the event type and `profile_id`
- Coin events are never emitted for managed profiles (Family Care) in MVP (profiling disabled for managed profiles per AC 2.2)
- If coin event bus is unavailable: milestone event is logged and retried with exponential backoff (max 3 retries, 24h window); failure does not block profile write operations
- Coin events do NOT carry health data; the event payload contains only: `{event_type, profile_id (hashed), triggered_at}`

**Primary condition determination for 50% completeness:**
The condition with the highest number of associated required fields in the Gap Analyzer intent map (AC 1.3) that is confirmed in the user's profile. If no condition is confirmed: milestone does not apply until first condition is confirmed.

*Verification:* Unit test confirming `PROFILE_FIRST_CONFIRMATION` fires on first `confirmed = true` entry and does not re-fire on subsequent confirmations; unit test for `PROFILE_COMPLETENESS_50` at 49% and 51% completeness; idempotency test (coin event bus receives exactly 1 event per milestone per profile across 10 confirm operations); coin event payload PII scan (zero health data in payload); retry test (bus unavailable → retry logged → profile write succeeds independently).

---

### Section 2 — Family Care Profile Isolation

---

**AC 2.1 — Profile-Level Data Isolation (Family Care)**

Elfie Family Care allows one account (`account_id`) to manage multiple profiles (`profile_id`) — self, children, elderly parents, partner. All profile data in Component 4 is isolated strictly by `profile_id`, not `account_id`.

**Isolation architecture — 4 layers:**

**Layer 1 — Database:**
- All queries on `user_health_profile_entries` and `pending_profile_extractions` MUST include `WHERE profile_id = :active_profile_id`
- Application service role enforces this at query-builder level; cross-profile joins are architecturally prohibited
- Database permission test must confirm that a query without `profile_id` filter on these tables returns 0 rows or raises an application-level exception

**Layer 2 — Session token:**
- `active_profile_id` is bound to the session token at conversation start; it is immutable for the duration of the conversation
- Session token schema addition:

```json
{
  "session_token": "<cryptographically random UUID>",
  "account_id_hash": "<HMAC of account_id>",
  "profile_id": "<UUID of selected profile>",
  "profile_locked": true,
  "expires_at": "<UTC timestamp>"
}
```

- `profile_locked: true` means `profile_id` cannot be modified after session creation; any attempt to modify it server-side results in session invalidation
- If user wants to ask about a different family member → must start a new conversation; the current conversation is closed

**Layer 3 — Entity extraction attribution:**
- All entities extracted by the NER pipeline are attributed to the `profile_id` from the session token
- NER does NOT attempt to infer subject from linguistic cues ("mẹ tôi", "my son", "for my father") — all entities go to the session's `active_profile_id`
- Rationale: subject detection from natural language is probabilistic and unreliable for health data; deterministic session-binding is required

**Layer 4 — Context Assembler:**
- Profile snapshot query: `WHERE profile_id = :active_profile_id`
- pgvector Tier 2 retrieval filtered by `metadata.profile_id = active_profile_id`
- Conversation buffer contains only turns from conversations where `profile_id = active_profile_id`
- No cross-profile data can appear in the assembled context regardless of account ownership

**Profile Selector UI rules:**
- Profile selector shown at AI Coach entry point when `account.profiles.count > 1`
- Selector displays profile names as set in Elfie app (e.g., "Bà Lan — Mẹ", "Minh — Con trai"); no health data shown in selector
- Default selection: the account's self-profile
- Managed profiles for under-18 users: AI Health Coach and profiling features disabled for those profiles per Component 1 AC 6.5 (under-18 restriction)

*Verification:* Cross-profile contamination test — create two profiles for same account with distinct health data; conduct conversations with each profile; assert zero data leakage between profile contexts; session mutation test — attempt to change `profile_id` mid-conversation via API; assert session invalidated; family selector UI test with ≥ 3 profiles; under-18 profile AI access denial test.

---

**AC 2.2 — Guardian Consent for Managed Profiles (MVP Restriction)**

Progressive profiling is enabled ONLY for the account holder's self-profile in MVP. Managed profiles (e.g., elderly parent, adult child) have profiling disabled until a dual-consent model is designed and legally reviewed (OQ-7).

**MVP enforcement:**
- Profiling consent gate (Section 4 AC 4.1) is presented only when `active_profile_id = account.self_profile_id`
- For managed profiles: NER pipeline is not invoked; profile store is not written; profile summary block is absent from context; profile selector shows a "Personalization not available for this profile" indicator

**Rationale:** PDPA Thailand and PDPD Vietnam have distinct rules for data processing on behalf of others (particularly adults managing care for elderly or disabled relatives). The consent model for this scenario requires separate legal review and a dual-consent flow design.

*Verification:* Test confirming NER not invoked when `active_profile_id ≠ account.self_profile_id`; test confirming profile store not written for managed profile; test confirming "Personalization not available" indicator shown in selector for managed profiles.

---

### Section 3 — RAG Enhancement

---

**AC 3.1 — Profile-Aware Query Expansion**

Before pgvector Tier 2 retrieval, the query is enriched with active profile context using a versioned expansion map (not an LLM call):

- Active confirmed conditions → condition synonyms and related biomarker keywords
- Active confirmed medications → drug class name and primary monitoring parameters
- Maximum expansion: original query tokens + ≤ 50 profile-derived expansion tokens
- Expansion terms must not introduce diagnostic language
- Tier 1 retrieval (direct DB fetch) is not affected

*Verification:* Unit tests for expansion map coverage (≥ 10 condition types, ≥ 5 drug classes); no diagnostic language in any expansion term; expansion capped at 50 tokens; latency ≤ 10ms P95.

---

**AC 3.2 — Profile-Aware Reranking**

After pgvector cosine similarity retrieval of top-10 candidates (threshold ≥ 0.75), chunks are re-ranked before top-5 passed to Context Assembler.

**Reranking formula:**

```
final_score = (0.7 × cosine_similarity) + (0.3 × profile_relevance_score)
```

**Profile relevance score:**
- `1.0` — chunk contains a term matching an active condition or medication name from the profile
- `0.5` — chunk contains a term matching the condition's parent category
- `0.0` — no profile term match

When user has no active profile: reranking degenerates to pure cosine similarity. Behavior is identical to Component 1 baseline.

*Verification:* Unit test confirming formula applied correctly; profile-conditioned chunk ranks above equally-similar non-profile chunk; empty-profile behavior identical to Component 1; no LLM call in reranking path.

---

**AC 3.3 — Context Assembly with Profile Injection**

Context Assembler produces the final LLM prompt in this fixed order:

1. **System prompt block** (static, version-controlled; Medical Affairs + Legal reviewed)
2. **Profile summary block** (≤ 200 tokens): active profile fields per AC 1.6 hedging rules; ordered by relevance to current intent; generated without LLM call
3. **Tier 1 data block**: last 7 days of structured health data (unchanged from Component 1 AC 1.2)
4. **Retrieved documents block**: top-5 re-ranked chunks from Tier 2 retrieval
5. **Conversation buffer block**: last N turns
6. **Current user message**

**Truncation priority (if context window limit approached):** conversation buffer (first) → retrieved documents (trim from bottom) → profile summary (never below 100 tokens if non-empty). Tier 1 data block never truncated.

**Empty profile:** profile summary block omitted entirely; no placeholder text.

*Verification:* Profile summary ≤ 200 tokens for fully-populated profile; truncation priority test; empty-profile test (no placeholder); profile summary generation does not invoke LLM; assembly latency ≤ 15ms P95.

---

**AC 3.4 — Retrieval Quality Regression Gate**

Before feature flag is enabled:

**Gate 1 — Empty-profile regression:** NDCG@5 on held-out evaluation set must be ≥ Component 1 baseline NDCG@5 − 0.02.

**Gate 2 — Profile-aware lift:** curated evaluation set of ≥ 50 queries with populated test profiles; profile-aware NDCG@5 must exceed baseline by ≥ 5 percentage points.

*Verification:* Retrieval evaluation script run in staging; Gate 1 and Gate 2 results in a signed report reviewed by Technical Advisor.

---

### Section 4 — Data Quality & Profile Integrity

---

**AC 4.1 — Append-Only Versioning Enforcement**

- Application service role: INSERT and SELECT only; no UPDATE or DELETE
- `superseded_by` is updated only within a single atomic transaction alongside the INSERT of the new version
- Logical deletion is an INSERT of `{deleted: true}` with `version` incremented; prior entry's `superseded_by` set in the same transaction
- Physical deletion occurs only via the full deletion pipeline (AC 5.4)

*Verification:* Database permission audit; transaction atomicity test; version chain integrity test after 5 sequential updates to same field.

---

**AC 4.2 — Confidence Score Calibration**

- Temperature scaling calibration on held-out validation set of ≥ 500 labeled extractions per language
- Post-calibration Expected Calibration Error (ECE) ≤ 0.05 per language
- Re-run after any NER model weight update; calibration parameters version-controlled alongside model version
- Uncalibrated scores must never be stored

*Verification:* Calibration report (ECE ≤ 0.05) required as deployment gate; automated ECE check in CI; Technical Advisor sign-off on calibration report before any NER model update ships.

---

**AC 4.3 — Conflict Resolution**

| Conflict scenario | Handling |
|---|---|
| New extraction, `confidence_score ≥ 0.85`, different value | INSERT new version, supersede prior immediately |
| New extraction, `0.60 ≤ confidence_score < 0.85`, different value | Stage as pending with `conflict_flag = true`; confirmation prompt in next session |
| New extraction, `confidence_score < 0.60`, different value | Discard silently; audit log event |
| New condition / medication (no prior entry) | Auto-add; no conflict flow |
| User-explicit correction ("Thực ra tôi 45 tuổi") | `correction_intent` detected; INSERT with `confirmed = true`, `confidence_score = 0.95`; supersede prior immediately; bypass staging |

*Verification:* Unit tests for all 5 conflict scenarios; correction-intent detection test ≥ 10 Vietnamese + English correction phrasing variants.

---

**AC 4.4 — Profile Data Must Not Be Used for Diagnosis**

System prompt permanent instruction (Medical Affairs + Legal sign-off required for any change):

> *"The User Health Profile contains self-reported context the user has mentioned in conversation. It is NOT a verified medical record, clinical assessment, or diagnostic tool. You must NEVER use profile data to diagnose, suggest a diagnosis, or infer a clinical condition the user has not already explicitly stated. Profile data exists solely to help you give more relevant, personalized explanations of the user's own health data."*

All condition references in responses must use attribution phrasing: *"Vì bạn có đề cập rằng bạn bị [bệnh]…"* — not *"Vì bạn bị [bệnh]…"* (which implies clinical determination by the AI).

*Verification:* Adversarial test suite ≥ 30 cases; zero diagnostic outputs permitted; attribution phrasing test ≥ 20 profile-personalized responses; run in regression suite before every production deployment.

---

### Section 5 — Privacy & Consent

---

**AC 5.1 — Combined Consent Modal with Dual Checkboxes (RESOLVED — OQ-4)**

Progressive profiling consent is collected in a **combined consent modal** alongside AI Health Coach consent (Component 1 AC 6.1). The modal contains two separate, independently ticked checkboxes:

- **Checkbox A** (required to use AI Health Coach): AI Health Coach data use consent
- **Checkbox B** (optional, independent): Progressive Profiling consent — *"Cho phép Elfie AI xây dựng hồ sơ sức khỏe cá nhân hóa từ các cuộc trò chuyện của chúng ta để đưa ra câu trả lời tốt hơn theo thời gian"*

Checkbox B is **unchecked by default**. User must actively opt in. Accepting Checkbox A without Checkbox B is valid — AI Health Coach functions normally without profiling.

**Required information displayed alongside Checkbox B:**
1. That the AI builds a health profile from conversation over time
2. What data types are collected: conditions, medications, demographics, lifestyle factors, biomarker preferences, chronic symptoms
3. Profile data used **only** to personalize AI explanations — not for diagnosis, not shared with ElfieCare, not shared with third parties, not used by insurers
4. Where to view and delete: Settings → Privacy → AI Health Profile
5. That profiling applies only to the self-profile; managed profiles (Family Care) are not profiled in this version

**Consent records stored separately:**

| Record | Stored with |
|---|---|
| AI Health Coach consent (Checkbox A) | user ID, consent version, timestamp, consent text hash — owned by Component 1 |
| Progressive Profiling consent (Checkbox B) | user ID, consent version, timestamp, consent text hash — owned by Component 4 |

**Declining Checkbox B:** AI Health Coach functions normally. NER pipeline not invoked. Profile store remains empty. Coin milestone events not emitted.

**Re-consent required when:** a new `field_group` is added to the Field Catalogue, profile data is used for any new purpose, or a new data recipient is introduced.

*Verification:* UX test confirming combined modal presents both checkboxes; Checkbox B unchecked by default; two independent consent records created after form submission; AI Health Coach functional when only Checkbox A ticked; NER disabled when Checkbox B not ticked; re-consent trigger test; Legal + Medical Affairs sign-off on combined modal copy before mobile implementation.

---

**AC 5.2 — Consent Inheritance from AI Health Coach (Component 1)**

All applicable privacy requirements from Component 1 are inherited without modification:

| Component 1 AC | Inheritance rule for Component 4 |
|---|---|
| AC 4.1 — HIPAA BAA | Profile store processes PHI; BAA scope must explicitly cover profile store before any user data is written |
| AC 4.10 — PII scrubber | NER pipeline runs after PII scrubber; extracted entities derived from scrubbed text only |
| AC 4.2 — Session token anonymization | `source_conversation_id` stores session token, not user identity |
| AC 4.3 — Encryption at rest | `user_health_profile_entries` and `pending_profile_extractions`: AES-256 at rest |
| AC 4.4 — Audit trail | Profile write events (field group, field key, confidence score, confirmed boolean, session token) added to audit log; raw extracted text NOT stored |
| AC 6.5 — Under-18 restriction | Profile building disabled for under-18 profiles; NER pipeline not invoked |

*Verification:* Code review confirming NER executes after PII scrubber; profile entries store session token not user ID; encryption configuration audit; under-18 profile NER-disabled test.

---

**AC 5.3 — User Visibility into Collected Profile**

Settings → Privacy → AI Health Profile provides 7 functions:

1. **Profile field view:** all stored fields grouped by `field_group`; each field shows active value, a confidence indicator (`High` = confirmed or confidence ≥ 0.85; `Provisional` = 0.60–0.84 unconfirmed; `Unconfirmed` = pending staging), and date last updated
2. **Primary condition completeness progress bar:** percentage of required fields (per AC 1.3 intent map) that are active for the user's primary confirmed condition; shown as a labeled progress bar (e.g., "Hypertension profile: 60% complete"); primary condition determined automatically per AC 1.8 rule
3. **Individual field correction:** user may edit any field value; applied as `confirmed = true`, `confidence_score = 0.95`, prior entry superseded
4. **Individual field deletion:** append-only tombstone; deleted fields excluded from context immediately
5. **Full profile deletion:** triggers deletion pipeline (AC 5.4); confirmation dialog required
6. **JSON export:** structured JSON via secure download link (48h expiry); processed within 24 hours
7. **Pending extractions view:** staged pending extractions with field name, extracted value, expiry date; user may confirm or dismiss directly

*Verification:* UX test for all 7 features; progress bar accuracy test (assert % matches active field count / required field count for primary condition); individual field deletion integration test; correction supersedes prior entry; JSON export format; pending extractions round-trip test.

---

**AC 5.4 — Profile Deletion Pipeline**

| Store | Action | SLA |
|---|---|---|
| `user_health_profile_entries` (PostgreSQL) | Soft-delete → hard-delete | Hard-delete within 72 hours |
| `pending_profile_extractions` (PostgreSQL) | Hard-delete | Within 72 hours |
| Redis (cached profile summaries) | Purged | Within 1 hour |
| Audit log linkage | `field_value` and `field_key` tombstoned; entry record retained | Within 72 hours |

Profile deletion does NOT delete AI Health Coach conversation history (separate stores, separate pipelines).

**User-facing copy (legal-reviewed):**
> *"Hồ sơ sức khỏe AI của bạn đã được xóa khỏi Elfie. Lịch sử trò chuyện AI Coach của bạn là riêng biệt và chưa bị xóa. Để quản lý lịch sử trò chuyện, hãy vào Cài đặt → Quyền riêng tư → Dữ liệu AI Coach."*

*Verification:* Integration test confirming each store clears within SLA; tombstone verification; SLA breach alert test.

---

**AC 5.5 — PDPA (Thailand) and PDPD (Vietnam) Compliance**

**Thailand PDPA B.E. 2562:**
- Explicit consent for sensitive personal data: satisfied by AC 5.1 profiling consent gate
- Data subject right of access: satisfied by AC 5.3 profile field view
- Right to erasure: satisfied by AC 5.4 72-hour pipeline
- Right to data portability: satisfied by AC 5.3 JSON export
- **DPO registration:** profiling activity must be added to Elfie's ROPA before any Thai user data is processed. Failure to update ROPA before launch is a launch-blocking compliance gap.

**Vietnam PDPD (Decree 13/2023):**
- Explicit consent: satisfied by AC 5.1
- **Data localization:** pending legal determination (see OQ-3); if in-country processing required, Vietnam launch is blocked until compliant infrastructure confirmed in writing by Legal
- Right to deletion: AC 5.4 72-hour pipeline
- Data breach notification: within 72 hours to MIST; Legal must confirm AI Health Profile is explicitly included in Elfie's existing breach response procedure before VN launch

*Verification:* Legal sign-off on PDPA Thailand DPO ROPA update before TH launch gate; legal sign-off on PDPD Vietnam compliance position documented and data localization resolved before VN launch gate.

---

**AC 5.6 — No Profile Data Shared with ElfieCare (MVP)**

Hard isolation:
- `user_health_profile_entries` and `pending_profile_extractions`: ElfieCare service role has zero permissions
- Tables not included in any ElfieCare patient data API contract
- No API endpoint exposes profile data to any external consumer in MVP

Any future sharing requires: (a) separate dual-consent flow, (b) new spec amendment, (c) new DPIA.

*Verification:* Database permission test (ElfieCare service role → permission denied on profile tables); API contract review; integration test confirming Component 3 data collector produces identical output regardless of profile store state.

---

### Section 6 — Integration with AI Health Coach (Component 1)

---

**AC 6.1 — Non-Breaking Integration with Component 1**

All Component 1 acceptance criteria must remain fully satisfied after this component is deployed:

| Component 1 AC | Regression check |
|---|---|
| AC 1.2 — Tiered context retrieval | Profile injection does not modify Tier 1/2/3 activation rules |
| AC 2.1 — 2-Stage Safety Classifier | Safety layer operates on complete buffered response including embedded questions; P95 ≤ 400ms maintained |
| AC 2.2 — Hard escalation triggers | Escalation evaluation unchanged; embedded questions suppressed when escalation fires |
| AC 2.3 — Diagnostic language prohibition | Profile-personalized responses must still pass diagnostic language prohibition test |
| AC 4.9 — No PII in LLM API payload | Profile summary block must pass PII scan |
| AC 5.1 — End-to-end latency | P50 ≤ 2,000ms, P95 ≤ 4,000ms maintained with full profile path |

*Verification:* Full Component 1 regression test suite run against updated pipeline before production deployment.

---

**AC 6.2 — Shared NER Pipeline with Component 3**

The NER inference service deployed for this component is shared with Component 3 (Pre-Visit Agent):

- Single versioned NER model; any update requires re-validation for both Component 3 and Component 4
- Service SLA: ≥ 99.9% availability
- Capacity sized for combined peak load (OQ-5 must be resolved before infrastructure provisioned)

**Graceful degradation:**
- NER timeout (> 150ms) or error: skip extraction; conversation continues without profile update or profile context injection; no user-facing error
- Profile retrieval failure: Context Assembler proceeds without profile block; silent degradation

*Verification:* Graceful degradation integration test (NER timeout → response delivered within P95 budget); load test for combined Component 3 + Component 4 volume at ≥ 99.9% uptime.

---

**AC 6.3 — End-to-End Latency Budget with Profile Path**

| Component | P95 target | Execution model |
|---|---|---|
| NER extraction (200-token message) | ≤ 150ms | Parallel with Tier 1 RAG retrieval |
| Profile retrieval from PostgreSQL | ≤ 30ms | Sequential after NER |
| Profile Gap Analyzer | ≤ 20ms | Sequential after profile retrieval |
| Query expansion (AC 3.1) | ≤ 10ms | Before Tier 2 RAG |
| Profile-aware reranking (AC 3.2) | ≤ 30ms | After Tier 2 retrieval |
| Profile summary generation + context injection | ≤ 15ms | After reranking, before LLM call |
| Post-generation question validation | ≤ 20ms | After LLM generation, before safety classifier |

Sequential overhead contributed by Component 4: ≤ 85ms P95. NER (≤ 150ms) runs in parallel with Tier 1 retrieval; not on critical latency path.

*Verification:* Isolated performance test per component; end-to-end load test (1,000 concurrent requests, 5 minutes); P50 ≤ 2,000ms and P95 ≤ 4,000ms; results reviewed by Technical Advisor before feature flag enabled.

---

### Section 7 — Technology Roadmap: AgenticRAG + GraphRAG (v2 / v3)

This section documents the planned architecture evolution for v2 and v3. It does not contain MVP acceptance criteria. All items in this section are **explicitly out of MVP scope**.

---

#### v2 — AgenticRAG (Agentic Multi-Hop Retrieval)

**Problem MVP solves poorly:** complex queries requiring data from multiple sources simultaneously (e.g., "Does the medication I'm taking affect my HbA1c result from yesterday?"). Single-pass vector RAG returns one set of chunks; it cannot orchestrate retrieval across structured DB + vector store + knowledge base in a reasoned sequence.

**v2 addition: LangGraph Agentic Orchestrator — complex queries only**

AgenticRAG does NOT replace single-pass retrieval for all queries. The Intent Classifier (Component 1) is extended in v2 to output a `query_complexity` flag: `simple` or `complex`. Only queries classified as `complex` are routed to the Agentic Orchestrator; all other queries continue through the existing single-pass pipeline unchanged. This preserves low latency for the majority of user queries.

**Complex query classification criteria:**

| Criterion | Example |
|---|---|
| References ≥ 2 distinct data source types | "Does my Metformin affect my HbA1c from yesterday?" (medication + lab) |
| Requires temporal comparison across > 1 time window | "Compare my sleep this month vs 3 months ago" |
| Involves drug–condition interaction reasoning | "Can my blood pressure medication be causing my ankle swelling?" |
| Multi-entity causal framing | "Why does my BP spike after I eat but not when I exercise?" |
| Explicit "why", "how does X affect Y", "compare X and Y" with multiple entities | "How does my weight trend relate to my glucose levels?" |

**Routing logic:**
```
Intent Classifier output
    ├── query_complexity = "simple" → single-pass pipeline (unchanged from MVP)
    └── query_complexity = "complex" → Agentic Orchestrator (LangGraph)
```

**Agentic Orchestrator — LangGraph state machine (complex queries only):**
```
[Agentic Orchestrator — LangGraph state machine]
     │
     ├── Iteration 1: Vector RAG on primary query intent
     │                + Structured DB query for user's primary data values
     ├── Iteration 2: Graph traversal from user's profile nodes (v3 only)
     │                or additional vector RAG on secondary topic
     └── Iteration 3: Vector RAG on tertiary supporting context
                      + Agentic Reflector: "Sufficient context to answer?"
                      → Yes: proceed to Context Assembler
                      → No and iterations < 3: continue
                      → No and iterations = 3: proceed with available context
```

**Latency management:** 3-iteration hard cap. Each iteration adds ~200–500ms. P95 latency for complex queries in v2 expected ~3,000–4,000ms. Simple queries retain MVP P95 (≤ 4,000ms end-to-end).

**Rate limiting for complex queries (RESOLVED):** Complex queries count as 1 message against the 10 messages/day rate limit, identical to simple queries. The rate limit is a user-fairness control, not a cost control; higher LLM cost for complex queries is an infrastructure concern managed separately. This decision is noted here for v2 planning.

**v2 Technology additions:**

| Component | Technology |
|---|---|
| Agentic Orchestrator | LangGraph (already chosen for MVP orchestration) |
| Agentic Reflector | Lightweight classifier or rule-based sufficiency check; not full LLM call |
| `query_complexity` classifier | Extension of Intent Classifier (Component 1); rule-based or fine-tuned on labeled complex/simple query pairs |
| Profile-aware routing | Gap Analyzer output routes to most relevant retrieval type per iteration |

---

#### v3 — GraphRAG (Medical Knowledge Graph)

**Problem v2 solves poorly:** even multi-hop retrieval cannot traverse the relational structure of medical knowledge. It cannot answer "Given that I take Amlodipine every evening, and I have hypertension, and I sleep 5 hours, which of these is most likely causing my morning BP spike?" through causal graph traversal — it can only retrieve relevant text chunks.

**v3 addition: Medical Knowledge Graph**

A property graph database (Neo4j or Apache AGE as PostgreSQL extension) containing:

**Node types:**
- `Condition` (ICD-10 coded)
- `Medication` (INN coded)
- `DrugClass`
- `Symptom` (MedDRA coded)
- `Biomarker`
- `LifestyleFactor`
- `ClinicalGuideline`

**Edge types:**

| Edge | Example |
|---|---|
| `TREATED_BY` | Hypertension → TREATED_BY → Amlodipine |
| `CAUSED_BY` | Morning BP spike → CAUSED_BY → Sleep < 6h |
| `CORRELATES_WITH` | Hypertension → CORRELATES_WITH → Cortisol peak pattern |
| `INTERACTS_WITH` | Amlodipine → INTERACTS_WITH → Simvastatin |
| `SIDE_EFFECT` | Amlodipine → SIDE_EFFECT → Ankle swelling |
| `OPTIMAL_TIMING` | Amlodipine → OPTIMAL_TIMING → Evening |
| `RISK_FACTOR_FOR` | Hypertension → RISK_FACTOR_FOR → Heart failure |
| `MONITORS` | HbA1c → MONITORS → Type 2 Diabetes |
| `REFERENCED_BY` | ClinicalGuideline → REFERENCED_BY → Condition |

**User Profile Subgraph overlay:**

Profile Store entries are synced as a per-user subgraph overlaid onto the Medical Knowledge Graph at query time:

```
[Profile: P001 — Nam, 45t]
    ├── HAS_CONDITION → [Condition: Hypertension]
    ├── TAKES → [Medication: Amlodipine 5mg]
    ├── LIFESTYLE_FACT → [Sleep: 5h avg]
    └── BIOMARKER_TREND → [Systolic BP: trending high AM]
```

**Multi-hop causal reasoning example:**

```
Query: "Tại sao huyết áp tôi cao buổi sáng?"

Graph traversal (P001):
  P001.HAS_CONDITION → Hypertension
  Hypertension.CORRELATES_WITH → Morning BP spike
  Morning BP spike.CAUSED_BY → Sleep < 6h     ✓ (P001 sleep = 5h)
  Morning BP spike.CAUSED_BY → Cortisol peak  ✓ (natural, always present)
  P001.TAKES → Amlodipine.OPTIMAL_TIMING → Evening  ✓ (medication timing is correct — not a cause)

Conclusion: sleep deprivation + cortisol surge; medication timing is already optimal
Evidence base: causal path traversed from user's actual profile
```

Vector search alone would retrieve articles about morning hypertension — it cannot traverse this reasoning chain and eliminate medication timing as a cause.

**v3 Technology additions:**

| Component | Technology | Notes |
|---|---|---|
| Graph Store | Neo4j or Apache AGE (PostgreSQL extension) | AGE preferred if staying PostgreSQL-only; Neo4j if graph query performance is critical |
| Medical Knowledge Graph seeding | Elfie 1,000+ articles + SNOMED CT + DrugBank + WHO/ISH/ADA/ESC guidelines | One-time build; quarterly update pipeline |
| Graph → Profile overlay | Profile Store entries → user subgraph at query time | Sync on every profile update |
| Graph-aware Gap Analyzer | Gap fields ranked by causal path distance to query intent | Replaces rule-based intent map with graph traversal |

**v3 Graph-aware Gap Detection:**

The Gap Analyzer becomes graph-aware: gaps are prioritized not by static intent-field mapping, but by traversing the knowledge graph to find which missing profile fields appear most directly on the causal path of the current query.

```
Query intent: morning_hypertension
Graph causal path traversal finds: sleep_hours on direct CAUSED_BY edge
→ Gap priority for sleep_hours: CRITICAL (direct causal node)
→ Gap priority for exercise_frequency: MODERATE (indirect, 2 hops)
→ Embedded question: "Bạn thường ngủ khoảng mấy tiếng mỗi đêm?"
```

**v3 Trade-offs to evaluate before commitment:**

| Benefit | Cost |
|---|---|
| Dramatically better causal reasoning for complex queries | Neo4j / AGE infra overhead + medical ontology maintenance pipeline |
| Eliminates reasoning errors from missing relational context | Knowledge graph must be updated when clinical guidelines change |
| Graph-aware gap detection dramatically more precise | System complexity increases significantly |
| Causal chain can be surfaced to users ("Here's why…") | P95 latency increases ~200–400ms for graph traversal |

---

#### Migration Path

```
MVP (shipped)
  └── Component 4: ProactiveRAG + Vector RAG + Progressive Profiling

v2 (after PMF validation at MVP scale)
  └── + AgenticRAG: LangGraph multi-hop orchestrator
  └── + Agentic Reflector: sufficiency check

v3 (after v2 load profiling + medical ontology pipeline built)
  └── + GraphRAG: Neo4j / AGE Medical Knowledge Graph
  └── + Graph-aware Gap Analyzer
  └── + User-visible causal explanation ("Why this matters for you")
```

---

## Open Questions

| # | Question | Blocks | Owner |
|---|---|---|---|
| OQ-1 | **RESOLVED — Vietnamese NER fallback:** MVP Vietnam launch proceeds with English-only NER (profiling available in English only). Vietnamese NER is a v1.1 gate: F1 ≥ 0.85 per entity type in Vietnamese required before Vietnamese-language profiling is enabled. UI indicator shown to Vietnamese users. See AC 1.2. | AC 1.2 (Vietnamese NER = v1.1 gate) | Technical Advisor + Medical Affairs |
| OQ-2 | **ASSUMED RESOLVED — ICD-10 normalization dictionary:** Elfie's existing 400+ disease catalogue is assumed to contain a reusable ICD-10 normalization asset sufficient as a starting dictionary. Medical Affairs approval is assumed granted for initial deployment. **Supporting evidence:** the deployed Clinical Decision Support feature (ElfieCare) already uses curated condition terminology and medical rule sets — this knowledge base is assumed to overlap with or directly provide the ICD-10/MedDRA normalization mapping required here. If this assumption is incorrect at implementation time, NER model training is blocked and timeline extends by the dictionary build sprint. | AC 1.2 normalization requirement | Medical Affairs + Technical Advisor |
| OQ-3 | **ASSUMED RESOLVED — Vietnam data localization:** Assumed Legal determination is that PDPD Decree 13/2023 does not require in-country infrastructure for this profile store use case, and existing cross-border processing under explicit consent satisfies the regulation. Vietnam launch proceeds on current infrastructure. If Legal determines otherwise at VN launch gate, this assumption is invalidated and VN launch is blocked 4–8 weeks for infrastructure remediation. | AC 5.5 PDPD compliance; VN launch gate | Legal + Engineering |
| OQ-4 | **RESOLVED — Consent UX:** Combined consent modal with two independent checkboxes (Checkbox A = AI Health Coach, Checkbox B = Progressive Profiling). Checkbox B unchecked by default. Both consents stored as separate records for independent revocation. AC 5.1 updated accordingly. | AC 5.1 | Product (UX) + Legal |
| OQ-5 | **ASSUMED RESOLVED — NER service combined capacity:** Assumed the NER inference service is sized (or will be sized during D-3 infrastructure sprint) to handle combined Component 3 + Component 4 peak load at ≥ 99.9% SLA. Assumed Component 3 peak load profile is available to Engineering before the NER service provisioning sprint begins. If capacity is insufficient, graceful degradation (AC 6.2) prevents user-facing impact but profile extraction rate drops during peak. | AC 6.2 shared service SLA | Technical Advisor + Engineering |
| OQ-6 | **RESOLVED — Profile-building gamification:** Added to MVP scope. Two coin milestone events: (a) first profile field confirmed (`PROFILE_FIRST_CONFIRMATION`), (b) primary condition profile completeness ≥ 50% (`PROFILE_COMPLETENESS_50`). Each fires at most once per profile. See AC 1.8. | AC 1.8 | Product Owner |
| OQ-7 | **Family Care managed profile profiling — v2 planned:** MVP is self-profile only (AC 2.2). v2 will design a dual-consent model (account holder consent + managed profile holder explicit consent where legally required) after legal review of PDPA Thailand and PDPD Vietnam guardian consent rules. Legal review to begin after MVP launch. | v2 planning; legal review timeline | Product + Legal |
| OQ-8 | **v3 GraphRAG graph store selection:** Apache AGE (PostgreSQL extension) vs Neo4j — decision at start of v3 planning based on projected graph size and query latency requirements. AGE avoids new infra; Neo4j provides better graph query performance at scale. | v3 Technology Roadmap §7 | Technical Advisor + Engineering |
| OQ-9 | **AgenticRAG complexity classifier training data:** The `query_complexity` classifier (v2) requires a labeled dataset of complex vs simple queries. Does Elfie have sufficient query logs from AI Health Coach MVP to build this training set, or must synthetic data be used? Minimum labeled dataset size and annotation process to be defined at v2 planning kickoff. | v2 AgenticRAG; Intent Classifier extension | Technical Advisor + Engineering |

---

## Dependencies

| # | Dependency | Required state | Notes |
|---|---|---|---|
| D-1 | **AI Health Coach (Component 1) — deployed** | In production or staging-complete | Component 4 is an enhancement layer; full Component 1 pipeline must be operational |
| D-2 | **HIPAA BAA with LLM provider (inherited from Component 1)** | BAA scope confirmed to cover profile store | Legal must confirm existing BAA scope explicitly includes profile store processing |
| D-3 | **Elfie NER Inference Service** | New infrastructure — must be built | Shared with Component 3; requires dedicated ML Engineering sprint; model selection, Vietnamese + English corpus training, calibration, deployment |
| D-4 | **ICD-10 + MedDRA normalization dictionaries** | Medical Affairs reviewed and approved | OQ-2 must be resolved; initial dictionary scope approved before NER model training begins |
| D-5 | **NER model validation** | F1 ≥ 0.85 per entity type; ECE ≤ 0.05 calibration | Blocking gate; no profile writing to production for real users until both thresholds met per language |
| D-6 | **Component 1 intent classifier output** | Operational | Gap Analyzer (AC 1.3) depends on intent classification output from Component 1 pipeline |
| D-7 | **PDPD Vietnam data localization legal determination (OQ-3)** | Written legal determination | Vietnam launch gate blocked until determination is in writing; no engineering workaround acceptable |
| D-8 | **PDPA Thailand DPO ROPA update** | Before any Thai user data is processed | Profiling activity must be registered in Elfie's ROPA before TH launch |
| D-9 | **Profiling consent copy — Medical Affairs + Legal review** | Sign-off before mobile implementation begins | Profiling consent modal copy (in Vietnamese + English) must be approved |
| D-10 | **Component 3 NER service load profile** | Load profile documented | NER inference service capacity must be sized for combined Component 3 + Component 4 peak load (OQ-5) |
| D-11 | **Elfie Family Care profile schema** | `profile_id` field accessible in session context | Required for AC 2.1 Family Care isolation; confirm profile_id is a stable, indexed foreign key in Elfie's profile store |
| D-12 | **Medical Record Scanning feature — structured data access** | Scanned health examination data queryable via Tier 1 RAG | Confirm schema compatibility between scanning feature output and Tier 1 structured retriever; scanned lab values and diagnoses should be retrievable with same `profile_id` scoping as other structured health data; if schema is incompatible, a mapping layer is required before Component 4 can consume this data |
