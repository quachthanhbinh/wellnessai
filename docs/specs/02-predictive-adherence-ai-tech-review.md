# Technical Advisor Review — Predictive Adherence AI (Draft v1)

**Reviewer:** Technical Advisor  
**Review date:** 2026-06-01  
**Spec version under review:** Draft v1  
**Verdict:** ❌ NOT READY — Score 6.4 / 10.0 (threshold: 9.0)

---

## Executive Summary

The spec shows solid foundational thinking and genuine product clarity. The goal, the feature engineering direction, and the consent model are sound starting points. However, the spec contains **4 Critical defects** that would cause implementation to either fail or create legal exposure, and **9 High-severity issues** that would produce a model or system that cannot meet its own stated acceptance criteria. The spec cannot be approved in its current form.

---

## CRITICAL Risks (Blockers — must be resolved before re-review)

---

### CRIT-1 — AUC Benchmark Is Invalid for the 11-Feature MVP Scope

**Location:** Scope (feature list), AC 1.2, Research: `technical-feasibility.md`

The spec targets AUC 0.78–0.85 and Precision@top10% ≥ 65% in AC 1.2. These benchmarks are lifted directly from the technical feasibility research, which states they are achievable with "~40–60 features." The MVP scope lists **11 features** — excluding the features that research identifies as having the strongest predictive signal: `medication_time_variance`, `bp_trend_14d`, `weight_volatility`, `sleep_regularity_score`, `last_vital_logged_hours`, and `session_length_trend`.

The research explicitly names `medication_time_variance` (variance in timing) as a strong dropout predictor and `vitals_log_slope_14d` is included but `last_vital_logged_hours` (recency since last log) is not — a recency signal is among the most predictive features in churn models. Running an XGBoost model on 11 features of which 3 are categorical/boolean (`disease_type`, `family_paired`, and indirect `time_since_diagnosis`) against the AUC targets from a 40–60 feature benchmark is an unvalidated assumption.

**Consequence:** The team will complete the full bias annotation, legal, and infrastructure pre-launch tracks (14+ combined weeks) only to discover at model validation (Gate P1-6) that AUC 0.78 cannot be achieved with this feature set. The launch gate will fail.

**Required fix:** Either (a) expand the MVP feature list to include the minimum set validated by internal offline experiments, with documented offline AUC evidence before spec approval, or (b) lower the AUC acceptance criteria to a threshold validated against the 11-feature set. The acceptance criteria must match the feature scope, not a larger feature set researched separately.

---

### CRIT-2 — AC 4.2 Rotating Salt Destroys Consent Revocation, Tombstoning, and Retraining Continuity

**Location:** AC 4.2, AC 4.5, AC 6.2, Research: `regulatory-and-compliance.md`

AC 4.2 specifies training data pseudonymization as "SHA-256 with rotating salt." This creates three compounding failures:

**Failure A — Right to Erasure is unenforceable.** Under PDPD (Vietnam), PDPA (Thailand), and their GDPR-equivalent profiling rights, pseudonymized data remains personal data if re-identification is possible via the key. SHA-256 with a rotating salt means a different training run produces a different hash for the same user. The right to erasure (AC 4.5, the 5-step tombstoning pipeline) requires identifying and removing all records belonging to a consenting user across all historical training datasets. With rotating salts, you cannot identify which records in a historical training snapshot belong to user X — the hash has changed. The tombstoning pipeline cannot work.

**Failure B — Cross-run retraining continuity is broken.** AC 6.2 specifies quarterly retraining with promotion criteria that require model performance comparison over time. If user identifiers change across training runs, you cannot detect data quality issues per user, cannot weight by recency, and cannot apply curriculum learning. The intervention feedback loop (AC 6.1, response events as retraining signals) requires linking a user's future behavior back to their training record — impossible with rotating salts.

**Failure C — The research doc itself contradicts this approach.** `regulatory-and-compliance.md` shows a pseudonymization approach using a "stable hash (same user = same hash, but irreversible)." AC 4.2 specifies the opposite. The research recommendation is correct; the AC is wrong.

**Required fix:** Replace "SHA-256 with rotating salt" with a stable per-user pseudonymization key stored in a separate key vault (access-controlled, audited). The key vault supports erasure by deleting the user's key, rendering all pseudonymized records permanently de-linkable — satisfying right to erasure without requiring data deletion across training archives.

---

### CRIT-3 — Training Label Definition Leakage Risk and Internal Inconsistency

**Location:** Research `technical-feasibility.md` (label definition), AC 1.1, AC 1.2

The spec does not define the dropout label in the spec itself — it is only described in the research doc as: `label = 1 if user goes from "active" to "< 2 logs per week" within next 21 days`. Three defects:

**Defect A — Feature/label window overlap.** `vitals_log_slope_14d` and `coins_earned_7d_slope` are both computed over windows (7d, 14d) that end on day T. The label checks behavior from day T to T+21. If training set construction does not enforce a strict gap between the feature computation cutoff and the label observation window start, any event on day T that is both a behavioral signal AND an indicator of the label period starting will create leakage. The spec has no temporal guard specification in AC 1.1 or the feature engineering pipeline description.

**Defect B — "Active" baseline undefined.** The label says "goes from 'active' to < 2 logs per week." "Active" is not defined in any AC. If a user is already at 2.5 logs/week before the prediction window, they are trivially close to the label threshold — is that user labeled positive? The eligibility criterion (AC 1.4: "≥1 event in last 30 days") is far too permissive as an "active" baseline and will contaminate the label with already-inactive users who were never truly at risk.

**Defect C — Label definition does not match "dropout" detection.** `< 2 logs per week` for one week could mean a holiday, illness, or travel — not structural dropout. The research doc's conservative definition (< 1 log per 14 days in next 30 days) is more robust. The spec's label definition risks labeling temporary disengagement as dropout, reducing label quality, and training a model that fires interventions at vacation travelers.

**Required fix:** Define the label formally in an AC. Specify the temporal gap enforced between feature cutoff and label window start. Define "active" with a minimum activity baseline. Include a "sustained inactivity" minimum (e.g., < 2 logs/week for 2 consecutive weeks) rather than a single-week threshold.

---

### CRIT-4 — ElfieCare Alert "No Action Logging" Is a Liability Trap, Not a Mitigation

**Location:** AC 2.3, Pre-Launch P2, Research: `regulatory-and-compliance.md`

The research doc recommends: "Không track hoặc log xem bác sĩ có hành động hay không (tránh tạo paper trail)." This reasoning is flawed and creates greater liability, not less.

**The actual liability scenario:** Elfie sends a High-tier ElfieCare alert. The patient later has an adverse event. In litigation, Elfie's audit trail (AC 4.4) shows the alert was sent. There is no record that the doctor acknowledged it. The doctor's defense is: "I never saw it, the system failed to deliver it." Elfie has sent a health-behavioral alert to a healthcare provider about a patient outcome — creating an implied duty of care — without any confirmation of delivery or acknowledgement. This is worse than having a dismissal log.

**Compounding issue:** AC 2.3 mandates "non-blocking on failure" for ElfieCare alerts. A High-tier intervention alert to a doctor can silently fail to deliver, with no retry escalation specified for the ElfieCare channel specifically. The spec should distinguish between push notification failure tolerance (acceptable) and doctor alert failure tolerance (not acceptable for the same threshold).

**Required fix:** Define a separate delivery guarantee for ElfieCare alerts (at minimum: delivery confirmation, not just "sent"). Add an explicit "alert received" state distinct from "alert acted upon." Do not log whether the doctor acted — that is correct. But delivery confirmation is legally required. Remove the "no logging" guidance; replace with "log delivery state only, not clinical response."

---

## HIGH Risks (Must be resolved before launch gate sign-off)

---

### HIGH-1 — Risk Tier Boundaries Are Internally Inconsistent With Intervention Selector

**Location:** Scope (Intervention Menu), Research: `technical-feasibility.md` (InterventionSelector code)

The spec defines tiers as Low [0.0–0.4], Medium [0.4–0.7], High [0.7–1.0]. The research doc's `InterventionSelector` uses entirely different thresholds: `< 0.6` for low-cost interventions and `< 0.75` for social accountability. A score of 0.65 would be Medium tier (triggering coin bonus or streak challenge) per the spec, but `InterventionSelector` code would send personalized content or family nudge. The tier boundaries and the selector logic are misaligned by design. When the engineering team implements this, they will have two incompatible reference documents.

**Required fix:** Reconcile the tier boundaries with the intervention selector thresholds in a single authoritative AC. Define whether the selector uses the tier enum or the raw `risk_score` float — these are different architectures with different implications for audit traceability.

---

### HIGH-2 — Batch Pipeline "Rollback to Last Successful State" Is Not Implementable as Described

**Location:** AC 5.3

"Rollback" in a batch scoring pipeline has no standard meaning. The spec does not define:
- Whether rollback means reverting risk scores in the feature store, reverting the intervention queue, or both
- Whether a 80%-complete batch that fails is partially committed (scores for completed users are written) or fully atomic
- The maximum staleness of "last successful state" scores that are safe to act on for High-tier doctor alerts

A partially failed batch where 60,000 of 100,000 users are scored creates a split state: some users have fresh scores, others have 24-hour-old scores. Firing doctor alerts based on stale High-tier scores is the precise liability scenario described in CRIT-4.

**Required fix:** Define whether the batch is atomic (all-or-nothing write via a staging table swap) or checkpoint-based. Specify a maximum score age policy: above X hours, High-tier interventions are suppressed, not fired on stale data. This must be an AC, not a deployment note.

---

### HIGH-3 — Bias Monitoring Thresholds Are Statistically Vacuous at MVP Scale

**Location:** AC 3.2, OQ-2

AC 3.2 requires per-demographic-slice AUC with a ±15 percentage point disparate impact threshold, quarterly. OQ-2 admits demographic field coverage is unknown. For VN + TH-only geo-gate with chronic disease users:

- The elderly (65+) slice in a mobile health app in SEA is typically <5% of DAU
- Rural vs. urban, which is a significant health disparity dimension in both markets, is not a declared demographic field
- At 5% of, say, 50,000 active users = 2,500 users in the slice, with dropout events at a base rate of ~20–30%, you have ~500–750 positive labels for evaluation
- At n=500 positives, the 95% confidence interval on an AUC of 0.78 is approximately ±0.037 — meaning a real 15pp disparity could be statistically indistinguishable from noise

The ±15pp threshold will pass audits for small slices purely because the confidence intervals overlap, creating a false assurance of fairness.

**Required fix:** Add a minimum-slice-size requirement for bias monitoring to be valid (e.g., ≥1,000 users with ≥200 positive labels per slice). Specify what happens when a demographic slice is too small to audit: either (a) the demographic dimension is excluded from the model features entirely, or (b) the slice is bootstrapped and reported with explicit uncertainty bounds.

---

### HIGH-4 — Feature Store P95 Latency SLA Conflates Batch and Online Serving Contexts

**Location:** AC 5.2

"Feature store read ≤200ms P95" is an online serving SLA. In the batch context, 100,000 users are read via bulk operations — the relevant metric is throughput (records/second) and total batch read time, not P95 per-record latency. If the feature store is optimized for 200ms P95 single-record reads (as in an OLTP serving layer), it will be wrong architecture for batch bulk reads. Conversely, if optimized for batch throughput, the 200ms P95 is not a meaningful measure of anything.

**Required fix:** Separate the feature store SLA into two contexts: (a) batch read throughput (minimum N records/second to complete the read phase within the 4-hour window), and (b) online serving P95 (only relevant if real-time scoring is added in v2). Remove the 200ms P95 from batch AC 5.2.

---

### HIGH-5 — Feedback Loop Creates Label Contamination in Retraining

**Location:** AC 6.1, AC 6.2, Scope — Out (A/B testing framework listed as v2+)

A/B testing is explicitly out of scope for MVP and v2+. The feedback loop ingests intervention response events as retraining signals. Without a control group (users who were at High risk but did not receive an intervention), the model will learn from a biased population: only users who received interventions. Users who improved will reinforce the model's behavior; users who churned despite intervention are rare in the High tier by Precision@top10% design.

The retraining signal in AC 6.2 will gradually produce a model that is optimized for "users who respond to interventions" rather than "users who are about to churn." The model will drift toward a selection-bias equilibrium, increasing false-positive rates over time as it learns to fire interventions at users who are already re-engaged.

**Required fix:** Either (a) define a holdout arm (a fraction of high-risk users who receive no intervention, preserved for label quality), or (b) define a retraining data policy that excludes all users who received an intervention from the positive-label training set during the quarter of their intervention. The spec must acknowledge this confound explicitly and document the chosen mitigation.

---

### HIGH-6 — Under-18 Exclusion Enforcement Is Undefined for Family-Managed Profiles

**Location:** AC 4.6, Platform context: Family Care

The Elfie platform explicitly supports child profiles managed by parents, including health tracking for toddlers and children. AC 4.6 states "no profiling of under-18 users" but does not specify:

- Whether the age check applies to the **account holder** (parent, adult) or the **profile being scored** (the child)
- How the under-18 exclusion is enforced for a family account where the adult's device logs both parent and child health events and the event log `user_id` may refer to either
- Whether a child profile managed under an adult account gets an `eligible_for_scoring` flag set at the profile level, not the account level

If the scoring pipeline excludes based on account holder age only, child profiles could be scored. If it excludes based on profile-level age and that field is absent or defaulted (many child profiles in health apps don't have DOB), the exclusion silently fails.

**Required fix:** Add an AC specifying (a) that scoring eligibility is checked at the **profile level** (not account level), (b) that profiles without a verifiable DOB are excluded by default, and (c) that the under-18 check is applied before any feature computation, not just before intervention delivery.

---

### HIGH-7 — High-Tier Cooldown Conflict Unresolved: Fatigue Guard vs. Clinical Need

**Location:** AC 3.1, AC 2.3

AC 3.1 mandates `MAX_INTERVENTIONS_PER_7_DAYS = 1` as a hard cap. This applies uniformly. A user who is genuinely deteriorating (e.g., no medication logs for 6 days, dropping vitals frequency) and whose risk score climbs from 0.75 to 0.92 during the 7-day cooldown window will receive no second intervention or doctor alert, because the first intervention was the week's quota.

The spec does not define whether the ElfieCare doctor alert counts against the user's fatigue cap. If it does: a user can receive a doctor alert but no user-facing intervention (or vice versa), which creates a scenario where the doctor is alerted to a patient they cannot reach because the user-facing channel is cooled down. If the doctor alert does not count against the cap: the ElfieCare alert path bypasses the fatigue guard entirely, which could fire daily doctor alerts.

**Required fix:** Define explicitly whether ElfieCare alerts count against the fatigue cap. Define an exception path for rapidly deteriorating High-tier users (e.g., score increase > N within the cooldown window triggers one override alert).

---

### HIGH-8 — EU AI Act Classification Is an Open Question but Must Be a Hard Gate

**Location:** OQ-5, Launch Gate item 12, Pre-Launch P2

OQ-5 asks: "EU AI Act classification status." The EU AI Act enforcement applies to systems deployed on EU residents from August 2026 — and Elfie operates in 30+ countries, including EU member states. Even with a VN + TH geo-gate for this feature, Elfie's existing EU user base creates risk if the classification question is unresolved and EU expansion is planned without re-architecture.

More critically, the EU AI Act requires that **before a high-risk AI system is placed on the market**, a conformity assessment is completed and technical documentation exists. "Open question" is not a valid pre-launch state for a feature that sends health-behavioral profiles to healthcare providers. The current classification argument (limited risk) requires legal validation, not just internal assumption.

**Required fix:** OQ-5 must become a hard gate in the Legal track (P2), not an open question. The launch gate checklist item 12 already lists it — but it must have a binary resolved/blocked state. Conditional launch without EU AI Act classification is not acceptable for a system that involves health data and healthcare professionals.

---

### HIGH-9 — Push Notification Channel Lacks Security Specification

**Location:** AC 2.2, Scope — Execution Layer

The spec specifies push notification delivery with time windows and failure handling but contains no security specification for the notification payload. For chronic disease users:

- Push notification payloads in FCM/APNs can be rendered in the OS notification tray, potentially visible to bystanders — payloads referencing health status (e.g., "We noticed you may need some support with your medication") may constitute disclosure of health information to unauthorized parties
- The spec does not specify whether the notification content is generic (no health reference in payload) with the personalization loaded on app-open, or whether personalized health content is in the payload itself
- There is no mention of certificate pinning for the push delivery pipeline to prevent token hijacking and notification spoofing

**Required fix:** Define the notification payload content policy: health-sensitive content must not be in the notification payload; the payload should contain only a deeplink or action token, with content rendered only after authenticated app-open. Add this as an AC in Section 2.

---

## Scoring

### Dimension Scores

| Dimension | Weight | Score | Weighted |
|---|---|---|---|
| User value clarity | 20% | 8.0 | 1.60 |
| Scope precision | 15% | 5.5 | 0.83 |
| Acceptance criteria quality | 20% | 5.5 | 1.10 |
| Technical feasibility | 20% | 4.5 | 0.90 |
| Regulatory compliance | 15% | 5.5 | 0.83 |
| Delivery realism | 10% | 6.5 | 0.65 |
| **TOTAL** | **100%** | | **5.91** |

### Score Rationale

**User value clarity (8.0):** The goal is unambiguous, the 2-3 week detection window is well-motivated by behavioral science literature, and the opt-in consent model correctly centers user control. Deduction: no quantified retention improvement target stated; "2-3 weeks" detection is the research claim, not a validated internal benchmark.

**Scope precision (5.5):** The 11-feature list is specific. However, the features named in scope and the AUC benchmarks are from different studies with different feature counts — the scope and the success criteria are mismatched (CRIT-1). The intervention selector thresholds in the research doc conflict with the tier boundaries in the spec (HIGH-1). The label definition is absent from the spec entirely (CRIT-3).

**Acceptance criteria quality (5.5):** The AC structure is detailed and follows good practice. Deductions: AC 4.2 rotating salt contradicts AC 4.5 tombstoning (CRIT-2); AC 5.2 conflates batch and online SLAs (HIGH-4); AC 1.3 boundary specification is ambiguous (upper/lower inclusivity not stated); AC 3.1 hard cap does not specify ElfieCare alert counting (HIGH-7); no AC defines the training label formally.

**Technical feasibility (4.5):** Batch architecture, XGBoost choice, and intervention delivery are sound. Deductions: AUC benchmark unvalidated for MVP feature set (CRIT-1); batch rollback semantics unimplementable as described (HIGH-2); feedback loop creates label contamination without A/B holdout (HIGH-5); rotating salt breaks cross-run analytics (CRIT-2); no temporal cross-validation requirement for the model.

**Regulatory compliance (5.5):** Strong effort on consent, opt-out, and doctor alert framing. Deductions: SHA-256 rotating salt fails right-to-erasure (CRIT-2); ElfieCare no-action-logging guidance is counterproductive (CRIT-4); EU AI Act classification is open (HIGH-8); under-18 enforcement undefined for child profiles (HIGH-6); PDPA/PDPD erasure pipeline is architecturally broken (CRIT-2).

**Delivery realism (6.5):** Pre-launch tracks are appropriately scoped. Deductions: critical path is not calculated (P1 + P2 overlap creates 14+ week minimum before launch gate, not stated); doctor ToS amendment is a conditional blocker for the entire High tier that is not flagged as a scope-conditional dependency; OQ-1 (label data availability) is unresolved and blocks P1 Gate 1.

---

## Verdict

### ❌ NOT READY — Score 5.91 / 10.0

Threshold for approval: 9.0. Delta: −3.09.

---

## Conditions Required for Approval

The following must be resolved in a revised spec before re-review:

### Critical (Spec cannot proceed to planning without resolution)

| # | Condition |
|---|---|
| C1 | Provide offline AUC evidence (internal experiment or literature reference specifically for ≤15 features on behavioral app data) validating the 0.78 target for the MVP feature set — OR — revise AC 1.2 targets to match a validated 11-feature baseline |
| C2 | Replace AC 4.2 "rotating salt" with a stable per-user pseudonymization key vault architecture; confirm tombstoning pipeline in AC 4.5 can execute against stable keys |
| C3 | Define the training label formally in a new AC (include: dropout definition, minimum sustained inactivity duration, "active" baseline definition, and temporal gap specification between feature cutoff and label window start) |
| C4 | Replace AC 2.3 ElfieCare alert "no action logging" guidance with a defined delivery confirmation state; add a separate delivery guarantee SLA for the ElfieCare channel |

### High (Must be resolved before launch gate, documented in revised spec)

| # | Condition |
|---|---|
| H1 | Reconcile risk tier boundaries [0.4 / 0.7] with intervention selector thresholds in a single authoritative AC; specify whether selector uses tier enum or raw score |
| H2 | Define batch atomicity model (staging table swap or checkpoint); add maximum score staleness policy for High-tier intervention suppression |
| H3 | Add minimum slice size requirement (users + positive labels) for bias monitoring validity; define handling when a demographic slice is below the threshold |
| H4 | Separate batch throughput SLA from online serving P95 in AC 5.2 |
| H5 | Define retraining holdout policy or intervention-contamination exclusion rule to prevent feedback loop label corruption |
| H6 | Add profile-level (not account-level) under-18 exclusion AC; define default behavior for profiles without a verifiable DOB |
| H7 | Define whether ElfieCare alerts count against `MAX_INTERVENTIONS_PER_7_DAYS`; add exception path for rapid deterioration within cooldown window |
| H8 | Promote OQ-5 (EU AI Act classification) from Open Question to Hard Gate in Legal track P2; add binary resolved/blocked condition to Launch Gate item 12 |
| H9 | Add notification payload content policy AC: health-sensitive content must not appear in push notification payload; content loaded only after authenticated app-open |

---

*Next step: Return to Product Owner for spec revision. Re-submit for Technical Advisor review when all Critical conditions are addressed.*
