# Project Manager Review — Agentic Patient Summary (Round 1)

**Reviewer:** Project Manager  
**Review date:** 2026-06-01  
**Spec version under review:** v1  
**Round:** 1 of debate loop (target ≥ 9.0/10 for APPROVED)  
**Verdict:** ⚠️ CONDITIONAL — Score **8.53 / 10.0**

---

## Executive Summary

The Agentic Patient Summary spec is substantively strong. The regulatory framing is precise and consistently applied, the acceptance criteria are detailed and testable, the compliance gate design is rigorous, and the consent architecture is production-grade. From a pure product and AC quality standpoint, this is the most complete of the three AI Continuity Loop specs at v1.

However, the spec has a structural delivery gap that prevents planning from beginning with confidence: **there is no milestone map, no mandated planning artifact, no combined cross-team capacity review, and no contingency path for the highest-probability external blocker (OQ-1 data residency)**. Four blocking conditions prevent safe planning sign-off as written.

Four blocking conditions (B1–B4) and four high-priority items (H1–H4) are documented below. If all four blocking conditions are addressed in v2, the projected score clears 9.0.

---

## Section 1 — Blocking Conditions

Blocking conditions are delivery gaps that prevent the planning team from safely sequencing or committing to execution. Each must be resolved in the spec before planning can begin.

---

### B1 — No Milestone Map Mandate

**The gap:** The spec defines P1, P2, and P3 tracks with gate checklists, but contains no week numbers, no critical path analysis, and no mandate to produce a milestone map before execution begins. Unlike Component 2 (Predictive Adherence AI, v2), which explicitly required a Week 0 milestone map as a P1-G0 prerequisite, this spec has no equivalent artifact requirement. The delivery team has no authoritative reference for: when P2 begins relative to P1 completion, when ElfieCare integration work must start, or what the critical path through OQ-1 resolution looks like.

**Why it blocks planning:** Without a milestone map mandate, there is no project plan cadence to enforce. Individual gate checklists without sequencing information cannot support resource planning, cross-team coordination, or schedule risk management.

**Required fix:** Add a P1-G0 gate item requiring a Week 0 milestone map to be produced by the Project Manager before any development begins. The map must show: P1 / P2 / P3 start and end target dates, ElfieCare and Elfie Mobile integration windows, OQ resolution deadlines, and the Medical Affairs review schedule across all P1-G0, P3-G1, and ongoing touchpoints. This is a planning artifact mandate — it does not need to be in the spec itself, but the spec must require it.

---

### B2 — Combined ElfieCare Backlog Risk Not Assessed

**The gap:** This spec requires ElfieCare engineering to deliver 4 items (pre-visit summary card, acknowledgment flow, inbound summary API, unavailable state — P1-G0-2). Component 2 (Predictive Adherence AI) independently requires ElfieCare to deliver 4 separate items (inbound alert API, alert card UI, delivery confirmation endpoint, ToS re-acceptance screen). That is 8 distinct ElfieCare deliverables across 2 features.

This spec requests a capacity commitment from ElfieCare EM in isolation. If ElfieCare EM signs off on Component 3's 4 items without the Component 2 scope in view — or if both commitment requests are processed by different Product Managers simultaneously — the resulting "capacity confirmed" signal is structurally unreliable.

**Why it blocks planning:** A false capacity confirmation from ElfieCare EM cascades silently. If ElfieCare deprioritizes either feature's deliverables mid-execution, the Elfie backend pipeline (which is "push" dependent on ElfieCare's inbound API) has no fallback. Both features' P2 tracks fail simultaneously, not progressively.

**Required fix:** P1-G0-2 must be amended to reference the combined Component 2 + Component 3 ElfieCare deliverable scope and require a single consolidated capacity commitment from ElfieCare EM. The commitment request should be coordinated across both feature PMs and must confirm: total sprint capacity available, sequencing plan for which feature's deliverables land in which sprint, and named engineering contact per deliverable group.

---

### B3 — OQ-1 Contingency Path Absent

**The gap:** OQ-1 (VN PDPD / TH PDPA data residency for LLM API calls) is a P2-G0-3 gate item — P2 cannot begin until it is resolved. The spec correctly identifies that OQ-1 "may require in-country LLM deployment or alternative provider." However, the spec defines only one outcome path: if OQ-1 resolves favorably (current cloud provider + BAA = compliant), proceed to P2. There is no defined path for the adverse outcome.

If OQ-1 resolution requires an in-country LLM deployment or a provider change, the entire P2 scope is affected: the BAA signed at P1-G0-1 may need to be renegotiated with a new provider, the model version pinned in AC 2.4 may change (triggering compliance gate re-testing), and data residency infrastructure adds scope that does not exist in any P track. OQ-1 resolution is estimated at 4–8 weeks (Legal-dependent); an adverse outcome adds an undefined further timeline.

**Why it blocks planning:** Planning cannot commit to a P2 start date without understanding the conditional scope attached to OQ-1. If the adverse path adds 8–16 weeks of infrastructure work, the milestone map cannot be constructed and resource commitments to ElfieCare integration become premature.

**Required fix:** Add an OQ-1 contingency section to the Pre-Launch Requirements. Define two explicit resolution paths:
- **Path A (favorable):** Cloud provider BAA + confirmed compliant data region for VN/TH → proceed to P2 as scoped.
- **Path B (adverse):** In-country requirement or provider change required → enumerate added scope (provider evaluation, new BAA, infrastructure provisioning, compliance gate re-test against new model), identify new gate items, and estimate additional calendar impact.

Path B does not need to be fully scoped in v1 — but the spec must acknowledge it exists, define its trigger condition, and assign ownership of the contingency assessment to Legal + Technical Advisor with a resolution deadline (recommended: resolve before P1 complete, not only at P2-G0).

---

### B4 — Medical Affairs Capacity Unconfirmed at P1-G0

**The gap:** Medical Affairs is a named reviewer or approver at the following points: P1-G0-4 (system prompt), P1-G0-5 (prohibited terms), P3-G0-2 (compliance gate test suite), P3-G1-1 (doctor acknowledgment language), P3-G1-2 (summary disclaimer), P3-G1-3 (patient consent copy), P3-G1-4 (PDF disclaimer), P3-G1-5 (all product surface copy), AC 2.4 (model version sign-off), AC 5.6 (EU AI Act human oversight mechanism description — owner "Product" but requires MA input), AC 6.4 (monthly 20-summary post-launch review), AC 6.4 (mandatory bias/quality review on any compliance gate miss), and ad-hoc reviews on prohibited terms list updates after model version changes.

That is a minimum of **12 distinct Medical Affairs engagements** across the pre-launch lifecycle, plus ongoing post-launch obligations. The spec names no MA individual, no team size, and no review turnaround SLA. If Medical Affairs is one person shared across Component 1, 2, and 3 pipelines, the serialization bottleneck may add weeks to P3-G1.

**Why it blocks planning:** P1-G0-4 and P1-G0-5 (the first two MA gates) are P1-G0 blockers — nothing starts until these are signed off. If MA capacity is unconstrained, the project can proceed. If MA is resource-constrained across multiple features, P1 cannot start on the planned date without explicit scheduling. The project plan cannot be drafted without this information.

**Required fix:** Add P1-G0-6: Medical Affairs capacity confirmation. The confirmation must include: (a) named MA reviewer(s) assigned to this feature, (b) review turnaround SLA for each engagement type (initial system prompt review: X business days; P3 copy batch review: Y business days), (c) MA engagement schedule across all P tracks reconciled against concurrent Component 1 and Component 2 MA obligations.

---

## Section 2 — High-Priority Items

High-priority items are planning risks that do not block spec approval but must be resolved before execution reaches the relevant gate. They do not block planning sign-off but must be tracked as open delivery risks.

---

### H1 — BAA Gates All P1 Work, Including BAA-Independent Deliverables

**The risk:** P1-G0 is structured as a single gate — all 5 items must clear before "any development begins." P1-G0-1 is the BAA. Of the 9 P1 track deliverables, 7 are architecturally independent of the LLM and have zero dependency on the BAA: Data Collector, Delta Analyzer, Consent data model, Pseudonymization, Audit log, Idempotency, and Pipeline atomicity. Only LLM prompt construction and the Compliance Gate require the BAA to be meaningful (since without the BAA you cannot pass health data to the LLM in any environment).

Enterprise LLM BAA negotiations with Anthropic or OpenAI take 2–8 weeks. Holding all 9 P1 deliverables hostage to BAA completion delays the project start by 2–8 weeks without technical justification. If the BAA takes 6 weeks, 7 deliverables that could have been in progress since Day 1 are 6 weeks behind schedule.

**Required action:** Before P1 kickoff, the team should resolve whether BAA-independent P1 work (Data Collector, Delta Analyzer, Consent model, Pseudonymization, Audit log, Idempotency, Pipeline atomicity) may begin immediately, with only LLM prompt construction and Compliance Gate development gated on BAA completion. If this split is agreed, the milestone map (B1) must reflect the two-track P1 start.

Note: If Component 2's BAA (same provider) is already signed or in progress, this may already be resolved — confirm at P1-G0 kickoff.

---

### H2 — Staged Rollout "Zero Compliance Gate Misses" Is Not Independently Verifiable

**The risk:** P3-G5 success criteria include "zero compliance gate misses in first 2 weeks." A compliance gate miss is defined as a case where the LLM produced prohibited language that passed the gate and was delivered to a doctor. At 100 active pairs generating approximately 100–200 summaries over 2 weeks, the only mechanism to verify zero misses is a full human review of all delivered summaries. The spec does not mandate this review for the staged rollout cohort — the 20-summary monthly review in AC 6.4 is post-launch only.

If the compliance gate has an undetected false negative pattern (a new prohibited phrasing not in the terms list), it will not be caught through monitoring metrics alone. Monitoring tracks compliance gate *activations*, not missed detections.

**Required action:** Add a P3-G5 gate item requiring 100% human review of all summaries delivered during the staged rollout period (100 pairs × up to 2 weeks = bounded, finite set). Medical Affairs or a trained reviewer conducts the review. Any prohibited language found in a delivered summary is an immediate rollout pause trigger and a compliance gate re-deployment event. This is distinct from the ongoing 20/month post-launch sample.

---

### H3 — Consent Revocation SLA Breach: No Regulatory Notification Path

**The risk:** AC 6.3 alerts on-call on any consent revocation deletion SLA breach (zero tolerance). P3-G4-4 mandates a runbook for consent revocation breach. But neither AC 6.3 nor P3-G4-4 defines what the runbook must accomplish at a regulatory level. Specifically:

1. VN PDPD and TH PDPA may require that a data subject (patient) be notified when their erasure/deletion request is not processed within the required period. The spec does not define whether a 24h SLA breach constitutes a notifiable event under either regime.
2. If the automated deletion pipeline has failed (the most likely cause of a breach), there is no defined force-deletion escalation path in the spec.
3. The spec does not define who owns the patient notification decision if a breach occurs.

A "write a runbook" gate item without content guidance produces a runbook that does not meet regulatory requirements.

**Required action:** Expand P3-G4-4 to specify that the consent revocation breach runbook must cover: (a) automated breach detection → manual force-deletion escalation path with a named owner, (b) patient notification decision tree (notify vs. not notify based on Legal assessment of VN PDPD / TH PDPA), (c) regulatory notification assessment (is this a reportable breach under applicable law?), (d) timeline for completing forced deletion after breach detection. Legal must sign off on the runbook before P3-G4 gate passes.

---

### H4 — OQ-7 (Doctor Re-acknowledgment) Has No Operational Playbook

**The risk:** OQ-7 asks whether all existing acknowledgments are invalidated when the acknowledgment language is updated, or only on next doctor action. The spec correctly defers this to "resolve before P3-G1." But the spec does not define what the operational answer requires — only the legal ruling.

If the answer is "all acknowledgments are invalidated immediately on language update," the operational consequence is: every scheduled push for every active doctor-patient pair is suspended until that doctor re-acknowledges. At launch scale, this could be hundreds of pairs. There is no batch re-acknowledgment campaign design in the spec, no defined owner for running such a campaign, no defined in-ElfieCare UI for surfacing a mass re-acknowledgment prompt, and no assessment of the doctor communication required.

If the answer is "only on next doctor action," the risk is that summaries continue to be delivered under old acknowledgment language for doctors who haven't visited ElfieCare recently — which may have legal exposure depending on the nature of the language change.

**Required action:** OQ-7 resolution must be paired with an operational playbook addressing both possible rulings: (a) immediate invalidation path — bulk re-acknowledgment campaign design, owner, and in-app UX; (b) lazy invalidation path — define the time boundary and patient communication if a doctor receives a summary under deprecated acknowledgment language. This playbook must be reviewed by Legal and Product before P3-G1.

---

## Section 3 — Scorecard

| Dimension | Weight | Score | Weighted | Notes |
|---|---|---|---|---|
| User value clarity | 20% | 9.5 | 1.90 | Purpose is unambiguous; "data synthesis tool / pre-visit briefing" framing is consistent throughout; physician and patient value both clearly stated |
| Scope precision | 15% | 8.0 | 1.20 | Scope-in/out table is clean; VN/TH boundary is hard-gated; cross-team deliverables enumerated; deducted for combined ElfieCare backlog risk (B2) and OQ-1 scope uncertainty (B3) which create scope ambiguity in P2 |
| AC quality | 20% | 9.0 | 1.80 | Best-in-class at v1: named constants, specific test types, verification clauses per AC. Minor deduction: OQ-3 (last visit date source) could silently invalidate AC 1.2 period calculation if data source is inaccurate — fallback behavior should surface to doctor |
| Technical feasibility | 20% | 8.5 | 1.70 | Pipeline components (OLS, LLM + compliance gate, consent model, pseudonymization) are all established patterns consistent with Component 2. OQ-1 adds unknown scope to the LLM data path. Not assigning TA-level issues — defer to TA review |
| Regulatory compliance | 15% | 9.5 | 1.43 | Outstanding: dual consent, 7-year audit log, pseudonymization consistent with Component 2, EU AI Act pre-documentation, geo-gate, prohibited framing list, compliance gate with version-controlled terms list, SOAP-like structure to avoid diagnostic framing. Minor deduction: H3 (revocation breach lacks regulatory notification path) |
| Delivery realism | 10% | 5.0 | 0.50 | Four blocking delivery gaps: no milestone map mandate (B1), combined ElfieCare backlog unaddressed (B2), OQ-1 contingency absent (B3), MA capacity unconfirmed (B4). These are the primary score suppressor. |

**Total weighted score: 8.53 / 10.0**

---

## Section 4 — Verdict

**⚠️ CONDITIONAL — Score 8.53 / 10.0. Not APPROVED.**

The spec does not meet the 9.0 threshold. Conditional approval requires all four blocking conditions to be resolved in v2. High-priority items H1–H4 do not block approval but must be tracked as open delivery risks and resolved before their respective gate stages.

### Conditions for approval (all required):

| # | Condition | Gate |
|---|---|---|
| C1 | Add P1-G0 gate item mandating a Week 0 milestone map (B1) | P1-G0 |
| C2 | Amend P1-G0-2 to require consolidated Component 2 + Component 3 ElfieCare capacity commitment from a single EM review (B2) | P1-G0 |
| C3 | Add OQ-1 contingency section defining Path A (favorable) and Path B (adverse) resolution paths with scope and ownership for the adverse path (B3) | Before P1 complete |
| C4 | Add P1-G0-6: Medical Affairs capacity confirmation with named reviewer(s), review SLAs, and cross-feature schedule reconciliation (B4) | P1-G0 |

### Projected score if C1–C4 resolved: **9.10 / 10.0**

The four high-priority items (H1–H4) account for the remaining 0.10 gap between projected score and a perfect delivery realism score. These are tracked delivery risks, not spec defects.

---

## Section 5 — Pre-Kickoff Planning Actions (non-conditions)

These items do not require spec changes but must be actioned at Week 0 planning regardless of approval status.

| # | Action | Owner |
|---|---|---|
| PK-1 | Confirm whether Component 2 BAA is already signed or in progress; if yes, Component 3's P1-G0-1 timeline may be compressed | Legal + PM |
| PK-2 | Initiate OQ-1 resolution with Legal immediately; target resolution before P1 completes so P2-G0-3 is not a last-minute block | Legal |
| PK-3 | Initiate OQ-3 resolution (last visit date source) early; if ElfieCare does not maintain structured visit dates, the period calculation fallback must be explicitly surfaced in summary UI | Product + ElfieCare EM |
| PK-4 | Confirm whether OQ-6 (PDF vs. encrypted email) requires any P2 scope expansion before P2-G0 | Product |
| PK-5 | Schedule Medical Affairs for P1-G0-4 and P1-G0-5 reviews as soon as draft system prompt and prohibited terms list are ready; do not let these become P1 exit-stage blockers | PM + Medical Affairs |
| PK-6 | Align with Component 2 PM on ElfieCare sprint allocation — confirm which feature's deliverables land first and in which order | PM + ElfieCare EM |
