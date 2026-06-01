# Project Manager Review — Agentic Patient Summary (Round 2)

**Reviewer:** Project Manager  
**Review date:** 2026-06-01  
**Spec version under review:** v2 (amendments A–N incorporated)  
**Round:** 2 of debate loop  
**Prior PM score:** 8.53 / 10.0 — Conditional (Round 1)  
**Verdict:** ⚠️ CONDITIONAL — Score **8.68 / 10.0**

---

## Executive Summary

All four Round 1 blocking conditions are resolved at the spec level. The delivery framework in v2 is substantially more complete: OQ-1 now has explicit contingency paths, the combined ElfieCare 9-deliverable commitment is mandated, a named Medical Affairs reviewer with review SLAs is required before development begins, and the Week 0 milestone map is a hard gate. Delivery realism — the primary score suppressor in Round 1 (5.0) — has increased to 9.0.

Two residual issues prevent clearing 9.0: (1) the consent revocation breach runbook content is still not specified (H3 carried from Round 1), leaving a regulatory notification gap that a gate item alone cannot close; and (2) TA Round 2's five new conditions (V3-C1 through V3-C5) have direct delivery implications — most significantly, V3-C4 (patient re-consent mechanism) may extend Elfie Mobile scope not currently captured in P1-G0-3, and V3-C2 (system prompt version change gate) adds Medical Affairs review load not accounted for in the P1-G0-6 MA capacity plan. Until these implications are absorbed back into the planning framework, the delivery plan is not self-consistent.

A v3 targeted fix — resolving V3-C1 through V3-C5 per TA requirements, specifying the runbook content for H3, and recalibrating P1-G0-6 for the additional MA gate load introduced by V3-C2 — clears 9.0.

---

## Section 1 — Blocking Condition Dispositions

---

### B1 — No Milestone Map Mandate

**✅ RESOLVED**

P1-G0-8 is present and well-formed. It mandates a Project Manager-produced Week 0 milestone map covering: P1/P2/P3 start dates and serialized dependencies, OQ-1 resolution deadline, ElfieCare integration windows, Medical Affairs review slots, OQ-1 contingency fork (Path A vs. Path B timelines), and P3-G5 staged rollout cohort criteria. Review by Technical Advisor and Product Lead is required before P1-G1 begins. Ownership is clear and the artifact content is prescriptive. This is a complete resolution of the original gap — the project now has a mandated planning artifact that enforces cross-team sequencing before any development begins.

---

### B2 — Combined ElfieCare Backlog Not Assessed

**✅ RESOLVED**

P1-G0-2 now explicitly mandates a single consolidated capacity plan from ElfieCare EM covering Component 2 (4 deliverables) + Component 3 (5 deliverables) = 9 total deliverables, with sprint sequencing, individual deliverable estimates, and delivery milestones for both features. The spec body also surfaces this requirement in the ElfieCare Integration section, making the 9-deliverable scope visible to all reviewers. A commitment obtained without Component 2 scope visible to ElfieCare EM is explicitly voided.

**One residual delivery note:** V3-C5 (the "viewed" definition gap — see Section 3) must be resolved before ElfieCare EM can finalize the estimate for deliverable (e) (the retraction API). The retraction API's "viewed" boundary definition determines which states trigger deletion and is a design input to that deliverable. P1-G0-2 capacity confirmation should not close until V3-C5 is resolved and communicated to ElfieCare engineering.

---

### B3 — OQ-1 Contingency Absent

**✅ RESOLVED**

P1-G0-0 is a hard gate before any LLM integration work begins. Path A (US-hosted provider + BAA compliant → proceed as scoped) and Path B (in-country deployment required → 4–8 week extension, provider re-selection, BAA renegotiation, compliance gate re-test against alternative model) are both explicitly defined with trigger conditions. Ownership is assigned to Legal. LLM-independent P1 deliverables may proceed in parallel with OQ-1 resolution, correctly separating the critical-path risk from the non-LLM build work.

The TA independently validated this resolution and noted one non-blocking assumption risk: LLM-independent P1 deliverables (Delta Analyzer output storage, audit log persistence, feature store location) may bake in data residency assumptions that Path B would require revisiting. The TA recommended the Week 0 milestone map (P1-G0-8) include a TA-produced data residency assumption document for LLM-independent deliverables before that work begins. This is a sound recommendation that should be incorporated into the P1-G0-8 map scope at no spec cost.

---

### B4 — Medical Affairs Capacity Unconfirmed

**✅ RESOLVED**

P1-G0-6 is present with: named MA reviewer(s) required, SLAs per engagement type (system prompt/prohibited terms ≤5 business days; copy review ≤3 business days; monthly sample review in MA calendar), and reconciliation against Component 1 and Component 2 MA obligations. This is a complete resolution of the original gap.

**One residual delivery note (related to V3-C2):** The TA's V3-C2 condition adds a new gate that was not in scope when P1-G0-6 was drafted: system prompt version changes now require Medical Affairs sign-off + compliance gate re-run. During P1, the system prompt is actively being developed and will iterate through multiple drafts before P1-G0-4 (the "final" MA approval). Each version change in production thereafter also consumes MA capacity. The P1-G0-6 MA load reconciliation was calculated without this gate in scope. If V3-C2 is adopted as a production operational requirement, the MA capacity plan must be updated to reflect that system prompt iteration adds MA review cycles beyond the baseline commitments. This is a downstream adjustment but must be acknowledged before P1-G0-6 is considered complete and P1 begins.

---

## Section 2 — High-Priority Item Assessments

---

### H2 — Staged Rollout Human Review

**✅ RESOLVED**

P3-G5 now requires 100% human review of all staged rollout summaries by Medical Affairs within 48 hours of delivery. This is distinct from and additional to the 20/month post-full-rollout sample. The distinction between compliance gate activations (caught failures, expected) and compliance gate misses (prohibited language that passed the gate and was delivered) is correctly drawn. The 100% review protocol for the staged rollout cohort closes the verification gap identified in Round 1. The Launch Gate Checklist includes "100% human review protocol for staged rollout summaries established with MA" as a required item. No residual gap.

---

### H3 — Consent Revocation SLA Breach Notification

**⚠️ PARTIALLY RESOLVED**

AC 6.3 remains unchanged: "Any breach (zero tolerance)" triggers an on-call page. P3-G4-4 mandates an on-call runbook covering "consent revocation breach." The runbook requirement is present — this is progress from v1, where the runbook was not scoped at all.

**The residual gap:** The runbook content is still not specified at the AC level. The Round 1 PM review identified four required content areas for regulatory compliance: (a) automated breach detection → manual force-deletion escalation path with a named owner, (b) patient notification decision tree (notify vs. not notify under VN PDPD / TH PDPA), (c) regulatory notification assessment (reportable breach determination), (d) timeline for forced deletion completion after breach detection, with Legal sign-off before P3-G4 passes. None of these content requirements appear in P3-G4-4. A gate item that says "write a runbook covering consent revocation breach" produces a runbook of unknown regulatory adequacy.

**Delivery risk:** Under VN Decree 13/2023/ND-CP and TH PDPA, a deletion SLA breach may be a notifiable event. If the runbook is written without Legal input on patient notification and regulatory reporting, the first real SLA breach could require emergency policy and regulatory escalation with no pre-approved process. This is a delivery risk that an inadequate runbook creates post-launch, not at gate time. The gate will appear to pass; the risk materializes later.

**Required addition:** P3-G4-4 must specify that the consent revocation breach runbook content is approved by Legal before the gate passes, and must enumerate the required content areas (force-deletion escalation owner, patient notification decision tree, regulatory notification assessment, forced deletion timeline). This is a single-paragraph addition to the P3-G4-4 checklist item.

---

### H4 — OQ-7 Operational Playbook

**✅ RESOLVED**

P3-G5 now includes an OQ-7 prerequisite that is specifically scoped to what Round 1 identified as missing. The resolution requirement covers: (a) Legal ruling on immediate vs. lazy invalidation, and (b) for the immediate invalidation path, a complete operational playbook covering batch re-acknowledgment campaign design, notification to affected doctors, UI design for re-acknowledgment prompt, owner assignment, and impact on scheduled push delivery during the campaign window. The spec is explicit that Legal ruling alone is not sufficient — the operational playbook must be approved before staged rollout begins. This blocks P3-G5, which is the correct gate placement. No residual gap.

---

## Section 3 — TA V3-C1 through V3-C5: Delivery Implications

The TA's Round 2 conditions are technical AC precision issues, not design changes. However, five of them have direct planning consequences that the PM must absorb before the spec is delivery-ready.

---

### V3-C1 — LLM Slot Context Design Choice (AC 2.1)

**Delivery implication: LOW**

This requires a single sentence added to AC 2.1 clarifying whether the LLM receives raw Delta Analyzer numbers (Choice B, Check 3 as the guard) or stripped classifications only (Choice A, defense-in-depth). Either choice is acceptable.

The delivery risk is implementation assumption divergence: without explicit specification, frontend/backend teams may implement different assumptions, or the choice may be made implicitly during implementation and not reviewed by Medical Affairs or Legal before P3-G0. If the wrong assumption propagates into the compliance gate test suite design, rework could occur at P3-G0-2.

**Action required:** Resolve before P1-G1. Add to the pre-P1-G0-4 system prompt review agenda: TA, Engineering, and Medical Affairs align on Choice A vs. B before system prompt v1 is drafted (since the system prompt's prohibitions must be calibrated to which design choice is made).

---

### V3-C2 — System Prompt Version Change Gate (AC 2.4)

**Delivery implication: MEDIUM**

The TA requires system prompt version changes to follow the same gate as model version changes: compliance gate test suite re-run + Medical Affairs sign-off + deployment via code change. This is architecturally correct given the two-stage design.

**The delivery consequence:** The system prompt is a living artifact. During P1, it will iterate through multiple drafts before P1-G0-4 locks v1. After launch, any correction or update to the system prompt (e.g., to address a new prohibited phrasing pattern, or refine narrative quality) requires MA sign-off and a compliance gate re-run. This gate is not currently reflected in the MA capacity plan at P1-G0-6.

**Specific impact:** If the MA review SLA for a system prompt change is 5 business days (per P1-G0-6), any post-launch system prompt update has a minimum 5-day MA sign-off lead time plus compliance gate test suite runtime before deployment. This is a reasonable production safety control but must be acknowledged by the team as an operational constraint before launch, and by Medical Affairs as an ongoing capacity commitment.

**Required action:** Before P1-G0-6 is finalized, add "system prompt version change reviews (post-launch)" to the MA capacity reconciliation scope. The frequency assumption (e.g., estimate 2–4 system prompt updates per year) should be agreed with Medical Affairs before P1-G0-6 closes.

---

### V3-C3 — Zero-Length Period Guard (AC 1.2)

**Delivery implication: MINIMAL**

A single-sentence validation guard: if `period_length_days < 2` on any trigger path, pipeline returns "Summary unavailable — no data period to summarize" before Delta Analyzer is called. Engineering effort is a one-line conditional. No cross-team dependencies. No gate sequencing impact.

**Action required:** Add to P1 deliverable scope for the pipeline trigger validation (minor engineering note only).

---

### V3-C4 — Patient Re-Consent Mechanism (MED-5 / HIGH)

**Delivery implication: MEDIUM-HIGH**

The TA has elevated this from MED to HIGH, driven by the regulatory asymmetry: the spec requires doctors to re-acknowledge when acknowledgment language is updated (AC 3.2), but no equivalent mechanism exists for patients when consent text is updated. VN Decree 13/2023/ND-CP (Article 11) and TH PDPA (Section 19) require consent to cover the actual processing performed — a consent text update that reflects changed processing scope may not be covered by existing consents.

Two resolution options exist:

**Option A (Full parity with AC 3.2):** Add a patient re-consent invalidation mechanism. This requires:
- Consent invalidation logic in the backend
- Patient re-consent prompt UI in Elfie Mobile (a new deliverable beyond the current P1-G0-3 scope)
- Delivery hold logic during the re-consent window (analogous to AC 3.2's acknowledgment hold behavior)
- Specification of whether holds apply to scheduled push only or also on-demand

This adds scope to the Elfie Mobile team (P1-G0-3) and may extend the consent data model. P1-G0-3 must be updated to reflect this before the gate closes.

**Option B (Legal ruling deferral):** Add a required Legal opinion gate — Legal determines whether patient re-consent is required under VN PDPD / TH PDPA before a mechanism is designed. This defers the mechanism but creates a gate before launch.

**PM recommendation:** Option B is the more delivery-conservative choice if Legal opinion is not already available, as it avoids adding Mobile scope on an unresolved legal question. However, if Legal's view is that re-consent is required, the mechanism (Option A) must be scoped before P3-G1, which means the option-selection decision must be made early in P1 — not deferred to P3.

**Required action:** Legal must be engaged at P1-G0 to provide the Option B ruling or confirm Option A is required. If Option A: P1-G0-3 (Elfie Mobile capacity confirmation) must be updated before development begins.

---

### V3-C5 — Definition of "Viewed" (AC 3.1 / AC 4.1)

**Delivery implication: LOW-MEDIUM**

The retraction API (ElfieCare deliverable (e)) is designed to mark "unviewed summaries" as deleted. Without a definition of which card states constitute "viewed," ElfieCare engineering cannot determine the API's deletion scope. The TA identified the ambiguous states: Dismissed, Snoozed, Available (not yet opened), and the in-progress reading scenario.

**Delivery risk:** If ElfieCare builds the retraction API before this definition is resolved, they may implement an incorrect "viewed" boundary and require rework. Given that deliverable (e) is part of the P1-G0-2 consolidated capacity commitment, ElfieCare EM's estimate for that deliverable may be based on an incorrect implementation assumption.

**Required action:** The "viewed" definition must be resolved (by Product) before P1-G0-2 capacity commitment is finalized and communicated to ElfieCare engineering. This is a sequencing dependency: P1-G0-2 cannot meaningfully close on deliverable (e) without it.

**PM-recommended definition to propose to Product:** "Viewed" = summary card has transitioned to Dismissed, Snoozed, or a tracked "opened" event (user explicitly opened full detail view). "Available" (delivered but not yet opened) and "Queued pending acknowledgment" are "unviewed" and subject to deletion SLA. This aligns with AC 4.1 states and is the operationally intuitive boundary.

---

## Section 4 — Residual Delivery Risks Register

| Risk | Severity | Gate affected | Action required |
|---|---|---|---|
| H3 runbook content not specified — regulatory notification path for SLA breach unresolved | MED | P3-G4-4 | Add required runbook content areas (force-deletion owner, patient notification decision tree, regulatory notification assessment, forced deletion timeline) + Legal sign-off requirement to P3-G4-4 checklist item |
| V3-C2 MA capacity recalibration — system prompt version change gate adds ongoing MA review load not in P1-G0-6 scope | MED | P1-G0-6 | Add system prompt version change reviews to MA capacity reconciliation before P1-G0-6 closes |
| V3-C4 patient re-consent — may add Elfie Mobile deliverable not in P1-G0-3 scope | MED-HIGH | P1-G0-3 | Engage Legal at P1-G0 to choose Option A or B; if Option A, update P1-G0-3 before development begins |
| V3-C5 "viewed" definition — ElfieCare deliverable (e) design input missing | LOW-MED | P1-G0-2 | Product to resolve "viewed" definition before P1-G0-2 capacity commitment is finalized with ElfieCare EM |
| B3 data residency assumptions — LLM-independent P1 work may bake in storage assumptions Path B invalidates | LOW | P1-G0-8 | Add TA data residency assumption doc requirement to P1-G0-8 milestone map scope |
| HIGH-4 partial — retroactive prior-period data change without period_start change produces stale delta comparisons | LOW | P1 build | Consider expanding period-boundary-drift exception to trigger on prior-period data hash change (TA R1) |
| MED-6 "viewed" boundary for retraction API (same as V3-C5) | LOW-MED | P1-G0-2 | Resolved with V3-C5 action above |

---

## Section 5 — Scorecard

| Dimension | Weight | v1 Score | v2 Score | Weighted | Notes |
|---|---|---|---|---|---|
| User value clarity | 20% | 9.5 | 9.5 | 1.90 | Stable: two-stage architecture, physician framing, patient access rights all precisely articulated; no ambiguity in what either party sees |
| Scope precision | 15% | 8.0 | 8.5 | 1.275 | B2 (combined ElfieCare) and B3 (OQ-1 scope uncertainty) resolved. Deducted: V3-C4 may add Mobile scope not in P1-G0-3; V3-C5 blocks P1-G0-2 finalization until "viewed" is defined |
| AC quality | 20% | 9.0 | 8.5 | 1.70 | B1–B4 gate additions are precise and actionable. Deducted: V3-C1–C5 represent five new AC precision gaps (all targeted, but pending resolution); H3 runbook content not specified |
| Technical feasibility | 20% | 8.5 | 8.5 | 1.70 | Two-stage architecture is sound; V3 conditions are AC precision issues, not design flaws. Consistent with TA Round 2 assessment |
| Regulatory compliance | 15% | 9.5 | 8.0 | 1.20 | MED-5 elevated to HIGH (patient re-consent gap — asymmetry with doctor re-acknowledgment is legally indefensible under VN PDPD Art. 11 and TH PDPA Sec. 19); H3 runbook regulatory notification content unspecified |
| Delivery realism | 10% | 5.0 | 9.0 | 0.90 | Major improvement: all four blocking conditions resolved, H2 and H4 resolved. Minor residuals: H3 runbook content, V3-C2 MA load addition, V3-C4 Mobile scope, data residency assumption doc |

**Total weighted score: 8.68 / 10.0**

---

## Section 6 — Verdict

**⚠️ CONDITIONAL — Score 8.68 / 10.0. Not APPROVED.**

The spec does not meet the 9.0 threshold. The delivery framework is now production-grade: the four Round 1 blocking conditions are fully resolved, H2 and H4 are precisely addressed, and the gate structure reflects mature planning discipline. The remaining gap is a combination of (a) one unresolved regulatory content gap (H3 runbook), (b) five TA technical AC conditions whose delivery implications have not been absorbed back into the planning framework, and (c) the regulatory asymmetry of patient re-consent (MED-5/V3-C4) which suppresses the Regulatory Compliance dimension.

### PM Conditions for v3 Approval

| # | Condition | Type | Gate affected |
|---|---|---|---|
| PM-C1 | Add required runbook content to P3-G4-4: force-deletion escalation owner, patient notification decision tree (VN PDPD / TH PDPA), regulatory notification assessment, forced deletion timeline post-breach-detection. Legal sign-off required before P3-G4 passes. | PM (unresolved H3) | P3-G4-4 |
| PM-C2 | Resolve V3-C4 (patient re-consent) via Option A or B before P1-G0-3. If Option A: Elfie Mobile deliverables for patient re-consent prompt, delivery hold logic, and re-consent state must be added to P1-G0-3 capacity confirmation scope before P1-G0 passes. If Option B: Legal ruling gate added to P1-G0 before P1-G0-3 closes. | Delivery implication of TA V3-C4 | P1-G0-3 |
| PM-C3 | Add "system prompt version change reviews (post-launch)" to P1-G0-6 MA capacity reconciliation scope, with agreed frequency estimate, before P1-G0-6 closes. | Delivery implication of TA V3-C2 | P1-G0-6 |
| PM-C4 | Resolve "viewed" definition (V3-C5) before P1-G0-2 capacity commitment is finalized with ElfieCare EM. Product must define which card states constitute "viewed" for retraction API purposes; definition communicated to ElfieCare engineering before deliverable (e) is estimated. | Delivery implication of TA V3-C5 | P1-G0-2 |

### TA Conditions Required for v3 (not PM blocking, but PM confirms delivery relevance)

The TA's V3-C1 through V3-C5 are independently required by Technical Advisor. PM confirms all five have delivery implications documented in Section 3 and should be resolved before P1-G1 begins. V3-C3 (zero-length period guard) has no delivery planning impact beyond being a P1 scope item.

### Projected score if PM-C1 through PM-C4 and TA V3-C1 through V3-C5 are resolved

| Dimension | Projected Score | Weighted |
|---|---|---|
| User value clarity | 9.5 | 1.90 |
| Scope precision | 9.0 | 1.35 |
| AC quality | 9.0 | 1.80 |
| Technical feasibility | 9.0 | 1.80 |
| Regulatory compliance | 9.0 | 1.35 |
| Delivery realism | 9.0 | 0.90 |
| **Total** | | **9.10** |

**Projected v3 Score: 9.10 / 10.0 — APPROVED**

The four PM conditions and the five TA conditions are all targeted, single-point fixes requiring no architectural redesign. The foundation laid by v2 is strong. The path to 9.0 is clear.

---

## Section 7 — Pre-Kickoff Planning Notes (non-conditions)

These do not require spec changes but must be actioned at Week 0.

| # | Action | Owner |
|---|---|---|
| PK-1 | Add TA data residency assumption document requirement to P1-G0-8 milestone map scope: TA documents which LLM-independent P1 deliverable storage locations are assumed before that work begins, enabling instant Path B impact assessment | PM + TA |
| PK-2 | Confirm whether Component 2 BAA is already signed; if yes, P1-G0-1 (BAA) timeline may be compressed for Component 3 | Legal + PM |
| PK-3 | Engage Legal on V3-C4 Option A vs. B decision at Week 0 — do not wait for P1-G0-3 to be threatened by an unresolved legal question | PM + Legal |
| PK-4 | Product to draft "viewed" definition for V3-C5 resolution before P1-G0-2 kick-off meeting with ElfieCare EM | Product |
| PK-5 | Confirm with MA whether system prompt iteration during P1 draft phase (before P1-G0-4) counts toward the ≤5 business day SLA or whether the SLA applies only to production changes | PM + MA Lead |
