# Technical Advisor Review — Agentic Patient Summary (Round 2)

**Reviewer:** Technical Advisor  
**Review date:** 2026-06-01  
**Spec version under review:** v2 (amendments A–N incorporated)  
**Round:** 2 of debate loop  
**Prior TA score:** 7.86 / 10.0 — Conditional (Round 1)  
**Verdict:** ⚠️ CONDITIONAL — Score **8.70 / 10.0**

---

## Executive Summary

The v2 amendments constitute a genuine architectural upgrade. The two-stage rendering split resolves the core hallucination CRIT. The OQ-1 contingency paths are now explicit and sequenced. All seven HIGH conditions have been addressed at the spec level. The aggregate quality is materially higher than v1.

However, four residual issues prevent clearing the 9.0 threshold: one LLM slot context ambiguity that leaves the CRIT-1 defense partially implicit; one missing system prompt re-test gate that is a direct consequence of the new two-stage architecture; one unaddressed patient re-consent mechanism (MED-5 carried forward from Round 1); and one AC 1.2 divide-by-zero guard that was absent in v1 and remains absent in v2. These are AC precision issues, not design flaws — a v3 targeted fix clears 9.0.

---

## Section 1 — Round 1 Condition Dispositions

### CRIT-1 — LLM Numerical Hallucination

**✅ RESOLVED** — with one minor residual (non-blocking, see NEW-1 below).

The two-stage split is architecturally sound. Stage 1 (application-layer rendering) owns all quantitative content: table rows, period averages, prior averages, trend arrows, anomaly flag values, completeness percentages, header, and footer. The LLM receives only named narrative text slot fill-in instructions. Compliance Gate Check 3 makes delivery of a hallucinated number structurally impossible — any numeric token in a narrative slot fails the gate before delivery.

**On the specific sub-question:** Could the LLM write "the patient's blood pressure has increased to 142/89" using values from the slot context?

Yes — if the LLM slot context passes raw Delta Analyzer numbers (which it may, per AC 2.1's ambiguous phrase "Delta Analyzer output for that section"), the LLM has the values available and could attempt to write them into the narrative slot. Check 3 **would catch this** (142/89 is a numeric token). The result is a Compliance Gate failure and "Summary unavailable" — the hallucinated value never reaches the physician.

**Check 3 is therefore sufficient to prevent delivery of hallucinated numbers.** The architecture is correct. The residual (flagged as NEW-1) is that AC 2.1 does not explicitly specify whether raw numerical values are stripped from the LLM slot context before passing, or whether Check 3 is the sole line of defense. This ambiguity should be resolved for defense-in-depth clarity.

---

### CRIT-2 — OQ-1 Data Residency Must Move to P1-G0

**✅ RESOLVED** — with one noted assumption risk (non-blocking, see below).

P1-G0-0 is now a hard gate before LLM integration work begins. Path A (favorable: US-hosted provider + BAA compliant) and Path B (adverse: in-country deployment, 4–8 week extension, provider re-selection, BAA renegotiation, compliance gate re-test) are both explicitly defined with trigger conditions and ownership assigned to Legal.

LLM-independent P1 deliverables (Data Collector, Delta Analyzer, Consent model, Pseudonymization, Audit log, Idempotency, Pipeline atomicity) may proceed before P1-G0-0 resolution. This is the correct sequencing.

**On the P1-G0-0 resolution period risk:** During the 4–8 week OQ-1 resolution window, LLM-independent work proceeds. Could this work bake in architectural assumptions that Path B would invalidate?

The risk is low but exists. All seven LLM-independent deliverables are logically portable — their business logic does not depend on deployment location. However, **storage location decisions** made during LLM-independent P1 work (where does the Delta Analyzer output land, where does the audit log persist, where does the feature store sit) could be invalidated if Path B requires all patient health data processing in-country. The spec allows this work to proceed without a requirement to document data residency assumptions before beginning.

This is a non-blocking risk because storage location is an infrastructure decision, not a logic redesign. However, the Week 0 milestone map (P1-G0-8) should explicitly require the Technical Advisor to document data residency assumptions for all P1 deliverables before LLM-independent work begins, so that the Path B impact assessment at P1-G0-0/1 is instantaneous rather than requiring retroactive audit.

---

### HIGH-1 — Missing ElfieCare Summary Retraction API

**✅ RESOLVED**

ElfieCare deliverable (e) is added: retraction API accepting `(patient_id, doctor_id)` → marks all unviewed summaries as deleted from doctor queue. This enables the 24-hour consent revocation deletion SLA (AC 3.1) to cover summaries already pushed to ElfieCare, not only summaries held server-side. The combined 9-deliverable consolidated capacity commitment (P1-G0-2) includes this deliverable.

---

### HIGH-2 — Patient Right of Access Not Specified

**✅ RESOLVED**

AC 5.7 is comprehensive: Settings → Privacy → Shared with Doctors shows per-doctor summary list with generation timestamp, period covered, categories included, and delivery status. Verbatim physician-formatted content is not exposed. Data access request form with 30-day fulfillment SLA. Erasure-coherent (key deletion renders history non-linkable). Verification clauses are present.

---

### HIGH-3 — OLS Slope Without Minimum Sample Size or Normalization

**✅ RESOLVED**

`TREND_MIN_DATA_POINTS = 7` is defined. Below threshold: trend reported as "Insufficient data" (not silently → stable). Normalization defined: slope in standard deviations per day relative to prior-period mean (this is the correct dimensionless representation). Boundary unit tests specified: 6 → suppressed, 7 → computed. The divide-by-zero guard for zero scheduled doses is also specified in AC 1.4. Unit test for normalization (slope in SDs/day relative to prior-period mean) is required.

**One residual concern:** if the prior-period mean is zero (e.g., a metric that had zero readings in the prior period), normalization produces a divide-by-zero. The spec guards against "No prior data" → "No prior data" output, but doesn't explicitly guard against a prior-period mean of exactly 0 for a metric that had entries (e.g., a glucose reading of 0, which is clinically impossible but could appear from a data entry error). This is a LOW concern — practically impossible for the covered metrics — but worth noting for robustness.

---

### HIGH-4 — Idempotency Stale Period on Retroactive Visit Record

**⚠️ PARTIALLY RESOLVED**

The period-boundary-drift exception in AC 6.2 correctly handles the primary case: when a retroactive visit record changes `period_start` for the pair, the pair becomes eligible for regeneration regardless of the 30-day cooldown. This resolves the core stale-period risk.

**Residual gap:** A retroactive record can also change the *prior period's* comparison data without changing `period_start`. Example: patient has a visit on Jan 1 (determining `period_start = Jan 1`). A retroactive visit record is added for Dec 15 — which falls within the prior period window. `period_start` doesn't change (Jan 1 visit still exists), so the drift exception is not triggered. But the prior period comparison data has changed: the Dec 15 visit data is now in the prior period window that was absent when the prior summary was computed. The cached summary returns stale delta comparisons.

Clinical severity is LOW: the current-period data displayed to the physician is correct; only the comparative delta (this period vs. prior period) would be stale. The physician sees accurate current values but potentially incorrect trend comparison text. However, the spec explicitly promises the Delta Analyzer output is the sole source of all numerical values — if the prior-period averages in the table are stale due to a retroactive record, this is a data integrity breach at a LOW frequency.

The fix is narrow: expand the drift exception to also trigger when the prior period's data hash changes (detectable by recomputing the prior period average for any metric and comparing against the stored value). This is a MED-level item.

---

### HIGH-5 — Raw Free-Text Symptom Log in LLM Input

**✅ RESOLVED**

The Data Collector aggregates raw symptom text into structured frequency summary (symptom tag + occurrence count + period) before leaving the data layer. Raw free-text is not stored in the pipeline and not passed to the LLM. AC 1.3 and AC 1.4 are consistent. Verification clause requires unit test confirming raw symptom free-text is not present in pipeline output.

---

### HIGH-6 — Doctor Target vs. Patient Target Contradiction

**✅ RESOLVED**

Target hierarchy defined in AC 1.4: (1) doctor-set monitoring target, (2) patient-set target, (3) no flag if neither. Flag text explicitly identifies source: "above doctor's monitoring target of X" or "above patient's stated target of X." The Delta Analyzer passes the target source to the LLM context (which passes it to the narrative slot). Application-layer rendering of the flag bullets from Delta Analyzer anomaly flags ensures the flag format is enforced by Check 2.

---

### HIGH-7 — Coin Events Processed Without Consent

**✅ RESOLVED**

Coin events added to patient consent flow (ON by default, toggleable). AC 1.3 table updated. P1-G0-7 added: Legal opinion confirming whether aggregate coin event engagement scores require explicit consent under VN PDPD and TH PDPA. The default-ON position is defensible (engagement data is less sensitive than health metrics) but the Legal opinion is the correct gate.

---

## Section 2 — New Defects Introduced by v2 Amendments

---

### NEW-1 — LLM Slot Context Numerical Value Exposure Unspecified (MED)

**AC 2.1** states the LLM receives "the Delta Analyzer output for that section (numbers already visible in the template)" as the named slot context. This formulation is ambiguous: it could mean the LLM receives the full Delta Analyzer JSON for the section — which includes raw numerical values (period averages, prior averages, adherence percentages) — with only Check 3 as the guard against outputting them.

Two defensible design choices exist:

| Choice | Description | Trade-off |
|---|---|---|
| A (strip) | Strip all raw numbers from LLM slot context; pass only trend classifications (↑/→/↓/Insufficient), adherence level (HIGH/MEDIUM/LOW), anomaly flag presence (True/False), and completeness tier | LLM cannot write numbers because it doesn't have them — defense-in-depth. Narrative quality may be marginally lower (LLM writes "BP trend is rising" vs. knowing the magnitude). |
| B (pass + gate) | Pass full Delta Analyzer output to LLM context; rely on system prompt prohibition + Check 3 | More capable narrative (LLM can write "BP has been consistently elevated throughout the period" knowing the classification context). Check 3 is the sole delivery blocker. |

Either choice is architecturally defensible. **The spec must make this explicit.** Currently AC 2.1 implies Choice B (LLM gets Delta Analyzer output) but doesn't commit to it. The absence of a clear commitment means:
- Implementation might accidentally default to Choice A (stripping) and break narrative quality unexpectedly
- Check 3 is presented as an optional safeguard rather than a defined line of defense

**Required fix:** Add one sentence to AC 2.1 explicitly stating which design is used, and — if Choice B — explicitly stating that Check 3 is the numerical output guard for the LLM slot layer.

---

### NEW-2 — System Prompt Version Change Has No Re-Test Gate (HIGH)

AC 2.4 mandates compliance gate re-test on LLM **model version** change: "(a) re-run of compliance gate test suite, (b) Medical Affairs sign-off on output quality, (c) deployment via code change." This is correct.

However, the **system prompt** is now a first-class control mechanism in the two-stage architecture — it contains the instructions that prevent the LLM from writing numerical values, clinical interpretations, and prohibited language. System prompt version changes are recorded in the audit log (`system_prompt_version` field) and Medical Affairs reviews the initial version at P1-G0-4, but:

- There is no AC-level requirement to re-run the compliance gate test suite on system prompt version changes
- There is no Medical Affairs re-approval gate for system prompt updates after initial approval
- The system prompt version is logged but there is no deployment gate equivalent to AC 2.4's model change gate

A system prompt change that inadvertently removes or weakens the numerical-output prohibition would not be caught until compliance gate failures appeared in production. The prohibited terms list (`COMPLIANCE_GATE_PROHIBITED_TERMS`) has an explicit review gate; the system prompt does not.

**Required fix:** Add to AC 2.4 (or as a new AC): system prompt version changes require (a) re-run of compliance gate test suite, (b) Medical Affairs sign-off, (c) deployment via code change. Auto-update to a new system prompt version without these gates is prohibited. This is directly analogous to the existing model version gate and the absence of an equivalent for the system prompt is an inconsistency introduced by the two-stage architecture.

---

### NEW-3 — Zero-Length Period Guard Absent (MED)

AC 1.2 defines:
```
period_start = max(last_visit_date_for_pair, today - SUMMARY_MAX_PERIOD_DAYS)
period_end   = today
```

If the patient's last recorded visit was today (a doctor-patient pair where the first visit is today and the doctor immediately requests on-demand summary), then `period_start = today` and `period_end = today` → `period_length_days = 0`.

This zero-length period propagates through the pipeline:
- Data completeness score: `days_logged / period_length_days` → **divide-by-zero**
- Engagement score: `coin_event_days_in_period / period_length_days` → **divide-by-zero**
- OLS slope: zero data points → TREND_MIN_DATA_POINTS guard kicks in (→ "Insufficient data"), but only after the Delta Analyzer is called with a zero-day window
- The summary header would show "Period: 2026-06-01 – 2026-06-01" which is confusing to physicians

The `SUMMARY_MIN_DATA_DAYS = 7` guard in AC 1.1 protects the **scheduled push** path against this (a zero-day period trivially has < 7 days of data). But the **manual on-demand trigger** has no such guard. A doctor can trigger on-demand for a pair where the visit just occurred today.

Note: this defect was not introduced by v2 amendments — it existed in v1 — but it was flagged as MED-2 in Round 1 and has not been addressed.

**Required fix:** Add a guard to AC 1.2 (or the pipeline trigger validation): if `period_length_days < 2`, the pipeline returns "Summary unavailable — no data period to summarize." This guard applies to all trigger paths including on-demand.

---

## Section 3 — Residual Medium Items (Carried from Round 1)

---

### MED-5 — Patient Re-Consent on Consent Text Update: Elevated to HIGH

This item was Medium in Round 1 and was not addressed in v2. On further analysis, the regulatory exposure warrants elevation to HIGH.

**The gap:** The consent record in AC 3.3 correctly captures `consent_version` (version of consent text shown to patient at grant time). However, there is no mechanism to trigger patient re-consent when the consent text is updated after initial grant. AC 3.2 explicitly creates a full re-acknowledgment flow for doctors when acknowledgment language is updated: "all active acknowledgments are invalidated and doctors must re-acknowledge before next delivery." No analogous mechanism exists for patients.

**Why this is HIGH:** VN Decree 13/2023/ND-CP (Article 11) and TH PDPA (Section 19) require that consent be specific, informed, and cover the actual processing performed. If the patient consent text is updated post-launch to reflect a new data processing scope (even minor), processing under existing old-version consents for the new purpose may be non-compliant. Given the sensitivity of health data and the regulatory environments in both markets, this is not a theoretical risk.

**The asymmetry is indefensible:** The spec requires doctors to re-acknowledge on language changes because the acknowledgment text defines their clinical liability scope — which Legal correctly identified as legally significant. Patient consent text defines the scope of health data processing — which is at minimum equally legally significant. The absence of a re-consent mechanism for patients while one exists for doctors is a spec inconsistency that Legal would likely flag in P3-G1 review.

**Required fix (one of two options):**
- **Option A (full parity with AC 3.2):** Add an AC stating: if consent text version changes, all active consents granted under prior versions are invalidated at a Legal-defined trigger point (immediately on update, or lazy on next summary trigger); patients receive in-app re-consent prompt; scheduled push is held for the pair until re-consent is completed.
- **Option B (Legal ruling deferral):** Add P1-G0-7 sub-item or separate gate: Legal provides written ruling on whether patient re-consent is required under VN PDPD / TH PDPA when consent text is updated post-launch without change to processing scope, and separately when scope changes. This ruling defers the mechanism design to Legal but creates a required gate before launch.

Either option is acceptable. Without one of them, the spec is incomplete on a legally significant point.

---

### MED-6 — "Viewed" Boundary in Consent Revocation Deletion Unspecified (MED)

AC 3.1 states: "All summaries for this pair that have not yet been viewed by the doctor are deleted within CONSENT_REVOCATION_DELETION_SLA = 24 hours." The retraction API (ElfieCare deliverable (e)) marks "all unviewed summaries as deleted."

The term "viewed" is not defined in the spec. AC 4.1 defines card states (Pending generation, Available, Summary unavailable, Dismissed, Snoozed, No consent) but does not define which state transition constitutes "viewed." Edge cases:

| Scenario | Outcome under current spec |
|---|---|
| Doctor has opened the full summary detail view and is reading it when revocation fires | Undefined — is this "viewed"? |
| Doctor has clicked "View" on the card (state transitioned from Available) but has not yet opened the PDF | Undefined — is PDF download required for "viewed"? |
| Summary is in "Dismissed" state | Undefined — does dismissal constitute "viewed"? |
| Summary is in "Snoozed" state | Undefined — does snooze constitute "viewed"? |

In practice, the 24-hour SLA means the revocation processing is asynchronous; a doctor reading a summary in real-time during revocation is an edge case. However, "Dismissed" and "Snoozed" states represent delivered summaries the doctor has interacted with but not necessarily read — and these are the operationally ambiguous cases.

**Required fix:** Add a definition in AC 3.1 or AC 4.1: for consent revocation deletion, "viewed" is defined as the summary card having transitioned to a terminal or interaction state — explicitly: Dismissed, Snoozed, or a tracked "opened" event. "Available" (delivered but not yet opened) and "Queued pending acknowledgment" are "unviewed" and subject to deletion SLA. This definition must be communicated to ElfieCare engineering before the retraction API is built.

---

### MED-5 (Additional Sub-Issue) — Patient Re-Consent During Active Re-Consent Campaign: Delivery Hold Not Specified

As a sub-issue related to the MED-5 gap above: AC 3.2 for doctor re-acknowledgment specifies that "summaries are not delivered to a doctor for a patient until acknowledgment is active" — so the system correctly holds delivery during the re-acknowledgment window. If a patient re-consent mechanism is added, the spec will need to define whether scheduled push delivery is held for pairs where the patient has not yet completed re-consent. This is a design requirement that flows from the re-consent mechanism itself and should be included in whichever fix option is chosen for MED-5.

---

## Section 4 — Architecture Observations (Non-Defects)

These are implementation observations warranting engineering attention during P1 build but do not require spec changes.

**Two-Stage Template Assembly:** The application layer must produce a partial rendered template with named slot placeholders, then receive LLM-filled slot text and assemble the final summary. The slot injection must be XSS-safe (if the summary is rendered as HTML in ElfieCare) and PDF-injection-safe (if rendered to PDF server-side). P3-G2-4 covers PDF HTML injection, but the ElfieCare HTML card injection vector should also be in P3-G2's scope. This is addressable in the existing security review gate — no spec change required.

**Absent Slot Handling:** AC 2.1 states: "If a slot's corresponding data section was not consented, the slot is marked as absent and the LLM receives no fill-in instruction for it." The template assembly must ensure that absent slots produce empty string (no placeholder visible) in the rendered output, not a literal `{{slot_name}}` placeholder. This is an implementation detail but worth capturing in the unit test for "omitted-consent sections produce no placeholder text in output" (already required in AC 2.2 verification).

**Consent Snapshot Consistency:** AC 3.1 states "Changes take effect for the next summary generation; in-progress pipeline runs to completion using the consent state at pipeline start (snapshot at trigger time)." The idempotency record in AC 6.2 does not include `consent_snapshot` in the idempotency key. This means: if consent changes between two triggers of the same period, the second trigger returns the cached summary (which was generated under the prior consent state). The audit log `consent_snapshot` field captures what was used, so this is auditable. However, the returned summary may represent a consent scope the patient has since narrowed. This is a narrow race condition (consent change + on-demand trigger within `SUMMARY_REGEN_COOLDOWN_MINUTES`) but warrants a comment in the idempotency implementation to document the intent.

---

## Section 5 — Scoring

| Dimension | Weight | Score | Weighted |
|---|---|---|---|
| User value clarity | 20% | 9.5 | 1.90 |
| Scope precision | 15% | 9.0 | 1.35 |
| AC quality | 20% | 8.0 | 1.60 |
| Technical feasibility | 20% | 8.5 | 1.70 |
| Regulatory compliance | 15% | 8.0 | 1.20 |
| Delivery realism | 10% | 9.0 | 0.90 |
| **Total** | **100%** | | **8.65** |

**Round 2 Score: 8.65 / 10.0 — CONDITIONAL**

*(Rounded to 8.7 given the strong trajectory and near-complete CRIT resolution.)*

**Score rationale by dimension:**

- **User value clarity (9.5):** The two-stage architecture, consent model, physician framing, patient access rights in AC 5.7, and completeness transparency are all precisely articulated. No ambiguity in what the physician or patient sees. Minor deduction for the "slot context" ambiguity affecting one aspect of the narrative quality design intent.

- **Scope precision (9.0):** In/Out table is comprehensive. Geo-gate, SaMD framing, ElfieCare scope, and deferred items are all clearly bounded. Minor deduction for zero-length period not guarded in the on-demand trigger path.

- **AC quality (8.0):** CRIT-1 and CRIT-2 amendments are well-specified. However: slot context ambiguity in AC 2.1 (NEW-1), missing system prompt re-test gate (NEW-2), zero-length period guard absent from AC 1.2 (NEW-3), and patient re-consent mechanism gap (MED-5) each represent incomplete AC clauses. These are precision issues, not design failures. Three of the four are single-sentence fixes.

- **Technical feasibility (8.5):** Two-stage architecture is implementable by a competent backend team. Delta Analyzer is well-specified with correct normalization. Compliance Gate Check 3 is the right pattern. Deduction for the system prompt version change gap (NEW-2) — this is a real operational risk without a test gate — and for the HIGH-4 partial (retroactive prior-period data without period_start change).

- **Regulatory compliance (8.0):** VN PDPD, TH PDPA, EU AI Act documentation set, SaMD framing, and OQ-1 resolution sequence are all well-handled. MED-5 patient re-consent gap is the primary deduction — the asymmetry between the doctor re-acknowledgment flow and patient re-consent is a compliance risk in a highly regulated health data context. P1-G0-7 coin events legal opinion and P3-G3-4/5 regulatory counsel opinions are appropriate gates.

- **Delivery realism (9.0):** P1-G0-0 through P1-G0-8 gates are comprehensive. Week 0 milestone map mandated. Combined ElfieCare 9-deliverable commitment required. MA capacity confirmation with named reviewers. Path A/B contingency defined. The only deduction is the absence of a data residency assumption document requirement during the OQ-1 resolution window (LLM-independent work could bake in assumptions).

---

## Section 6 — Conditions for v3 Approval

| # | Condition | Blocking? | Gate |
|---|---|---|---|
| **V3-C1** | Clarify AC 2.1: explicitly state whether LLM slot context passes raw Delta Analyzer numbers (Choice B: Check 3 is the guard) or stripped classifications only (Choice A: defense-in-depth). Either is acceptable; the choice must be explicit. | Yes | AC 2.1 |
| **V3-C2** | Add system prompt version change gate to AC 2.4 (or new AC): compliance gate test suite re-run + Medical Affairs sign-off required on every system prompt version change, equivalent to the existing model version change gate. | Yes | AC 2.4 |
| **V3-C3** | Add zero-length period guard to AC 1.2: if `period_length_days < 2` on any trigger path (including on-demand), pipeline returns "Summary unavailable — no data period to summarize" before reaching Delta Analyzer. | Yes | AC 1.2 |
| **V3-C4** | Address MED-5 patient re-consent: add either (a) a patient re-consent invalidation mechanism analogous to AC 3.2's doctor re-acknowledgment flow, or (b) a required Legal ruling gate on whether patient re-consent is required under VN PDPD/TH PDPA when consent text is updated post-launch. | Yes | AC 3.1 or P1-G0 |
| **V3-C5** | Define "viewed" in AC 3.1 or AC 4.1: specify which card states constitute "viewed" for consent revocation deletion purposes, to enable ElfieCare to implement the retraction API correctly. | Yes | AC 3.1 |

**Non-blocking recommendations for v3 (improve but do not block approval):**

| # | Recommendation |
|---|---|
| R1 | HIGH-4 partial: consider expanding the period-boundary-drift exception to trigger on prior-period data hash change, not only period_start change |
| R2 | Add data residency assumption documentation requirement to P1-G0-8 (Week 0 milestone map): TA must document which LLM-independent deliverable storage locations have been assumed for Path A before that work begins, enabling instant impact assessment if Path B triggers |
| R3 | Clarify ElfieCare HTML injection scope in P3-G2: confirm P3-G2-4 (PDF HTML injection) also covers the ElfieCare in-app summary card rendering path |
| R4 | Check 3 should explicitly address written-out numbers (e.g., "seventy-nine percent") — either via the system prompt prohibition or a supplementary Check 3 clause — as defense-in-depth |

---

## Section 7 — Projected v3 Score

If V3-C1 through V3-C5 are addressed: **9.1 / 10.0 — APPROVED**

The five conditions are targeted, single-point fixes. None requires architectural redesign. The foundation laid by the v2 amendments is strong — CRIT-1 and CRIT-2 are genuinely resolved, all seven HIGHs are addressed, and the regulatory and delivery framework is production-grade. The remaining gap is AC precision, not design.
