# Technical Advisor Review — Agentic Patient Summary (Round 3)

**Reviewer:** Technical Advisor  
**Review date:** 2026-06-01  
**Spec version under review:** v3 (amendments O–W from TA+PM Round 2 incorporated)  
**Round:** 3 (final confirmation)  
**Prior TA score:** 8.70 / 10.0 — Conditional (Round 2)  
**Verdict:** ✅ APPROVED — Score **9.2 / 10.0**

---

## Section 1 — V3 Condition Dispositions

| Condition | Status | Note |
|---|---|---|
| **V3-C1** — AC 2.1 slot context design choice | ✅ RESOLVED | Choice A (strip numbers) explicitly adopted. AC 2.1 now states: LLM slot context contains only trend classifications (↑/→/↓/Insufficient), patient's primary condition, and period dates. Raw Delta Analyzer numerical values are explicitly excluded with a named design rationale. Check 3 (numerical token detection) is retained as defense-in-depth. The LLM has no numbers to copy from context, making hallucination structurally impossible even if system prompt instructions are not followed. Both the design choice and its rationale are unambiguous. |
| **V3-C2** — System prompt version change gate | ✅ RESOLVED | AC 2.4 updated with `System prompt version pinning (V3-C2 amendment)`. System prompt updates now require (a) compliance gate test suite re-run against updated prompt, (b) Medical Affairs sign-off ≤5 business days, (c) deployment via code change. Auto-update prohibited. System prompt version is logged per summary in the audit log (`system_prompt_version` field in AC 5.4). P1-G0-6 updated to allocate MA capacity for post-launch system prompt reviews (PM-C3 co-amendment). The gate is now symmetric with the model version change gate — the gap identified in NEW-2 is closed. |
| **V3-C3** — Zero-length period guard | ✅ RESOLVED | AC 1.2 updated with `SUMMARY_MIN_PERIOD_DAYS = 3`. If `(period_end - period_start) < 3 days` on any trigger path (including on-demand), pipeline returns `"Summary unavailable — insufficient data period"` before reaching Delta Analyzer. Guard applies universally — not only to scheduled push. The threshold of 3 days is more conservative than the minimum fix required (which was `< 2 days` to guard divide-by-zero only); this is a reasonable clinical data quality floor. A 0-, 1-, or 2-day period produces no summary. A 3-day period may produce all-"Insufficient data" trend directions (below the 7-point OLS minimum), but the data completeness and engagement scores compute cleanly — no divide-by-zero. |
| **V3-C4** — Patient re-consent on consent text update | ✅ RESOLVED | AC 3.3 updated with full re-consent mechanism. On `CONSENT_TEXT_VERSION` update: active consents with `consent_version` < current version are marked `stale`. On next patient app open: updated consent modal displayed; scheduled push paused until re-consent. If not re-consented within `CONSENT_RE_CONSENT_WINDOW_DAYS = 30` days: treated as revocation; consent revocation pipeline (AC 3.1) runs. The mechanism is symmetric with the doctor re-acknowledgment flow (AC 3.2) — full parity is now in place. The MED-5 regulatory asymmetry under VN PDPD Article 11 / TH PDPA Section 19 is closed. |
| **V3-C5** — Define "viewed" boundary for retraction API | ✅ RESOLVED | AC 3.1 updated with precise definition: "Viewed" = doctor explicitly clicked "View" to open full summary content = `viewed_at` timestamp set. Summaries in Available, Snoozed, or Dismissed states where doctor did not click View have `viewed_at IS NULL` and are subject to retraction on consent revocation. P1-G0-2 updated to require Product to confirm this definition to ElfieCare EM before the capacity estimate for deliverable (e) closes (PM-C4 co-amendment). The definition is implementable, testable, and communicated to the correct delivery dependency. |

---

## Section 2 — PM Co-Condition Dispositions

| Condition | Status | Note |
|---|---|---|
| **PM-C1** — P3-G4-4 runbook content | ✅ RESOLVED | P3-G4-4 updated. Runbook must include: (a) force-deletion escalation path with named owner and 4h SLA when automated revocation pipeline fails; (b) patient notification decision tree for VN PDPD and TH PDPA compliance on SLA breach (including self-reportable vs. regulatory-authority-notification determination); (c) force-deletion command for manual execution with access-control guard; (d) post-breach review process and timeline. Runbook content reviewed by Legal before launch. Content is operationally complete. |
| **PM-C3** — P1-G0-6 MA capacity for system prompt changes | ✅ RESOLVED | P1-G0-6 updated: MA capacity for post-launch system prompt version change reviews (≤5 business days per update) is now explicitly allocated in deployment planning. See V3-C2 disposition above. |
| **PM-C4** — "viewed" definition before ElfieCare EM closes capacity estimate | ✅ RESOLVED | P1-G0-2 updated: Product must confirm the `viewed_at = null` → unviewed definition to ElfieCare EM before P1-G0-2 closes. See V3-C5 disposition above. |

---

## Section 3 — New Defects Introduced by v3 Amendments

No CRIT or HIGH defects are introduced by the v3 amendments. Four LOW editorial gaps are noted below.

---

### NEW-R1 — `stale` consent state not reflected in AC 3.3 data model table (LOW)

The V3-C4 amendment introduces a `stale` consent state ("active consents … are marked as stale at update time"). However, the AC 3.3 consent data model table does not include a field or status value representing this state. The existing fields are: `consent_id`, `patient_id`, `doctor_id`, `categories_enabled`, `granted_at`, `last_modified_at`, `revoked_at`, `consent_version`.

The `stale` state is implied by the mechanism text but is not represented in the schema. An implementation team relying on the table alone would not add the field.

**Recommended fix (non-blocking):** Add either a `stale_since` timestamp (null if not stale) or a `consent_status` enum field (`active | stale | revoked`) to the AC 3.3 data model table. This is a one-row addition to an existing table.

---

### NEW-R2 — AC 3.3 verification clause not updated for V3-C4 re-consent mechanism (LOW)

The verification clause for AC 3.3 covers the original consent schema only. It does not include tests for the re-consent mechanism introduced by V3-C4:

- Test confirming active consent records with `consent_version` < `CONSENT_TEXT_VERSION` are marked `stale` on version update
- Test confirming patient app displays updated consent modal on next open when consent is `stale`
- Test confirming scheduled push is paused while consent is `stale`
- Test confirming non-re-consent after `CONSENT_RE_CONSENT_WINDOW_DAYS = 30` triggers consent revocation pipeline

**Recommended fix (non-blocking):** Add four verification items to AC 3.3 covering the stale-consent lifecycle. Analogous tests exist for the doctor re-acknowledgment flow (AC 3.2 verification).

---

### NEW-R3 — AC 1.4 "LLM is told the target source" is stale (LOW)

AC 1.4 states: *"The Delta Analyzer does NOT perform clinical inference. The LLM is told the target source in the prompt context."*

This sentence was written when the LLM was involved in generating flag text. Under the V3-C1 design (Choice A: numbers stripped), the LLM slot context contains only trend classifications, patient condition, and period dates. Anomaly flags are rendered entirely by the application layer (Check 2 validates their format). The LLM does not receive, reference, or generate flag content — so passing the target source to the LLM is neither needed nor consistent with AC 2.1.

The sentence is technically harmless (it simply won't be in the slot context payload) but is misleading to implementers reading AC 1.4 in isolation.

**Recommended fix (non-blocking):** Remove or update the sentence in AC 1.4 to: *"The Delta Analyzer does NOT perform clinical inference. Anomaly flag text is generated by the application layer, not the LLM (AC 2.2); the flag text explicitly identifies the target source."*

---

### NEW-R4 — Coin events category absent from AC 3.1 consent modal table (LOW, carry-over)

The coin events category was added to AC 1.3 as "ON by default, toggleable" (HIGH-7 amendment), but the AC 3.1 consent categories defaults table does not include it. The table lists Vitals, Medication adherence, Physical activity, Symptom logs, Lab results, and AI Coach conversations. Coin events are absent.

This means the consent modal description in AC 3.1 does not show coin events as a configurable option, which is inconsistent with AC 1.3. This gap was present in Round 2 and remains in v3.

**Recommended fix (non-blocking):** Add coin events row to the AC 3.1 consent categories table: `Coin events (engagement proxy) | ON by default | Toggle in consent flow and Settings`.

---

## Section 4 — Carry-Over Items (Non-Blocking, Not V3 Conditions)

These items were non-blocking in Round 2 and have not been addressed. They are re-stated for the planning record.

**HIGH-4 partial — Retroactive prior-period data (MED):** AC 6.2 period-boundary-drift exception triggers only when `period_start` changes. A retroactive visit record added within the prior period (without changing `period_start`) leaves the cached prior-period comparison data stale without triggering regeneration. The physician sees correct current-period data but potentially incorrect prior-period deltas. Clinical severity is LOW (only delta comparisons affected, not absolute values). The narrow fix — expand the drift exception to also trigger when a prior-period data hash changes — remains recommended for the P1 implementation backlog.

**OLS prior-period mean = 0 (LOW):** If a metric has a prior-period mean of exactly zero (theoretically impossible for covered metrics but possible from data entry error), the normalization calculation in AC 1.4 produces a divide-by-zero. A guard (`if prior_period_mean == 0: skip normalization, classify slope as "Insufficient data"`) is recommended as an implementation-level safeguard.

---

## Section 5 — Architecture Observations (No Spec Changes Required)

**V3-C1 narrative quality trade-off (confirmed):** By stripping numbers from the LLM slot context, the LLM writes purely qualitative narrative ("blood pressure trend has been consistently rising throughout the period"). It cannot write magnitude-qualified narrative ("blood pressure has risen by approximately 8 mmHg"). This is the correct trade-off — the physician sees exact values in the application-layer rendered table directly above the narrative slot; the narrative's role is trend framing, not numerical reporting. No spec change required.

**Re-consent and on-demand trigger interaction:** V3-C4 specifies that scheduled push is paused while consent is `stale`. On-demand trigger behavior during the `stale` window is not explicitly specified. Reasonable interpretation: on-demand trigger should also be blocked during the `stale` window (since the patient's effective consent scope is under review). This is an implementation assumption worth confirming during P1 build, but does not require a spec amendment.

**ElfieCare retraction API `viewed_at = null` filter:** The retraction API (deliverable (e)) must delete summaries where `viewed_at IS NULL` for the given `(patient_id, doctor_id)` pair. This filter logic is now fully specified by V3-C5. The integration test in AC 3.1 ("pending summary deleted within SLA") should be extended to confirm the retraction API correctly leaves summaries with non-null `viewed_at` intact. This is an implementation detail; the spec intent is clear.

---

## Section 6 — Scoring

| Dimension | Weight | Round 2 Score | Round 3 Score | Weighted |
|---|---|---|---|---|
| User value clarity | 20% | 9.5 | 9.5 | 1.90 |
| Scope precision | 15% | 9.0 | 9.5 | 1.43 |
| AC quality | 20% | 8.0 | 9.0 | 1.80 |
| Technical feasibility | 20% | 8.5 | 9.0 | 1.80 |
| Regulatory compliance | 15% | 8.0 | 9.0 | 1.35 |
| Delivery realism | 10% | 9.0 | 9.0 | 0.90 |
| **Total** | **100%** | **8.70** | | **9.18** |

**Round 3 Score: 9.2 / 10.0 — APPROVED**

---

**Score rationale by dimension:**

- **User value clarity (9.5, unchanged):** V3-C1 removes the last narrative quality ambiguity by making the slot context design explicit. The two-stage architecture, consent model, physician framing, and completeness transparency are precisely specified. No change to score — the 9.5 round-2 rating already accounted for the near-complete CRIT-1 resolution.

- **Scope precision (9.5, +0.5):** V3-C3 closes the zero-length period gap that was the primary scope precision deduction in Round 2. The only remaining scope gap is coin events absent from AC 3.1 consent table (NEW-R4, LOW editorial). Score increase of 0.5 is warranted.

- **AC quality (9.0, +1.0):** All five V3 conditions are resolved at the AC level. The residual deduction is for four LOW editorial gaps (NEW-R1 through NEW-R4): `stale` state not in data model, verification clause not updated for V3-C4, stale AC 1.4 sentence, and coin events absent from AC 3.1 table. None are implementation-blocking, but all represent spec precision shortfalls. Score increase of 1.0 reflects full resolution of the blocking AC gaps.

- **Technical feasibility (9.0, +0.5):** V3-C2 closes the system prompt version change operational risk. V3-C3 closes the Delta Analyzer divide-by-zero. Remaining deductions: HIGH-4 partial (retroactive prior-period data, MED carry-over) and prior-period mean=0 edge case (LOW). The architecture is technically sound and implementable by a competent team. Score increase of 0.5 reflects closure of the primary technical risk items.

- **Regulatory compliance (9.0, +1.0):** V3-C4 resolves the material compliance asymmetry under VN PDPD Article 11 / TH PDPA Section 19. Patient re-consent now has full parity with doctor re-acknowledgment — the most significant regulatory deduction in Round 2 is closed. V3-C5 ensures the retraction API definition reaches ElfieCare before implementation, protecting the 24-hour revocation deletion SLA. Remaining deduction is marginal — coin events in AC 3.1 table (LOW). Score increase of 1.0 is warranted.

- **Delivery realism (9.0, unchanged):** P1-G0-2, P1-G0-6 and P3-G4-4 updates are solid. The OQ-1 resolution window risk (data residency assumptions during LLM-independent work) remains an observation but is not a spec gap. No change.

---

## Section 7 — Final Verdict

**✅ APPROVED — 9.2 / 10.0**

All five V3 conditions (V3-C1 through V3-C5) are fully resolved. All three PM co-conditions (PM-C1, PM-C3, PM-C4) are incorporated. No new CRIT or HIGH defects are introduced by the v3 amendments.

The four new LOW editorial items (NEW-R1 through NEW-R4) are recommended for cleanup before P1-G0 but do not block spec approval or development start. The two carry-over non-blocking items (HIGH-4 partial, prior-period mean=0) are recommended for the P1 implementation backlog.

This spec is approved to proceed to planning (Project Manager) and development start (P1-G0 gate sequence).

**Recommended editorial cleanup before P1-G0 (non-blocking):**
1. Add `stale` state field to AC 3.3 data model table (NEW-R1)
2. Add V3-C4 re-consent lifecycle tests to AC 3.3 verification clause (NEW-R2)
3. Update stale "LLM is told the target source" sentence in AC 1.4 (NEW-R3)
4. Add coin events row to AC 3.1 consent categories table (NEW-R4)
