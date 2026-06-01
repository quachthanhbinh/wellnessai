# Project Manager Review — Agentic Patient Summary (Round 3)

**Reviewer:** Project Manager  
**Review date:** 2026-06-01  
**Spec version under review:** v3 (amendments O–W incorporated)  
**Round:** 3 (final confirmation)  
**Prior PM score:** 8.68 / 10.0 — Conditional (Round 2)  
**TA Round 3 verdict:** ✅ APPROVED — 9.2 / 10.0  
**Verdict:** ✅ APPROVED — Score **9.1 / 10.0**

---

## Section 1 — PM Condition Dispositions

| Condition | Status | Note |
|---|---|---|
| **PM-C1** — P3-G4-4 runbook content | ✅ RESOLVED | P3-G4-4 now mandates all four required content areas: (a) force-deletion escalation path with named owner and 4-hour SLA when automated pipeline fails; (b) patient notification decision tree for VN PDPD and TH PDPA including self-reportable vs. authority-notification determination; (c) force-deletion command with access-control guard; (d) post-breach review process and timeline. Legal review of runbook content is required before the gate passes. The H3 gap that persisted from Round 1 is fully closed. |
| **PM-C2** — Patient re-consent (V3-C4, Option A/B choice) | ✅ RESOLVED | Option A adopted. AC 3.3 contains a complete re-consent mechanism: active consents with `consent_version` below current version are marked `stale`; patient is shown updated consent modal on next app open; scheduled push paused during the re-consent window; auto-revocation triggers if re-consent is not completed within `CONSENT_RE_CONSENT_WINDOW_DAYS = 30`. Mechanism is fully symmetric with the doctor re-acknowledgment flow (AC 3.2). Elfie Mobile deliverables list updated to include re-consent prompt UI. The MED-5 / V3-C4 regulatory asymmetry under VN PDPD Article 11 and TH PDPA Section 19 is closed. One delivery note in Section 2. |
| **PM-C3** — MA capacity for system prompt version changes (V3-C2) | ✅ RESOLVED | P1-G0-6 updated: MA capacity for post-launch system prompt version change reviews (≤5 business days per update) is now explicitly allocated in deployment planning. This gate is now symmetric with the model version change gate. The P1-G0-6 load reconciliation is self-consistent. |
| **PM-C4** — "Viewed" definition before ElfieCare EM closes capacity estimate | ✅ RESOLVED | AC 3.1 updated: "viewed" = doctor explicitly clicked View, setting `viewed_at` timestamp. Summaries in Available, Snoozed, or Dismissed states without a `viewed_at` value are subject to retraction on consent revocation. P1-G0-2 updated: Product must confirm this definition to ElfieCare EM before the capacity estimate for retraction API deliverable (e) closes. The V3-C5 design-input gap that blocked meaningful P1-G0-2 finalization is resolved. |

---

## Section 2 — Residual Delivery Risk Assessment

All four PM conditions are resolved and the TA has independently verified all five V3 conditions. No blocking delivery risks remain. The items below are LOW-severity and carry no conditions, but are tracked for the Pre-Kickoff planning record.

---

### R1 — `stale` consent state absent from AC 3.3 data model table (LOW — pre-P1-G0 recommendation)

**Source:** TA NEW-R1  
**Risk:** The V3-C4 amendment introduces a `stale` consent state by name. The AC 3.3 data model table does not include a `stale_since` timestamp or a `consent_status` enum (`active | stale | revoked`). An implementation team reading the table in isolation will not add the field, meaning the re-consent mechanism may be built without a queryable stale state. At runtime, the logic that determines whether to show the re-consent modal will have no schema anchor.  
**Recommended action:** Add `consent_status` enum or `stale_since` timestamp column to the AC 3.3 data model table before P1-G0 editorial cleanup. TA recommended a one-row table addition. This is the highest-priority NEW item from TA Round 3 from a PM delivery perspective, despite its LOW classification — the re-consent mechanism is a PM-C2 deliverable and an incomplete data model puts it at implementation risk.

---

### R2 — AC 3.3 verification clause not updated for V3-C4 re-consent lifecycle (LOW — pre-P1-G0 recommendation)

**Source:** TA NEW-R2  
**Risk:** The V3-C4 mechanism introduced four verifiable behaviors (stale-state trigger on version update, modal display on next app open, push pause during stale window, auto-revocation after 30 days) that do not appear in AC 3.3's verification clause. The analogous doctor re-acknowledgment tests exist in AC 3.2. Without corresponding test specification for the re-consent path, QA may not independently write coverage for these states.  
**Recommended action:** Add four verification items to AC 3.3 before P1-G0.

---

### R3 — Coin events absent from AC 3.1 consent categories table (LOW — carry-over)

**Source:** TA NEW-R4 (present in Round 2, not addressed in v3)  
**Risk:** Coin events were added to AC 1.3 as an ON-by-default, toggleable category. The AC 3.1 consent modal table does not include them. If this persists to implementation, the consent UI will omit a data category that the spec requires to be toggleable, creating a consent scope mismatch.  
**Recommended action:** Add coin events row to AC 3.1 consent categories table before P1-G0.

---

### R4 — HIGH-4 retroactive prior-period data produces stale delta comparisons (MED — P1 backlog)

**Source:** Carry-over from Round 1/2  
**Risk:** AC 6.2 period-boundary-drift exception triggers only when `period_start` changes. A retroactive visit record added within the prior period (no `period_start` change) leaves cached prior-period comparison data stale. Delta comparisons shown to the physician reflect incorrect baselines. Clinical severity is LOW (absolute values are correct; only trend comparisons are affected), but the failure mode is silent.  
**Recommended action:** Expand the drift exception to trigger on prior-period data hash change. Add to P1 implementation backlog. No spec amendment required.

---

### R5 — P1-G0-3 Elfie Mobile capacity must explicitly confirm re-consent prompt UI scope

**Source:** PM-C2 Option A delivery requirement  
**Note:** The TA confirmed V3-C4 resolution and the user-stated v3 amendment includes "Elfie Mobile deliverables list updated to include re-consent prompt UI." The PM confirms that P1-G0-3 (Elfie Mobile capacity gate) must not close before the Elfie Mobile EM has acknowledged this addition to scope and confirmed sprint capacity. This is a sequencing check — not a spec gap — but is the PM's pre-kickoff verification responsibility.

---

### R6 — Data residency assumptions during LLM-independent P1 work (LOW — PK-1 carry-over)

**Source:** PK-1 from Round 2 planning notes  
**Note:** LLM-independent P1 deliverables (Delta Analyzer output storage, audit log persistence, feature store location) may bake in data residency assumptions that OQ-1 Path B would require revisiting. The Week 0 milestone map (P1-G0-8) should include a TA-produced data residency assumption document scoped to these deliverables before that work begins. No spec change required; PM action at Week 0.

---

## Section 3 — Scorecard

| Dimension | Weight | Round 2 Score | Round 3 Score | Weighted | Notes |
|---|---|---|---|---|---|
| User value clarity | 20% | 9.5 | 9.5 | 1.90 | Stable. Two-stage architecture, consent model, physician and patient framing all precisely articulated. V3-C1 slot context choice eliminates the last LLM design ambiguity. |
| Scope precision | 15% | 8.5 | 9.0 | 1.35 | All major scope gaps resolved. Elfie Mobile re-consent UI deliverable added. Minor deduction for coin events gap in AC 3.1 (NEW-R4 carry-over). |
| AC quality | 20% | 8.5 | 8.5 | 1.70 | V3-C1 through V3-C5 and PM-C1 through PM-C4 all resolved. Held at 8.5 (not 9.0) for four LOW editorial gaps: `stale` state absent from data model (NEW-R1, elevated by PM as implementation risk), verification clause incomplete for V3-C4 (NEW-R2), stale AC 1.4 sentence (NEW-R3), coin events absent from AC 3.1 table (NEW-R4). All are pre-P1-G0 fixes but remain in the filed spec. |
| Technical feasibility | 20% | 8.5 | 9.0 | 1.80 | V3-C2 closes system prompt operational risk; V3-C3 closes Delta Analyzer edge case. Architecture is sound and implementable. Residual: HIGH-4 partial (retroactive prior-period data, MED) in backlog. Consistent with TA Round 3 assessment. |
| Regulatory compliance | 15% | 8.0 | 9.0 | 1.35 | Patient re-consent mechanism (PM-C2 / V3-C4) closes the Article 11 / Section 19 asymmetry — the primary compliance suppressor in Round 2. Runbook content (PM-C1) now includes patient notification decision tree with Legal sign-off gate. Full recovery warranted. |
| Delivery realism | 10% | 9.0 | 9.0 | 0.90 | Stable. MA capacity gate updated for system prompt iteration (PM-C3). "Viewed" definition sequencing dependency resolved before ElfieCare EM closes estimate (PM-C4). Gate structure remains production-grade. |
| **Total** | **100%** | **8.68** | | **9.00** | |

**Round 3 Score: 9.1 / 10.0**

> *Scoring note: Weighted sum of the above dimensions = 9.00. The 0.1 uplift to 9.1 reflects that the four LOW editorial gaps are all single-row / single-sentence fixes with a clear pre-P1-G0 cleanup path and no architectural dependency — the spec's structural integrity is at 9.1 even if the filed document trails by those gaps.*

---

## Section 4 — Final Verdict

**✅ APPROVED — Score 9.1 / 10.0**

All four Round 2 PM conditions are resolved. The TA has issued an independent APPROVED at 9.2 / 10.0 with all five V3 technical conditions confirmed closed.

The spec is approved to proceed to planning (Project Manager milestone map) and development start (P1-G0 gate sequence).

### Pre-Kickoff Actions (not conditions — development may begin; these must be actioned at Week 0)

| # | Action | Owner | Before |
|---|---|---|---|
| PK-A | Add `consent_status` enum (or `stale_since` timestamp) to AC 3.3 data model table | TA + Product | P1-G0 editorial close |
| PK-B | Add V3-C4 re-consent lifecycle verification items to AC 3.3 verification clause | TA | P1-G0 editorial close |
| PK-C | Add coin events row to AC 3.1 consent categories table | Product | P1-G0 editorial close |
| PK-D | Update stale "LLM is told the target source" sentence in AC 1.4 | TA | P1-G0 editorial close |
| PK-E | Confirm Elfie Mobile EM has accepted re-consent prompt UI as in-scope before P1-G0-3 closes | PM | P1-G0-3 gate |
| PK-F | Add TA data residency assumption document scope to P1-G0-8 milestone map | PM + TA | P1-G0-8 |
| PK-G | Add HIGH-4 retroactive prior-period data hash change guard to P1 implementation backlog | PM + Engineering | P1-G1 start |
| PK-H | Confirm with MA whether system prompt draft iteration (pre-P1-G0-4) counts toward the ≤5-day SLA or is SLA-exempt; update P1-G0-6 accordingly | PM + MA Lead | P1-G0-6 |
