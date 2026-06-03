# Tóm tắt mapping JD → Repo và các phần bổ sung

## Mục tiêu
Tài liệu này tóm tắt cách repo hiện tại đáp ứng các yêu cầu trong JD, những phần thiếu đã được thêm nhanh (scaffold), và giải thích ngắn gọn lựa chọn công nghệ.

## 1) Mapping nhanh JD → Evidence trong repo
- Lead & process: Quy trình và rules nằm ở `AGENTS.md` và `docs/rules/*.md` (architecture, testing). Có policy, review gates và checklist.
- Microservices & architecture: Thiết kế service được mô tả trong `final-vi.md` (AICoachService, ProfilingService, AdherenceAIService, PatientSummaryService). Pipeline event-driven và profile store mô tả rõ.
- Agentic AI & RAG: Hướng dẫn triển khai Proactive RAG và Agentic RAG chi tiết trong `docs/guides/proactive-agentic-rag-implementation-guide.md`.
- Data pipelines & inference: `docs/specs/02-predictive-adherence-ai.md` mô tả batch scoring, feature store và model choices (XGBoost/LightGBM). Real-time được để out-of-scope.
- Privacy/Compliance: Agentic Patient Summary spec và Predictive Adherence spec có nhiều yêu cầu tuân thủ, consent, key-vault pseudonymization.

## 2) Những phần còn thiếu (production-readiness)
- CI/CD workflow (GitHub Actions) — MISSING (thêm mẫu `ci.yml` dưới `.github/workflows/`).
- Container image build / Dockerfile cho từng service — MISSING (thêm Dockerfile mẫu cho `ProfilingService`).
- Minimal runnable service code + healthcheck endpoints — MISSING (thêm scaffold FastAPI service `ProfilingService`).
- Automated tests & test runner integration — MISSING (thêm pytest sample).
- K8s manifests / deployment examples — MISSING (thêm manifest mẫu cho minh hoạ).
- Monitoring / metrics / runbooks — MISSING (documented in spec, not implemented).

Những phần trên đã được scaffold trong `infra/profiling_service/` và `.github/workflows/ci.yml` để bạn có thể demo nhanh năng lực vận hành backend.

## 3) Các file mới tôi đã thêm (đường dẫn)
- `docs/quick-apply-summary.md` (file này)
- `infra/profiling_service/README.md` — hướng dẫn nhanh
- `infra/profiling_service/requirements.txt` — dependency
- `infra/profiling_service/Dockerfile` — build image
- `infra/profiling_service/app/main.py` — FastAPI minimal service (health endpoints)
- `infra/profiling_service/tests/test_health.py` — pytest sample
- `.github/workflows/ci.yml` — CI workflow build + test
- `infra/k8s/profiling-deployment.yaml` — deployment/service mẫu

## 4) Giải thích công nghệ ngắn gọn (tại sao chọn)
- FastAPI: nhẹ, async, tài liệu tốt, phù hợp để tạo microservice health/ingest endpoints và dễ test.
- Docker: chuẩn hóa environment, cần để deploy từng microservice trong architecture microservices.
- GitHub Actions: tích hợp CI phổ biến; workflow mẫu cho build/test giúp chứng minh CI/CD advocacy.
- Pytest + httpx: unit/integration test nhanh cho service; dễ chạy trong CI.
- XGBoost / LightGBM (đã nêu trong spec): phù hợp cho tabular behavioral features, hiệu năng và explainability tốt so với LLM ở phần này.
- pgvector / Redis / Postgres: (mô tả trong guide) — pgvector cho vector search RAG, Redis cho cache/profile snapshot; Postgres cho append-only profile store.

## 5) Next steps đề xuất (ứng tuyển)
1. Review file này và cho phép tôi commit/scaffold tiếp nếu muốn mở rộng (ví dụ: health endpoint ingest minimal, Prometheus metrics, example deployment pipeline to ECR/GHCR).
2. Nếu bạn muốn, tôi sẽ: (A) tạo slide CV-ready mapping (1 trang) hoặc (B) mở rộng scaffold thành một demo runnable (build image + run container + test). Chọn A hoặc B.

---
_Tạo tự động: 03-Jun-2026_
