# Project Manager Review — Predictive Adherence AI (Round 3 — Final Re-Score)

**Reviewer:** Project Manager  
**Review date:** 2026-06-01  
**Spec version under review:** v2 (amended — post TA Round 2 confirmation)  
**Round 2 PM score:** 7.95 / 10.0 — CONDITIONAL (CA-1 through CA-4 unresolved)  
**Verdict:** ✅ APPROVED — Score **9.00 / 10.0**

---

## Executive Summary

All four PM conditional approval items (CA-1 through CA-4) have been confirmed resolved by the Technical Advisor's Round 2 review. The three v2-introduced NM defects (NM-1, NM-2, NM-3) have also been corrected prior to this round. The Technical Advisor's Round 3 review confirms all defects are resolved with no new issues introduced.

This is a clean closure. The spec now meets the 9.0 threshold for full approval. No residual spec conditions remain. Six pre-kickoff planning actions (PK-1 through PK-6) from Round 2 carry forward as project execution responsibilities — they are not spec conditions and do not affect approval status.

---

## Section 1 — CA Condition Resolution Acknowledgement

The four Round 2 PM conditional items were directly mapped to TA HIGH-severity defects. TA Round 2 has confirmed all four as fully resolved.

### CA-1 — Fatigue Cap / ElfieCare Alert Interaction (TA HIGH-7)

**Condition:** Add AC defining whether ElfieCare doctor alerts count against `MAX_INTERVENTIONS_PER_7_DAYS`; define exception path for rapidly deteriorating High-tier users.

**TA Round 2 confirmation:** HIGH-7 RESOLVED.

**PM acknowledgement:** ✅ RESOLVED

The undefined fatigue cap interaction was the most operationally significant of the four conditions — it created a scenario where doctor and patient channels could diverge silently. With the interaction now formally specified in an AC, engineering has a single authoritative rule for both channels. The exception path for deteriorating High-tier users prevents the fatigue cap from blocking clinically important alerts.

---

### CA-2 — Under-18 Profile-Level Exclusion (TA HIGH-6)

**Condition:** Add AC specifying scoring eligibility checked at profile level (not account level); profiles without verifiable DOB excluded by default; under-18 check applied before feature computation.

**TA Round 2 confirmation:** HIGH-6 RESOLVED.

**PM acknowledgement:** ✅ RESOLVED

This was the only open regulatory compliance gap affecting a population the Elfie platform explicitly supports. Profile-level enforcement (rather than account-level) is the correct architectural boundary given Elfie's family account model. The "before feature computation" placement ensures no behavioral data is extracted from excluded profiles. This fix closes the last regulatory compliance spec defect.

---

### CA-3 — Tier Boundary / Intervention Selector Reconciliation (TA HIGH-1)

**Condition:** Reconcile tier boundaries [0.4/0.7] with intervention selector thresholds [0.6/0.75] into a single authoritative table; specify tier enum vs. raw float; remove research doc from normative scope.

**TA Round 2 confirmation:** HIGH-1 RESOLVED.

**PM acknowledgement:** ✅ RESOLVED

This was the sole source of scope precision degradation in Round 2. The conflicting threshold tables would have produced two incompatible engineering implementations, with a product decision forced mid-sprint rather than captured in the spec. The reconciled authoritative table eliminates this ambiguity entirely. Scope precision rises accordingly.

---

### CA-4 — Feature Store SLA Separation (TA HIGH-4)

**Condition:** Separate AC 5.2 into (a) batch throughput in records/second sufficient for the 4-hour window, and (b) online serving P95 applicable only when real-time scoring is added in v2+.

**TA Round 2 confirmation:** HIGH-4 RESOLVED.

**PM acknowledgement:** ✅ RESOLVED

The original AC 5.2 specified a 200ms P95 latency — a meaningful real-time constraint — in a batch scoring context where P95 latency is architecturally irrelevant. The separation removes a performance specification that would have been untestable and meaningless in the batch execution context. Engineering can now correctly measure and gate batch throughput without chasing an inapplicable latency metric.

---

## Section 2 — NM Defect Resolution Confirmation

Three v2-introduced defects (identified in TA Round 2, confirmed fixed prior to this review) are acknowledged below.

### NM-1 — Delivery Failure Suppression Patient Safety Gap (AC 2.3)

**Issue:** When AC 2.3's `non-blocking on failure` applied to High-tier ElfieCare alerts during an active 14-day suppression window, delivery failures could be silently discarded with no retry or operator notification. A patient entering a deterioration pattern could receive no doctor alert and no escalation for up to 14 days.

**Fix:** AC 2.3 amended with single-sentence carve-out: delivery failures for High-tier ElfieCare alerts are logged to the operations queue regardless of suppression state; the suppression window governs new alert generation, not failure retry handling.

**PM acknowledgement:** ✅ RESOLVED — closes the delivery planning risk and the patient safety gap simultaneously. This was the most significant NM item from a regulatory standpoint.

---

### NM-2 — AC 1.5 Label Window End Date Ambiguity

**Issue:** AC 1.5's label window was defined with a clear start cutoff but an implicit end date, allowing label observation windows to vary across scoring batches and producing inconsistent training data construction.

**Fix:** End date explicitly defined in AC 1.5.

**PM acknowledgement:** ✅ RESOLVED — removes a subtle but compounding source of training data inconsistency that would have been difficult to diagnose after model development began.

---

### NM-3 — AC 6.4 HOLDOUT_SALT Immutability

**Issue:** AC 6.4's SHA-256 hash-based holdout assignment relied on a `HOLDOUT_SALT` that had no immutability guarantee. Salt rotation (e.g., during a key rotation event) would reassign cohort membership, invalidating the holdout comparison.

**Fix:** `HOLDOUT_SALT` declared immutable in AC 6.4 with explicit prohibition on rotation.

**PM acknowledgement:** ✅ RESOLVED — cohort stability is now a hard AC requirement, not an implicit assumption. The quarterly treatment vs. holdout comparison retains its validity across retraining cycles.

---

## Section 3 — TA Round 3 Confirmation

The Technical Advisor's Round 3 review confirms:
- All defects resolved (HIGH-1, HIGH-4, HIGH-6, HIGH-7, NM-1, NM-2, NM-3)
- No new issues introduced

**PM acknowledgement:** With no new TA defects and all prior conditions closed, there are no remaining grounds for conditional rather than full approval.

---

## Section 4 — Final Dimension Scores

### User Value Clarity (20%) — Score: 8.5 (unchanged)

The user value proposition is strong and unchanged. The NM-2 label window fix and NM-3 cohort stability fix strengthen confidence in measurement validity, but do not address the two remaining limitations that constrain this dimension.

**Remaining limitations (inherent feature-stage constraints, not spec defects):**
- The "2–3 week advance detection" claim is validated by external research, not internal Elfie data. This will be tested at P1-G6 model validation — the appropriate checkpoint for an offline claim.
- No business-outcome retention improvement target is stated. Technical model performance targets (AUC, Precision@top10%) are specified; a retention lift target was not added.

These are known, accepted constraints for this stage of development. They do not reduce delivery confidence.

---

### Scope Precision (15%) — Score: 9.2 (from 8.0)

CA-3 resolution (HIGH-1) removes the primary deduction from Round 2. The spec now has a single authoritative threshold table with no conflicting reference documents. Combined with the v2 scope specificity already assessed at 8.0 (ElfieCare 4 components, push 3 enhancements, P3 infrastructure baseline, copy 4-type × 2-language matrix, all with named owners), scope precision is now strong.

**Remaining minor gap:** Holdout cohort implementation (scoring-without-intervening logic, quarterly comparison report) is not explicitly listed in the P3 scope line items. This is PK-3 from Round 2 — a low-severity pre-kickoff planning action. It does not constitute a spec defect; the AC 6.4 definition is complete, and the scope line addition is a project plan artifact.

**Delta from Round 2:** +1.2 (HIGH-1 resolution is the full driver)

---

### Acceptance Criteria Quality (20%) — Score: 9.2 (from 7.5)

All four CA conditions resolved, plus three NM fixes — seven AC improvements since the Round 2 score. The resulting AC set covers:

| AC | Fix | Source |
|---|---|---|
| AC 1.5 | Label window start/end, temporal gap, sustained inactivity | CRIT-3 (v2) |
| AC 1.5 | End date precision | NM-2 |
| AC 2.3 | Delivery failure logging for High-tier regardless of suppression | NM-1 |
| AC 2.5 | Push notification payload security | HIGH-9 (v2) |
| AC 3.2 | Bootstrap CI validation for demographic slices | HIGH-3 (v2) |
| AC 4.2 | Key vault pseudonymization | CRIT-2 (v2) |
| AC 5.2 | Batch SLA separated from online serving P95 | CA-4 / HIGH-4 |
| AC 5.3 | Batch atomicity with stale score suppression | HIGH-2 (v2) |
| AC 6.4 | Holdout cohort SHA-256 assignment + HOLDOUT_SALT immutability | CA-3 addendum + NM-3 |
| Fatigue cap rule | ElfieCare alert exception path defined | CA-1 / HIGH-7 |
| Scoring eligibility | Profile-level under-18 check before feature computation | CA-2 / HIGH-6 |

**Remaining minor gap:** Quarterly holdout report format, metrics definition, and ownership are unspecified (PK-3). This is an operational planning item — the reporting artifact is defined post-launch, not a pre-launch AC. Deduction: -0.5 from a 9.5 ceiling driven by the otherwise complete AC coverage.

**Delta from Round 2:** +1.7

---

### Technical Feasibility (20%) — Score: 9.0 (from 7.5)

CA-3 (HIGH-1) and CA-4 (HIGH-4) resolutions remove the two implementation specification conflicts that made the technical feasibility score most uncertain in Round 2. Engineering now has:
- A single authoritative tier/threshold table (no competing reference documents)
- A correctly scoped batch throughput SLA (distinct from online serving P95)
- NM-3 HOLDOUT_SALT immutability (retraining continuity preserved across key rotation events)

**Remaining accepted risks (properly gated, not spec defects):**
- OQ-6 Vietnam PDPD data residency: Gated at P2-G0, quantified at 4–8 week P3 extension. Outside engineering control; correctly handled.
- MLflow Model Registry: Acknowledged greenfield, 4–6 week estimate flagged as unvalidated. Appropriate for spec stage.

**Delta from Round 2:** +1.5

---

### Regulatory Compliance (15%) — Score: 9.2 (from 8.0)

CA-2 (HIGH-6 under-18) and NM-1 (AC 2.3 delivery safety) represent the two regulatory compliance improvements in this round. Together with the v2 fixes already assessed in Round 2 (key vault erasure compliance, delivery confirmation endpoint, ToS re-acceptance mechanism, EU AI Act gate owner), the compliance posture is now robust.

**NM-1 specific regulatory impact:** The original delivery failure suppression gap created a scenario where Elfie sent a health-behavioral alert to a licensed physician with no delivery confirmation during a 14-day suppression window. Depending on jurisdiction, this creates an implied-duty-of-care failure scenario. The AC 2.3 amendment closes this by decoupling delivery retry from suppression state.

**Remaining accepted risk:**
- OQ-6 Vietnam PDPD data residency: Gated at P2-G0. If in-country deployment is required, architecture may require redesign. This is a known, quantified, gated risk — not a spec defect.

**Delta from Round 2:** +1.2

---

### Delivery Realism (10%) — Score: 9.0 (from 8.5)

The delivery framework established in v2 (Week 0 milestone map mandate, 18 named gate owners, gated cross-team dependencies, infrastructure baseline, fallback mechanisms) remains intact. No delivery framework regressions were introduced. NM-1 removes the delivery planning ambiguity around ElfieCare alert failure handling during suppression windows.

**Remaining pre-kickoff risks (execution risks, not spec defects):**
- PK-1: ElfieCare team capacity for 4 deliverables unconfirmed (Week 0 action)
- PK-2: Medical Affairs capacity across 4 touch points unconfirmed (Week 0 action)
- PK-5: OQ-6 fork must appear in Week 0 milestone map (Week 0 action)

These are correctly deferred to Week 0 planning. The spec gates them appropriately; the project plan resolves them.

**Delta from Round 2:** +0.5

---

## Section 5 — Final Score

| Dimension | Weight | Round 2 Score | Round 3 Score | Weighted |
|---|---|---|---|---|
| User value clarity | 20% | 8.5 | 8.5 | 1.70 |
| Scope precision | 15% | 8.0 | 9.2 | 1.38 |
| Acceptance criteria quality | 20% | 7.5 | 9.2 | 1.84 |
| Technical feasibility | 20% | 7.5 | 9.0 | 1.80 |
| Regulatory compliance | 15% | 8.0 | 9.2 | 1.38 |
| Delivery realism | 10% | 8.5 | 9.0 | 0.90 |
| **TOTAL** | **100%** | **7.95** | **9.00** | **9.00** |

**Round 2 → Round 3 delta: +1.05 points** (7.95 → 9.00)  
**Total Round 1 → Round 3 delta: +3.22 points** (5.78 → 9.00)

---

## Section 6 — Verdict

### ✅ APPROVED — Score 9.00 / 10.0

**Threshold met.** No remaining spec conditions.

All 9 Round 1 PM blocking conditions (B1–B9): ✅ Confirmed resolved (Round 2)  
All 4 Round 2 PM conditional items (CA-1 through CA-4): ✅ Confirmed resolved (TA Round 2 + Round 3)  
NM-1 delivery safety gap: ✅ Confirmed resolved (AC 2.3 amendment)  
NM-2 label window end date: ✅ Confirmed resolved  
NM-3 HOLDOUT_SALT immutability: ✅ Confirmed resolved  
New TA defects (Round 3): None  

The spec is approved for planning and P1-G0 kickoff.

---

## Section 7 — Carry-Forward Pre-Kickoff Actions

These items are project execution responsibilities. They are not spec conditions and do not affect approval status. All are required before their respective gates.

| # | Action | Owner | Gate |
|---|---|---|---|
| PK-1 | Confirm ElfieCare team availability and capacity for all 4 deliverables (API, alert card, delivery confirmation, ToS re-acceptance screen); obtain effort estimate and sprint commitment | PM + ElfieCare Engineering Lead | Week 0 (before P2 begins) |
| PK-2 | Confirm Medical Affairs capacity across all 4 project touch points (bias audit review, medication adherence copy, premium card Figma, P1-G1 pre-engagement); flag if concurrent P2/P3 track load creates bottleneck | PM + Medical Affairs Lead | Week 0 |
| PK-3 | Add holdout cohort implementation to P3 scope list (scoring-without-intervening logic, quarterly comparison report); name quarterly report owner | Product Owner | Before P3-G0 |
| PK-4 | Add fallback coin range to AC 7.1 (e.g., "15–30 coins, final amount subject to economy owner approval at pre-launch Gamification Economy Review") | Product Owner | Before P2-G3 |
| PK-5 | Include OQ-6 timeline fork (base vs. +4–8 week data residency extension) in Week 0 milestone map; brief all stakeholders on contingency at kickoff | PM | Week 0 |
| PK-6 | Name owner for push platform team involvement assessment (PM-B3); confirm who determines whether platform team engagement is required | PM | Before P3-G2 |

---

*This spec is approved. Proceed to Week 0 planning and P1-G0 kickoff upon resolution of cross-team availability and resource confirmations above.*
