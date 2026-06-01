# Feature Brief — AI Continuity Loop

**Date:** 2026-06-01 | **Status:** Brainstorm  
**Repo:** wellnessai | **Platform:** Elfie

---

## Tóm tắt

Ba tính năng AI riêng lẻ không đủ mạnh. Kết hợp lại, chúng tạo thành một **vòng lặp liên tục** giữ người dùng gắn bó, ngăn họ bỏ điều trị, và đưa dữ liệu thực tế của họ thẳng vào tay bác sĩ — tất cả hoàn toàn tự động.

```
User mở app
      │
      ▼
[AI Health Coach]  ◄──────────────────────────────┐
Hỏi & tổng hợp dữ liệu sức khỏe hàng ngày        │
      │                                           │
      ▼                                           │
[Predictive Adherence AI]                         │
Phát hiện nguy cơ bỏ điều trị 2–3 tuần trước     │
→ Tự động chọn intervention phù hợp ─────────────┘
      │
      ▼
[Agentic Patient Summary]
Trước mỗi tái khám: tự tổng hợp hồ sơ gửi vào ElfieCare
→ Bác sĩ thấy toàn cảnh 30 ngày qua trong 10 giây
```

---

## Bài toán

### Phía người dùng
- Người mắc bệnh mãn tính cần theo dõi hàng ngày, nhưng **không có ai giúp họ hiểu dữ liệu** của chính mình.
- Sau 6–12 tháng, **dưới 50% bệnh nhân** tiếp tục uống thuốc đúng giờ.
- Elfie hiện đã thu thập vitals, medication log, wearable data — nhưng user vẫn nhìn vào **những con số thô** mà không có ngữ cảnh.

### Phía bác sĩ
- Bác sĩ mất **5–10 phút mỗi lần tái khám** chỉ để hỏi "tuần qua bạn làm gì?" mà câu trả lời thường không chính xác.
- ElfieCare có Pre-Visit Agent và Consultation Scribe, nhưng **chưa có cầu nối** với dữ liệu tự theo dõi của patient trên Elfie App.

### Khoảng trống thị trường
- AI coaching hiện tại trên Elfie chỉ dành cho **gói insurer** — người dùng thông thường không có.
- Không đối thủ nào trong thị trường emerging có vòng lặp **consumer app → AI → doctor** khép kín.

---

## Ba thành phần của giải pháp

### 1. AI Health Coach (free cho tất cả)

**"Chat với dữ liệu sức khỏe của bạn"**

User có thể hỏi bằng ngôn ngữ tự nhiên, AI trả lời dựa trên toàn bộ lịch sử của họ trên Elfie.

**Ví dụ tương tác:**
- *"Huyết áp của tôi tuần này có bình thường không?"*
- *"Tại sao tôi ngủ kém hơn tháng trước?"*
- *"Tôi có đang tiến bộ so với mục tiêu cân nặng không?"*

**Constraints quan trọng:**
- Không đưa ra chẩn đoán hoặc khuyến nghị thay đổi thuốc
- Mọi câu trả lời liên quan đến điều trị phải có disclaimer và gợi ý hỏi bác sĩ
- CDS-adjacent: công cụ hiểu, không phải công cụ chẩn đoán
- Coins cho các conversation milestone để giữ gamification

---

### 2. Predictive Adherence AI — "Dropout Prevention Engine"

**"Biết trước ai sẽ bỏ điều trị 2–3 tuần trước khi xảy ra"**

Mô hình học từ 3B+ coin events, engagement patterns, và retention history để tính **adherence risk score** cho từng user. Khi risk tăng, hệ thống tự chọn intervention phù hợp nhất.

**Intervention menu (tự động chọn theo context):**
| Risk level | Intervention |
|---|---|
| Thấp | Coin bonus streak reminder |
| Trung bình | Gamification challenge mới, badge mới |
| Cao | Nudge từ family member (nếu đã pair) |
| Rất cao | Doctor nudge qua ElfieCare |

**Data advantage:** Elfie đã có longitudinal dataset lớn nhất ở thị trường emerging — đây là moat thực sự mà đối thủ không thể copy nhanh.

---

### 3. Agentic Patient Summary — Cầu nối App ↔ ElfieCare

**"Bác sĩ thấy 30 ngày qua trong 10 giây, không cần hỏi"**

Trước mỗi lịch tái khám (detected từ appointment reminders đã có), một AI agent tự động:
1. Thu thập toàn bộ dữ liệu Elfie của patient từ lần khám trước đến nay
2. Tổng hợp thành structured clinical summary (vitals trend, adherence rate, symptom changes, lab delta)
3. Gửi vào ElfieCare của bác sĩ phụ trách

**Ví dụ output:**
```
Bệnh nhân: Nguyễn Văn A | 30 ngày qua (01/05 – 01/06/2026)
─────────────────────────────────────────────────
Huyết áp:   TB 142/89 mmHg  ↑ +8/+5 so với tháng trước
Medication: 26/30 ngày ✓ | Bỏ: 4/5 (ngày 12, 19, 23, 27, 31/05)
Bước chân:  TB 4,200 bước/ngày  ↓ −38% so với tháng trước
Cân nặng:   82.4 kg  ↑ +1.2 kg
Triệu chứng tự báo: đau đầu buổi sáng (3 lần), chóng mặt (1 lần)
─────────────────────────────────────────────────
⚠️ Cần chú ý: BP tăng + adherence thấp + giảm vận động
```

**Privacy:** Patient phải opt-in cho data sharing với bác sĩ. Không tự động, không im lặng.

---

## Tại sao ba thành phần này cần đi cùng nhau

| Riêng lẻ | Vấn đề |
|---|---|
| Chỉ AI Coach | User hiểu dữ liệu nhưng bác sĩ vẫn mù |
| Chỉ Predictive AI | Giữ user nhưng không tạo thêm giá trị y tế |
| Chỉ Patient Summary | Bác sĩ có data nhưng user không gắn bó đủ để tạo ra data chất lượng |

**Kết hợp:** AI Coach tạo engagement → Predictive AI giữ engagement → Patient Summary biến engagement thành clinical value → Bác sĩ tin tưởng Elfie hơn → Recommend nhiều hơn → Thêm user → Nhiều data hơn → AI tốt hơn.

---

## Fit với DNA của Elfie

| Nguyên tắc Elfie | AI Continuity Loop |
|---|---|
| Free cho tất cả | AI Coach miễn phí; Premium version cho insurer |
| Medically-proven | Mọi output AI có citation; bác sĩ luôn là người quyết định cuối |
| Gamified | Coins cho conversation, coins khi risk score cải thiện |
| Privacy-first | Opt-in cho mọi data sharing; HIPAA/GDPR compliant by design |
| Multi-disease | Hoạt động với toàn bộ 400+ bệnh đang support |
| Proactive | Predictive AI là bước nâng cấp tự nhiên của proactive outreach hiện có |

---

## Rủi ro cần giải quyết trong spec

1. **Regulatory:** AI Coach không được vượt qua ranh giới CDS-adjacent → cần medical review quy trình response
2. **Privacy:** Patient Summary opt-in flow phải rõ ràng, granular (chọn loại data chia sẻ)
3. **Hallucination:** AI Coach trả lời sai về sức khỏe nguy hiểm hơn nhiều so với hallucination thông thường → cần guardrails và citation bắt buộc
4. **Model bias:** Predictive Adherence AI có thể bias theo demographics nếu training data không balanced
5. **Doctor adoption:** Patient Summary vô nghĩa nếu bác sĩ không check ElfieCare → cần adoption plan song song

---

## Bước tiếp theo

Workflow: **SPEC → PLAN → IMPLEMENT (TDD) → VERIFY**

Giao Product Owner: làm rõ scope, acceptance criteria, và ranh giới regulatory cho từng component.
