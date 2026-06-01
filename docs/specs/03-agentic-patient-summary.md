# Agentic Patient Summary — Product Spec

**Component:** AI Continuity Loop — Component 3 of 3  
**Status:** APPROVED FOR PLANNING  
**Date:** 2026-06-01  
**Spec version:** v3 final (3-round debate loop)  
**Approval scores:**

| Round | TA Score | PM Score | Outcome |
|---|---|---|---|
| 1 | 7.86 / 10 | 8.53 / 10 | Conditional — 9 HIGH/CRIT defects |
| 2 | 8.70 / 10 | 8.68 / 10 | Conditional — 5 amendments required |
| 3 | **9.20 / 10** | **9.10 / 10** | ✅ **APPROVED** (avg 9.15/10) |

---

## Goal

Automatically synthesize up to 30 days of Elfie patient self-monitoring data — vitals, medication adherence, physical activity, symptom logs, lab results, and engagement signals — into a structured pre-visit briefing delivered to the treating physician in ElfieCare before each consultation, so that every follow-up begins with a complete, factual account of the patient's inter-visit period rather than patient recall. The system is a **data synthesis tool**, not a clinical decision support system: all numerical values are computed from structured data; the LLM writes only the narrative wrapper; the physician retains full clinical judgment; and the summary is explicitly framed as a well-organized copy of the patient's own self-reported data. This feature operates exclusively in Vietnam (VN) and Thailand (TH) at MVP.

---

## Scope

### In (MVP)

1. **Two trigger modes:** (a) manual on-demand pull by the doctor from ElfieCare; (b) scheduled 30-day push for patients with active doctor-patient consent links
2. **Data collection pipeline** covering six data categories subject to patient consent: vitals (BP, HR, glucose, weight), medication adherence logs, physical activity (steps), symptom logs (opt-in), lab results (opt-in), coin events (engagement proxy)
3. **Delta Analyzer:** computes per-metric trend direction (linear OLS slope), anomaly detection (value outside patient-set target), adherence rate, and engagement score for the current period vs. the prior period of equal length
4. **Application-layer summary renderer + LLM narrative generator (two-stage, CRIT-1 amendment):**
   - All tables, quantitative values, flags, data completeness scores, and header/footer text are rendered directly from Delta Analyzer output by the application layer — NOT by the LLM
   - LLM receives only named narrative text slots to fill (trend observation sentences, medication adherence sentences, engagement observation sentences) within a fixed template; numerical values appear in the template as pre-filled literals sourced from Delta Analyzer output
   - This design makes numerical hallucination structurally impossible in the physician-visible sections; the Compliance Gate audits LLM narrative text only, not the rendered quantitative fields
5. **Compliance Gate:** verifies dual consent (patient + doctor acknowledgment) before every summary delivery; creates an immutable audit log entry per summary; scans LLM output for prohibited clinical interpretation language before release
6. **Delivery — in-app ElfieCare card:** summary rendered as a card in the ElfieCare doctor's patient queue; doctor can View, Dismiss, Snooze (7 days), or trigger on-demand regeneration
7. **PDF export:** for paper-based clinics; generated on demand from the same summary payload; includes mandatory disclaimer header
8. **Dual consent system:** granular patient data-sharing consent per doctor-patient pair; one-time per-pair doctor acknowledgment; consent revocation pipeline with immediate summary deletion
9. **Consent revocation:** patient can revoke data sharing at any time; all pending and delivered-but-retained summaries for that doctor-patient pair are deleted within 24 hours; audit log entry tombstoned (not deleted)
10. **Completeness transparency:** every summary shows a per-category data completeness score (days logged / days in period); LLM output explicitly states coverage gaps
11. **Summary atomicity:** if any pipeline stage fails, doctor receives "Summary unavailable — please review patient record manually"; no partial summary is ever delivered
12. **Idempotency:** summary generation is idempotent per `(patient_id, doctor_id, period_start)`; the same inputs produce the same summary slot and do not create duplicate summaries
13. **VN + TH geo-gate:** server-side enforcement; summary generation and delivery restricted to patients registered in Vietnam or Thailand; ElfieCare doctors treating VN/TH patients
14. **LLM provider BAA:** LLM provider must have a signed BAA agreement before any patient health data is passed to the model (named pre-launch gate)

**ElfieCare Integration (cross-team dependency, named):** Five new ElfieCare capabilities are required (HIGH-1 amendment adds deliverable (e)). ElfieCare engineering team must confirm engineering effort, sprint availability, and delivery commitment covering **both Component 2 (4 deliverables) and Component 3 (5 deliverables) in a single consolidated capacity plan** before this spec is approved for planning:
- (a) Pre-visit summary card component in patient queue UI (View / Dismiss / Snooze / Regenerate actions)
- (b) Doctor acknowledgment flow: one-time per-patient-link modal with explicit AI-non-clinical-finding language
- (c) Inbound summary API endpoint accepting structured summary payload from Elfie backend
- (d) "Summary unavailable" state in the patient queue card (fallback display)
- **(e) Summary retraction API:** endpoint that accepts `(patient_id, doctor_id)` and marks all unviewed summaries for that pair as deleted, removing them from the doctor queue — required for consent revocation deletion SLA (AC 3.1). Without this, Elfie can only delete summaries held server-side; summaries already pushed to ElfieCare cannot be recalled.

**Elfie Mobile (patient-facing) Deliverables:**
- (a) Data sharing consent flow: per-doctor-link consent modal with granular category toggles (AC 3.1)
- (b) Settings → Privacy → Shared with Doctors section: per-doctor toggle with category breakdown, revoke link
- (c) Consent change notification: in-app confirmation when patient revokes sharing

### Explicitly Out (v2+)

| Item | Reason deferred |
|---|---|
| Appointment auto-detection trigger (iCal / Google Calendar) | Requires OAuth calendar integration; separate engineering track |
| HL7 FHIR R4 DocumentReference export | EHR integration requires per-hospital credential management |
| Encrypted email delivery to non-ElfieCare doctors | Delivery security model not fully defined for this channel |
| Doctor-configurable summary template (full vs. brief) | UX and backend complexity; standard template sufficient at MVP |
| AI Coach conversation history in summary | Separate consent model; depends on Component 1 privacy architecture review |
| EU / global market rollout | Blocked pending EU AI Act conformity assessment (High-risk classification near-certain per Annex III) |
| Real-time continuous summary updates | This is a pre-visit briefing system, not a monitoring alert system |
| Insurer or pharma PSP data sharing | Commercial and consent model not confirmed for MVP markets |
| Caregiver / family access to summary | Separate third-party consent model |

---

## Acceptance Criteria

### Section 1 — Trigger & Data Collection

---

**AC 1.1 — Trigger modes**

Two and only two trigger modes are supported at MVP:

| Mode | Actor | Condition | Behavior |
|---|---|---|---|
| Manual on-demand | Doctor (ElfieCare) | Doctor clicks "Generate Summary" in patient queue | Initiates pipeline immediately; doctor sees "Generating…" state; result delivered within `SUMMARY_GENERATION_SLA` |
| Scheduled 30-day push | System | `SUMMARY_SCHEDULE_DAYS = 30`; evaluated daily per active consent link | Triggers at midnight VN/TH local time for eligible pairs; delivers to doctor queue without requiring doctor action |

A doctor-patient pair is eligible for scheduled push if and only if:
1. Patient consent is active (AC 3.1)
2. Doctor acknowledgment is active (AC 3.2)
3. At least `SUMMARY_MIN_DATA_DAYS = 7` days of logged data exist in the summary period
4. No summary has been generated for this pair in the last `SUMMARY_SCHEDULE_DAYS = 30` calendar days

Appointment auto-detection (from appointment reminder system or calendar integration) is explicitly **not** an MVP trigger. If a future appointment system integration provides an event, the pipeline treats it as a manual trigger but does not block MVP delivery on its absence.

*Verification:* Integration test confirming manual trigger initiates pipeline and completes within SLA. Integration test confirming scheduled job evaluates all active consent links daily and fires only for eligible pairs. Test confirming pairs with `< SUMMARY_MIN_DATA_DAYS` data are excluded from scheduled push.

---

**AC 1.2 — Summary period determination**

The summary covers the period from the patient's last recorded doctor visit (for this doctor-patient pair) to today, capped at `SUMMARY_MAX_PERIOD_DAYS = 30` days.

```
period_start = max(last_visit_date_for_pair, today - SUMMARY_MAX_PERIOD_DAYS)
period_end   = today
```

If no prior visit is recorded for this doctor-patient pair, the period defaults to the last 30 days.

**Zero-length period guard (V3-C3 amendment):** If `(period_end - period_start) < SUMMARY_MIN_PERIOD_DAYS = 3`, the pipeline returns `"Summary unavailable — insufficient data period"` to the doctor. This prevents divide-by-zero in Delta Analyzer completeness, trend, and engagement computations when a trigger fires on the same day as a new visit is recorded.

The prior comparison period is the equal-length window immediately preceding `period_start`:

```
prior_period_end   = period_start - 1 day
prior_period_start = prior_period_end - (period_end - period_start)
```

If the prior period predates the patient's account creation, delta comparisons for that period are shown as "No prior data" — the LLM does not estimate or infer values for the missing prior period.

*Verification:* Unit tests for period calculation covering: first-ever visit (no prior visit), normal follow-up (visit within 30 days), long gap (visit > 30 days ago, caps at 30). Unit test for prior period calculation on edge case where prior period predates account creation.

---

**AC 1.3 — Data collection scope**

The Data Collector fetches only data categories for which patient consent is active (AC 3.1). Data fetched is strictly bounded to `[period_start, period_end]`.

| Data category | Consent default | Collected fields |
|---|---|---|
| Vitals (BP, HR, glucose, weight) | ON | Value, timestamp, data source (manual / wearable / device) |
| Medication adherence | ON | Medication name, dose, scheduled time, logged time or missed flag |
| Physical activity | ON | Steps per day; any logged wearable sync |
| Symptom logs | OFF (opt-in) | **Structured only:** symptom tag + occurrence count + period. Raw free-text entries are aggregated into structured symptom frequency by the Data Collector before leaving the data layer. Raw free-text is NOT stored in the pipeline and NOT passed to the LLM (HIGH-5 amendment). |
| Lab results | OFF (opt-in) | Uploaded document reference, uploader-entered value, timestamp |
| Coin events (engagement proxy) | **ON by default, toggleable** — added to consent flow (HIGH-7 amendment) | Coin transaction date; engagement score computed as `(coin_event_days / period_length_days)` |

The raw event log is NOT passed to the LLM. The Data Collector produces a structured normalized output, which becomes the sole input to the Delta Analyzer. The LLM receives Delta Analyzer output, not Data Collector output.

The AI Coach conversation history is **not** a collectable data category at MVP, regardless of patient consent. This requires a separate consent model dependent on Component 1 architecture review.

*Verification:* Integration test confirming data collection for each category is correctly gated on consent state (including coin events category). Unit test confirming raw event log is not present in LLM input payload. Unit test confirming AI Coach history is never included regardless of consent flags. Unit test confirming raw symptom free-text is not present in pipeline output (only structured frequency summary exits the Data Collector for symptoms).

---

**AC 1.4 — Delta Analyzer outputs**

The Delta Analyzer produces a structured delta object for each data category collected. This object is the complete input to the LLM (plus patient context — AC 2.1). The Delta Analyzer computes:

| Output | Computation | Notes |
|---|---|---|
| Per-metric trend direction | OLS linear slope over `period_start → period_end` | Expressed as ↑ / → / ↓ based on slope sign and magnitude threshold `TREND_SLOPE_THRESHOLD` |
| Per-metric period average | Mean of all readings in current period | Used as the primary displayed value |
| Per-metric prior average | Mean of all readings in prior period | Null if no prior data |
| Anomaly flag | Value > or < patient-set target in Settings | True/False per metric; target source must be recorded |
| Adherence rate | `(doses_logged / doses_scheduled) × 100` expressed as percentage | Per medication |
| Engagement score | `(coin_event_days_in_period / period_length_days)` | Float [0,1]; proxy for app engagement |
| Data completeness per category | `(days_with_at_least_one_log / period_length_days) × 100` | Integer percentage; shown in summary |

Named constants:
- `TREND_SLOPE_THRESHOLD = 0.1` — slope threshold in **standard deviations per day** relative to the metric's prior-period mean. Slopes with absolute value < threshold are classified as "→" (stable).
- `TREND_MIN_DATA_POINTS = 7` — minimum number of observations required to compute a valid OLS slope. If fewer than 7 data points exist in the current period for a metric, the trend direction is reported as "Insufficient data" rather than ↑/→/↓. A "Insufficient data" result is communicated to the physician in the completeness section — it is never silently converted to "→ (stable)".

**Anomaly flag target hierarchy (HIGH-6 amendment):** Anomaly detection uses the following priority order:
1. **Doctor-set monitoring target** (if set in ElfieCare for this patient) — used first
2. **Patient-set target** (from Elfie app Settings) — used if no doctor target
3. **No flag raised** if neither target is set

The flag text explicitly identifies whose target is being referenced:
- Doctor target: `"⚠️ [Metric] above doctor's monitoring target of [value] — for discussion"`
- Patient target: `"⚠️ [Metric] above patient's stated target of [value] — for discussion"`

The Delta Analyzer does NOT perform clinical inference. Anomaly flags reference the target hierarchy defined above — the LLM does not receive target source information (per V3-C1 two-stage architecture).

*Verification:* Unit tests for slope classification covering: rising, falling, stable, single-data-point (→ Insufficient data), 6-data-point (→ Insufficient data), 7-data-point (→ valid classification). Unit test for `TREND_MIN_DATA_POINTS` boundary: 6 → suppressed; 7 → computed. Unit test for normalization: slope in standard deviations per day relative to prior-period mean. Unit test for adherence rate with zero scheduled doses (divide-by-zero guard). Unit test for anomaly flag priority hierarchy: doctor target used when available, falls back to patient target, no flag when neither exists. Integration test confirming Delta Analyzer output — not LLM output — is the sole source of all numerical values in the rendered summary.

---

### Section 2 — Summary Generation

---

**AC 2.1 — Two-Stage Summary Construction Architecture (CRIT-1 amendment)**

Summary construction is split into two stages to make LLM numerical hallucination structurally impossible in physician-visible sections:

**Stage 1 — Application-layer rendering (no LLM involvement):**
- All quantitative fields are rendered directly from Delta Analyzer output by the application layer
- Rendered fields include: all table rows (Vital Signs, Medication Adherence, Physical Activity), flag bullets (from anomaly flags), data completeness scores, period dates, header, footer disclaimer
- The rendered template contains **named narrative text slot placeholders** (e.g., `{{vitals_trend_observation}}`, `{{adherence_narrative}}`, `{{engagement_observation}}`)
- The Delta Analyzer output values are injected into the template directly; they do NOT pass through the LLM

**Stage 2 — LLM narrative fill-in:**
The LLM receives:
1. **System prompt** (static, version-controlled, Medical Affairs + Legal reviewed): instructs the LLM to write narrative sentences filling named text slots only; explicitly prohibits the LLM from writing any numerical value; defines permitted observation formats (non-clinical, trend observation, no diagnosis, no treatment recommendation).
2. **Named slot context** (dynamic per-summary): For each text slot, the **trend classification only** (↑/→/↓/Insufficient) and the patient's primary condition and summary period dates. **Raw Delta Analyzer numerical values are NOT included in the slot context (V3-C1 design choice: strip numbers from LLM context).** This design makes Check 3 (numerical token detection) redundant in the happy path — the LLM has no numbers to copy from context — but Check 3 remains as a defense-in-depth guard against model-generated numbers. Patient PII is not in the LLM context. Raw event log is not in the LLM context. Free-text symptom log is NOT in the LLM context (structured symptom frequency only per AC 1.4).

The LLM fills narrative text slots only. If a slot's corresponding data section was not consented, the slot is marked as absent and the LLM receives no fill-in instruction for it — it does not generate a placeholder.

The patient identifier is re-attached to the assembled summary only after LLM output has passed the Compliance Gate (AC 2.3).

*Verification:* Code review confirming no PII in LLM input, no raw event log, no free-text symptom entries. Integration test confirming all numerical values in the final rendered summary match Delta Analyzer output exactly. Unit test confirming system prompt version is logged per summary generation. Unit test confirming LLM output containing a numerical value in a narrative text slot triggers Compliance Gate Check 3 (numerical token in narrative slot → prohibited term failure).

---

**AC 2.2 — Summary output structure (two-stage rendering)**

The final summary is assembled from application-layer rendered fields + LLM-filled narrative text slots. Sections for which no data was collected (consent not granted) are omitted entirely — the LLM does not generate placeholder text for absent sections.

| Section | Content | Requirement |
|---|---|---|
| Header | Period, preparation timestamp, mandatory disclaimer | Static template; not LLM-generated |
| Vital Signs | Table: metric, this-period average, prior-period average, target, trend arrow | All values rendered from Delta Analyzer by application layer; LLM fills `{{vitals_trend_observation}}` narrative text slot only |
| Medication Adherence | Per-medication adherence rate and missed-day count; LLM narrative sentence | All rates rendered from Delta Analyzer; LLM fills `{{adherence_narrative}}` slot only |
| Physical Activity | Average steps per day, trend | Values from Delta Analyzer |
| Symptom Log | Symptom frequency summary; patient-reported free-text items | Only present if patient consented |
| Lab Results | Uploaded values with patient-entered labels and dates | Only present if patient consented; LLM does not interpret lab values |
| Flags for Discussion | One bullet per anomaly flag from Delta Analyzer | Application-layer rendered from Delta Analyzer anomaly flags; required format: "⚠️ [Metric] above/below [doctor's monitoring / patient's stated] target of [value] — for discussion"; LLM does NOT generate flags |
| Data Completeness | Per-category: days logged / period length, as percentage | Application-layer rendered; required in every summary |
| Disclaimer footer | "Data as recorded by patient. Verify with in-office measurement. Receipt of this summary does not create clinical obligation." | Static; not LLM-generated |

**Required disclaimer text** (exact wording; not paraphraseable by LLM):
> *This summary is AI-generated from patient self-reported data. It is a pre-visit briefing only — not a clinical finding, not a diagnosis, and not a treatment recommendation. Data completeness and accuracy have not been independently verified. Verify all values with in-office measurement before clinical use.*

*Verification:* Output schema validation test run against 20 synthetic delta inputs. Test confirming disclaimer text matches required wording exactly. Test confirming omitted-consent sections produce no placeholder text in output. Test confirming flag format matches required string pattern.

---

**AC 2.3 — Compliance Gate: prohibited language scan**

Every LLM output passes through the Compliance Gate before delivery. The Compliance Gate runs two checks in sequence:

**Check 1 — Keyword / regex scan:**

The following term categories are prohibited in LLM output. Any match causes the summary to be rejected (not delivered; pipeline logs failure):

| Category | Example prohibited terms |
|---|---|
| Clinical diagnosis | "hypertensive crisis", "appears to be developing", "consistent with", "diagnostic of", "suggests diagnosis" |
| Treatment recommendation | "recommend", "consider increasing", "should adjust", "dosage change", "titrate" |
| Clinical urgency framing | "urgent", "emergency", "immediately contact", "seek care now", "dangerous" |
| Risk prediction language | "risk of", "likely to develop", "trending toward", "predicts" |

The prohibited term list is version-controlled in code as a named constant: `COMPLIANCE_GATE_PROHIBITED_TERMS`. The list is reviewed by Medical Affairs and Legal before each deployment and after any LLM model version change.

**Check 2 — Flag format validation:**

Since flags are rendered by the application layer (not the LLM), this check validates that the rendered flags conform to the required pattern before delivery. Any flag bullet not matching the approved format pattern is a compliance gate failure.

**Check 3 — Narrative text slot numerical token detection (CRIT-1 amendment):**

The LLM fills narrative text slots only. If any LLM-generated narrative text slot contains a numeric token (integer or decimal number, e.g., "142/89", "79%", "22"), this is a compliance gate failure. Numerical presentation is exclusively the responsibility of the application-layer renderer; any LLM-generated number indicates the system prompt was not followed.

On compliance gate failure (any of the three checks): summary is not delivered. Doctor receives: *"Summary unavailable — please review patient record manually."* Failure event logged to audit trail with `failure_reason: compliance_gate` and the check that failed (no patient data in failure log). Operations queue is notified for human review.

*Verification:* Unit tests for each prohibited term category with 5 pass/fail sentences per category. Unit test: LLM output containing "142/89" in a narrative slot → Check 3 fails. Unit test: LLM output with no numeric tokens → Check 3 passes. Integration test confirming compliance gate failure produces correct doctor-facing message and audit log entry.

---

**AC 2.4 — LLM model and provider requirements**

| Requirement | Specification |
|---|---|
| Provider BAA | Signed HIPAA Business Associate Agreement required before any health data is passed to the model. This is a hard pre-launch gate (Pre-Launch P1-G0-1). |
| Permitted providers | Claude 3.5 Sonnet or GPT-4o (same providers as Component 1; same BAA, subject to OQ-1 Path A confirmation). Other providers require separate Legal and Security review. |
| Model version pinning | Production uses a pinned model version. Version changes require: (a) re-run of compliance gate test suite, (b) Medical Affairs sign-off on output quality, (c) deployment via code change. Auto-upgrade to new model versions is prohibited. |
| **System prompt version pinning (V3-C2 amendment)** | The system prompt is version-controlled. System prompt updates require: (a) re-run of compliance gate test suite against updated prompt, (b) Medical Affairs sign-off (≤5 business days per P1-G0-6 SLA), (c) deployment via code change. Auto-update of system prompt is prohibited. This gate is equivalent to the model version change gate. System prompt version is logged per summary generation in the audit log (AC 5.4). |
| Data region | LLM API calls must be routed to a data region consistent with VN and TH patient data residency requirements (OQ-1 Path A/B determination). |

*Verification:* Pre-launch gate checklist item confirming BAA on file. CI test confirming model version is a pinned constant, not a dynamic config value. Pre-launch sign-off from Medical Affairs on output quality for pinned version.

---

**AC 2.5 — Summary generation SLA and timeout**

| Metric | Target |
|---|---|
| `SUMMARY_GENERATION_SLA` | P95 ≤ 45 seconds for on-demand trigger; P95 ≤ 10 minutes for scheduled push (asynchronous) |
| LLM call timeout | `LLM_TIMEOUT_SECONDS = 30` |
| Total pipeline timeout | `PIPELINE_TIMEOUT_SECONDS = 60` |
| On timeout | Pipeline aborts; doctor receives "Summary unavailable" message; event logged |

The on-demand path shows a loading state in ElfieCare UI during generation. The scheduled push path delivers silently to the queue; doctor sees the card on next ElfieCare load.

*Verification:* Load test: 50 concurrent on-demand triggers; P95 within SLA. Synthetic timeout injection test confirming abort behavior and correct doctor-facing message.

---

### Section 3 — Consent & Permissions

---

**AC 3.1 — Patient data-sharing consent**

Patient consent is **per doctor-patient pair**. A patient who links to two doctors has two independent consent records. Revoking consent for Doctor A does not affect consent for Doctor B.

**Consent categories and defaults:**

| Data category | Default state | Change mechanism |
|---|---|---|
| Vitals (BP, HR, glucose, weight) | ON | Toggle in consent flow and Settings |
| Medication adherence | ON | Toggle in consent flow and Settings |
| Physical activity | ON | Toggle in consent flow and Settings |
| Symptom logs | OFF | Opt-in toggle in consent flow and Settings |
| Lab results | OFF | Opt-in toggle in consent flow and Settings |
| Coin events (engagement proxy) | ON | Toggle in consent flow and Settings |
| AI Coach conversations | OFF | Not available at MVP (see Scope — Out) |

**Consent grant flow:** Patient grants consent when linking a doctor in the Elfie app. The consent modal displays: (a) the doctor's name, (b) the full list of data categories with defaults shown, (c) the summary frequency (30-day scheduled + on-demand by doctor), (d) a plain-language description of what the doctor will see. Consent requires explicit affirmative action (not pre-checked "I agree" at bottom of flow).

**Settings access:** Patient can modify individual category toggles at any time via Settings → Privacy → Shared with Doctors → [Doctor Name]. Changes take effect for the next summary generation; in-progress pipeline runs to completion using the consent state at pipeline start (snapshot at trigger time).

**Consent revocation:** Patient can revoke full consent for a doctor-patient pair. On revocation:
1. No new summaries are generated for this pair
2. All summaries for this pair that have not yet been **viewed** by the doctor are deleted within `CONSENT_REVOCATION_DELETION_SLA = 24 hours`. **"Viewed" means the doctor explicitly clicked "View" to open the full summary content. Summaries in Available, Snoozed, or Dismissed states where the doctor did not click View are considered unviewed and are subject to deletion (V3-C5 amendment).** This definition is implemented as a `viewed_at` timestamp set when the doctor opens the View action — null `viewed_at` = unviewed.
3. Summaries already viewed by the doctor are not retroactively deleted (already delivered to clinical workspace; doctor retains responsibility for deletion of their own records)
4. Doctor receives in-ElfieCare notification: *"[Patient] has disconnected data sharing. No further summaries will be generated."*
5. Consent revocation and deletion event are recorded in the audit log

Patient receives in-app confirmation when revocation is complete.

*Verification:* Integration test: patient grants consent, generates summary, revokes consent → pending summary deleted within SLA, no new summaries generated. Test confirming per-category toggle correctly gates corresponding data category from collection (AC 1.3). Test confirming consent snapshot is taken at trigger time and is not affected by mid-pipeline consent changes.

---

**AC 3.2 — Doctor acknowledgment**

Before any summary is delivered to a doctor for a specific patient-link, the doctor must complete a one-time acknowledgment for that doctor-patient pair.

**Acknowledgment content (exact language; not paraphraseable):**

> *I acknowledge that Elfie pre-visit summaries are AI-generated from patient self-reported data. They are a pre-visit briefing only — not a clinical finding, not a diagnostic output, and not a treatment recommendation. Receipt of a summary does not create or expand any clinical obligation. I remain solely responsible for all clinical decisions. I can deactivate summary delivery at any time.*

Doctor must click "I Acknowledge and Activate" — no implicit acceptance. A dismiss action without clicking the button does not constitute acknowledgment.

**Acknowledgment state:**

- The acknowledgment is per-doctor-patient pair, not per-summary and not per-doctor globally
- Acknowledgment is recorded with timestamp and doctor user ID in the audit log
- If a doctor de-links a patient and re-links later, a new acknowledgment is required
- If the acknowledgment language is updated (e.g., after Legal review), all active acknowledgments are invalidated and doctors must re-acknowledge before next delivery

**Gate behavior:** Summaries are not delivered to a doctor for a patient until acknowledgment is active. The scheduled push pipeline checks acknowledgment state before delivery. If acknowledgment is missing, the summary is queued for delivery but not delivered; an in-ElfieCare prompt asks the doctor to complete acknowledgment.

*Verification:* Integration test: create doctor-patient pair with no acknowledgment → trigger summary → summary queued, not delivered, acknowledgment prompt shown. Integration test: doctor completes acknowledgment → queued summary delivered. Test confirming language invalidation causes re-acknowledgment flow.

---

**AC 3.3 — Consent data model**

Each consent record contains:

| Field | Type | Notes |
|---|---|---|
| `consent_id` | UUID | Immutable; primary key |
| `patient_id` | String (pseudonymized) | Key-vault pseudonymized (AC 5.2) |
| `doctor_id` | String | ElfieCare doctor identifier |
| `categories_enabled` | JSONB | Per-category boolean map; snapshot at each change |
| `granted_at` | Timestamp (UTC) | Time of initial consent grant |
| `last_modified_at` | Timestamp (UTC) | Time of last category change |
| `revoked_at` | Timestamp (UTC) | Null if active; set on revocation |
| `consent_version` | String | Version of consent text shown to patient; immutable after grant |
| `stale` | Boolean | True if consent_version < current CONSENT_TEXT_VERSION; patient must re-consent before next summary; false otherwise |

Consent records are **never deleted** — revocation sets `revoked_at`, it does not delete the record. This supports regulatory audit requirements.

**Patient re-consent on consent text update (V3-C4 amendment, MED-5 resolution):** If the patient consent text is updated (e.g., after Legal review adds a new disclosure), all active consent records with `consent_version` < current `CONSENT_TEXT_VERSION` are marked as `stale` at update time. On next app open, the patient is shown the updated consent modal before any summary is generated. Until the patient re-consents, the pair's scheduled push is paused (no new summaries). If the patient does not re-consent within `CONSENT_RE_CONSENT_WINDOW_DAYS = 30` days, the consent is treated as revoked and the consent revocation pipeline (AC 3.1) runs. This mechanism is symmetric with the doctor acknowledgment re-acknowledgment flow (AC 3.2) — both parties must consent to the current terms.

*Verification:* Unit tests confirming consent record schema (including `stale` field). Test confirming revocation sets `revoked_at` and does not delete record. Test confirming `consent_version` is recorded at grant and is immutable after grant. Test confirming `CONSENT_TEXT_VERSION` increment marks all prior-version active consents as `stale = true`. Integration test: stale consent → patient app open → re-consent modal shown; scheduled push paused during stale period. Integration test: stale consent not re-consented after `CONSENT_RE_CONSENT_WINDOW_DAYS` days → consent revocation pipeline runs.

---

### Section 4 — Delivery

---

**AC 4.1 — ElfieCare in-app card**

The primary delivery surface is a card in the ElfieCare doctor's patient queue. Card states:

| State | Trigger | Display |
|---|---|---|
| Pending generation (on-demand) | Doctor clicked "Generate" | Loading indicator with "Generating summary…" |
| Available | Generation complete | Card with period label, completeness score, "View" button |
| Summary unavailable | Pipeline failure or compliance gate failure | "Summary unavailable — please review patient record manually" with timestamp |
| Dismissed | Doctor clicked "Dismiss" | Card removed from active queue; accessible in history |
| Snoozed | Doctor clicked "Snooze 7 days" | Card hidden for 7 days; reappears after snooze period |
| No consent | Patient has not granted consent or has revoked | Card not shown; no indication of data that would have been in summary |

Doctor actions available on an "Available" card: View, Dismiss, Snooze (7 days), Download PDF.

There is no "Urgent" or "Alert" state. No visual treatment (color, icon, sound) that implies clinical urgency is used on any summary card. The card heading reads "Pre-Visit Briefing" — not "Alert", "Warning", or "Notification".

*Verification:* UI test covering all card state transitions. Code review confirming no "urgent", "alert", "warning" class names or ARIA roles applied to summary cards. ElfieCare integration test confirming card is rendered from summary API payload.

---

**AC 4.2 — PDF export**

PDF export is generated on demand when the doctor clicks "Download PDF" on an Available card.

PDF requirements:
- Generated from the same summary payload as the in-app card (no re-generation; no LLM call)
- Header on every page: *"Pre-visit briefing — AI-generated from patient self-reported data. Not a clinical finding. Verify all values with in-office measurement."*
- Footer on every page: page number, generation timestamp, summary period
- No patient name in the PDF (patient referred to by condition and period only; PHI is the doctor's responsibility once downloaded)
- No Elfie branding that implies clinical authority (no "Elfie Medical" or similar)
- PDF generation uses server-side rendering — no client-side generation of health data

*Verification:* PDF generation integration test confirming disclaimer appears on every page. Test confirming no patient name in generated PDF. Test confirming PDF content is identical to in-app card content (same source payload).

---

**AC 4.3 — On-demand regeneration**

A doctor may request regeneration of a summary for a patient at any time (manual trigger, AC 1.1). Regeneration:

- Creates a new summary slot for the current period; does not overwrite the prior summary
- Is idempotent: if a summary for `(patient_id, doctor_id, period_start)` already exists and was generated within `SUMMARY_REGEN_COOLDOWN_MINUTES = 60` minutes, the existing summary is returned and no new LLM call is made
- After the cooldown, a new generation is permitted (data may have updated)

*Verification:* Unit test confirming idempotency: two triggers within cooldown window return same summary, one LLM call logged. Unit test confirming trigger after cooldown creates new summary.

---

**AC 4.4 — Doctor-side deactivation**

A doctor may deactivate summary delivery for a specific patient at any time from within ElfieCare. On deactivation:
- No new summaries generated for this pair
- Existing summaries in the doctor's queue remain visible (already delivered to the doctor's workspace)
- Patient is not notified (this is the doctor's workspace setting)
- Doctor can reactivate at any time; reactivation does not require new patient consent (patient consent is separate) but does require re-confirmation of the doctor acknowledgment if the acknowledgment was invalidated (AC 3.2)

*Verification:* Integration test: doctor deactivates → trigger fires → no summary generated, no error. Test confirming existing queue summaries persist after deactivation.

---

---

**AC 5.7 — Patient Right of Access to Summary History (HIGH-2 amendment)**

Patients have a right to access personal data about them under VN PDPD Article 9 and TH PDPA Section 30. Every summary generated about a patient constitutes derived personal data.

Required patient-facing access:
- In Settings → Privacy → Shared with Doctors → [Doctor Name]: patient can view a list of all summaries generated for each linked doctor
- Per-entry disclosure: generation timestamp, period covered, data categories included, delivery status (delivered / unavailable)
- Patient does NOT receive the verbatim physician-facing summary content (which is formatted for clinical context), but receives a plain-language "what was shared" disclosure sufficient to exercise PDPD/PDPA data subject rights
- This summary history view is retained subject to the same `ERASURE_SLA` as other summary records (key deletion renders it non-linkable)
- Patient can submit a data access request for the full summary content via in-app form; fulfillment SLA: 30 days

*Verification:* Integration test: generate 3 summaries for a patient-doctor pair → patient view shows all 3 with correct metadata. Test confirming verbatim physician-formatted summary content is not exposed in the patient-facing view. Erasure test: key deleted → summary history view returns empty. Data access request flow end-to-end test.

---

### Section 5 — Privacy & Compliance

---

**AC 5.1 — Regulatory framing enforcement**

The system is framed as a "data synthesis tool" and a "pre-visit briefing" throughout all patient-facing, doctor-facing, and external-facing surfaces.

The following language is **prohibited** in any product surface, marketing material, press release, or legal document associated with this feature:

| Prohibited term | Reason |
|---|---|
| "Clinical decision support" | Triggers SaMD/regulatory classification |
| "Clinical recommendation" | Creates clinical liability |
| "Alert" (for summary delivery) | Implies clinical urgency and duty to act |
| "Diagnosis" | SaMD trigger |
| "Treatment recommendation" | SaMD trigger |
| "AI-detected" (for clinical conditions) | Implies clinical inference |

Permitted framing: "pre-visit briefing", "data synthesis", "patient self-reported data summary", "pre-visit preparation tool".

This AC is enforced via: (a) copy review by Medical Affairs and Legal before any text is shipped; (b) a prohibited-language checklist in the launch gate.

*Verification:* Pre-launch review by Medical Affairs and Legal covering all product surfaces. Launch gate checklist item confirming sign-off completed.

---

**AC 5.2 — Key-vault pseudonymization**

Patient identifiers in the summary pipeline are pseudonymized using a key-vault approach consistent with Component 2 (Predictive Adherence AI, AC 4.2).

- `patient_id` is pseudonymized before data is written to the feature store and before any LLM call
- The pseudonymization key is stored in a key vault (not in the application database)
- Key deletion renders the patient's summary history permanently non-re-linkable
- Right-to-erasure: patient requests deletion → key deleted from vault → all summary records for that patient become permanently de-linked within `ERASURE_SLA = 30 days`
- Erasure pipeline runs audit log entry confirming key deletion (no patient data in the audit record — the audit record contains only pseudonymized ID and deletion timestamp)

*Verification:* Unit test confirming pseudonymized ID is the only patient reference in LLM input. Integration test: key deletion → attempt to re-link summary record → failure. Erasure pipeline test: request → key deleted → audit entry created within SLA.

---

**AC 5.3 — Data minimization**

The pipeline enforces data minimization at three points:

1. **Period boundary:** Data Collector fetches only records within `[period_start, period_end]`. No historical data outside this window is fetched.
2. **Consent boundary:** Data Collector fetches only categories with active patient consent (AC 3.1). Categories without consent are not fetched, not stored in the pipeline, and not passed to the LLM.
3. **LLM input boundary:** The LLM receives only the Delta Analyzer output JSON and patient context. The LLM does not receive raw event log, prior summaries, or any data outside the current period's delta.

*Verification:* Unit tests confirming each minimization boundary. Code review confirming no raw event log fields appear in LLM request payload. Integration test confirming revoked category data is absent from generated summary when consent was previously active.

---

**AC 5.4 — Audit log requirements**

Every summary pipeline execution creates an immutable audit log entry. The audit log records:

| Field | Content |
|---|---|
| `summary_id` | UUID (unique per generation) |
| `patient_id` | Pseudonymized |
| `doctor_id` | ElfieCare doctor identifier |
| `trigger_type` | `manual` or `scheduled` |
| `trigger_timestamp` | UTC |
| `period_start` | Date |
| `period_end` | Date |
| `consent_snapshot` | Categories active at pipeline start (JSONB) |
| `doctor_acknowledgment_active` | Boolean |
| `llm_model_version` | Pinned version string |
| `system_prompt_version` | Version hash |
| `compliance_gate_result` | `pass` / `fail` |
| `compliance_gate_failure_reason` | Matched term(s) if `fail`; null if `pass` |
| `delivery_outcome` | `delivered` / `unavailable` / `queued_pending_acknowledgment` |
| `delivery_timestamp` | UTC; null if not delivered |

The audit log is append-only. Existing entries cannot be modified or deleted. Retention: minimum `AUDIT_LOG_RETENTION_YEARS = 7` years.

*Verification:* Integration test confirming audit entry created for each pipeline execution (success and failure). Test confirming compliance gate failure populates `compliance_gate_failure_reason` without patient data. Retention policy test confirming entries are not deleted before retention period.

---

**AC 5.5 — VN + TH geo-gate**

Summary generation and delivery is restricted to patients with a registered country of VN (Vietnam) or TH (Thailand). Enforcement is server-side via the patient's registration record country code.

- Patients registered outside VN/TH: no summary generated, no consent flow shown in app
- Geo-gate is evaluated at pipeline trigger time, not at consent grant time
- If a patient's registered country changes (account update), geo-gate is re-evaluated on next scheduled trigger

This gate is not a feature flag and is not configurable by operators without a code deployment.

*Verification:* Integration test: trigger pipeline for patient with country = `US` → no pipeline execution. Test confirming gate is checked at trigger time. Test confirming non-VN/TH patient sees no consent flow in Elfie app.

---

**AC 5.6 — EU AI Act pre-launch preparation**

The Agentic Patient Summary is assessed as near-certain **High-risk AI** per EU AI Act Annex III (intends to influence medical decisions; automated processing of health data; vulnerable population). While the feature is VN + TH only at MVP and does not fall under EU AI Act jurisdiction, the following documentation is required before launch to support a future EU conformity assessment:

| Document | Owner | Gate |
|---|---|---|
| Risk management documentation (Article 9) | Technical Advisor | P2-G0 |
| Technical documentation (Article 11) | Engineering | P2-G0 |
| Data governance documentation (Article 10) | Data / Legal | P2-G0 |
| Human oversight mechanism description (Article 14) | Product | P2-G0 |
| Post-market monitoring plan (Article 17) | Product | P3-G4 |

These documents are required for the pre-launch gate checklist and will be maintained as living documents after launch.

*Verification:* All five documents present and reviewed by Legal before P2-G0. Launch gate checklist item confirming documentation complete.

---

### Section 6 — Reliability & Monitoring

---

**AC 6.1 — Pipeline atomicity**

The summary pipeline is atomic. A summary is either delivered in its complete, compliant form or not delivered at all.

Failure modes that result in "Summary unavailable" delivery to doctor:

| Failure mode | Handling |
|---|---|
| Data Collector error (data store unavailable, timeout) | Pipeline aborts; unavailable message sent |
| Delta Analyzer error (computation failure) | Pipeline aborts; unavailable message sent |
| LLM call timeout (`LLM_TIMEOUT_SECONDS = 30`) | Pipeline aborts; unavailable message sent |
| LLM call error (5xx, rate limit) | Single retry with `RETRY_DELAY_SECONDS = 5`; if retry fails, pipeline aborts; unavailable message sent |
| Compliance Gate failure (prohibited language detected) | Pipeline aborts; unavailable message sent; operations queue notified |
| Delivery failure (ElfieCare API unavailable) | Retry up to `MAX_DELIVERY_RETRIES = 3` with exponential backoff; if all retries fail, summary retained server-side for `DELIVERY_RETRY_WINDOW_HOURS = 24`; if still undelivered, doctor receives asynchronous unavailable notification |

No partial summary is ever delivered under any failure mode. The "Summary unavailable" message is the complete fallback for all failure modes.

*Verification:* Synthetic failure injection test for each failure mode confirming correct abort behavior and doctor-facing message. Test confirming no partial summary content appears in doctor queue under failure conditions.

---

**AC 6.2 — Idempotency with Period-Boundary-Drift Exception (HIGH-4 amendment)**

Summary generation is idempotent per `(patient_id, doctor_id, period_start)`.

- If a summary slot for this tuple already exists: return the existing summary (no new pipeline execution)
- The cooldown exception (AC 4.3) allows re-generation after `SUMMARY_REGEN_COOLDOWN_MINUTES = 60` minutes
- Idempotency key is computed as `SHA-256(patient_pseudonymized_id + doctor_id + period_start_date)`
- Idempotency records are not deleted when a summary is dismissed or snoozed
- **Period-boundary-drift exception:** Before applying the 30-day cooldown, the scheduled push evaluator computes the current `period_start` for this pair. If the computed `period_start` differs from the `period_start` stored in the most recent delivered summary, the pair is **eligible for regeneration** regardless of the 30-day cooldown — the visit record has changed and the prior summary covers the wrong period. The 60-minute regeneration cooldown (AC 4.3) still applies to prevent duplicate burst triggering.

*Verification:* Unit test: same period_start within cooldown → cached summary returned, one LLM call logged. Unit test: period_start changes due to retroactive visit entry → pair eligible for regeneration despite recent summary. Test confirming idempotency key computation is deterministic across workers. Test confirming dismiss/snooze do not invalidate idempotency.

---

**AC 6.3 — Operational monitoring**

The following metrics are emitted and monitored in the operations dashboard:

| Metric | Alert threshold |
|---|---|
| Summary generation success rate | < 95% over 1-hour window |
| Compliance gate failure rate | > 2% over 24-hour window |
| LLM call P95 latency | > `LLM_TIMEOUT_SECONDS × 0.8` (early warning) |
| Pipeline P95 end-to-end latency (on-demand) | > `SUMMARY_GENERATION_SLA × 0.8` |
| Delivery failure rate (ElfieCare) | > 5% over 1-hour window |
| Consent revocation deletion SLA breach | Any breach (zero tolerance) |

On-call engineer is paged on any alert threshold breach. Compliance gate failure rate alert includes sample of matched terms (no patient data) for human review.

*Verification:* Staging environment smoke test confirming all metrics are emitted. Alert threshold configuration reviewed by Engineering Lead before launch.

---

**AC 6.4 — Post-launch error monitoring and feedback**

After launch, the following feedback mechanisms are required:

1. **Doctor feedback on summary quality:** Doctor can flag a summary as "Inaccurate data" or "Inappropriate content" from within ElfieCare. Flags are routed to the operations queue for human review within `FLAG_REVIEW_SLA_HOURS = 48` hours.
2. **Adverse event reporting:** If a doctor reports that a summary contained content that caused or contributed to a clinical error, the report is escalated immediately to Medical Affairs and Legal. No automated handling — human review only.
3. **Monthly summary quality review:** A sample of 20 summaries per month is reviewed by a Medical Affairs reviewer for compliance gate effectiveness and output quality. Findings documented. If prohibited language is found in a delivered summary (compliance gate miss), this triggers a mandatory gate review and re-deployment of the prohibited terms list.

*Verification:* Launch gate checklist item confirming feedback routing is operational. Pre-launch test of adverse event escalation path. Monthly review calendar entry created before launch.

---

## Pre-Launch Requirements

### P1 — Foundation (gate: P1-G0)

**P1-G0 Gate: before any development begins**

| # | Item | Owner | Status |
|---|---|---|---|
| P1-G0-0 | **OQ-1 resolution (CRIT-2 + B3 amendment): VN PDPD / TH PDPA data residency determination for LLM API calls.** Written determination required: (a) Does routing pseudonymized patient health data to a US-hosted LLM API constitute regulated cross-border transfer under VN Decree 13/2023/ND-CP and TH PDPA? (b) If yes: is there a compliant provider with VN/TH regional endpoint? **If no compliant path: LLM integration is a feature architecture blocker.** OQ-1 must be resolved before any P1 work begins on LLM integration. LLM-independent P1 deliverables (Data Collector, Delta Analyzer, Consent model, Pseudonymization, Audit log, Idempotency, Pipeline atomicity) may begin in parallel with OQ-1 resolution. **Contingency paths: Path A (favorable):** US-hosted provider with BAA is compliant; proceed with AC 2.4 provider selection. **Path B (adverse):** In-country or regional LLM deployment required; extends P1 timeline by 4–8 weeks; provider selection, BAA renegotiation, and compliance gate re-test against alternative model required. | Legal | Open |
| P1-G0-1 | LLM provider BAA signed (provider determined after OQ-1 resolution at P1-G0-0). LLM integration work begins ONLY after this gate AND P1-G0-0. LLM-independent deliverables may proceed before this gate. | Legal | Open |
| P1-G0-2 | **Combined ElfieCare capacity commitment (B2 + PM-C4 amendment):** ElfieCare engineering team confirms a single consolidated capacity plan covering **Component 2 (4 deliverables) + Component 3 (5 deliverables) = 9 ElfieCare deliverables total**, with sprint sequencing, individual deliverable estimates, and delivery milestones for both features. A commitment obtained without Component 2 scope visible to ElfieCare EM is not valid. **Before P1-G0-2 closes, Product must confirm the "viewed" boundary definition for the summary retraction API deliverable (e) — specifically, whether `viewed_at = null` (Available/Snoozed/Dismissed without View click) = unviewed for retraction purposes (V3-C5/PM-C4 amendment). ElfieCare EM's effort estimate for deliverable (e) depends on this definition.** | ElfieCare EM + Product | Open |
| P1-G0-3 | Elfie Mobile team confirms: capacity for patient consent flow, Settings → Privacy → Shared with Doctors UI, and patient summary history view (AC 5.7). | Elfie Mobile EM | Open |
| P1-G0-4 | System prompt v1 reviewed and approved by Medical Affairs and Legal. | Medical Affairs + Legal | Open |
| P1-G0-5 | Prohibited terms list v1 reviewed and approved by Medical Affairs and Legal. | Medical Affairs + Legal | Open |
| P1-G0-6 | **Medical Affairs capacity confirmation (B4 amendment):** Named Medical Affairs reviewer(s) confirmed with review turnaround SLAs for each engagement type: (a) system prompt / prohibited terms review: ≤5 business days; (b) copy review (consent modal, disclaimer, acknowledgment language): ≤3 business days; **(c) system prompt version change reviews post-launch (V3-C2/PM-C3 amendment): ≤5 business days per update, allocated MA capacity in deployment planning;** (d) post-launch monthly sample review: allocated in MA calendar before launch. Reconciled against Component 1 and Component 2 MA review obligations. | Medical Affairs Lead | Open |
| P1-G0-7 | **Coin events consent legal opinion (HIGH-7 amendment):** Written Legal opinion confirming that aggregate engagement scores derived from coin event frequency are (or are not) sensitive personal data under VN PDPD and TH PDPA, and whether explicit consent is required. Coin events category added to patient consent flow at MVP regardless (toggle ON by default per AC 1.3 amendment). | Legal | Open |
| P1-G0-8 | **Week 0 milestone map (B1 amendment):** Project Manager produces and circulates a Week 0 milestone map showing P1/P2/P3 start dates and serialized dependencies, OQ-1 resolution deadline, ElfieCare integration windows, MA review slots, OQ-1 contingency fork (Path A vs. Path B timelines), and P3-G5 staged rollout cohort selection criteria. Map reviewed by Technical Advisor and Product Lead before P1-G1 begins. | Project Manager | Open |

**P1 track deliverables:**

- Data Collector: fetch pipeline for all 6 data categories, period calculation, consent gating
- Delta Analyzer: all computed outputs (AC 1.4); unit test coverage ≥95% of computation logic
- LLM prompt construction: input spec (AC 2.1), PII exclusion enforcement
- Compliance Gate: keyword scan + flag format validation (AC 2.3); test suite covering all prohibited term categories
- Consent data model: schema, API endpoints, revocation pipeline (AC 3.3, AC 3.1)
- Pseudonymization: key-vault integration consistent with Component 2 (AC 5.2)
- Audit log schema and write path (AC 5.4)
- Idempotency key computation and enforcement (AC 6.2)
- Pipeline atomicity and failure handling (AC 6.1)

---

### P2 — Integration & Delivery (gate: P2-G0)

**P2-G0 Gate: before ElfieCare integration begins**

| # | Item | Owner | Status |
|---|---|---|---|
| P2-G0-1 | P1 pipeline runs end-to-end in staging with synthetic patient data; all P1 unit and integration tests passing | Engineering Lead | Open |
| P2-G0-2 | EU AI Act documentation set complete: risk management, technical documentation, data governance, human oversight mechanism (AC 5.6) | Technical Advisor + Legal | Open |
| P2-G0-3 | OQ-1 Path A confirmed (resolved at P1-G0-0); data residency path confirmed in architecture | Legal + Engineering | Open |
| P2-G0-4 | ElfieCare API contract finalized (inbound summary endpoint, acknowledgment endpoint, delivery confirmation endpoint) | Elfie Backend + ElfieCare Backend | Open |

**P2 track deliverables:**

- ElfieCare integration: summary card UI, acknowledgment flow, doctor deactivation (AC 4.1, AC 3.2, AC 4.4)
- PDF export generation (AC 4.2)
- On-demand regeneration with idempotency cooldown (AC 4.3)
- Scheduled 30-day push pipeline: cron job, eligibility evaluation, batch delivery
- Manual trigger path: API endpoint, loading state, SLA enforcement
- Doctor-facing "Summary unavailable" state
- Elfie Mobile: patient consent flow modal, Settings → Privacy → Shared with Doctors (AC 3.1)
- Consent revocation deletion pipeline with `CONSENT_REVOCATION_DELETION_SLA` enforcement
- Geo-gate enforcement (AC 5.5)
- Operational monitoring metrics emission (AC 6.3)

---

### P3 — Hardening & Launch Preparation (gate: P3-G0 through P3-G5)

**P3-G0: QA and staging validation**

| # | Item | Owner | Status |
|---|---|---|---|
| P3-G0-1 | End-to-end integration tests passing: all AC verification clauses executed in staging | QA | Open |
| P3-G0-2 | Compliance Gate test suite: 100% pass rate on all prohibited term categories | QA + Medical Affairs | Open |
| P3-G0-3 | Consent revocation deletion pipeline tested: pending summary deleted within SLA | QA | Open |
| P3-G0-4 | PDF export tested: disclaimer present, no patient name, content matches in-app card | QA | Open |

**P3-G1: Legal and Medical Affairs final review**

| # | Item | Owner | Status |
|---|---|---|---|
| P3-G1-1 | Doctor acknowledgment language reviewed and approved | Legal + Medical Affairs | Open |
| P3-G1-2 | Summary disclaimer text reviewed and approved | Legal + Medical Affairs | Open |
| P3-G1-3 | Patient consent modal copy reviewed and approved | Legal + Medical Affairs | Open |
| P3-G1-4 | PDF export disclaimer reviewed and approved | Legal + Medical Affairs | Open |
| P3-G1-5 | All product surface copy reviewed against prohibited language list (AC 5.1) | Medical Affairs | Open |

**P3-G2: Security review**

| # | Item | Owner | Status |
|---|---|---|---|
| P3-G2-1 | OWASP review of summary API endpoints (authentication, authorization, injection) | Security | Open |
| P3-G2-2 | Penetration test of patient consent API: verify cross-patient data isolation | Security | Open |
| P3-G2-3 | Audit log tamper-resistance reviewed | Security | Open |
| P3-G2-4 | PDF export: confirm no server-side HTML injection via LLM output | Security | Open |

**P3-G3: Load and reliability testing**

| # | Item | Owner | Status |
|---|---|---|---|
| P3-G3-1 | Load test: 50 concurrent on-demand triggers; P95 ≤ `SUMMARY_GENERATION_SLA` | Engineering | Open |
| P3-G3-2 | Failure injection test: all pipeline failure modes produce correct abort behavior | Engineering | Open |
| P3-G3-3 | Scheduled push batch test: 1,000 synthetic patient-doctor pairs processed in overnight window with scheduled push distribution across `SCHEDULED_PUSH_WINDOW_HOURS` (MED-1 amendment); confirm no LLM API rate limit failures | Engineering | Open |
| P3-G3-4 | VN + TH local SaMD/medical device classification assessment (MED-3 amendment): written opinion from regulatory counsel in both markets confirming feature does not require medical device registration under VN Circular 14/2023/TT-BYT and TH Medical Device Act B.E. 2562 | Legal + Regulatory Counsel | Open |
| P3-G3-5 | Medical liability counsel opinion (MED-4 amendment): legal opinion from VN + TH medical liability counsel confirming disclaimer language and doctor acknowledgment flow is adequate to disclaim clinical obligation in those jurisdictions | Legal + VN/TH Counsel | Open |

**P3-G4: Operational readiness**

| # | Item | Owner | Status |
|---|---|---|---|
| P3-G4-1 | Monitoring alerts configured and tested in staging (AC 6.3) | Engineering | Open |
| P3-G4-2 | Doctor feedback routing operational (AC 6.4) | Engineering + Ops | Open |
| P3-G4-3 | Adverse event escalation path tested (AC 6.4) | Ops + Medical Affairs | Open |
| P3-G4-4 | On-call runbook: summary pipeline failure, compliance gate spike, consent revocation breach. **Runbook must include (PM-C1 amendment): (a) force-deletion escalation path when automated consent revocation pipeline fails (named owner and 4-hour escalation SLA); (b) patient notification decision tree for VN PDPD and TH PDPA compliance in case of SLA breach (including whether breach is self-reportable or requires regulatory authority notification); (c) force-deletion command for manual execution with access-control guard; (d) post-breach review process and timeline.** Runbook content reviewed by Legal before launch. | Engineering + Legal | Open |
| P3-G4-5 | Post-market monitoring plan documented (AC 5.6) | Product | Open |

**P3-G5: Staged rollout**

Launch to a limited cohort: maximum 100 active doctor-patient pairs in VN + TH, all pairs with established doctors who have completed the acknowledgment flow in staging. Full rollout only after:
- Zero compliance gate **misses in delivered summaries** — compliance gate activations (caught failures) are expected; what is being monitored is **false negatives** (prohibited language delivered to physician). During the staged rollout, 100% of delivered summaries must be human-reviewed by Medical Affairs within 48h of delivery to confirm no compliance gate miss. (H2 amendment — 100% human review required in staged rollout; 20/month sample review is post-full-rollout)
- Zero adverse event reports in first 2 weeks
- Summary generation success rate ≥ 97% over the rollout period
- **P3-G5 OQ-7 prerequisite (H4 amendment):** OQ-7 (doctor re-acknowledgment on language update) must be resolved before P3-G5 begins. Resolution must include: (a) Legal ruling on whether invalidation is immediate (all acknowledgments invalidated at update) or lazy (only next interaction); (b) for immediate invalidation path: operational playbook for batch re-acknowledgment campaign, including notification to all affected doctors, UI design for re-acknowledgment prompt, owner, and impact on scheduled push delivery during the re-acknowledgment window. Legal ruling alone is not sufficient — the operational playbook must be approved before staged rollout.

---

## Launch Gate Checklist

All items must be checked before general availability:

- [ ] OQ-1 data residency determination complete (Path A or B confirmed) (P1-G0-0)
- [ ] LLM provider BAA signed and on file (consistent with OQ-1 determination) (Legal)
- [ ] Combined ElfieCare engineering delivery commitment confirmed (Component 2 + Component 3, 9 total deliverables) (ElfieCare EM)
- [ ] System prompt v1 approved by Medical Affairs and Legal
- [ ] Prohibited terms list v1 approved by Medical Affairs and Legal
- [ ] Doctor acknowledgment language approved by Legal and Medical Affairs
- [ ] Patient consent modal copy approved by Medical Affairs
- [ ] Summary disclaimer text approved by Legal
- [ ] PDF disclaimer approved by Legal
- [ ] All product surface copy reviewed against prohibited language list (AC 5.1) — Medical Affairs sign-off
- [ ] EU AI Act documentation set complete (AC 5.6)
- [ ] Data residency assessment complete for VN + TH (OQ-1)
- [ ] OWASP security review complete and findings resolved
- [ ] End-to-end integration test suite 100% passing in staging
- [ ] Compliance Gate test suite 100% passing
- [ ] Load test: P95 on-demand SLA verified
- [ ] Consent revocation deletion pipeline tested within SLA
- [ ] Monitoring alerts configured and tested
- [ ] Doctor feedback routing operational
- [ ] Adverse event escalation path tested
- [ ] On-call runbook reviewed by Engineering Lead
- [ ] Medical Affairs capacity confirmed with named reviewer(s) and review SLAs (P1-G0-6)
- [ ] Coin events consent legal opinion obtained (P1-G0-7)
- [ ] VN + TH SaMD/medical device classification opinion from regulatory counsel (P3-G3-4)
- [ ] VN + TH medical liability counsel opinion on disclaimer adequacy (P3-G3-5)
- [ ] OQ-7 resolved: doctor re-acknowledgment operational playbook approved (P3-G5 prerequisite)
- [ ] AC 5.7 patient summary history view tested and operational
- [ ] 100% human review protocol for staged rollout summaries established with MA
- [ ] Staged rollout plan (P3-G5 criteria) agreed by Product, Engineering, and Medical Affairs
- [ ] Post-market monitoring plan documented

---

## Open Questions

| # | Question | Owner | Impact if unresolved |
|---|---|---|---|
| OQ-1 | Do VN PDPD and TH PDPA require patient health data to be processed in-country? **ESCALATED to P1-G0-0 (CRIT-2 amendment).** Resolution determines LLM provider architecture. **Path A** (favorable): US-hosted provider + BAA compliant. **Path B** (adverse): in-country deployment required; 4–8 week extension; provider re-selection. | Legal | Blocks LLM integration work in P1; LLM-independent deliverables may proceed |
| OQ-2 | What is the ElfieCare patient queue architecture? Does it support a card API model (summary pushed from Elfie backend) or does it poll? Impact on delivery latency design. | ElfieCare Engineering | Affects delivery architecture; must resolve before P2 starts |
| OQ-3 | For scheduled push: how is "last visit date" for a doctor-patient pair determined? Is this available in ElfieCare data? Or does Elfie maintain its own appointment record? | Product + ElfieCare EM | Affects period calculation accuracy (AC 1.2); must resolve before P2-G0 |
| OQ-4 | Should delivered summaries be retained in ElfieCare indefinitely, or should there be a retention policy (e.g., delete after 12 months)? Interaction with audit log retention and patient right to erasure. | Legal + Product | Affects storage design and right-to-erasure scope; must resolve before P3-G1 |
| OQ-5 | If a patient's regular doctor is unavailable and another doctor uses ElfieCare to view the same patient, should that second doctor receive or be able to trigger a summary? Requires consent model extension. | Product | Deferred to v2 if not resolved; default = no: only consented doctor receives summaries |
| OQ-6 | Is PDF export the right fallback for paper clinics, or is encrypted email needed? If email: what delivery security standard applies? | Product | If email is required, it may extend P2 scope; resolve before P2-G0. Note: encrypted email is explicitly **out of scope at MVP** (see Scope — Out); this question is asking whether to change that decision. |
| OQ-7 | After doctor acknowledgment language is updated by Legal, must all existing doctors re-acknowledge before the next scheduled push, or only before the next doctor-initiated action? **Must be resolved before P3-G5 (H4 amendment); requires both legal ruling AND operational playbook covering batch re-acknowledgment campaign, notification design, and delivery impact.** | Legal + Product | Blocks P3-G5 staged rollout if unresolved |
