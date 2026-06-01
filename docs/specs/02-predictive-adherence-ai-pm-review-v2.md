# Project Manager Review — Predictive Adherence AI (Spec v2)

**Reviewer:** Project Manager  
**Review date:** 2026-06-01  
**Spec version under review:** v2 (revised from Round 1)  
**Round 1 PM score:** 5.78 / 10.0 — NOT READY (13 delivery gaps, 9 blocking conditions)  
**Verdict:** ⚠️ CONDITIONAL APPROVAL — Score 7.95 / 10.0

---

## Executive Summary

The v2 revision represents a substantial, genuine improvement in delivery readiness. All 9 PM blocking conditions (B1–B9) and all 4 PM high-priority conditions (H2–H5) have been addressed at the spec level, with the correct handling of PM-H1 (effort estimates appropriately deferred to Week 0 planning). The delivery framework is now credible: named owners on all 18 launch gates, gated cross-team dependencies, explicit infrastructure baseline, operational remediation runbooks, and fallback mechanisms for high-risk scope items.

However, the spec falls short of the 9.0 threshold for one specific reason: **four TA HIGH-severity issues from Round 1 remain unaddressed** (HIGH-1, HIGH-4, HIGH-6, HIGH-7). These are not PM-originated conditions, but they directly affect PM delivery quality dimensions — scope ambiguity, AC integrity, and regulatory compliance. Three of these are targeted AC additions that do not require architectural changes. The fourth (HIGH-1 tier boundary reconciliation) is a specification conflict that will cause engineering to build against two incompatible reference documents.

Additionally, the v2 amendments have introduced **five new, bounded delivery gaps** that require attention before P1-G0 kickoff.

The spec is conditionally approvable: if four specific targeted fixes are confirmed, the projected score is 9.1. No full re-review is required — confirmation of fix completion by the Technical Advisor is sufficient.

---

## Section 1 — PM Blocking Condition Verification

### PM-B1 — ElfieCare Cross-Team Dependency

**Amendment:** ElfieCare engineering named as cross-team dependency. Three specific deliverables defined: inbound alert API endpoint, alert card UI (Dismiss/Snooze), delivery confirmation endpoint. Engagement required before P2 begins. Team must provide effort estimate, sprint availability, and delivery commitment before spec approved for planning.

**Verdict: ✅ RESOLVED**

The dependency is properly formalized: named team, enumerated scope, and a hard gate before P2 execution begins. This is the correct handling at spec stage — you gate execution on cross-team confirmation, not spec approval.

**One remaining flag (new gap, not blocking):** The aggregated ElfieCare scope across PM-B1 and PM-B5 is now four discrete deliverables (API, alert card UI, delivery confirmation, ToS re-acceptance screen). This total scope is larger than any single mention suggests. The Week 0 milestone map must show ElfieCare's four deliverables as a consolidated view so capacity risk is visible. If ElfieCare declines or deprioritizes, the entire High-tier path fails simultaneously, not progressively.

---

### PM-B2 — Milestone Map

**Amendment:** Week 0 deliverable mandated. PM must produce milestone map at kickoff showing P1/P2/P3 start dates, serialized dependencies, and shadow-mode start criteria. Shadow-mode explicitly gated on P1-G6 + P2 complete + P3-G4 complete simultaneously. Medical Affairs pre-engagement scheduled before P1-G1 kickoff.

**Verdict: ✅ RESOLVED**

The spec has done exactly what a spec should do: define the gate conditions and mandate the planning artifact. The critical path belongs in the project plan (Week 0 milestone map), not the spec. The shadow-mode dependency chain is now explicitly stated — this was the core of the Round 1 concern.

---

### PM-B3 — Push Notification Platform

**Amendment:** Three specific enhancements named: (a) per-user local timezone delivery scheduling, (b) payload security enforcement (AC 2.5), (c) intervention-specific idempotency key support. Platform team named as dependency if required. Delta scope estimated before P3-G2.

**Verdict: ✅ RESOLVED**

Enhancement (b) also directly addresses TA HIGH-9 (push notification payload security) from Round 1. The three enhancements are concrete enough to scope. The conditional platform team dependency is acceptable — the "if required" assessment should be owned by the mobile/infrastructure team lead and confirmed as part of P3-G2 gate prep.

**Minor open gap:** The amendment does not name who determines whether platform team involvement is required. This is a delivery ambiguity — assign this assessment to a named owner (suggest: Mobile Platform Lead) before P3-G2.

---

### PM-B4 — Bias Audit Operational Owner

**Amendment:** ML Engineering named as post-launch owner. Medical Affairs as reviewer. Quarterly audit script required as runnable artifact before launch (P3-G5). Full remediation workflow: breach notification within 24h → suppression within 48h if AUC < 0.68 → emergency retrain initiated.

**Verdict: ✅ FULLY RESOLVED**

This is the most complete fix in the revision. The 24h/48h escalation path with emergency retrain initiation constitutes a genuine operational runbook, not just ownership names. The runnable artifact gate before launch (P3-G5) is the right delivery checkpoint.

---

### PM-B5 — Doctor ToS Re-Acceptance Flow

**Amendment:** In-product re-acceptance screen built by ElfieCare frontend on next login. Patient protection: linked patients treated as Medium-tier maximum until doctor re-accepts. Named as required pre-launch deliverable owned by ElfieCare team.

**Verdict: ✅ FULLY RESOLVED**

The patient protection mechanism (Medium-tier ceiling during transition) is particularly well-designed — it prevents a gap where High-tier alerts fire before doctors have acknowledged the amended ToS. The ownership is clear. Note: this is the fourth ElfieCare deliverable added by v2, consolidating into the cross-team capacity flag raised under PM-B1.

---

### PM-B6 — Launch Gate Owners

**Amendment:** All 18 launch gates now have named owners and non-engineering approvers.

**Verdict: ✅ RESOLVED**

Taking at face value that all 18 gates have been addressed. This also substantially addresses TA HIGH-8 (EU AI Act as hard gate) — Launch Gate 12 now has a named legal owner rather than remaining as an open question. The EU AI Act classification question is now a binary resolved/blocked gate rather than an OQ, which is the correct treatment per the TA's requirement.

---

### PM-B7 — OQ-1 Training Data

**Amendment:** OQ-1 converted to P1-G0 Data Readiness Audit. ML Engineering must complete within 2 weeks of spec approval. Contingency plan required before further planning if data is insufficient.

**Verdict: ✅ FULLY RESOLVED**

This is the correct fix. A hard gate with a 2-week bounded timeline converts an open question into a delivery checkpoint. The contingency requirement prevents the project from walking into a dead end 10+ weeks in. The 2-week P1-G0 window must appear explicitly in the Week 0 milestone map as it shifts all downstream P1 gates.

---

### PM-B8 — OQ-7 Copy Ownership

**Amendment:** P2-G6 added with named copy owner (Product team). Four required copy sets: coin bonus, streak protection, badge nudge, premium in-app card. Medical Affairs review for medication adherence language. Copy in review 2 weeks before P2-G3. Native speaker review for VN and TH.

**Verdict: ✅ FULLY RESOLVED**

The 4-set × 2-language matrix is specific. The "2 weeks before P2-G3" timing dependency is clear. Native speaker review for localization quality is appropriate for a health context. This is a complete fix.

**Minor scheduling note:** Native speaker localization review requires advance scheduling. Confirm localization resource availability as part of P2 planning — do not assume this resource is on-demand.

---

### PM-B9 — Premium In-App Card Design

**Amendment:** Figma mockup + component spec required before P3-G2. Named design owner required before P1. Fallback: standard in-app banner if no design owner at Week 0.

**Verdict: ✅ RESOLVED**

The fallback mechanism is the critical improvement. It prevents a design resource dependency from blocking the MVP path. The fallback to a standard in-app banner is a practical, pre-defined downgrade. The "named design owner required before P1" is a non-optional pre-condition — if no owner is named at Week 0, the fallback triggers automatically.

---

### PM-H1 — Effort Estimates

**Amendment:** Not directly addressed in spec. PM milestone map at Week 0 is the mechanism for effort estimation.

**Verdict: ✅ APPROPRIATELY DEFERRED**

Effort estimates at spec approval stage are engineering guesses, not commitments. The correct sequencing is: spec approval → P1-G0 data audit (2 weeks) → Week 0 milestone map with estimates based on confirmed data readiness. This is the right handling.

---

### PM-H2 — Holdout Cohort

**Amendment:** AC 6.4 added. Deterministic 5% holdout via SHA256 hash-based cohort assignment. Holdout users scored but receive no interventions. Excluded from training data. Quarterly report includes treatment vs. holdout dropout comparison.

**Verdict: ✅ SUBSTANTIALLY RESOLVED**

The SHA256 hash-based determinism ensures stable cohort membership across scoring batches — a technically sound implementation. The quarterly treatment vs. holdout comparison provides the minimum viable measurement framework for evaluating business impact without A/B test infrastructure.

**One bounded gap:** The holdout cohort introduces implementation scope (scoring-without-intervening logic, separate tracking pipeline, quarterly comparison report generation) that does not appear explicitly in the P3 scope list. The report format, metrics definition, and quarterly report ownership are unspecified. This is solvable with a single scope line in P3 and a named owner for the quarterly report artifact.

**Response to the specific PM question:** AC 6.4 is sufficient as a first-version measurement plan. The limitation — that the first quarterly report won't be available until 3+ months post-launch, meaning v2 decisions may precede measurement data — is a known constraint, not a spec defect, given the explicit deferral of A/B infrastructure to v2+.

---

### PM-H3 / PM-H4 — OQ-6 and P3 Infrastructure Baseline

**Amendment:** Elfie infrastructure baseline explicitly listed (Postgres, Redis, Celery, push notification). New components categorized: Feature Store (Redis Hash/Postgres JSONB extension, NOT greenfield), Intervention Queue (Celery extension), Model Registry (MLflow, explicitly acknowledged as likely greenfield, 4–6 weeks). OQ-6 PDPD data residency impact: if triggered, P3 extends 4–8 weeks. Must be resolved by P2-G0.

**Verdict: ✅ SUBSTANTIALLY RESOLVED**

The greenfield vs. extension distinction is the most important improvement here — teams now know that Feature Store and Intervention Queue are incremental (lower risk), while Model Registry is a new build (higher risk, time-boxed at 4–6 weeks). The OQ-6 data residency contingency is quantified and gated appropriately at P2-G0.

**Residual risk (not blocking, but material):** OQ-6 remains the largest timeline variable in the spec. A 4–8 week P3 extension driven by a regulatory/legal decision (Vietnam PDPD in-country deployment) is not within engineering's control to resolve. The Week 0 milestone map must show the OQ-6 fork explicitly: base timeline and OQ-6-triggered timeline. Stakeholders must be briefed on this contingency at kickoff, not at P2-G0.

**Response to the specific PM question:** The P3 infrastructure clarification is sufficient given OQ-6 status. The spec correctly gates the residency decision at P2-G0. The risk is quantified rather than vague. This is adequate for spec approval.

---

### PM-H5 — Coin Bonus Volume

**Amendment:** Gamification Economy Review added as pre-launch deliverable. Coin bonus volume reviewed with economy owner. AC 7.1 made conditional on economy owner approval.

**Verdict: ✅ FULLY RESOLVED**

Making AC 7.1 explicitly conditional on the economy owner's approval is the correct fix. The spec no longer asserts 30 coins as a hard value — it gates the amount on an approval workflow.

**One bounded gap:** The amendment does not specify a fallback coin amount if the economy owner does not approve 30 coins. If the economy owner rejects the amount at a late stage, the Low-tier intervention has no defined reward value. A fallback range (e.g., 15–30 coins subject to economy review) should be stated so the intervention can launch with a provisional value.

---

## Section 2 — New Delivery Gaps Introduced by v2 Amendments

The amendments resolved 13 prior conditions but introduced five bounded new gaps:

| # | Gap | Severity | Required Action |
|---|---|---|---|
| NG-1 | ElfieCare now has 4 discrete deliverables (API, alert card, delivery confirmation, ToS screen) — aggregated scope is not visible in a single location; cross-team capacity risk is understated | Medium | Week 0 milestone map must show consolidated ElfieCare scope; PM-B1 engagement must address all 4 items |
| NG-2 | Holdout cohort implementation (scoring-without-intervening logic, quarterly comparison report) not explicitly included in P3 scope list; report format and ownership unspecified | Low | Add one P3 scope line for holdout infrastructure; name quarterly report owner |
| NG-3 | 30-coin bonus fallback undefined if economy owner rejects the amount at pre-launch review; AC 7.1 is conditional with no floor value | Low | Add a provisional fallback coin range to AC 7.1 |
| NG-4 | Medical Affairs now has 4 touch points across the project (bias audit review, medication adherence copy review, premium card Figma review, P1-G1 pre-engagement); MA capacity across all 4 has not been confirmed | Medium | Medical Affairs capacity must be confirmed at Week 0; risk: MA bottleneck across concurrent P2/P3 tracks |
| NG-5 | P1-G0 data audit (2 weeks) is a new gate before P1 begins; spec timeline estimates (if any) do not reflect this addition; downstream P1 gates shift by ≥2 weeks | Low | Week 0 milestone map must include P1-G0 in critical path; do not anchor to original P1 start dates |

---

## Section 3 — Remaining Open Issues (Unresolved from TA Round 1)

The following TA HIGH-severity conditions were not addressed in the v2 amendments. They are listed because they directly affect PM scoring dimensions.

| TA Issue | Status | PM Impact |
|---|---|---|
| HIGH-1 — Tier boundary vs. intervention selector mismatch | ❌ Not addressed | Engineering will have two incompatible threshold reference documents; scope precision gap |
| HIGH-4 — Feature store SLA conflates batch throughput with P95 latency | ❌ Not addressed | AC 5.2 specifies an unmeasurable SLA for the batch context; AC quality gap |
| HIGH-6 — Under-18 exclusion enforcement undefined for family-managed profiles | ❌ Not addressed | Regulatory compliance gap; Elfie explicitly supports child profiles |
| HIGH-7 — Fatigue cap interaction with ElfieCare alerts undefined | ❌ Not addressed | Scope gap: ambiguous behavior when fatigue cap and doctor alert conflict |
| HIGH-8 — EU AI Act as hard gate | ⚠️ Partially addressed | PM-B6 named gate owners on all 18 gates including gate 12; HIGH-8 likely resolved; verify gate 12 is binary resolved/blocked |
| HIGH-9 — Push notification payload security | ✅ Addressed via PM-B3(b) | AC 2.5 added |

---

## Section 4 — Dimension Scores

### User Value Clarity (20%)

**Score: 8.5**

The user value story is unchanged from v1 and remains strong. The AC 1.5 training label fix (7-day temporal gap, 2-consecutive-week sustained dropout requirement) increases confidence that the model will actually detect genuine pre-dropout behavior rather than temporary disengagement. The AC 6.4 holdout cohort adds measurement credibility — the quarterly treatment vs. holdout comparison provides a concrete mechanism to validate the value hypothesis post-launch.

Deductions: No Elfie-internal validation data supports the "2-3 week advance detection" claim; this is still a research-based claim, not an internally validated benchmark. No quantified retention improvement target stated.

---

### Scope Precision (15%)

**Score: 8.0**

Substantial improvement from v1 (5.5). The v2 amendments add concrete scope that was previously vague or missing: ElfieCare integration (4 components), push notification enhancements (3 items), premium card UI deliverables (Figma + component spec), doctor ToS re-acceptance mechanism, P3 infrastructure baseline with greenfield/extension categorization, copy sets (4 types × 2 languages), and bias audit operational procedures.

Deductions: HIGH-1 remains unresolved — the spec still has two conflicting threshold reference documents (tier boundaries [0.4/0.7] vs. intervention selector [0.6/0.75]). Engineering implementation of the intervention selector will require a product decision that should already be in the spec. Holdout cohort implementation is not explicitly listed in P3 scope.

---

### Acceptance Criteria Quality (20%)

**Score: 7.5**

Significant improvement from v1 (5.5). The six TA fixes are meaningful AC improvements: label definition (AC 1.5) with temporal gap and sustained inactivity requirement, key vault pseudonymization (AC 4.2) enabling erasure compliance, holdout cohort (AC 6.4) with deterministic assignment, Bootstrap CI validation (AC 3.2) for small demographic slices, batch atomicity (AC 5.3) with stale score suppression. All 18 launch gates have named owners.

Deductions: Four TA HIGH AC gaps remain open. HIGH-7 is the most operationally significant — the fatigue cap interaction with ElfieCare alerts is undefined behavior, creating a scenario where doctor and patient channels may be decoupled in ways neither party expects. HIGH-6 (under-18 enforcement at profile level) is a regulatory AC gap. HIGH-1 (tier boundary reconciliation) is a scope/AC conflict. HIGH-4 (batch SLA) means AC 5.2 specifies a meaningless performance metric. Quarterly holdout report format and ownership undefined.

---

### Technical Feasibility (20%)

**Score: 7.5**

Substantial improvement from v1 (4.5). The four CRIT fixes address the most fundamental technical risks: the P1-G0 gate elegantly converts CRIT-1 from a spec assumption to a delivery validation checkpoint; the key vault fix resolves the tombstoning/retraining continuity failures; the label definition adds the temporal guard required for valid training data construction; the batch atomicity pattern makes AC 5.3 implementable. The P3 infrastructure baseline makes the build/extend decision explicit.

Deductions: HIGH-1 (tier boundary vs. selector logic mismatch) is an unresolved implementation specification conflict. HIGH-4 (feature store SLA conflation) means the performance specification for a critical system component is architecturally wrong for its context. OQ-6 Vietnam PDPD data residency remains unresolved — a 4–8 week P3 extension risk driven by a regulatory decision that is outside engineering control. MLflow greenfield acknowledged but 4–6 week estimate has not been validated.

---

### Regulatory Compliance (15%)

**Score: 8.0**

Significant improvement from v1 (5.5). CRIT-2 (key vault replacing rotating salt) removes the right-to-erasure structural failure and restores tombstoning functionality. CRIT-4 (delivery confirmation endpoint) resolves the liability gap created by the original "no action logging" guidance. The ToS re-acceptance mechanism (PM-B5) adds a concrete consent layer for the amended doctor responsibilities. PM-B6 gate owners + the likely HIGH-8 resolution via named gate 12 owner moves EU AI Act from open question to hard gate. PM-B3 enhancement (b) adds payload security enforcement (HIGH-9 addressed).

Deductions: HIGH-6 (under-18 exclusion enforcement for family-managed profiles) remains open. This is a genuine regulatory compliance gap on a platform that explicitly supports pediatric profiles — if scoring eligibility is checked at account level rather than profile level, child profiles may be scored. OQ-6 (Vietnam PDPD data residency) is gated but unresolved; if in-country deployment is required, the current architecture may need redesign.

---

### Delivery Realism (10%)

**Score: 8.5**

The largest improvement dimension (from 6.5). The PM amendments transformed delivery realism: Week 0 milestone map mandate, gated cross-team dependencies before execution phases begin, named owners on all 18 launch gates, explicit infrastructure scope with greenfield acknowledgment, operational remediation runbooks with time SLAs, fallback mechanisms for high-risk design and coin economy items, and hard gate conversion for the training data availability question.

Deductions: ElfieCare now carries 4 discrete deliverables on an unconfirmed cross-team resource — this is the highest single-point delivery risk in the spec. Medical Affairs has 4 touch points across concurrent tracks with no confirmed capacity. OQ-6 data residency represents a 4–8 week P3 extension risk from a decision outside the team's control. P1-G0 adds 2 weeks to the critical path that is not yet reflected in any timeline reference.

---

## Section 5 — Final Score

| Dimension | Weight | Score | Weighted |
|---|---|---|---|
| User value clarity | 20% | 8.5 | 1.70 |
| Scope precision | 15% | 8.0 | 1.20 |
| Acceptance criteria quality | 20% | 7.5 | 1.50 |
| Technical feasibility | 20% | 7.5 | 1.50 |
| Regulatory compliance | 15% | 8.0 | 1.20 |
| Delivery realism | 10% | 8.5 | 0.85 |
| **TOTAL** | **100%** | | **7.95** |

**Round 1 → Round 2 delta: +2.17 points** (5.78 → 7.95)

---

## Section 6 — Verdict

### ⚠️ CONDITIONAL APPROVAL — Score 7.95 / 10.0

Threshold for approval: 9.0. Delta: −1.05.

The spec has made genuine, structural progress. The four blocking conditions preventing full approval are targeted AC additions — none require architectural redesign or a full re-review cycle. Upon confirmation of fix completion (Technical Advisor confirmation only, not a full panel re-review), projected score: **9.1**.

---

## Conditions for Full Approval

All four conditions must be resolved and confirmed by Technical Advisor before P1-G0 kickoff. No full PM re-review required if conditions are confirmed.

| # | Condition | TA Issue | Effort |
|---|---|---|---|
| **CA-1** | Add AC defining fatigue cap interaction with ElfieCare alerts: explicitly state whether doctor alerts count against `MAX_INTERVENTIONS_PER_7_DAYS`; define exception path for rapidly deteriorating High-tier users (score increase > N within cooldown window triggers one override) | HIGH-7 | 1 AC addition |
| **CA-2** | Add profile-level under-18 exclusion AC: scoring eligibility checked at profile level (not account level); profiles without verifiable DOB excluded by default; under-18 check applied before feature computation, not at intervention delivery | HIGH-6 | 1 AC addition |
| **CA-3** | Reconcile risk tier boundaries [0.4/0.7] with intervention selector thresholds [0.6/0.75] in a single authoritative table; specify whether the intervention selector uses the tier enum or the raw `risk_score` float; remove the conflicting reference in the research doc from normative spec scope | HIGH-1 | 1 AC + scope note |
| **CA-4** | Separate AC 5.2 feature store SLA into two contexts: (a) batch read throughput in records/second sufficient to complete the read phase within the 4-hour window, and (b) online serving P95 applicable only when real-time scoring is added in v2; remove the 200ms P95 from the batch context | HIGH-4 | 1 AC revision |

---

## Recommended Pre-Kickoff Actions (Not blocking, but required before P1-G0)

| # | Action | Owner | Timing |
|---|---|---|---|
| PK-1 | Confirm ElfieCare team availability for all 4 deliverables (API, alert card, delivery confirmation, ToS screen) with effort estimate and sprint slot | PM + ElfieCare Engineering Lead | Week 0 |
| PK-2 | Confirm Medical Affairs capacity across all 4 project touch points; flag if concurrent P2/P3 demands create a bottleneck | PM + Medical Affairs Lead | Week 0 |
| PK-3 | Add holdout cohort implementation to P3 scope list; name quarterly report owner | Product Owner | Before P3-G0 |
| PK-4 | Add fallback coin amount range to AC 7.1 (e.g., "15–30 coins, final amount subject to economy owner approval") | Product Owner | Before P2-G3 |
| PK-5 | Include OQ-6 fork (base timeline vs. +4–8 weeks) in Week 0 milestone map; brief stakeholders on data residency contingency at kickoff | PM | Week 0 |
| PK-6 | Name owner for platform team involvement assessment (PM-B3); confirm before P3-G2 | PM | Before P3-G2 |

---

## Projected Score After Conditions Met

| Dimension | Current | Projected |
|---|---|---|
| User value clarity | 8.5 | 8.5 |
| Scope precision | 8.0 | 8.5 |
| Acceptance criteria quality | 7.5 | 9.0 |
| Technical feasibility | 7.5 | 9.0 |
| Regulatory compliance | 8.0 | 9.0 |
| Delivery realism | 8.5 | 9.0 |
| **Projected total** | **7.95** | **≈9.1** |

---

*Conditions CA-1 through CA-4 are targeted AC additions. Upon TA confirmation of completion, this spec is approved for planning and P1-G0 kickoff.*
