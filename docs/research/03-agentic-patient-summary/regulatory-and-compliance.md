# Agentic Patient Summary — Regulatory & Compliance Research

**Component:** Agentic Patient Summary  
**Research date:** 2026-06-01

---

## Câu hỏi regulatory cốt lõi

> *Agentic Patient Summary có phải là SaMD không? Nó tạo ra liability gì khi đưa data vào tay bác sĩ?*

**Câu trả lời ngắn:** Không phải SaMD — nếu được framing đúng là "data synthesis tool", không phải "clinical decision support." Tuy nhiên đây là component có **regulatory complexity cao nhất** trong 3 components, vì nó nằm tại giao điểm giữa patient data, doctor workflow, và clinical decision-making.

---

## Phân tích SaMD / Non-SaMD

### FDA Framework

Patient Summary là một dạng "Patient-Generated Health Data (PGHD) aggregator" — phổ biến và đã có guidance.

**Không phải SaMD nếu:**
- Chỉ aggregate và display dữ liệu mà bác sĩ có thể tự thu thập bằng cách hỏi patient
- Không đưa ra clinical interpretation ("BP này cho thấy…")
- Bác sĩ tự đọc và tự quyết định — AI chỉ là "secretary"

**Rủi ro trở thành SaMD nếu:**
- Summary bao gồm AI-generated clinical interpretation ("trending toward hypertensive crisis")
- Automatic risk scoring mà bác sĩ không thể audit

**Mitigation trong design:**
```
✅ "BP average: 142/89 mmHg (↑ from 134/84 last period)"
✅ "⚠️ Flag: Value above patient's stated target of <140/90"
❌ "Patient appears to be developing uncontrolled hypertension"
❌ "Recommend increasing antihypertensive dosage"
```

### EU AI Act

Agentic Patient Summary gần như chắc chắn **High-risk AI** theo Annex III vì:
- Intends to influence medical decisions
- Involves vulnerable population (chronic patients)
- Automated processing of health data

**Yêu cầu High-risk AI (EU AI Act, Article 9–15):**

| Yêu cầu | Elfie implementation |
|---|---|
| Risk management system | Document risks + mitigation (bắt đầu từ file này) |
| Data governance | Training/test data requirements documented |
| Technical documentation | System description, architecture, validation |
| Record-keeping | Automatic logging (đã có audit trail) |
| Transparency | Doctor must know it's AI-generated |
| Human oversight | Doctor can dismiss/override summary |
| Accuracy, robustness, cybersecurity | Performance metrics documented |
| Post-market monitoring | Track errors/adverse events |

---

## Consent Framework — Critical Design Decision

### Dual consent requirement

Agentic Patient Summary **chia sẻ data theo 2 chiều** → cần consent từ cả 2 phía:

**1. Patient consent (data sharing)**
```
"Cho phép Elfie chia sẻ dữ liệu sức khỏe của tôi với bác sĩ [Dr. X] dưới 
dạng tóm tắt trước mỗi lần tái khám."

Loại data được chia sẻ:
☑ Chỉ số sức khỏe (huyết áp, cân nặng, nhịp tim)
☑ Lịch sử uống thuốc
☑ Hoạt động thể chất
☐ Nhật ký triệu chứng (tùy chọn)
☐ Lịch sử hội thoại với AI Coach (tùy chọn)

Tần suất: Trước mỗi lịch tái khám / Mỗi 30 ngày
Bác sĩ: [Dr. Nguyen Van B] — có thể hủy liên kết bất cứ lúc nào
```

**2. Doctor consent (receiving patient data in ElfieCare)**
```
"Tôi đồng ý nhận tóm tắt dữ liệu sức khỏe từ bệnh nhân của tôi qua ElfieCare.
Tôi hiểu rằng:
- Đây là dữ liệu tổng hợp, không thay thế đánh giá lâm sàng
- Tôi có thể tắt tính năng này bất cứ lúc nào
- Dữ liệu được lưu trữ tuân thủ [local privacy law]"
```

### Consent granularity

Không phải binary on/off — nên cho phép patient control cụ thể:

| Data category | Default | Changeable |
|---|---|---|
| Vitals (BP, HR, glucose) | ON | Yes |
| Medication adherence | ON | Yes |
| Physical activity | ON | Yes |
| Symptom logs | OFF | Yes — opt-in |
| AI Coach conversations | OFF | Yes — opt-in, separate consent |
| Lab results | OFF | Yes — opt-in |

---

## Vấn đề pháp lý quan trọng

### 1. "Duty to act" khi bác sĩ nhận summary

**Scenario:** Bác sĩ nhận summary thấy BP rất cao → không hành động → patient bị biến chứng → patient/family kiện bác sĩ "đã được thông báo mà không làm gì."

**Phân tích:** Đây là **rủi ro của bác sĩ, không của Elfie** — nhưng Elfie không nên tạo điều kiện cho situation này.

**Mitigations:**
- Không gửi summary "emergency" framing — chỉ là "FYI before visit"
- Doctor terms: explicit "receipt of this summary does not create clinical obligation"
- Không dùng từ "alert" cho summary — dùng "pre-visit briefing"
- Cân nhắc: chỉ deliver khi doctor đã confirm "I will see this patient" (appointment confirmed)

### 2. Data accuracy liability

**Scenario:** App bug gây ra vitals hiển thị sai → bác sĩ ra quyết định dựa trên data sai → harm.

**Mitigations:**
- Disclaimer rõ ràng: "Data as recorded by patient. Verify with in-office measurement."
- Show data source (manual entry vs. wearable vs. device)
- Show data confidence: "Low completeness (< 50% days logged) — interpret with caution"
- Phải có legal review về disclaimer language

### 3. Cross-border data transfer

**Scenario:** Patient ở Vietnam, bác sĩ ở France → data transferred cross-border.

**Analysis:** Thường không phải issue nếu:
- Patient initiates/consents to the sharing
- Standard Contractual Clauses (SCCs) in place
- Consistent with Elfie's existing GDPR framework

---

## HIPAA Specifics (US market)

**Business Associate Agreement (BAA)** cần thiết cho:
- LLM provider nhận health data để generate summary
- ElfieCare platform nếu used by US-licensed physicians
- Any third-party receiving summary data

**Minimum Necessary standard:** Summary should include minimum data necessary for the clinical purpose — không dump toàn bộ patient history nếu chỉ cần 30-day vitals summary.

**Patient Access Rights:** Theo HIPAA, patients có right to access their own health records, including data used to generate summaries → Elfie phải provide this access via app.

---

## Đặc thù theo thị trường

| Thị trường | Yêu cầu đặc thù |
|---|---|
| **Vietnam** | Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân: consent bắt buộc cho sensitive health data; data localization cho some categories |
| **Thailand** | PDPA Section 26: health data là sensitive data, explicit consent bắt buộc; cross-border transfer cần adequate protection |
| **Brazil** | LGPD Article 11: health data = sensitive; processing cần consent hoặc legitimate interest documented |
| **France/EU** | GDPR Article 9 + EU AI Act: consent required, DPIA (Data Protection Impact Assessment) likely required |
| **US** | HIPAA: BAA required; state laws vary (California CMIA stricter than HIPAA) |

---

## Compliance checklist cho spec

- [ ] Dual consent flow: patient grants sharing + doctor acknowledges receipt
- [ ] Granular data category controls in patient settings
- [ ] Disclaimer language: medical/legal review trước launch
- [ ] EU AI Act: High-risk classification → technical documentation + conformity assessment
- [ ] HIPAA: BAA with LLM provider before processing US patient data
- [ ] Data minimization: summary generation pipeline logs what data was included + why
- [ ] Doctor terms of service: no clinical duty created by receipt of summary
- [ ] Audit trail: every summary generated, delivered, viewed — logged with timestamp
- [ ] Vietnam PDPD: data localization review for local patient data
- [ ] DPIA: conduct Data Protection Impact Assessment for EU deployment
- [ ] Patient right of access: ability to see/download all summaries sent about them
- [ ] Revocation flow: if patient revokes consent, delete pending summaries + notify doctor
