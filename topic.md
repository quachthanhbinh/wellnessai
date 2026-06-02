# Feature Brief — AI Continuity Loop

**Date:** 2026-06-02 | **Status:** Spec in progress (C1 approved, C4 pending review, C2/C3 drafted)
**Repo:** wellnessai | **Platform:** Elfie

---

## Tóm tắt

Bốn component AI, hai layer. Layer 1 (C1 + C4) xây dựng trải nghiệm cá nhân hóa tích lũy theo thời gian trên consumer app. Layer 2 (C2 + C3) dùng data từ Layer 1 để giữ user không bỏ điều trị và đưa data thực tế thẳng vào tay bác sĩ — tất cả hoàn toàn tự động.

```
User mở app
      │
      ▼
┌──────────────────────────────────────────────────────────┐
│  [C1] AI Health Coach                                    │◄──────────────┐
│  Chat với dữ liệu sức khỏe bằng ngôn ngữ tự nhiên       │               │
│        │                              ↑                  │               │
│        │  trích xuất thực thể         │ ngữ cảnh         │               │
│        ▼  (NER song song)             │ profile (~200t)  │               │
│  [C4] Proactive RAG + Progressive Profiling              │               │
│  Tự xây hồ sơ sức khỏe cá nhân từ hội thoại            │               │
│  → Mỗi session thông minh hơn session trước             │               │
└──────────────────────────────────────────────────────────┘               │
      │                                                                     │
      │  engagement signals + enriched profile features                     │
      ▼                                                                     │
[C2] Predictive Adherence AI                                               │
Phát hiện nguy cơ bỏ điều trị 2–3 tuần trước                             │
→ Tự động chọn intervention phù hợp ──────────────────────────────────────┘
      │
      │  enriched profile data (v2+)
      ▼
[C3] Agentic Patient Summary
Trước mỗi tái khám: tổng hợp 30 ngày gửi vào ElfieCare
→ Bác sĩ thấy toàn cảnh trong 10 giây
```

**Tại sao 4 chứ không phải 3:** Nếu không có C4, AI Health Coach (C1) bắt đầu lại từ đầu mỗi session — user phải nói lại bệnh, thuốc, lối sống mỗi lần. C4 là lớp bộ nhớ tích lũy biến C1 từ "chatbot trả lời câu hỏi" thành "AI biết tôi là ai". C4 cũng là input quality multiplier cho C2 (feature giàu hơn) và C3 (summary đầy đủ hơn).

---

## Bài toán

### Phía người dùng
- Người mắc bệnh mãn tính cần theo dõi hàng ngày, nhưng **không có ai giúp họ hiểu dữ liệu** của chính mình.
- Sau 6–12 tháng, **dưới 50% bệnh nhân** tiếp tục uống thuốc đúng giờ.
- Elfie hiện đã thu thập vitals, medication log, wearable data — nhưng user vẫn nhìn vào **những con số thô** mà không có ngữ cảnh.
- AI Health Coach không có bộ nhớ: mỗi session bắt đầu lại từ đầu, user phải lặp lại thông tin cá nhân, AI không nhận ra pattern dài hạn.

### Phía bác sĩ
- Bác sĩ mất **5–10 phút mỗi lần tái khám** chỉ để hỏi "tuần qua bạn làm gì?" mà câu trả lời thường không chính xác.
- ElfieCare có Pre-Visit Agent và Consultation Scribe, nhưng **chưa có cầu nối** với dữ liệu tự theo dõi của patient trên Elfie App.

### Khoảng trống thị trường
- AI coaching hiện tại trên Elfie chỉ dành cho **gói insurer** — người dùng thông thường không có.
- Không đối thủ nào trong thị trường emerging có vòng lặp **consumer app → AI có bộ nhớ → doctor** khép kín.

---

## Bốn thành phần của giải pháp

### 1. AI Health Coach — C1 (free cho tất cả)

**"Chat với dữ liệu sức khỏe của bạn"**

User có thể hỏi bằng ngôn ngữ tự nhiên, AI trả lời dựa trên toàn bộ lịch sử của họ trên Elfie (vitals, medication log, lab results, wearable data). Không có bộ nhớ hội thoại dài hạn ở bản thân C1 — đó là vai trò của C4.

**Ví dụ tương tác:**
- *"Huyết áp của tôi tuần này có bình thường không?"*
- *"Tại sao tôi ngủ kém hơn tháng trước?"*
- *"Tôi có đang tiến bộ so với mục tiêu cân nặng không?"*

**Constraints quan trọng:**
- Không đưa ra chẩn đoán hoặc khuyến nghị thay đổi thuốc
- Mọi câu trả lời liên quan đến điều trị phải có disclaimer và gợi ý hỏi bác sĩ
- CDS-adjacent: công cụ hiểu, không phải công cụ chẩn đoán
- Coins cho các conversation milestone để giữ gamification

**Spec:** `docs/specs/01-ai-health-coach.md` — APPROVED

---

### 4. Proactive RAG + Progressive Profiling — C4 (memory layer của C1)

**"AI ghi nhớ bạn là ai — không cần điền form"**

Lớp bộ nhớ tích lũy chạy bên trong C1. Tự động trích xuất thực thể sức khỏe (bệnh, thuốc, nhân khẩu học, lối sống) từ hội thoại tự nhiên bằng NER pipeline, lưu vào hồ sơ sức khỏe cá nhân theo từng `profile_id`, và inject lại vào context của mọi session tiếp theo.

**Ví dụ tích lũy giá trị:**
- Session 1: User nhắc đến tiểu đường type 2 khi hỏi về HbA1c → C4 ghi nhận `condition: "type 2 diabetes"` với confidence score
- Session 3: User hỏi về giấc ngủ → C4 inject "User có tiểu đường type 2" vào context, AI tự liên kết insulin resistance với sleep quality mà không cần user nhắc lại
- Session 7: Profile 50% complete → Elfie Coin milestone, AI ngừng hỏi những gì đã biết, chỉ hỏi những gì còn thiếu cho câu hỏi hiện tại

**Ba cơ chế cốt lõi:**
1. **NER extraction** — GLiNER/SpaCy chạy song song với RAG retrieval sau PII scrubber; 7 entity types; không phải LLM
2. **Profile Gap Analyzer** — rule-based, map query intent → required fields → embed ≤ 2 follow-up questions vào response khi thiếu data
3. **Profile-aware RAG** — query expansion + reranking dựa trên active profile fields; context summary ~200 tokens injected vào mọi prompt

**Gamification:** Elfie Coins tại 2 milestones: first confirmed field + profile 50% complete cho primary condition.

**Family Care:** Profile isolation cứng theo `profile_id` — tuyệt đối không cross-profile. MVP chỉ áp dụng cho self-profile; managed profiles (bố mẹ, con cái) là v2 sau legal review.

**Roadmap:**
- MVP: Rule-based orchestration + vector RAG
- v2: AgenticRAG — LangGraph multi-hop cho complex queries (chỉ queries phức tạp, không thay toàn bộ pipeline)
- v3: GraphRAG — Medical Knowledge Graph (Neo4j/AGE) cho causal reasoning

**Spec:** `docs/specs/04-proactive-rag-progressive-profiling.md` — PENDING REVIEW

---

### 2. Predictive Adherence AI — C2 — "Dropout Prevention Engine"

**"Biết trước ai sẽ bỏ điều trị 2–3 tuần trước khi xảy ra"**

Mô hình học từ 3B+ coin events, engagement patterns, và retention history để tính **adherence risk score** cho từng user. Khi risk tăng, hệ thống tự chọn intervention phù hợp nhất. Trong v2+, enriched profile data từ C4 sẽ bổ sung thêm clinical features (medication complexity, chronic condition burden) vào risk model.

**Intervention menu (tự động chọn theo context):**
| Risk level | Intervention |
|---|---|
| Thấp | Coin bonus streak reminder |
| Trung bình | Gamification challenge mới, badge mới |
| Cao | Nudge từ family member (nếu đã pair) |
| Rất cao | Doctor nudge qua ElfieCare |

**Data advantage:** Elfie đã có longitudinal dataset lớn nhất ở thị trường emerging — đây là moat thực sự mà đối thủ không thể copy nhanh.

**Spec:** `docs/specs/02-predictive-adherence-ai.md` — DRAFTED

---

### 3. Agentic Patient Summary — C3 — Cầu nối App ↔ ElfieCare

**"Bác sĩ thấy 30 ngày qua trong 10 giây, không cần hỏi"**

Trước mỗi lịch tái khám (detected từ appointment reminders đã có), một AI agent tự động:
1. Thu thập toàn bộ dữ liệu Elfie của patient từ lần khám trước đến nay
2. Tổng hợp thành structured clinical summary (vitals trend, adherence rate, symptom changes, lab delta)
3. Gửi vào ElfieCare của bác sĩ phụ trách

Trong v2+, profile data từ C4 (confirmed conditions, medications, chronic symptoms) bổ sung thêm context cho summary — bác sĩ thấy không chỉ "số đo" mà còn "bối cảnh lâm sàng" từ hội thoại.

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

**Spec:** `docs/specs/03-agentic-patient-summary.md` — DRAFTED

---

## Tại sao bốn thành phần này cần đi cùng nhau

| Thiếu component | Vấn đề |
|---|---|
| Thiếu C1 (AI Health Coach) | Không có giao diện hội thoại → C4 không có input |
| Thiếu C4 (Progressive Profiling) | C1 bắt đầu từ đầu mỗi session; C2 thiếu clinical features; C3 summary thiếu context bệnh lý từ hội thoại |
| Thiếu C2 (Predictive Adherence) | User hiểu và được cá nhân hóa nhưng vẫn bỏ điều trị sau 6 tháng; engagement drop không được ngăn chặn |
| Thiếu C3 (Patient Summary) | Data phong phú nhưng bác sĩ không nhận được; vòng lặp consumer → doctor bị đứt; doctor adoption không có |

**Flywheel:** C1+C4 tạo engagement + data chất lượng → C2 giữ engagement → C3 biến engagement thành clinical value → bác sĩ tin Elfie → recommend nhiều hơn → thêm user → data tốt hơn → AI tốt hơn.

---

## Fit với DNA của Elfie

| Nguyên tắc Elfie | AI Continuity Loop |
|---|---|
| Free cho tất cả | C1 AI Coach miễn phí; C4 Progressive Profiling miễn phí; Premium version cho insurer |
| Medically-proven | Mọi output AI có citation; bác sĩ luôn là người quyết định cuối; AI chỉ "lập luận", không "sáng tạo kiến thức" |
| Gamified | Coins cho conversation milestones (C1), profile milestones (C4), khi risk score cải thiện (C2) |
| Privacy-first | Opt-in cho mọi data sharing; hồ sơ profile isolated theo `profile_id`; HIPAA/GDPR/PDPA/PDPD compliant by design |
| Multi-disease | Hoạt động với toàn bộ 400+ bệnh đang support; Field Catalogue và intent map của C4 extensible |
| Proactive | C2 là bước nâng cấp tự nhiên của proactive outreach hiện có; C4 embed follow-up questions chủ động vào hội thoại |
| Hyper-Personalization | C4 biến "AI biết tuốt" thành "AI thấu hiểu": kết nối trực tiếp với "vòng đời sinh hoạt" của từng user |

---

## Trạng thái spec

| Component | Spec | Trạng thái |
|---|---|---|
| C1 — AI Health Coach | `docs/specs/01-ai-health-coach.md` | APPROVED |
| C2 — Predictive Adherence AI | `docs/specs/02-predictive-adherence-ai.md` | DRAFTED (PM review v3) |
| C3 — Agentic Patient Summary | `docs/specs/03-agentic-patient-summary.md` | DRAFTED (TA review v3) |
| C4 — Proactive RAG + Progressive Profiling | `docs/specs/04-proactive-rag-progressive-profiling.md` | PENDING REVIEW |

**Thứ tự triển khai đề xuất:** C1 (deployed) → C4 (enhance C1, no dependency on C2/C3) → C2 (depends on C1 engagement data; C4 features optional in v1) → C3 (depends on C1 + C4 for enriched summaries in v2)

---

## Rủi ro cần giải quyết trong spec

1. **Regulatory (C1, C4):** AI Coach không được vượt qua ranh giới CDS-adjacent; profile data không được dùng để chẩn đoán → Medical Affairs sign-off bắt buộc trước mọi deployment
2. **Privacy (C3, C4):** Patient Summary opt-in và Progressive Profiling consent phải rõ ràng, granular; hồ sơ profile isolated tuyệt đối theo `profile_id`; PDPD Vietnam data localization là launch-blocking nếu Legal xác định yêu cầu in-country
3. **Hallucination (C1, C4):** AI Coach trả lời sai về sức khỏe nguy hiểm hơn hallucination thông thường; profile data sai có thể dẫn đến personalization sai → 2-stage safety layer + adversarial test suite bắt buộc; NER confidence threshold và staging flow ngăn profile sai được dùng
4. **Model bias (C2):** Predictive Adherence AI có thể bias theo demographics nếu training data không balanced → fairness audit trước production
5. **Doctor adoption (C3):** Patient Summary vô nghĩa nếu bác sĩ không check ElfieCare → cần adoption plan song song
6. **NER accuracy (C4):** Việt Nam v1 launch với English-only NER (Vietnamese là v1.1 gate); F1 ≥ 0.85 per entity type là hard deployment gate

---

## Bước tiếp theo

Workflow: **SPEC → PLAN → IMPLEMENT (TDD) → VERIFY**

| Ưu tiên | Action | Owner |
|---|---|---|
| 1 | Technical Advisor review C4 spec (`04-proactive-rag-progressive-profiling.md`) | Technical Advisor |
| 2 | Project Manager review C4 spec và lập delivery plan | Project Manager |
| 3 | Legal xác định viết bằng văn bản: PDPD Vietnam data localization cho profile store | Legal |
| 4 | Medical Affairs confirm: ICD-10 dictionary từ disease catalogue hiện có có đủ dùng cho C4 NER không | Medical Affairs |
| 5 | Engineering: C4 NER service capacity sizing cho combined C3 + C4 load | Technical Advisor + Engineering |
