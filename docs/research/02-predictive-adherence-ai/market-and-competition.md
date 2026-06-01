# Predictive Adherence AI — Market & Competition Research

**Component:** Predictive Adherence AI ("Dropout Prevention Engine")  
**Research date:** 2026-06-01

---

## Bài toán thị trường

### Con số adherence toàn cầu

| Chỉ số | Số liệu | Nguồn |
|---|---|---|
| Adherence bệnh nhân mãn tính sau 1 năm | < 50% | WHO, 2024 |
| Chi phí non-adherence toàn cầu/năm | ~$528B | IQVIA, 2024 |
| Nhập viện do non-adherence | ~33% tổng nhập viện | Annals of Internal Medicine |
| Hypertension controlled rate | ~20% bệnh nhân | ISH Global Report |

→ **Non-adherence là vấn đề kinh tế y tế lớn nhất thế giới**, nhưng không có giải pháp dự đoán được scale.

### Thị trường "Medication Adherence Technology"

| Segment | Quy mô 2025 | CAGR |
|---|---|---|
| Digital medication management | ~$3.2B | 21% |
| Remote patient monitoring | ~$29B | 18% |
| Predictive analytics in healthcare | ~$18B | 26% |

---

## Landscape cạnh tranh

### Dedicated Adherence Tech

| Sản phẩm | Approach | Thị trường | Gap |
|---|---|---|---|
| **AiCure** | Computer vision (face recognition) xác nhận uống thuốc | US pharma/clinical trials | Quá invasive; chỉ cho clinical setting |
| **Adherium (Hailie)** | Smart inhaler sensor + app | COPD/asthma | Hardware-dependent; narrow disease |
| **PatchRx** | Bluetooth pill bottle cap + app | US market | Hardware required; expensive |
| **Medisafe** | Pill reminder + social support | Consumer | Reactive (reminder), không predictive |
| **Propeller Health** | Smart inhaler sensor | Respiratory | Hardware required |
| **mPharma** | Medication access + adherence tracking | Africa | Supply-side focus, không AI prediction |

### Predictive Analytics trong Health (Rộng hơn)

| Sản phẩm | Approach | Gap so với Elfie |
|---|---|---|
| **Health Catalyst** | Hospital EHR data analytics | Không consumer-facing; B2B only |
| **Veradigm** | Claims data + EHR prediction | Claims-based; không real-time behavior data |
| **Cogito** | Behavioral AI từ phone signals | Privacy concerns; không health-specific |
| **Wellframe** | Care management + engagement prediction | Insurer B2B only; expensive |

### Nhận xét cạnh tranh

**Khoảng trống lớn nhất:**
- Tất cả giải pháp hiện tại đều **reactive** (nhắc nhở khi đến giờ) hoặc **hardware-dependent**
- **Không ai** có đủ longitudinal behavioral + clinical data từ consumer để train predictive model
- Elfie có **data advantage duy nhất**: vitals + medication + wearable + coin events + engagement patterns — đây là multi-modal behavioral signal mà không đối thủ nào có

---

## Evidence từ nghiên cứu khoa học

### Adherence prediction — Những gì đã được chứng minh

| Yếu tố dự đoán adherence | Predictive power | Nghiên cứu |
|---|---|---|
| Medication logging streak decline | High | Dayer et al., 2013 |
| App engagement drop (DAU/WAU ratio) | High | Torous et al., 2021 |
| Vitals tracking frequency decline | Medium-High | Anglada-Martinez et al., 2016 |
| Step count decrease | Medium | Lim et al., 2022 |
| Login time-of-day shift | Medium | Kumar et al., 2020 |
| Sleep irregularity increase | Medium | Naber et al., 2019 |
| Missed medication streaks (2+ days) | Very High | Vrijens et al., 2017 |

**Key insight:** Sự suy giảm adherence **có thể phát hiện 14–21 ngày trước** khi user hoàn toàn bỏ điều trị, thông qua các behavioral micro-signals trong app.

### Intervention effectiveness

| Loại intervention | Adherence improvement | Evidence |
|---|---|---|
| SMS/push reminder | +5–8% | Meta-analysis, 20 RCTs |
| Gamification streak bonus | +12–18% | Elfie internal + Hamari et al. |
| Social accountability (family nudge) | +15–22% | Burke et al., 2015 |
| HCP outreach | +25–30% | Schroeder et al., 2004 |
| Personalized AI coaching | +18–24% | Preliminary evidence |

→ **HCP outreach là hiệu quả nhất** nhưng đắt nhất. Elfie có thể target nó chính xác hơn với prediction model thay vì outreach tất cả.

---

## Cơ hội kinh doanh cho Elfie

### Pharma monetization

PSP (Patient Support Programs) của pharma **đang trả rất nhiều** cho adherence improvement. Nếu Elfie có thể chứng minh:
- Adherence rate tăng X% trong cohort dùng Predictive AI
- Hospitalizations giảm Y%

→ Pharma sẵn sàng trả $5–15/patient/month cho giải pháp này (vs. traditional PSP cost $30–80/patient/month)

### Insurer ROI model

| Metric | Baseline | With Predictive AI | Delta |
|---|---|---|---|
| Adherence rate (1 year) | 45% | ~60–65% (projected) | +15–20% |
| Hospital admissions/1000 members | 120 | ~96–102 | −15% |
| Cost per member per year saved | — | ~$200–400 | — |

---

## Positioning

> *"Đối thủ nhắc bạn uống thuốc. Elfie biết trước khi bạn sắp quên — và can thiệp trước khi quá muộn."*
