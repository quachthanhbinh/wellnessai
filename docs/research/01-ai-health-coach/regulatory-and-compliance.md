# AI Health Coach — Regulatory & Compliance Research

**Component:** AI Health Coach  
**Research date:** 2026-06-01

---

## Câu hỏi regulatory cốt lõi

> *Elfie AI Health Coach có phải là "Software as a Medical Device" (SaMD) không?*

**Câu trả lời ngắn:** Không — **nếu** được thiết kế đúng theo định nghĩa CDS-adjacent (Clinical Decision Support, không phải Clinical Decision Making).

---

## Framework phân loại

### FDA (US) — SaMD / CDS Guidance (2022)

FDA phân loại CDS software theo 4 tiêu chí:

| Tiêu chí | AI Health Coach (Elfie) | Kết quả |
|---|---|---|
| Intended use liên quan đến serious condition? | Có (hypertension, diabetes) | ⚠️ Risk factor |
| Intended for healthcare professional? | Không (consumer) | ⚠️ Higher scrutiny |
| Provides diagnosis or treatment recommendation? | **Không** — giải thích data, không chẩn đoán | ✅ Key protection |
| Clinician can independently review basis? | **Có** — mọi response đều có data source rõ ràng | ✅ Key protection |

**Kết luận FDA:** Nếu AI Coach chỉ **display/explain user's own data** và không đưa ra clinical recommendations → **Non-device CDS**, không cần FDA clearance.

**Ranh giới cần giữ:**
- ✅ "Huyết áp của bạn tuần này trung bình 142/89 — cao hơn tháng trước 8 điểm"
- ✅ "ISH guidelines khuyến nghị BP dưới 140/90 cho hypertension Stage 1"
- ❌ "Bạn nên tăng liều amlodipine"
- ❌ "Kết quả này cho thấy bạn có thể bị tiểu đường type 2"

### EU AI Act (2024, enforced 2026)

AI Health Coach nằm trong phân loại **"High-risk AI system"** theo Annex III — health and safety.

**Yêu cầu bắt buộc:**
- Conformity assessment trước khi deploy ở EU
- Technical documentation (AI system description, training data, validation)
- Human oversight requirement — user phải luôn có thể "override" AI
- Transparency: user phải biết họ đang tương tác với AI
- Accuracy, robustness, cybersecurity requirements
- Post-market monitoring

**Elfie đã có:** ISO27001, SOC2 T2, GDPR compliance → base foundation sẵn.  
**Cần thêm:** AI-specific documentation, conformity assessment, human oversight mechanism.

### HIPAA (US)

- AI Coach xử lý **Protected Health Information (PHI)** → yêu cầu BAA với LLM API provider
- **OpenAI:** Có HIPAA BAA (Enterprise tier)
- **Anthropic:** Có HIPAA BAA (Enterprise)
- **Google Gemini:** Có HIPAA BAA (Vertex AI)
- Conversation logs phải encrypted + access controls + audit trail

### PDPA (Thailand) / PDPD (Vietnam) / LGPD (Brazil)

Tất cả đều yêu cầu:
- **Explicit consent** trước khi process health data cho AI
- **Right to explanation** — user được quyền hỏi "tại sao AI nói vậy"
- **Data minimization** — chỉ dùng data cần thiết cho query
- **Deletion right** — user có thể xóa conversation history

---

## Rủi ro pháp lý cụ thể

### Rủi ro 1: Liability khi AI cho lời khuyên sai

**Scenario:** AI Coach nói "BP của bạn ổn" nhưng thực ra đang nguy hiểm → user bị tai biến.

**Mitigation:**
- Disclaimer rõ ràng trong onboarding: "AI Coach không thay thế tư vấn y tế"
- Hardcoded escalation triggers (BP > 180/120 → "Gọi bác sĩ ngay")
- AI không bao giờ nói "bình thường/ổn" — chỉ nói "theo guidelines X, target là Y, của bạn đang là Z"
- Terms of Service rõ ràng về giới hạn trách nhiệm

### Rủi ro 2: Off-label use trong markets chưa cleared

**Scenario:** User ở thị trường mà AI health advice bị regulate chặt (EU, US) dùng AI Coach và claim nó là medical advice.

**Mitigation:**
- Geofencing: tắt hoặc giới hạn features theo quốc gia
- Footer disclaimer trên mọi AI response
- Không tự mô tả là "AI doctor" hoặc "medical AI" trong marketing

### Rủi ro 3: Data breach của health conversations

**Scenario:** Conversation logs bị leak → user health information bị lộ.

**Mitigation:**
- Encrypt conversations at rest (AES-256) + in transit (TLS 1.3)
- No PII trong logs gửi đến LLM provider
- 90-day auto-deletion default (configurable)
- SOC2 audit trail

---

## Đối chiếu với thị trường hiện tại của Elfie

| Thị trường | Regulatory body | AI health app classification | Đánh giá rủi ro |
|---|---|---|---|
| Vietnam | MOH Vietnam | Chưa có framework AI health cụ thể | 🟢 Thấp — window opportunity trước khi regulate |
| Thailand | FDA Thailand | Medical device notification nếu diagnostic | 🟡 Trung bình — cần legal review |
| Brazil | ANVISA | RDC 657/2022 cho SaMD | 🟡 Trung bình — CDS non-device exemption cần document |
| France/EU | CE + EU AI Act | High-risk AI, conformity assessment | 🔴 Cao — cần EU AI Act compliance trước deploy |
| US | FDA | Non-device CDS nếu không diagnostic | 🟡 Trung bình — BAA required, legal review needed |

**Chiến lược rollout:** Launch tại Vietnam/SEA trước (lower regulatory hurdle) → gather RWE → EU/US expansion với full compliance dossier.

---

## Checklist compliance cho spec

- [ ] Legal review: Xác nhận AI Coach = Non-device CDS tại từng thị trường mục tiêu
- [ ] BAA ký với LLM provider trước khi xử lý PHI
- [ ] Onboarding flow: informed consent rõ ràng về AI, không phải bác sĩ
- [ ] Escalation protocol: hardcoded triggers cho urgent symptoms
- [ ] EU AI Act: technical documentation + human oversight mechanism
- [ ] Data processing: không gửi PII sang third-party API
- [ ] Audit trail: log mọi AI response với timestamp + model version
- [ ] Medical review: bác sĩ review sample responses định kỳ (monthly audit)
- [ ] Disclaimer: rõ ràng, ngắn gọn, trong mọi conversation
