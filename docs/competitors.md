# Competitor Analysis — Elfie (Runner-ups)

Tài liệu này tổng hợp các đối thủ "runner-up" đã được phân tích, giải thích các tính năng chính mà họ cung cấp, và một bảng đánh giá tính năng (weightage) theo mức độ quan trọng/khả thi với mô hình hiện tại của `Elfie`.

## Mục tiêu
- Lưu trữ thông tin đối thủ để tham chiếu nội bộ.
- Giúp ưu tiên roadmap sản phẩm bằng cách đánh giá tính năng theo tác động với mô hình doanh nghiệp của `Elfie`.

---

## Đối thủ và tính năng chính (tóm tắt + giải thích)

### Omada Health
- Tính năng nổi bật: CDC-recognized structured programs (ví dụ Diabetes Prevention Program - DPP) với bằng chứng lâm sàng công khai.
- Giải thích: Các chương trình chuẩn hoá (DPP) thường đi kèm curriculum, measurement plan và báo cáo outcomes. Điều này giúp Omada bán cho employers/insurers vì họ có dữ liệu RCT/real-world chứng minh ROI.

### Lark Health
- Tính năng nổi bật: AI conversational coach 24/7 và các can thiệp CBT-style tự động hoá.
- Giải thích: Lark tối ưu cho scale bằng automation — người dùng tương tác qua chat bot, nhận intervention theo thời gian thực, giảm chi phí coach con người và tăng tần suất tương tác.

### Medisafe
- Tính năng nổi bật: Barcode scanning, pharmacy/Rx-sync, pill-level reminders, caregiver sharing và refill reminders.
- Giải thích: Tích hợp trực tiếp với quy trình đơn thuốc/nhà thuốc giúp tăng tuân thủ — tính năng này rất hấp dẫn với PSP và pharma vì liên quan trực tiếp tới adherence metrics.

### Vida Health
- Tính năng nổi bật: 1:1 licensed clinician assignment (therapists, dietitians) kết hợp với chương trình số.
- Giải thích: Kết hợp con người có thể nâng cao outcomes cho các ca phức tạp; vận hành theo mô hình có chi phí cao hơn nhưng có thể được bán như dịch vụ có phí cho insurers/employers.

### Noom
- Tính năng nổi bật: Psychology-first curriculum (CBT-driven micro-lessons) và content funnel tối ưu cho retention.
- Giải thích: Noom đầu tư vào lesson sequencing, behavioural nudges và content testing để giữ người dùng tham gia dài hạn — hữu ích cho wellness programs.

### MyFitnessPal
- Tính năng nổi bật: Food database lớn, barcode food logging, nutrition breakdown và UX logging cực nhanh.
- Giải thích: Giá trị ở khả năng collect food data chính xác và ít friction — cơ sở dữ liệu thực phẩm + logging UX rất quan trọng cho chương trình dinh dưỡng.

### Propeller Health / ResMed
- Tính năng nổi bật: Device-grade respiratory sensors và event-level monitoring (inhaler sensors).
- Giải thích: Thiết bị kèm theo cho phép thu thập dữ liệu sự kiện y tế (inhaler use, wheeze events) — hữu ích cho chương trình COPD/hen và cho phép cảnh báo lâm sàng.

### Pear / Akili (DTx vendors)
- Tính năng nổi bật: Prescription digital therapeutics (DTx) có quy trình phê duyệt lâm sàng / regulatory.
- Giải thích: DTx có thể được kê đơn và thanh toán như therapy; đòi hỏi nghiên cứu lâm sàng, phê duyệt và quy trình kê đơn.

---

## Bảng tính năng — Mức độ ưu tiên (Weightage) cho `Elfie`

Chú giải cột:
- **Feature**: tên tính năng.
- **Description**: mô tả ngắn.
- **Present in Elfie?**: liệu `Elfie` hiện có (dựa trên `docs/elfie-platform-context.md`).
- **Source Competitors**: những đối thủ chính cung cấp tính năng này.
- **Weightage (1-5)**: mức ưu tiên đề xuất cho `Elfie` — 5 = rất quan trọng/ưu tiên cao; 1 = thấp hoặc không phù hợp ngay.
- **Rationale (ngắn)**: lý do xếp hạng theo mô hình doanh nghiệp và điểm mạnh `Elfie`.

| Feature | Description | Present in Elfie? | Source Competitors | Weightage (1-5) | Rationale |
|---|---|---:|---|---:|---|
| Pharmacy / Rx sync & refill reminders | Kết nối sự kiện Rx, barcode scan, refill alerts | Partial (manual import / med DB) | Medisafe, pharmacy integrations | 5 | Tác động trực tiếp đến adherence & PSP revenue; Elfie đã có medication DB nhưng thiếu Rx-level integration. |
| Pill-level reminders + caregiver sharing | Dose-specific reminders, caregiver escalation | Partial | Medisafe | 5 | Nhu cầu cao cho chronic care; tăng engagement và giá trị cho gia đình/clinicians. |
| 24/7 AI conversational coach | Chat-first automated coaching, CBT-style flows | Partial (AI coaching & journaling) | Lark, Noom | 5 | Tăng scale engagement, giảm chi phí hỗ trợ; phù hợp với ElfieCoins gamification. |
| Licensed 1:1 clinician programs | Billed clinician coaching (dietitian/therapist) | Partial (ElfieCare for clinicians exists) | Vida Health | 4 | Tăng hiệu quả cho ca phức tạp; có thể mở nguồn doanh thu B2B. |
| CDC-recognized structured programs (DPP) | Standardized prevention programs with published outcomes | No | Omada | 4 | Giúp bán cho employers/insurers bằng chứng ROI; cần đầu tư nghiên cứu/partnership. |
| Employer ROI dashboards & HR analytics | Dashboards, cohort analytics, cost-savings modelling | Partial | Omada | 5 | Cốt lõi cho bán B2B; Elfie có analytics nhưng cần bộ dashboard chuyên sâu cho HR. |
| Prescription Digital Therapeutics (DTx) pathway | Regulatory-cleared prescribable apps | No | Pear, Akili | 2 | Cao chi phí/time-to-market; phù hợp nếu Elfie muốn phát triển DTx. |
| Device-grade sensors / inhaler integration | Inhaler sensors, event-level respiratory monitoring | No | Propeller / ResMed | 3 | Có giá trị cho hô hấp; nhưng cần partnerships với device vendors. |
| Food database + fast logging UX | Large food DB, barcode scanning, nutrition auto-calculation | Partial | MyFitnessPal | 3 | Hữu ích cho nutrition programs; Elfie có wellness content but may lack full DB UX. |
| Automated CBT micro-lessons & content funnels | Sequenced lessons, A/B tested micro-content | Partial | Noom | 4 | Tăng retention cho wellness; tích hợp tốt với existing programs. |
| Care escalation & clinical workflows | Escalation to providers, escalation rules & audits | Partial | Omada, Vida | 4 | Quan trọng cho safety và bán cho providers; ElfieCare has tools but can deepen workflows. |

---

## Gợi ý hành động nhanh (3 tính năng ưu tiên để bắt đầu)
1. **Pharmacy / Rx sync + pill-level reminders** (Weightage 5): tích hợp với một số nhà thuốc/đối tác Rx API, thêm barcode scan và refill events.
2. **Employer ROI dashboards** (Weightage 5): xây dựng dashboard cohort và PMPM ROI models để tăng doanh thu B2B.
3. **24/7 AI conversational coach** (Weightage 5): mở rộng khả năng AI chat hiện có thành flow CBT tự động hoá cho engagement liên tục.

---

File lưu tại: `docs/competitors.md`.

Nếu muốn, tôi có thể:
- xuất file này thành PDF hoặc CSV bảng tính; hoặc
- mở rộng từng tính năng thành PRD ngắn 1 trang.
