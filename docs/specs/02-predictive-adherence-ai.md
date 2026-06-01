# Predictive Adherence AI — Product Spec (Approved)

**Component:** AI Continuity Loop — Component 2 of 3  
**Status:** APPROVED FOR PLANNING  
**Date:** 2026-06-01  
**Spec version:** v3 (final, 3-round debate loop)  

---

## Debate Loop Summary

| Round | Technical Advisor | Project Manager | Key issues resolved |
|---|---|---|---|
| 1 | 5.91 | 5.78 | Draft only — 4 Critical + 9 High + 13 PM gaps |
| 2 | 8.47 | 7.95 | All Round 1 defects resolved; NM-1 introduced; PM CA-1–4 confirmed via TA |
| 3 | **9.03** | **9.00** | NM-1/2/3 fixed; CA-1–4 confirmed RESOLVED; both agents issued APPROVED |

---

## Goal

Detect Elfie user dropout risk 2–3 weeks ahead of disengagement and automatically deliver targeted, tiered interventions — gamification nudges for lower-risk users and engagement alerts to linked doctors for higher-risk users — so that chronic disease patients on the Elfie platform in Vietnam and Thailand maintain their medication adherence and health tracking habits without requiring manual outreach from the care team.

---

## Scope

### In (MVP)

1. **Behavioral dropout prediction model:** XGBoost / LightGBM trained on 11 behavioral and contextual features per user; daily batch scoring of all scoreable active users; outputs `risk_score` (0–1 float) and `risk_tier` enum (Low / Medium / High)
2. **Risk-tiered intervention selector:** maps `risk_tier` → intervention type from the Intervention Menu; enforces fatigue cap; fires interventions via push notification, in-app, or ElfieCare channels
3. **Intervention Menu (4 types):**
   - *Coin streak bonus* — 30 coins awarded on next authenticated app open (Medium tier)
   - *Streak protection challenge* — complete 1 activity to protect streak (Medium tier)
   - *Badge achievement nudge* — progress-to-next-badge prompt (Medium tier)
   - *Premium in-app engagement card* — full-screen modal on next app open (High tier)
   - *ElfieCare engagement alert* — doctor-facing engagement signal card (High tier, doctor-facing only, requires doctor linkage + ToS re-acceptance)
4. **Daily batch scoring pipeline:** feature engineering on 30-day behavioral windows; feature store write; intervention queue dispatch; 4-hour overnight batch window
5. **Feature store:** per-user feature vector storage (Postgres JSONB or Redis Hash extension); batch export path for scoring; online read API for audit and admin tooling
6. **Explicit opt-in consent flow:** separate from Elfie ToS; opt-out toggle in Settings → Privacy → AI Predictions; no penalty for opting out
7. **Key vault-based right-to-erasure pipeline:** stable per-user pseudonymization; key deletion = permanent non-re-linkability (AC 4.2, AC 4.5)
8. **Bias monitoring:** quarterly per-demographic-slice AUC evaluation with bootstrap confidence intervals; runnable audit script (P3-G5)
9. **Gamification integration:** AI-triggered coin bonuses via existing Elfie coin pipeline
10. **VN + TH geo-gate:** scoring and delivery restricted to Vietnam and Thailand; server-side country code from registration record
11. **Holdout cohort (5%):** deterministic hash-based; scored but no interventions; excluded from training; primary business impact measurement vehicle (AC 6.4)

**ElfieCare Integration (cross-team dependency):** New capability required in the ElfieCare doctor workspace:
- (a) New inbound engagement alert API endpoint (ElfieCare backend team)
- (b) New UI surface: alert card with "Dismiss" and "Snooze 7 days" actions
- (c) Delivery confirmation endpoint (returns `200 OK` when alert persisted in doctor workspace)

Named cross-team dependency: ElfieCare engineering team. Engagement required before P2 begins. ElfieCare team must provide estimated engineering effort, sprint availability, and delivery commitment before this spec is approved for planning.

**Doctor ToS Re-Acceptance Flow:** Existing ElfieCare doctors must re-accept the amended ToS before receiving High-tier engagement alerts. Mechanism: in-product re-acceptance screen on next ElfieCare login (ElfieCare frontend). Patient protection during window: patients linked to non-accepting doctors are Medium-tier maximum (High-tier ElfieCare alert suppressed).

**Notification Pipeline Enhancements:** Existing Elfie push notification pipeline extended with: (a) per-user local timezone delivery scheduling (08:00–20:00 window), (b) payload security enforcement (no health content per AC 2.5), (c) intervention-specific idempotency key support. If platform team owns the notification service, they are a named dependency.

**Premium Engagement Card UI Component:** Full-screen modal card on next app open. Design deliverables required before P3-G2: (a) Figma mockup reviewed by UX Lead and Medical Affairs, (b) component specification (animation, dismiss behavior, CTA variants, dark mode), (c) iOS and Android implementation. Named design owner required before P1 begins. Fallback: if no design owner at Week 0, defaults to standard in-app banner for MVP.

### Explicitly Out (v2+)

| Item | Reason deferred |
|---|---|
| Real-time / on-demand risk scoring | Batch-only MVP; real-time requires separate latency architecture |
| Family member third-party nudge | Separate consent model required for third-party-triggered interventions |
| Insurer-sponsored intervention tier | Commercial model not confirmed for MVP markets |
| LLM-generated personalized copy | Depends on AI Health Coach safety layer (Component 1); separate dependency not resolved at MVP |
| EU / US / global rollout | Blocked: P2-G0 EU AI Act classification; FDA non-device framing not validated in US |
| Causal inference (treatment effect estimation) | Post-MVP when sufficient intervention response data exists |
| Online (continuous) retraining | Adds significant infra complexity; periodic offline retraining is MVP |
| Additional features: `medication_time_variance`, `bp_trend_14d`, `weight_volatility`, `sleep_regularity_score`, `last_vital_logged_hours` | v2+ feature expansion after MVP AUC validated |
| A/B testing framework | Holdout cohort (AC 6.4) provides controlled impact measurement without full A/B framework |
| User-visible explanation of "why this intervention" | v2+ after intervention feedback data matures |

---

## Acceptance Criteria

### Section 1 — Model & Scoring

**AC 1.1 — Feature Set (MVP: 11 features)**

The production model is trained on the following 11 behavioral features computed from Elfie event logs:

| Feature | Type | Window | Signal |
|---|---|---|---|
| `medication_adherence_7d` | Float [0,1] | 7-day | % doses logged on time |
| `medication_streak_current` | Integer | Point-in-time | Current unbroken adherence streak length (days) |
| `medication_missed_last_3d` | Integer | 3-day | Count of missed medication days in last 3 days |
| `vitals_log_frequency_7d` | Float | 7-day | Vitals log events per week |
| `vitals_log_slope_14d` | Float | 14-day | Linear trend in vitals log frequency (OLS slope; declining = risk) |
| `dau_wau_ratio` | Float [0,1] | 7-day | Daily active / weekly active ratio |
| `notification_open_rate` | Float [0,1] | 14-day | Rate of push notification opens |
| `coins_earned_7d_slope` | Float | 7-day | Linear trend in coins earned (declining = disengagement) |
| `disease_type` | Categorical | Static | Primary disease (hypertension / diabetes / other) |
| `time_since_diagnosis` | Integer | Point-in-time | Days since diagnosis (new patients drop faster) |
| `family_paired` | Boolean | Point-in-time | Whether user has an active family accountability partner |

Model architecture: XGBoost or LightGBM. Training window: 30 days of behavioral history per user. Feature computation cutoff date: T. Mandatory temporal gap between T and label window: 7 days (AC 1.5).

*Verification:* Feature engineering unit tests confirm each feature computes correctly on 20 synthetic user trajectories. Pipeline integration test confirms all 11 features populated for ≥95% of eligible users in a staging batch run.

---

**AC 1.2 — Model Performance Thresholds**

| Metric | Threshold | Notes |
|---|---|---|
| AUC (ROC) — overall | ≥ confirmed by P1-G0; **floor: 0.72** | 5-fold temporal cross-validation (no random split) |
| Precision@top10% | ≥ 60% | Users ranked by descending risk_score |
| Recall of High-tier users | ≥ 65% | Users with true dropout in held-out test split |
| Brier score | ≤ 0.22 | Calibration metric |
| Positive label prevalence | ≥ 10% | If lower: SMOTE or class-weighting required; document method |

> **AUC threshold note:** The AUC threshold is locked after P1-G0 completes. Minimum acceptable floor is 0.72. If P1-G0 validates ≥0.78 is achievable, the threshold is set to 0.78. The threshold cannot be lowered without Technical Advisor approval.

Evaluation methodology: 5-fold temporal cross-validation. Each fold trains on data from earlier months and tests on a later month. Holdout cohort users (AC 6.4) are excluded from all model evaluation.

*Verification:* ML validation report for every model candidate: confusion matrix, ROC curve with AUC, Precision@top10%, Recall of High-tier users, Brier score, and 5-fold temporal cross-validation summary with per-fold AUC. Report reviewed and signed by Technical Advisor before model promoted to staging.

---

**AC 1.3 — Risk Tier Classification**

| Tier | Score range | Intervention action |
|---|---|---|
| Low | [0.0, 0.4) | No AI-triggered intervention |
| Medium | [0.4, 0.7) | Automated gamification intervention (AC 2.1) |
| High | [0.7, 1.0] | Premium in-app card + ElfieCare alert (if doctor linked + ToS accepted) |

Boundary values: 0.4 → Medium (inclusive); 0.7 → High (inclusive); 0.399 → Low.

The risk tier thresholds (0.4, 0.7) are named constants in code: `RISK_TIER_MEDIUM_THRESHOLD = 0.4`, `RISK_TIER_HIGH_THRESHOLD = 0.7`. Not configurable via feature flag, environment variable, or admin panel. Changes require code deployment with Technical Advisor review.

> **Authoritative thresholds note:** The 0.4/0.7 boundaries are authoritative in this spec. Pre-spec feasibility documents contain exploratory threshold values (0.6, 0.75) that are superseded by this spec. Any reference to alternative thresholds in research files or design documents is non-binding.

*Verification:* Unit tests asserting correct tier assignment for boundary values: 0.0, 0.399, 0.4, 0.699, 0.7, 1.0. Code review confirming thresholds are named constants not backed by config.

---

**AC 1.4 — Scoring Eligibility**

A user is included in the daily scoring batch if and only if ALL four conditions are met:
1. User has opted in to AI Predictions (AC 4.1) — consent recorded
2. User's profile age is ≥18 (profile-level check per AC 4.6)
3. User's registered country is VN or TH (server-side geo-gate)
4. User has logged ≥1 event in the last 30 days (minimum activity signal)

Users not meeting all four criteria are excluded silently; no intervention triggered; no error logged. Eligibility re-evaluated on every daily batch cycle.

*Verification:* Batch pipeline integration test confirming ineligible users (no consent / under-18 profile / non-SEA / zero events in 30 days) are absent from scored output.

---

**AC 1.5 — Training Label: Sustained Dropout Definition**

The training label is formally defined as follows:

- **"Active" entry baseline:** A user qualifies for inclusion in the training population only if they were "active" (≥3 logs/week) for at least 2 of the 3 calendar weeks immediately preceding the feature computation cutoff date T. This filter prevents nearly-inactive users from inflating the positive label rate.
- **Feature cutoff date T:** The date through which all behavioral features are computed.
- **Mandatory temporal gap:** Minimum 7-day gap between feature cutoff T and label observation window start (T+7). No events from T through T+7 may be used in any feature computation.
- **"Dropout" label = 1:** User transitions to "inactive" — defined as < 2 logs/week for **2 consecutive calendar weeks** — within the label observation window (T+7 through T+28). Single-week inactivity alone does NOT trigger a positive label (prevents holiday / illness / travel false positives).
- **"No dropout" label = 0:** User remains at ≥2 logs/week for at least one of the two label-window weeks.
- **Label observation window closes at T+28.** The 2-consecutive-weeks dropout criterion requires observing two full calendar weeks within [T+7, T+28], giving 21 days of observation.
- **Treatment washout:** The 7-day period immediately following any prior AI-triggered intervention is excluded from label computation. If the label observation window overlaps a treatment period, that user-window pair is excluded from the training dataset.
- **Minimum positive label prevalence:** If training dataset has <10% positive label rate, oversample with SMOTE or class-weighting; document method in ML validation report.

*Verification:* Label computation script validated on 20 synthetic user trajectories covering: (a) single-week vacation (label = 0), (b) sustained 2-week dropout (label = 1), (c) recovery pattern (active→inactive→active; label per 2-consecutive-week rule), (d) post-intervention washout (user-window pair excluded), (e) near-inactive user not meeting active entry baseline (excluded from training population).

---

### Section 2 — Intervention Delivery

**AC 2.1 — Intervention Selector**

The Intervention Selector maps a user's `risk_tier` **enum value** (not raw `risk_score` float) to a single intervention per 7-day rolling window.

> The Intervention Selector operates on the `risk_tier` enum value (Low/Medium/High), NOT on the raw `risk_score` float. Risk tier is assigned once in the scoring pipeline (AC 1.3) and stored with the score. No re-evaluation of raw score inside the Intervention Selector.

Selection rules:
1. **Fatigue guard (first check):** if user received any AI-triggered intervention within the last 7 days → skip (no intervention this cycle); log fatigue cap hit
2. **Holdout check:** if user is in holdout cohort (AC 6.4) → skip (no intervention regardless of risk tier)
3. **Tier = Low:** no intervention; exit
4. **Tier = Medium:** select from {coin bonus, streak protection challenge, badge nudge} using:
   - `medication_streak_current ≥ 3` AND `medication_adherence_7d ≥ 0.5`: streak protection challenge
   - `coins_earned_7d_slope < 0` (declining coin engagement): coin bonus offer
   - Otherwise: badge achievement nudge
5. **Tier = High:** always trigger premium in-app engagement card; additionally trigger ElfieCare alert ONLY IF `user.elfiecare_doctor_linked = true` AND doctor has re-accepted ToS

Selector output is logged: user pseudonym, batch_date, risk_score, risk_tier, intervention_type_selected, elfiecare_alert_sent (boolean).

*Verification:* Unit tests for all 7 selector paths including holdout skip and fatigue cap skip. Integration test confirming `risk_tier` field is the sole input to selector logic. Test confirming doctor without ToS re-acceptance does not receive ElfieCare alert.

---

**AC 2.2 — Push Notification Delivery**

- Delivery window: 08:00–20:00 in user's registered timezone. Notifications outside this window are queued for the next delivery window.
- Delivery channels: APNs (iOS), FCM (Android), Web Push
- Failure handling: single non-blocking delivery attempt per push notification. On failure: log `delivery_state = failed`; do not retry; do not suppress user from next scoring cycle
- Payload: governed by AC 2.5 (generic title + body; deeplink only)
- Idempotency: each notification delivery uses `intervention_id` (UUID) as idempotency key; duplicate dispatch within same scoring cycle → no-op

*Verification:* Integration tests: (a) notification queued at 23:00 delivered after 08:00 next day; (b) delivery failure logged without retry; (c) duplicate `intervention_id` → no-op at push layer.

---

**AC 2.3 — ElfieCare Doctor Engagement Alert — Mandatory Framing and Delivery**

**Alert content (non-clinical; administrative engagement signal only):**
- Example message: *"[Patient display name] hasn't logged their medication in [N] days. You may want to check in with them."*
- Disclaimer displayed on every alert card: *"Elfie engagement signal · Not a clinical finding or recommendation."*
- Alert UI: alert card with "Dismiss" and "Snooze 7 days" actions

**Prohibited terms in doctor alert copy (version-controlled list):** "risk", "urgent", "critical", "deteriorating", "worsening", "alert", "requires action", any language implying clinical urgency or change in health status.

**Doctor ToS amendment (required before launch):** must include: *"Elfie engagement signals are informational only. They are not clinical alerts and do not create an obligation to take clinical action. Elfie does not accept liability for clinical decisions or omissions in response to engagement signals."*

**Delivery mechanism:**
- ElfieCare alerts use a delivery confirmation API endpoint (not fire-and-forget)
- Log delivery state per alert: `sent` / `confirmed` (ElfieCare API acknowledged) / `failed`
- Retry policy: up to 3 retries with exponential backoff (1h, 2h, 4h) before declaring failure
- On 3 consecutive delivery failures: trigger ops team alert. **The `ELFIECARE_ALERT_CAP_DAYS = 14` rolling window cap applies ONLY to confirmed-delivered alerts. Delivery failures do NOT count as delivered alerts for cap purposes and do NOT initiate the 14-day suppression window. Alert eligibility for the patient resumes as soon as the delivery channel is confirmed operational. The deterioration exception (`risk_score` increase ≥0.20 per AC 3.1) applies normally regardless of previous delivery failures.**
- Audit log: contains `delivery_state` and number of attempts; does NOT contain whether the doctor clinically responded

*Verification:* Integration test: ElfieCare API unavailable → 3 retries with correct backoff → failure logged → ops team alerted. Confirm: patient's alert eligibility is NOT suppressed after failure (only ops team alerted). Recovery test: failure at T=0 → channel restored at T=5h → patient intervention at T=6h → ElfieCare alert sent normally. Audit log entry: `delivery_state` present; no clinical action field. Prohibited term scan test on all alert templates: zero occurrences of banned terms.

---

**AC 2.4 — Intervention Delivery Specifications**

| Intervention | Tier | Channel | Delivery | Award/Action |
|---|---|---|---|---|
| Coin streak bonus | Medium | Push + in-app | Push (AC 2.5 compliant) → in-app on open | 30 coins credited on authenticated open + 1 qualifying log |
| Streak protection challenge | Medium | Push + in-app | Push (AC 2.5 compliant) → challenge card on open | 7-day completion window; streak rules unchanged |
| Badge achievement nudge | Medium | Push + in-app | Push (AC 2.5 compliant) → notification center | Badge unlockable in-app |
| Premium in-app engagement card | High | In-app only | Full-screen modal on next authenticated app open | Dismissable with 1 tap; logged as response event |

Intervention selection is idempotent per scoring cycle: same user, same batch date, same `intervention_id` → no duplicate delivery.

*Verification:* End-to-end test for each of 4 intervention types: push delivered, in-app event triggered, audit log entry written.

---

**AC 2.5 — Push Notification Payload Content Policy**

All AI-triggered push notifications (APNs, FCM, Web Push) must comply with:

**Permitted payload fields only:**
- `notification_id` (UUID)
- `deep_link` (URL to specific in-app screen; no health data encoded in query params)
- `title`: generic only (permitted: *"Elfie has something for you"*, *"You have a new challenge"*; PROHIBITED: any medication name, biomarker value, disease reference, risk level)
- `body`: equally generic (permitted: *"Open Elfie to check it out"*; PROHIBITED: any health content)

All health-related content (streak count, medication name, risk score, challenge details, coin amount) is rendered in-app after authenticated deep link open — never in the OS notification tray.

**Automated enforcement:** a payload content scanner (regex + prohibited term word list) runs before any notification is dispatched. Payload containing prohibited terms is rejected before dispatch and logged as a policy violation.

*Verification:* Test: dispatch notification with health content in title → rejected before dispatch, policy violation logged. Test: deeplink-only generic payload → dispatched. Manual review of all 4 intervention notification templates before launch gate sign-off.

---

**AC 2.6 — Geo-Gate Enforcement**

- Risk scoring pipeline only produces scores for users with `registration_country ∈ ["VN", "TH"]`
- Intervention delivery API enforces same allow-list before dispatching any notification or ElfieCare alert
- Country code sourced from server-side registration record; NOT from IP address or device locale
- If user's country code changes to outside allow-list after scoring: delivery suppressed; suppression event logged
- Allow-list expansion requires: (a) Legal review, (b) server config update, (c) P2-equivalent compliance review for new market

*Verification:* Integration tests: VN user → scored, delivered; TH user → scored, delivered; US user → not scored, not delivered; country-change-to-US post-scoring → delivery suppressed.

---

### Section 3 — Fairness & Safety

**AC 3.1 — Intervention Fatigue Cap**

Named constant: `MAX_INTERVENTIONS_PER_7_DAYS = 1`

A user may receive at most 1 AI-triggered user-facing intervention per 7-day rolling window. The cap applies to: coin bonus, streak challenge, badge nudge, premium in-app card. Rolling window from last intervention delivery timestamp (not calendar week).

The fatigue guard is the **first check** in the Intervention Selector (before risk tier logic). A user in cooldown with a High-tier score has their premium in-app card queued for immediate delivery at cooldown expiry — it is not skipped.

This constant is NOT configurable via feature flag, environment variable, admin panel, or A/B test configuration.

**ElfieCare doctor alerts are doctor-facing (not user-facing) and do NOT count toward `MAX_INTERVENTIONS_PER_7_DAYS`.**

Separate ElfieCare alert frequency cap: **maximum 1 ElfieCare alert per patient per linked doctor per 14-day rolling window.**

Exception: a second alert within the 14-day window is permitted ONLY IF `risk_score` has increased by ≥0.20 since the previous confirmed-delivered alert (significant deterioration). This exception applies to: (a) normal 14-day cap; (b) does NOT bypass delivery failure tracking (see AC 2.3 — delivery failures do not count as delivered alerts).

Named constants: `ELFIECARE_ALERT_CAP_DAYS = 14`, `ELFIECARE_ALERT_DETERIORATION_EXCEPTION_DELTA = 0.20`

*Verification:* Unit tests: (a) user-facing cap: intervention at T=0 → blocked at T=6d23h → allowed at T=7d0h1min; (b) ElfieCare cap: alert at T=0 → no second at T=13d; (c) deterioration exception: alert at T=0, risk_score +0.21 at T=5d → second alert allowed; (d) risk_score +0.19 → second alert blocked; (e) alert at T=0, delivery failure, channel restored at T=2h → second alert sent normally (no 14-day suppression from failure). Code review confirming `MAX_INTERVENTIONS_PER_7_DAYS` is a named constant not backed by config.

---

**AC 3.2 — Bias Monitoring Pipeline**

Quarterly bias audit required before any model version enters production and every 90 days thereafter.

| Demographic slice | Minimum AUC | Minimum sample (positive + negative) |
|---|---|---|
| Age 18–35 | ≥ 0.72 | n ≥ 200 |
| Age 36–55 | ≥ 0.72 | n ≥ 200 |
| Age 56+ | ≥ 0.68 | n ≥ 100 |
| Disease type: hypertension | ≥ 0.72 | n ≥ 200 |
| Disease type: diabetes | ≥ 0.72 | n ≥ 200 |
| Country: VN | ≥ 0.72 | n ≥ 200 |
| Country: TH | ≥ 0.72 | n ≥ 200 |

Disparate impact threshold: no slice may have AUC more than 15 percentage points below the overall model AUC.

**Small-slice statistical validity:**
- For slices with n < 200: compute bootstrap 95% CI (1,000 bootstrap samples). If CI width > 0.10: flag as "underpowered — qualitative review only" (no numeric threshold enforcement). If CI width ≤ 0.10: apply numeric threshold.
- For 56+ age group (minimum n = 100): AUC threshold 0.68 only if CI width ≤ 0.15; otherwise qualitative review.
- Bias report must state CI and sample size per slice explicitly.
- If a slice is chronically underpowered after 2 quarterly audits: flag as data collection gap; Product sets demographic coverage improvement target.

**If any slice with n ≥ 200 fails numeric threshold:** model blocked from deployment; retrain required.

Post-launch operational owner: ML Engineering. Reviewer: Medical Affairs. Quarterly audit script is a version-controlled, runnable artifact (P3-G5 deliverable). Remediation workflow: slice fails → ML Engineering notified within 24h → if AUC < 0.68 for any slice → feature suppressed for that demographic slice within 48h → emergency retrain initiated.

*Verification:* Bias report produced for every model candidate using held-out data split by demographic slice; per-slice AUC, bootstrap 95% CI, sample sizes, overall AUC, disparate impact calculated. Underpowered slices labeled correctly. Audit script runnable artifact tested in staging.

---

**AC 3.3 — User Opt-Out — No Penalty**

Users may opt out of Predictive AI at any time:
- Opt-out path: Settings → Privacy → AI Predictions → Off (2 taps + confirmation)
- Opt-out takes effect within next batch cycle (≤ 24 hours)
- Opt-out: excludes user from scoring, cancels pending interventions, stops ElfieCare AI alerts for that patient
- **Zero coin penalty, zero streak penalty, zero badge loss** for opting out
- Existing earned coins/streaks/badges are fully retained
- Opting out does NOT disable manual medication reminders or non-AI notification types
- Opt-out preference stored server-side (not device-local)
- No dark patterns in opt-out flow (no false coin-loss warnings, no pre-ticked re-opt-in, no false urgency copy)

*Verification:* End-to-end test: High-risk user opts out → next batch cycle excludes user → no intervention queued → no ElfieCare alert sent. Coin balance test: user with 500 coins opts out → balance unchanged. UX test: opt-out requires exactly 2 taps from Settings + one confirmation; dark pattern checks.

---

### Section 4 — Privacy & Compliance

**AC 4.1 — Explicit Behavioral Profiling Consent**

Required before any risk scoring begins. Consent screen must disclose:
1. That Elfie uses the user's health activity patterns (medication logs, vital logs, app engagement, coin activity) to personalize reminders and interventions
2. That this involves automated profiling
3. What types of interventions may be sent (notifications, in-app messages, optional doctor alert if doctor linked)
4. That the user can opt out at any time without penalty (Settings → Privacy → AI Predictions)
5. Link to Privacy Policy section covering automated decision-making

Consent stored with: `user_id`, `consent_version`, `consent_timestamp`, `consent_text_hash`. Re-consent required if: new feature types added to profiling, new data categories added, new intervention channel added.

This consent is **separate** from the AI Health Coach consent (Component 1). Users who consented to Component 1 are NOT automatically opted into Component 2 profiling.

*Verification:* Test: user who consented to AI Health Coach is not scored by Predictive AI until separate consent recorded. Consent record audit: all 5 required fields present. Re-consent trigger test: consent_version increment → consent screen on next app open.

---

**AC 4.2 — Stable Per-User Pseudonymization Key Vault**

- Each user is assigned a single persistent pseudonymization key stored in an access-controlled, audited key vault (write-once per user; read-only from training and scoring pipelines)
- All training data and audit logs are keyed to this stable identifier across all training runs
- **Right-to-erasure:** implemented by deleting the user's key from the vault. All archived training records with that user's pseudonym become permanently non-re-linkable (key deletion is irreversible). No record deletion required across training archives.
- Key vault access log is an audit trail; access restricted to training pipeline service account only
- Training pipeline reads the key vault; never exposes key mappings to any other system
- Cross-run consistency: same user produces same pseudonym across all training runs → retraining continuity preserved
- Key rotation: not supported for existing keys. New user registrations after a vault key rotation get new keys; existing keys do not rotate.

*Verification:* Key vault access log reviewed. Integration test: two training runs for same user produce identical pseudonyms. Erasure test: delete user's vault key → pseudonym lookup fails; archived records with that pseudonym remain but are permanently non-linkable. Access control test: no system other than training pipeline service account can read key mappings.

---

**AC 4.3 — Training Data Scope and Consent Basis**

Training data sourced only from users who have:
1. Accepted Elfie Privacy Policy language covering behavioral analysis for service improvement
2. Opted in to AI Predictions (AC 4.1)

Data from users who have revoked consent (AC 4.5) is excluded from all future training runs from the revocation date. Holdout cohort users (AC 6.4) are excluded from training data.

*Verification:* Training pipeline test: opted-out user's records absent from training dataset prepared after opt-out date. Holdout user records absent from training dataset.

---

**AC 4.4 — Audit Trail**

Every AI-triggered intervention generates an audit log entry containing:
- User pseudonym (stable key from AC 4.2)
- Timestamp (UTC)
- `risk_score` at time of trigger
- `risk_tier` at time of trigger
- Intervention type selected
- `delivery_state` (sent / confirmed / failed)
- Number of delivery attempts
- `intervention_id` (UUID; idempotency key)
- Batch cycle identifier
- Model version in production at time of scoring

Audit log does NOT contain: user's real identity, health content of notification payload, or any record of whether the doctor took clinical action.

Audit log: append-only; 24-month retention minimum; access restricted to authorized audit service account.

*Verification:* Integration test: all required fields present in audit log for each intervention type. PII scan: zero occurrences of user real name, email, or phone in audit logs. Append-only enforcement test.

---

**AC 4.5 — Right to Erasure (Consent Revocation Pipeline)**

| Step | Action | SLA |
|---|---|---|
| 1 | Mark user as "consent revoked"; exclude from next batch cycle | Immediate (synchronous) |
| 2 | Cancel all pending intervention queue entries for user | Within 1 hour (best-effort; failures logged) |
| 3 | Delete user's pseudonymization key from key vault (AC 4.2) | Within 24 hours (guaranteed) |
| 4 | Delete user's feature vector from feature store | Within 24 hours (guaranteed) |
| 5 | Tombstone audit log entries: replace user pseudonym with permanent tombstone marker; entry count retained for audit integrity; entries remain non-linkable | Within 72 hours (guaranteed) |
| 6 | Audit record written with completion timestamp for Steps 1–5 | Upon completion of each step |

SLA breach: if Steps 3–5 not confirmed within stated SLA → alert operations team → notify user.

*Verification:* Integration test: revoke consent for user with active intervention in queue + feature store entries + audit log entries. Assert: (a) queue item cancelled within 1 hour; (b) key vault key deleted within 24h; (c) feature store cleared within 24h; (d) audit entries exist with tombstone value (not deleted); (e) no rows returned on user_id join after tombstone; (f) entry count unchanged. Per-step completion timestamps asserted in final audit record.

---

**AC 4.6 — No Profiling of Under-18 Profiles**

- Scoring and intervention delivery is applied at the **profile level**, not the account level
- Family accounts with multiple profiles: each profile evaluated independently
  - Child profile (DOB indicates age < 18): excluded from scoring; no AI intervention
  - Adult profile (DOB indicates age ≥ 18): eligible per normal criteria
- Profile with absent or unverifiable DOB: excluded from scoring until age confirmed
- Profiles registered under "child/dependent" profile type: always excluded regardless of DOB field value
- Age and profile-type check runs at feature computation time (not at intervention delivery time)

*Verification:* Test matrix: (a) parent account with child profile → child not scored, parent scored; (b) standalone account missing DOB → not scored; (c) child profile type regardless of DOB → not scored; (d) adult profile confirmed age > 18 → scored.

---

### Section 5 — Performance & Reliability

**AC 5.1 — Batch Scoring Window SLA**

Daily batch pipeline (feature engineering + model inference + feature store write + intervention queue dispatch) must complete within a **4-hour overnight window** for all scoreable users.

Load test requirement: pipeline must demonstrate 4-hour SLA at 5× projected launch DAU. Launch DAU targets defined at Week 0 planning kickoff.

*Verification:* Staging load test with representative data volume confirming 4-hour completion.

---

**AC 5.2 — Performance — Batch Throughput vs. Online Serving SLAs**

**Batch pipeline throughput (primary SLA):**
- Target: ≥1,000 users scored per second (vectorized XGBoost/LightGBM batch inference)
- Batch scoring pipeline reads feature store via **bulk batch export** (not real-time read API)
- Validated at 5× projected launch DAU

**Online serving SLA (feature store read API — for audit, monitoring dashboard, and admin tooling only; NOT the batch scoring path):**
- P95 single-user feature vector retrieval: ≤200ms
- Applies to: model monitoring dashboard lookups, admin feature inspection tools

*Verification:* Batch throughput test: 1M synthetic user records scored within 4-hour window on target hardware. Online API test: 100 concurrent single-user requests, P95 ≤200ms.

---

**AC 5.3 — Batch Pipeline Atomicity and Failure Handling**

Write-commit atomicity:
- Feature store writes for a batch cycle are staged in a temporary partition until all users are scored
- Staged scores committed as a single atomic transaction replacing prior batch cycle's values
- On failure before commit: staged values discarded; previous committed scores remain active; no partial update to live feature store
- On commit failure: rollback to previous state; no partial user updates visible

**Stale score policy:** if committed scores are older than 48 hours (= 2 consecutive batch failures):
- High-tier interventions: **SUPPRESSED** (no ElfieCare alerts or premium in-app cards from stale data)
- Medium-tier interventions: may proceed with staleness warning logged
- Named constant: `HIGH_TIER_STALE_SCORE_SUPPRESSION_HOURS = 48`
- Staleness check occurs at intervention dispatch time (not at batch scoring time); selector checks `score_timestamp` before dispatching High-tier alerts

On any batch failure: on-call engineer alert (PagerDuty or equivalent). On 2 consecutive batch failures: escalation to Engineering Lead.

*Verification:* Chaos test: inject OOM error at 50% of scoring completion. Assert: (a) staged values discarded; (b) feature store shows previous committed values unchanged; (c) on-call alert fired. Stale score test: mark last committed scores as 49 hours old; assert High-tier interventions suppressed, Medium-tier allowed. Atomic commit test: failure during commit step → no partial user updates visible.

---

**AC 5.4 — Availability**

- Batch pipeline: target 99.5% monthly successful completion rate (≤ 3.6 hours of failed batch windows per month)
- Intervention execution: target 99.0% delivery rate for users in the execution queue
- ElfieCare alert delivery: retry policy per AC 2.3 (3 retries); on failure → ops alert (not 14-day suppression)

*Verification:* 30-day staging monitoring report showing batch success rate and intervention delivery rate.

---

### Section 6 — Monitoring & Retraining

**AC 6.1 — Intervention Response Event Tracking**

Every AI-triggered intervention generates response events stored pseudonymously:

| Event | Trigger |
|---|---|
| `intervention_delivered` | Notification sent or in-app message queued |
| `notification_opened` | Notification tapped or push opened |
| `challenge_completed` | Streak challenge CTA tapped and qualifying activity logged |
| `challenge_abandoned` | 7-day challenge window expired without completion |
| `card_opened` | Premium in-app card viewed ≥ 3 seconds |
| `card_dismissed` | Card explicitly dismissed with one tap |
| `intervention_ignored` | No response event within 48 hours of delivery |

Events stored pseudonymized with same key as AC 4.2. Feature drift detection: weekly Kolmogorov-Smirnov test on each feature's distribution vs. training baseline; alert triggered if p < 0.01 for any feature.

*Verification:* Integration test confirming all 7 event types fire on simulated user interaction paths. Pseudonymization verified: event store contains no raw user_id. Drift detection test: inject synthetic drift in `medication_adherence_7d`; confirm alert fires.

---

**AC 6.2 — Quarterly Retraining and Model Promotion**

- Retraining cadence: minimum once per quarter
- A retrained model is not automatically promoted; it must pass all thresholds in AC 1.2 and AC 3.2
- **Shadow mode validation (2 weeks before promotion):** new model scores all eligible users but triggers NO interventions; shadow scores logged only. Shadow mode cannot start until P1 (all 7 gates), P2 (all gates), and P3-G4 complete simultaneously.
- **Promotion criteria:** (a) AUC meets AC 1.2 threshold; (b) bias audit per AC 3.2 passes; (c) shadow mode AUC consistent with offline validation (within ±0.04); (d) Technical Advisor sign-off
- Auto-promotion blocked if: candidate model AUC degrades > 0.05 relative to prior production model on same held-out test set

Training data for retraining: holdout cohort users (AC 6.4) excluded from training data and labels. Intervention feedback from treatment group included subject to AC 1.5 treatment washout filter.

Model artifact versioned with: training date, feature set version, hyperparameter config, all validation metrics. Previous model version retained 90 days for rollback.

*Verification:* Retraining runbook documented and tested in staging. Promotion gate test: model with AUC = 0.70 → blocked. Auto-degradation test: candidate AUC 0.79 vs production 0.85 → auto-promotion blocked (delta = 0.06 > 0.05).

---

**AC 6.3 — Production Model Performance Monitoring**

| Metric | Alert threshold | Action |
|---|---|---|
| Overall AUC (21-day lag) | Drops below 0.68 | Escalate to ML Engineering; retrain initiated within 7 days |
| 30-day acted-rate | Drops below 10% | Product review; intervention copy and selector logic audited |
| High-tier false positive rate | Exceeds 40% | ML Engineering review; threshold calibration |
| ElfieCare alert volume per week | Exceeds 500/week OR > 20% of active doctor-linked users | Product + Medical Affairs review |

Labels for production monitoring computed with 21-day lag.

*Verification:* Monitoring dashboard deployed in staging; alert rule test: inject mock metric values at threshold → confirm alerts fire.

---

**AC 6.4 — Holdout Cohort for Outcome Measurement**

- Deterministic 5% holdout cohort: users where `SHA256(user_id + HOLDOUT_SALT)[0] % 20 == 0`
- **`HOLDOUT_SALT` is a fixed immutable constant defined once at feature launch and never modified. Rotating this value changes cohort membership and invalidates all longitudinal comparisons — treat it as equivalent to a schema migration in terms of change control.**
- Holdout users are scored daily (risk_score computed) but receive NO AI-triggered interventions regardless of risk tier
- Holdout users receive normal Elfie gamification, manual reminders, and ElfieCare interactions
- Holdout cohort excluded from model training (features and labels)
- Quarterly monitoring report must include: treatment group intervention rate, holdout group dropout rate, treatment group dropout rate; dropout rate delta is the primary business impact metric
- Holdout cohort assignment is not disclosed to users (not user-visible)

*Verification:* Integration test: holdout users receive no intervention from scoring pipeline. Training dataset test: holdout user records absent from training features and labels. Quarterly report format test: treatment vs. holdout dropout rate comparison present.

---

### Section 7 — Gamification Integration

**AC 7.1 — Coin Bonus Offer**

- Coin bonus amount: 30 coins (fixed pending gamification economy review — see note below)
- Offer is valid for 48 hours from delivery time
- Coins credited via existing Elfie coin pipeline upon: (a) user taps CTA and (b) completes 1 qualifying activity (medication log or vital log)
- Award is idempotent per `intervention_id` (second claim of same offer → no-op at coin service layer)
- If user is no longer at Medium or High risk when claim is made (model ran again): coins still awarded; commitment was made at time of offer
- Coin events tagged with source: `"adherence_ai_intervention"` in coin event log

> **Gamification Economy Review required:** Before spec approval, Product team must obtain approval from the Elfie coin economy owner for: (a) 30-coin bonus amount; (b) projected weekly issuance at launch DAU. AC 7.1 is conditional on economy owner approval.

*Verification:* Integration test: coin bonus trigger → user claims within 48h after completing qualifying log → 30 coins credited. Idempotency test: double-claim → coins credited once. Expiry test: claim at T=49h → rejected, no coins. Source tag test: coin event log entry has `source = "adherence_ai_intervention"`.

---

**AC 7.2 — Streak Protection Challenge**

- Message framing: *"Your [N]-day streak is at risk! Log your [medication/vitals] today to protect it."*
- Display prompt only — does NOT modify streak calculation logic, does NOT grant streak grace days
- Counts as 1 intervention for the 7-day user-facing fatigue cap (AC 3.1)

*Verification:* UX test: streak count N matches `medication_streak_current`. Streak logic test: user receives challenge but does not log → streak broken per normal rules (no grace day). Fatigue cap test: streak challenge sent → no second AI intervention for 7 days.

---

**AC 7.3 — No Penalty for Non-Response to AI Intervention**

Users who receive and ignore an AI-triggered intervention (all types) experience zero coin penalty, zero streak penalty, and zero badge loss.

*Verification:* Test: user with 200 coins and 10-day streak ignores coin bonus offer → at T=49h (offer expired) → balance = 200 coins; streak unchanged (if daily logs continued per normal rules); no badge revoked.

---

## Pre-Launch Requirements

**These tracks must begin immediately upon spec approval. No feature launch until all gates in all tracks are passed.**

---

### P1 — ML Development Track

**Duration:** 10–12 weeks (P1-G1 may begin ONLY after P1-G0 confirms data sufficiency)  
**Owner:** ML Engineering  
**Medical Affairs pre-engagement:** confirm dedicated review capacity for P1-G5 (bias audit sign-off) before P1-G1 kickoff. A single Medical Affairs resource may not hold P1-G5 and any P2 gate sign-off in the same calendar week.

| Gate | Deliverable | Exit criteria | Target week |
|---|---|---|---|
| **P1-G0** | Data Readiness & AUC Feasibility Audit | (1) ≥90 days of event log data confirmed for ≥10,000 VN+TH active users; (2) ≥1,000 positive label examples (active→inactive) in dataset; (3) offline 5-fold temporal cross-validation of 11-feature model produces AUC point estimate ≥0.72 with 95% CI; AUC threshold for launch locked based on P1-G0 result; if AUC estimate <0.72: halt, escalate, feature may be deferred | Week 2 |
| P1-G1 | Feature engineering pipeline | All 11 features computing correctly on synthetic users; pipeline running in staging | Week 4 |
| P1-G2 | Feature set validation | Feature importance review by ML Engineering + Medical Affairs sanity check (medication features expected in top 5) | Week 5 |
| P1-G3 | Model candidate trained | XGBoost or LightGBM candidate; ML validation report produced with all AC 1.2 metrics | Week 7 |
| P1-G4 | Model passes AC 1.2 thresholds | AUC ≥ P1-G0 confirmed threshold, Precision@top10% ≥ 60%, Recall ≥ 65%, Brier score ≤ 0.22 | Week 8 |
| P1-G5 | Bias audit passed | All demographic slices with sufficient sample size pass AC 3.2 thresholds; bootstrap CI reported; disparate impact within ±15pp; report signed by Technical Advisor and Medical Affairs lead | Week 10 |
| P1-G6 | Shadow mode completed | Model runs 2 weeks in staging without triggering interventions; AUC estimate from lagged labels consistent with P1-G4 (within ±0.04) | Week 12 |

---

### P2 — Legal & Compliance Track

**Duration:** 6–8 weeks (begins in parallel with P1 after P1-G0)  
**Owner:** Legal + Medical Affairs + Product  
**Blocks:** Launch Gates #1, #2, #3, #7, #8

| Gate | Deliverable | Exit criteria |
|---|---|---|
| **P2-G0** | EU AI Act Classification | Written determination: High-risk (Annex III) or Limited-risk; if High-risk: conformity assessment scope defined; EU rollout confirmed blocked at MVP regardless. **Required within 2 weeks of spec approval.** |
| P2-G1 | Doctor ToS amendment | Clause per AC 2.3 added; reviewed by Legal lead; version-controlled in ToS repository |
| P2-G2 | Behavioral profiling consent copy | Consent screen copy approved by Legal (PDPD/PDPA compliance); Vietnamese and Thai translations reviewed by native-speaker Legal counsel |
| P2-G3 | Doctor-facing alert templates | All templates: Medical Affairs + Legal sign-off per AC 2.3; prohibited term scan passed; zero occurrences of banned terms |
| P2-G4 | Privacy impact assessment (DPIA) | DPIA covering automated profiling, demographic data in bias monitoring, pseudonymization scheme; approved by DPO or Legal equivalent |
| P2-G5 | OQ-6 data residency determination | Written determination on whether PDPD (Vietnam) requires in-country deployment of feature store. If yes: P3 extended by 4–8 weeks; cloud provider / infra decision documented. |
| P2-G6 | Intervention copy delivery | All copy sets (coin bonus, streak challenge, badge nudge, premium card) in Vietnamese + English; Medical Affairs review for medication adherence language; native speaker review for VN + TH; deployed in P3-G2 (intervention queue) |

---

### P3 — Infrastructure Readiness

**Duration:** 4–6 weeks (greenfield model registry may add 2–4 weeks; OQ-6 data residency may add 4–8 weeks)  
**Owner:** Engineering (Platform)

**P3 infrastructure baseline (existing Elfie systems):** Postgres (user data), Redis (session/cache), Celery (async tasks), existing push notification service (APNs + FCM).

**Required new/extended components:**
- (a) Feature Store: Postgres JSONB or Redis Hash extension (NOT greenfield)
- (b) Intervention Queue: Celery task queue extension (NOT greenfield)
- (c) Model Registry: MLflow or equivalent — **likely greenfield** (4–6 weeks additional)
- (d) Notification pipeline enhancements (3 enhancements per AC scope item; platform team dependency if applicable)

If OQ-6 (P2-G5) requires in-country VN deployment of feature store: adds 4–8 weeks to P3 timeline; must be resolved before P3 architecture is finalized.

| Gate | Deliverable | Exit criteria |
|---|---|---|
| P3-G1 | Feature store deployed | Batch write SLA (4-hour window) demonstrated at 5× launch DAU; single-user read P95 ≤200ms; 90-day retention policy active |
| P3-G2 | Intervention queue deployed | Delivery time-of-day guard (08:00–20:00 local time per AC 2.2) working in staging; all 4 intervention types deliverable; idempotency keys enforced; payload content scanner (AC 2.5) active |
| P3-G3 | Model registry operational | Model versioning, artifact storage, rollback within 4 hours tested; rollback SLA confirmed |
| P3-G4 | Monitoring dashboard deployed | All AC 6.3 metrics visible; alert rules active; end-to-end test with synthetic metric values at threshold |
| P3-G5 | Quarterly bias audit script | Version-controlled runnable artifact; produces per-slice AUC with bootstrap CI; disparate impact calculated; validated on synthetic audit data |

---

### Medical Affairs Capacity Note

Medical Affairs is a named approver for: P1-G5 (bias audit sign-off), P2-G3 (doctor alert template review), and P2-G6 (intervention copy review). Confirm dedicated Medical Affairs capacity for all three at Week 0 kickoff. A single Medical Affairs resource may not hold P1-G5 and P2-G3 sign-off in the same calendar week.

---

### Milestone Map Note

Project Manager must produce a milestone map at Week 0 kickoff showing:
- P1, P2, P3 start dates and serialized dependencies
- P1-G0 critical path impact (adds ~2 weeks before P1-G1 can begin)
- OQ-6 resolution fork (base timeline vs. 4–8 week data residency extension)
- Shadow mode start criteria: all of P1-G6, P2 complete, P3-G4 complete simultaneously
- Medical Affairs pre-engagement scheduled before P1-G1 kickoff
- ElfieCare team engagement deadline (before P2 begins)

---

## Launch Gate Checklist

All 18 items must be marked PASS before feature flag is enabled for any real user. Technical Advisor signs off on complete checklist.

| # | Gate | Owner | Verification Method |
|---|---|---|---|
| 1 | P1-G0: AUC feasibility audit completed; data sufficiency confirmed; AUC threshold locked | ML Engineering | Signed data readiness + AUC feasibility report |
| 2 | P1-G4: Model passes locked AUC threshold, Precision@top10% ≥60%, Recall ≥65%, Brier ≤0.22 on chronological test split | ML Engineering | Signed ML validation report with confusion matrix and AUC curve |
| 3 | P1-G5: Bias audit passed; all slices with n≥200 meet per-slice AUC; disparate impact ±15pp; bootstrap CIs reported | ML Engineering + Medical Affairs | Signed bias report |
| 4 | P1-G6: Shadow mode completed; AUC estimate from lagged labels within ±0.04 of P1-G4 result | ML Engineering | Shadow mode report reviewed by Technical Advisor |
| 5 | Training label script: validated on 20 synthetic trajectories (5 scenario types per AC 1.5) | ML Engineering | Test report with per-scenario pass/fail |
| 6 | Training data isolation: pseudonymization confirmed in ETL; PII scan of output feature matrix → zero hits; network isolation verified; holdout users excluded from training dataset | Engineering + Security | Code review + automated PII scan report + infra review |
| 7 | Doctor ToS amendment (P2-G1) live in production; version increment confirmed; re-acceptance screen deployed by ElfieCare frontend team | Legal + ElfieCare | ToS version log; re-acceptance flow tested |
| 8 | EU AI Act classification documented (P2-G0): High-risk or Limited-risk; EU rollout confirmed blocked; if High-risk: conformity assessment scope on file | Legal | Written classification determination |
| 9 | Behavioral profiling consent screen (P2-G2): approved by Legal; Vietnamese and Thai copy reviewed by native-speaker Legal counsel; consent record structure confirmed | Legal + Engineering | Consent record audit; legal sign-off doc |
| 10 | DPIA (P2-G4) approved | DPO / Legal | Signed DPIA document |
| 11 | Doctor-facing alert templates (P2-G3): prohibited term scan passed; Medical Affairs sign-off | Medical Affairs + Legal | Prohibited term scan report; sign-off document |
| 12 | OQ-6 data residency determination completed (P2-G5) | Legal + Engineering | Written determination on file |
| 13 | Intervention fatigue cap: unit tests for all boundary values pass; `MAX_INTERVENTIONS_PER_7_DAYS` confirmed as named constant not backed by config | Engineering | Test report + code review sign-off |
| 14 | ElfieCare alert delivery: (a) confirmation endpoint returns delivery_state; (b) 3-retry backoff confirmed; (c) delivery failures do NOT trigger 14-day suppression; (d) ops alert on 3 failures; (e) deterioration exception (≥0.20) works across failure history | Engineering | Integration test report confirming all 5 sub-items |
| 15 | Batch pipeline atomicity: chaos test at 50% completion → staged values discarded, previous committed scores unchanged, on-call alert fired | Engineering | Chaos test report |
| 16 | Stale score policy: High-tier interventions suppressed when scores > 48h old; Medium-tier allowed; `HIGH_TIER_STALE_SCORE_SUPPRESSION_HOURS = 48` is a named constant | Engineering | Integration test report + code review |
| 17 | Consent revocation pipeline (AC 4.5): all 5 steps completed within stated SLAs; tombstone verified (entries exist, user pseudonym = tombstone value, no linkable join); per-step timestamps in final audit record | Engineering | Integration test report with per-step timing |
| 18 | Geo-gate: VN → scored and delivered; TH → scored and delivered; US → not scored; country-change-to-US → delivery suppressed | Engineering | Integration test report |

---

## Open Questions

| # | Question | Status |
|---|---|---|
| OQ-1 | Sufficient historical training data? | **RESOLVED via P1-G0.** ML Engineering must complete data readiness audit within 2 weeks of spec approval. If data insufficient: contingency plan (expand label window, extend data collection, defer to v2) required before P1-G1 can be scheduled. |
| OQ-2 | Demographic field coverage (age, gender) in VN/TH user profiles? | **Open.** If <60% coverage, bias audit slice thresholds may not be achievable at launch. ML Engineering must report coverage in P1-G0. |
| OQ-3 | ElfieCare doctor linkage rate at launch? | **Open — Business decision.** If <10% of active users have a linked doctor, ElfieCare alert path is low-impact at MVP. Product lead must decide: (a) proceed with High-tier path regardless of linkage rate; (b) defer ElfieCare alert path to v2 if linkage rate < threshold. Decision required before P2 begins. |
| OQ-4 | Coin bonus amount (30 coins): is this calibrated against existing Elfie economy? | **Open — gamification economy review required before spec is finalized for planning.** AC 7.1 conditional on economy owner approval. |
| OQ-5 | EU AI Act classification | **RESOLVED via P2-G0.** Legal must produce written determination within 2 weeks of spec approval. |
| OQ-6 | PDPD Vietnam data residency for feature store? | **Being resolved via P2-G5.** Legal determination required before P3 architecture can be finalized. If in-country deployment required: P3 timeline extends 4–8 weeks. |
| OQ-7 | Intervention copy ownership | **RESOLVED via P2-G6.** Copy owned by Product team. Required sets documented in P2-G6. Medical Affairs review required. |

---

*This spec is APPROVED FOR PLANNING. Technical Advisor (9.03/10) and Project Manager (9.00/10) issued APPROVED verdicts in Round 3. All Critical, High, and newly-introduced NM defects are resolved. Open Questions OQ-1, 5, 7 resolved; OQ-2, 3, 4, 6 require action before planning can begin.*
