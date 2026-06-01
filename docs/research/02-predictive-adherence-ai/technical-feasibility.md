# Predictive Adherence AI — Technical Feasibility Research

**Component:** Predictive Adherence AI ("Dropout Prevention Engine")  
**Research date:** 2026-06-01

---

## Kiến trúc tổng thể

```
Raw event stream (real-time)
  vitals_logged / medication_taken / steps_synced / app_opened / coin_earned
        │
        ▼
[Feature Engineering Pipeline]
  → Sliding window aggregations (7-day, 14-day, 30-day)
  → Behavioral trend signals (slope, variance, streak length)
  → Cross-signal correlations
        │
        ▼
[Adherence Risk Model]
  Input: ~40–60 features per user
  Output: risk_score (0–1) + top contributing factors
        │
        ▼
[Intervention Selector]
  Looks up user context: family paired? insurer sponsored? disease type?
  Selects optimal intervention from intervention menu
        │
        ▼
[Execution Layer]
  → Push notification / in-app message
  → ElfieCare alert (doctor) if risk > threshold
  → Family nudge (if opted in)
  → Coin bonus activation
```

---

## Feature Engineering

### Behavioral features (từ event logs)

```python
# Medication features
medication_adherence_7d    # % liều đúng giờ trong 7 ngày
medication_streak_current  # Streak dài nhất hiện tại
medication_missed_last_3d  # Số ngày bỏ thuốc trong 3 ngày qua
medication_time_variance   # Variance thời gian uống thuốc (thất thường = risk signal)

# Vitals tracking features
vitals_log_frequency_7d    # Số lần log vitals / tuần
vitals_log_slope_14d       # Trend: tăng/giảm frequency
last_vital_logged_hours    # Giờ từ lần log gần nhất

# App engagement features  
dau_wau_ratio              # Daily/Weekly active ratio
session_length_trend       # Trend độ dài session
notification_open_rate     # Rate mở notification gần đây
coins_earned_7d_slope      # Trend coins earned (giảm = disengagement signal)

# Health outcome features
bp_trend_14d               # BP trend (tăng = có thể cảm thấy "khỏe rồi" → bỏ thuốc)
weight_volatility          # Cân nặng biến động nhiều = stress signal
sleep_regularity_score     # Sleep schedule irregularity

# Demographic/contextual (static)
disease_type               # Hypertension vs Diabetes vs... (different dropout curves)
time_since_diagnosis       # New patients drop faster
insurer_sponsored          # Boolean — has external accountability
family_paired              # Boolean — has family accountability
```

### Target variable

```
label = 1 if user goes from "active" to "< 2 logs per week" within next 21 days
label = 0 otherwise

Training window: 30 days of history → predict 21-day dropout
```

---

## Model Selection

### Baseline

**XGBoost / LightGBM** — recommended cho MVP:
- Tốt với tabular behavioral data
- Interpretable (feature importance, SHAP values)
- Fast inference (~1ms per prediction)
- Không cần GPU
- Easy to audit (regulatory requirement)

**Benchmark expectations:**
- AUC: 0.78–0.85 (từ literature trên similar behavioral data)
- Precision@top10%: 65–75%
- Recall của high-risk users: 70–80%

### V2 options

**Temporal models (khi có đủ data):**
- LSTM hoặc Transformer trên event sequences → captures temporal patterns tốt hơn
- Requires: 100K+ users × 6+ months history cho training
- Marginal gain over XGBoost: ~3–7% AUC (thường không đủ justify complexity ở scale nhỏ)

---

## Training Data

### Elfie đã có gì

| Data type | Est. size | Quality |
|---|---|---|
| Medication logs | 3B+ events | High (app-generated) |
| Vitals readings | 500M+ readings | High |
| User retention events (churn) | Millions of examples | Medium (định nghĩa churn cần chuẩn hóa) |
| Wearable sync events | 200M+ | Medium |
| Coin events | 3B+ | High |

→ **Training data volume không phải vấn đề**. Thách thức là **label quality** (định nghĩa chính xác "sắp dropout").

### Label definition challenge

```
Conservative: user has < 1 log per 14 days in next 30 days
Aggressive:   user has < 3 logs per 7 days in next 21 days

Tradeoff:
- Conservative → fewer positives, fewer false alarms, miss some at-risk users
- Aggressive → more positives, more interventions, risk "alert fatigue"

Recommendation: Start aggressive, tune precision/recall based on intervention cost
```

---

## Intervention Selector

```python
class InterventionSelector:
    def select(self, user: UserContext, risk_score: float) -> Intervention:
        
        if risk_score < 0.4:
            return None  # No action
        
        elif risk_score < 0.6:
            # Low-cost interventions first
            if user.has_active_streak:
                return CoinStreakBonus(multiplier=2.0)
            else:
                return MotivationalChallenge(disease=user.primary_disease)
        
        elif risk_score < 0.75:
            # Social accountability
            if user.family_paired and user.family_consent_intervention:
                return FamilyNudge(message_template="check_in")
            else:
                return PersonalizedContent(topic=user.top_dropout_reason)
        
        else:
            # High-risk: escalate to human
            if user.insurer_sponsored or user.doctor_linked:
                return DoctorAlert(severity="medium", summary=risk_summary(user))
            else:
                return ProactiveOutreach(channel="push", urgency="high")
```

### Intervention fatigue prevention

- Không trigger > 1 intervention per 7-day window per user
- Track intervention history: nếu 3 interventions liên tiếp không hiệu quả → escalate tier
- A/B test intervention types để optimize per user segment

---

## MLOps & Monitoring

### Deployment

| Phase | Frequency |
|---|---|
| Batch scoring | Daily (score all active users overnight) |
| Real-time scoring | On-demand khi bác sĩ query patient risk |
| Model retraining | Monthly (automated) |
| Full model review | Quarterly (human review) |

### Monitoring metrics

```
Model health:
  - AUC trên holdout set (monthly)
  - Feature drift detection (weekly)
  - Prediction distribution shift (daily)

Business metrics:
  - Intervention trigger rate (% users/day)
  - Intervention effectiveness: adherence rate 30d post-intervention
  - False positive rate (interventions on users who didn't churn)
  - Alert fatigue: notification open rate of intervention messages
```

### Bias monitoring

**Critical:** Model có thể bias theo:
- Age (elderly lower engagement baseline → false positives)
- Disease type (hypertension vs. diabetes different baseline patterns)
- Country/device type (Android vs iOS engagement patterns differ)

**Mitigation:** Train separate models per disease cohort; monitor AUC by demographic slice.

---

## Infrastructure requirements

| Component | Technology | Scale requirement |
|---|---|---|
| Feature store | Postgres + Redis cache | 1M users, daily batch |
| Model serving | FastAPI + scikit-learn/XGBoost | <10ms inference |
| Training pipeline | Python + MLflow | Monthly batch |
| Experiment tracking | MLflow (self-hosted) | — |
| A/B testing framework | Custom or PostHog | 10 concurrent experiments |

**Cost estimate (1M users):** ~$200–400/month compute for daily batch scoring. Very low.
