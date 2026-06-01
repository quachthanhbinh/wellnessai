# Predictive Adherence AI — Regulatory & Compliance Research

**Component:** Predictive Adherence AI ("Dropout Prevention Engine")  
**Research date:** 2026-06-01

---

## Phân loại regulatory

### Là SaMD hay không?

Predictive Adherence AI **không phải SaMD** theo định nghĩa FDA/IMDRF nếu:
- Output là **engagement intervention** (nudge, reminder, reward) — không phải clinical recommendation
- Không thay đổi treatment plan, dosage, hoặc clinical pathway
- Healthcare provider vẫn là người quyết định cuối về điều trị

**Analogy hữu ích:** Netflix recommendation engine dự đoán bạn sắp churn và gửi promo — không ai classify đó là "software device". Elfie Predictive AI làm tương tự với health engagement.

---

## Phân tích theo jurisdiction

### FDA (US)

**Classification:** Non-device administrative support software

Theo FDA 21st Century Cures Act (Section 3060), phần mềm phục vụ "administrative support of a health care facility" và "general purpose computing" được **exempt khỏi device regulation**.

**Điều kiện exempt:**
- ✅ Không intended to diagnose, treat, cure, mitigate, prevent disease
- ✅ Output là administrative action (send notification, award coins)
- ✅ Does not acquire, process, or analyze medical images for diagnostic purpose
- ⚠️ **Nếu output bao gồm clinical alert gửi đến bác sĩ** → cần careful framing (xem bên dưới)

**Doctor alert framing — critical distinction:**

| Framing | Classification |
|---|---|
| ❌ "Patient X shows signs of hypertensive crisis" | Clinical alert → potential SaMD |
| ✅ "Patient X has not logged their medication in 5 days — you may want to follow up" | Administrative engagement alert → Non-device |

### EU AI Act (2026 enforcement)

Predictive Adherence AI **có thể** bị phân loại là **High-risk AI** (Annex III, 5(a)) vì:
- Liên quan đến health outcomes
- Ảnh hưởng đến behavior của bệnh nhân mãn tính

**Yêu cầu nếu High-risk:**
- Conformity assessment (có thể tự thực hiện nếu không có notified body requirement)
- Technical documentation: training data sources, validation methodology, performance metrics
- Human oversight: users must be able to opt out of AI interventions
- Post-market monitoring plan
- Accuracy và robustness testing

**Mitigation:** Argue for "limited risk" classification nếu:
- Model chỉ trigger low-stakes interventions (push notifications, coin bonuses)
- Doctor alerts clearly labeled as "engagement signal, not clinical finding"
- Full opt-out available

### PDPD (Vietnam) / PDPA (Thailand) / LGPD (Brazil)

**Profiling consent requirement:**

Predictive AI cấu thành **automated profiling** theo GDPR/các luật tương đương → cần:
- Informed consent trước khi profile user
- Quyền không bị subject to automated decision (nếu có consequences)
- Right to explanation: user có thể hỏi "tại sao tôi nhận được thông báo này?"

**Elfie implementation:**
```
Onboarding consent: "Elfie uses your health activity patterns to personalize support 
and send you reminders when we notice you may need encouragement. You can turn 
this off at any time in Settings > Privacy."
```

---

## Vấn đề nhạy cảm đặc biệt

### 1. Doctor alert — Liability khi bác sĩ không hành động

**Scenario:** Elfie gửi alert "Patient X has low adherence" → Bác sĩ không follow up → Patient bị biến chứng.

**Rủi ro:** Bác sĩ hoặc insurer claim Elfie created a "duty to monitor" mà không fulfill.

**Mitigation:**
- Alert framing: "FYI, engagement signal" — not "clinical alert requiring action"
- Doctor terms of service: explicit disclaimer về non-clinical nature của alerts
- Alert có "snooze" và "dismiss" rõ ràng — bác sĩ không bị "forced" review
- Không track hoặc log xem bác sĩ có hành động hay không (tránh tạo paper trail)

### 2. False positive interventions — User harm

**Scenario:** AI sai lầm flag user là high-risk → User nhận quá nhiều interventions → User frustrated → Churn nhanh hơn.

**Mitigation:**
- Hard cap: maximum 1 AI-triggered intervention per 7 days
- User can dismiss with one tap + feedback reason
- Negative feedback → immediate model signal (online learning)
- Precision > Recall trong tuning: better to miss some at-risk users than over-interrupt

### 3. Discrimination theo nhóm dân số

**Scenario:** Model performs poorly cho elderly users hoặc một dân tộc cụ thể → họ nhận nhiều false-positive alerts hoặc bị miss.

**Mitigation:**
- Fairness metrics trong model evaluation (AUC per demographic slice)
- Annual bias audit (có thể bundle với existing ISO27001 audit)
- Disaggregated performance reporting trong technical documentation

---

## Data governance cho training

### Consent cho training data

**Câu hỏi:** Elfie có thể dùng historical user data để train Predictive AI không?

**Trả lời:**
- **Cần kiểm tra Privacy Policy hiện tại** — có cover "improve our services through data analysis" không?
- Nếu có (thường có trong standard privacy policy) → có thể argue legitimate interest
- **Best practice:** thêm explicit opt-in cho "Contribute your anonymized data to improve Elfie's health predictions"
- Dữ liệu training phải được anonymize/pseudonymize trước khi đưa vào training pipeline

### Anonymization cho training

```python
# Training data pipeline (pseudocode)
def prepare_training_data(raw_events: DataFrame) -> DataFrame:
    # Replace user_id with stable hash (same user = same hash, but irreversible)
    events["user_hash"] = events["user_id"].apply(sha256_hash)
    
    # Remove direct identifiers
    events = events.drop(columns=["user_id", "email", "phone", "name"])
    
    # Remove quasi-identifiers that could re-identify via rare combinations
    events = events.drop(columns=["exact_location", "device_id"])
    
    # Keep: timestamps (generalized to week/month), health metrics, behavioral signals
    return events
```

---

## Compliance checklist cho spec

- [ ] Privacy Policy update: add explicit mention of behavioral profiling for engagement
- [ ] Onboarding: consent flow cho predictive personalization (opt-in recommended)
- [ ] User settings: opt-out toggle cho AI-driven interventions
- [ ] Doctor alert framing: legal review của exact language trước launch
- [ ] EU AI Act: determine if High-risk or Limited-risk classification; prepare technical doc
- [ ] Training data: confirm legal basis, anonymization pipeline documented
- [ ] Fairness audit: define demographic slices, set minimum AUC thresholds per slice
- [ ] Intervention cap: hard-coded limit per user per time window
- [ ] Model documentation: training data, validation set, performance metrics — required for EU AI Act
