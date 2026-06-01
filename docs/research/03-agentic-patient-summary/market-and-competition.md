# Agentic Patient Summary — Market & Competition Research

**Component:** Agentic Patient Summary (Consumer ↔ ElfieCare bridge)  
**Research date:** 2026-06-01

---

## Bài toán thị trường

### Consultation quality gap

| Pain point | Data |
|---|---|
| Thời gian bác sĩ dành để "hỏi lại lịch sử" | 3–8 phút / lần khám (WHO, 2023) |
| Độ chính xác của patient self-report | 60–70% (bệnh nhân không nhớ chính xác) |
| Tỷ lệ bác sĩ muốn có home monitoring data | 87% (American Heart Association survey) |
| Tỷ lệ bệnh nhân thực sự mang data đến khám | < 15% |
| Tái nhập viện trong 30 ngày do thiếu follow-up data | ~20% (US Medicare data) |

### Opportunity

Khoảng cách giữa **dữ liệu bệnh nhân tự thu thập** và **dữ liệu bác sĩ nhìn thấy** là một trong những inefficiency lớn nhất của hệ thống y tế toàn cầu. Elfie đang ở vị trí lý tưởng để làm cầu nối này.

---

## Landscape cạnh tranh

### Clinical Summary / Patient Data Portability

| Sản phẩm | Approach | Gap |
|---|---|---|
| **Apple Health Records** | HL7 FHIR integration với hospital EHR | Chỉ pull data từ EHR → bác sĩ; không push home monitoring data → bác sĩ |
| **CommonHealth** | FHIR-based health record aggregator | Technical-first; không có AI summary layer; no emerging market presence |
| **Google Health** | Health data aggregation | Aggregator only; không tạo actionable summary cho bác sĩ |
| **Validic** | Remote patient monitoring data integration | Enterprise/B2B; không consumer-facing; expensive |
| **Dexcom CLARITY** | CGM data summary cho bác sĩ | Single disease (diabetes only); hardware-tied |
| **Withings** | Wearable + clinical summary | Hardware-tied; chỉ for Withings device users |

### EHR "Patient-Generated Health Data" Features

| EHR Vendor | Feature | Gap |
|---|---|---|
| **Epic MyChart** | Patient-generated data integration | Chỉ trong Epic ecosystem; US-centric |
| **Cerner (Oracle)** | Remote monitoring integration | Enterprise setup; not accessible for individual clinics |
| **HealthTap** | AI summary to telehealth doc | US only; telehealth-specific |

### Emerging market competitors

Thực tế: **Không có sản phẩm nào** trong emerging markets (Vietnam, Thailand, Brazil) tạo ra automated AI summary từ patient home monitoring data và đưa vào clinical workflow. Đây là **blue ocean** tại thị trường chính của Elfie.

---

## "Show Me Your Elfie" — Elfie's existing bridgehead

Elfie đã có một primitive version: bác sĩ có thể xem patient's Elfie dashboard trong ElfieCare. 

**Limitation hiện tại:**
- Manual: bác sĩ phải chủ động mở → xem → interpret raw data
- No AI synthesis: chỉ là data display, không có narrative summary
- No push: bác sĩ không nhận proactively trước khám
- No delta analysis: không so sánh với lần khám trước

**Agentic Patient Summary là bước tiến hóa tự nhiên của tính năng này.**

---

## Phân tích giá trị B2B

### Pharma — PSP enhancement

PSPs hiện tại tốn phần lớn chi phí cho **nurse/pharmacist call-backs** để thu thập patient-reported outcomes (PROs). Nếu Agentic Summary tự động hóa việc này:

| Metric | Traditional PSP | With Agentic Summary |
|---|---|---|
| Data collection cost per patient/month | $15–40 | ~$2–5 |
| Data completeness | 60–70% (patient recall) | 85–95% (app-logged) |
| Reporting turnaround | 1–2 weeks | Real-time |

→ Pharma trả premium cho **automated, high-quality PRO collection**.

### Insurer — Care gap identification

Insurer cần biết: "Bệnh nhân X có đang được chăm sóc đúng cách không?"

Agentic Summary cho phép care manager của insurer thấy patient data aggregation mà không cần gọi điện hỏi — tiết kiệm chi phí care management đáng kể.

---

## Positioning

> *"Lần đầu tiên trong lịch sử, mọi cuộc tái khám đều bắt đầu bằng sự thật — không phải ký ức."*

**Competitive moat:** Để có Agentic Summary tốt, cần: (1) consumer app đủ lớn, (2) bác sĩ platform, (3) data integration. Elfie là **tổ chức duy nhất** có cả 3 ở thị trường emerging.
