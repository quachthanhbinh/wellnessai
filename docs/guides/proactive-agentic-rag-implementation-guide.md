# Hướng Dẫn Triển Khai Proactive RAG & Agentic RAG

**Phiên bản:** 1.0  
**Ngày:** 2026-06-02  
**Dự án:** Elfie AI Health Coach — Component 4 (Proactive RAG + Progressive Profiling)  
**Ngôn ngữ code:** Python 3.11+

---

## Mục Lục

1. [Tổng Quan Kiến Trúc](#1-tổng-quan-kiến-trúc)
2. [Bước 1 — PII Scrubber (Kế thừa)](#2-bước-1--pii-scrubber-kế-thừa)
3. [Bước 2 — NER Pipeline (Entity Extraction)](#3-bước-2--ner-pipeline-entity-extraction)
4. [Bước 3 — Profile Store (PostgreSQL)](#4-bước-3--profile-store-postgresql)
5. [Bước 4 — Profile Gap Analyzer](#5-bước-4--profile-gap-analyzer)
6. [Bước 5 — Proactive RAG: Query Expansion](#6-bước-5--proactive-rag-query-expansion)
7. [Bước 6 — Proactive RAG: Profile-Aware Reranking](#7-bước-6--proactive-rag-profile-aware-reranking)
8. [Bước 7 — Context Assembly với Profile Injection](#8-bước-7--context-assembly-với-profile-injection)
9. [Bước 8 — Embedded Follow-up Questions](#9-bước-8--embedded-follow-up-questions)
10. [Bước 9 — Low-Confidence Confirmation Flow](#10-bước-9--low-confidence-confirmation-flow)
11. [Bước 10 — Agentic RAG (v2): LangGraph State Machine](#11-bước-10--agentic-rag-v2-langgraph-state-machine)
12. [Bước 11 — Full Pipeline Integration](#12-bước-11--full-pipeline-integration)
13. [Checklist Triển Khai](#13-checklist-triển-khai)

---

## 1. Tổng Quan Kiến Trúc

### 1.1 Sự khác biệt giữa RAG thông thường, Proactive RAG và Agentic RAG

| | RAG Thông Thường | Proactive RAG | Agentic RAG |
|---|---|---|---|
| **Retrieval** | Tìm kiếm theo câu hỏi hiện tại | Tìm kiếm + làm giàu bằng profile người dùng | Nhiều vòng retrieval, tự quyết định khi nào đủ thông tin |
| **Profile** | Không có | Tích lũy từ hội thoại, dùng để rerank | Profile thay đổi input của từng vòng lặp |
| **Orchestration** | Đơn tuyến (linear) | Đơn tuyến + NER chạy song song | State machine, có thể quay lại bước trước |
| **Câu hỏi follow-up** | Không | Có (tối đa 2 câu, hướng gap profile) | Có, nhưng do agent quyết định |
| **Độ phức tạp** | Thấp | Trung bình | Cao |
| **MVP** | ✓ Component 1 | ✓ Component 4 | v2 |

### 1.2 Luồng xử lý tổng thể

```
User Message
     │
     ▼
[PII Scrubber]  ──────────────────── Point A (tẩy PII trước khi NER và RAG)
     │
     ├─────────────────────┬──────────────────────────┐
     ▼                     ▼                          ▼
[Intent Classifier]  [NER Pipeline]        [Tier 1 RAG Retrieval]
                     (GLiNER / SpaCy)       (vitals, meds, lab DB)
                           │
                           ▼
                    [Profile Store Update]
                    (PostgreSQL append-only)
                           │
                           ▼
                    [Profile Snapshot]
                           │
     ◄─────────────────────┘
     │
     ▼
[Profile Gap Analyzer]  ← so sánh intent vs profile hiện tại
     │
     ▼
[Agentic Orchestrator]          ← MVP: rule-based; v2: LangGraph
     │
     ├──► [Profile-Aware Query Expansion]
     ├──► [Vector RAG]  (pgvector, top-10 → rerank → top-5)
     ├──► [Structured Retriever]  (Elfie DB: vitals, meds)
     └──► [GraphRAG]  ← v3: Neo4j / Apache AGE
                  │
          [Agentic Reflector]  ← v2: "Đủ ngữ cảnh chưa?" loop
                  │
                  ▼
         [Context Assembler]
         System Prompt + Profile Summary (≤200 tokens)
         + Tier 1 data + Chunks + Conversation buffer
                  │
[PII Scrubber]  ──────── Point B (tẩy PII trước khi gửi lên LLM)
                  │
                  ▼
         [Reasoning LLM]  (Claude 3.5 Sonnet / GPT-4o)
                  │
         [Post-gen Question Validator]
                  │
         [2-Stage Safety Layer]
                  │
                  ▼
         [Response + follow-up questions (0–2)]
```

### 1.3 Phụ thuộc kỹ thuật

```
# requirements.txt
gliner==0.2.0          # NER model
spacy==3.7.4           # fallback NER
langchain==0.2.0       # RAG orchestration
langgraph==0.1.0       # Agentic RAG (v2)
pgvector==0.2.5        # vector search
psycopg[binary]==3.1   # PostgreSQL async
redis==5.0.0           # profile cache
anthropic==0.28.0      # Claude API
tiktoken==0.7.0        # token counting
pydantic==2.7.0        # data validation
```

---

## 2. Bước 1 — PII Scrubber (Kế thừa)

> PII Scrubber được kế thừa từ Component 1 và chạy tại **hai điểm** trong pipeline: Point A (trước NER/RAG) và Point B (trước LLM).

NER pipeline và Context Assembler **chỉ nhận văn bản đã được tẩy PII**. Không bao giờ cho phép văn bản thô đi qua.

```python
# pii_scrubber.py
import re
from dataclasses import dataclass

@dataclass
class ScrubResult:
    scrubbed_text: str
    replacements: dict[str, str]  # {placeholder: original} — dùng cho audit log

class PIIScrubber:
    """
    Tẩy PII trước khi đưa vào NER pipeline và trước khi gửi lên LLM.
    Đây là component kế thừa từ Component 1 — không sửa logic, chỉ gọi.
    """

    PATTERNS = [
        # Số điện thoại Việt Nam
        (r'\b(0[3-9]\d{8})\b', '[PHONE]'),
        # Email
        (r'\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b', '[EMAIL]'),
        # Số CCCD / CMND (9 hoặc 12 chữ số)
        (r'\b\d{9}(\d{3})?\b', '[ID_NUMBER]'),
        # Tên (heuristic: chuỗi 2-4 từ bắt đầu bằng chữ hoa liên tiếp)
        # Lưu ý: trong production, dùng NER-based name detector thay vì regex
        (r'\b([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ][a-záàảãạăắằẳẵặâấầẩẫậđéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ]+\s){2,4})', '[NAME]'),
    ]

    def scrub(self, text: str) -> ScrubResult:
        replacements = {}
        scrubbed = text
        for pattern, placeholder in self.PATTERNS:
            matches = re.findall(pattern, scrubbed)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                replacements[placeholder] = match
            scrubbed = re.sub(pattern, placeholder, scrubbed)
        return ScrubResult(scrubbed_text=scrubbed, replacements=replacements)
```

---

## 3. Bước 2 — NER Pipeline (Entity Extraction)

### 3.1 Tại sao dùng NER thay vì LLM?

- **Tốc độ**: NER model (GLiNER) ≤ 150ms P95 trên tin nhắn 200 token; LLM sẽ tốn 1–3 giây
- **Chi phí**: NER là inference local, không tốn API token
- **Determinism**: NER cho output ổn định, dễ test và debug
- **Kiến trúc**: LLM là reasoning engine, không phải knowledge source — nguyên tắc kế thừa từ Component 1

### 3.2 Entity types cần extract

| Entity Type | Mục tiêu | Ví dụ tiếng Việt |
|---|---|---|
| `CONDITION` | `CONDITIONS` trong profile | "Tôi bị tiểu đường type 2" |
| `MEDICATION` | `MEDICATIONS` | "Tôi đang uống Metformin 500mg" |
| `DEMOGRAPHIC` | `DEMOGRAPHICS` | "Tôi 45 tuổi", "tôi nặng 68 kg" |
| `LIFESTYLE_FACTOR` | `LIFESTYLE` | "Tôi chạy 3 lần một tuần" |
| `SYMPTOM_CHRONIC` | `SYMPTOMS_CHRONIC` | "Tôi hay đau đầu buổi sáng" |
| `BIOMARKER_PREFERENCE` | `BIOMARKER_PREFERENCES` | "Tôi muốn giữ huyết áp dưới 130" |
| `TEMPORAL_CONTEXT` | metadata only (không lưu độc lập) | "từ năm ngoái", "đã 5 năm" |

### 3.3 Code NER Pipeline

```python
# ner_pipeline.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import gliner  # hoặc spacy tùy model đã chọn

class EntityType(str, Enum):
    CONDITION = "CONDITION"
    MEDICATION = "MEDICATION"
    DEMOGRAPHIC = "DEMOGRAPHIC"
    LIFESTYLE_FACTOR = "LIFESTYLE_FACTOR"
    SYMPTOM_CHRONIC = "SYMPTOM_CHRONIC"
    BIOMARKER_PREFERENCE = "BIOMARKER_PREFERENCE"
    TEMPORAL_CONTEXT = "TEMPORAL_CONTEXT"

@dataclass
class ExtractedEntity:
    entity_type: EntityType
    raw_value: str          # giá trị thô từ tin nhắn
    normalized_value: str   # giá trị đã chuẩn hóa (ICD-10, INN, SI units)
    confidence_score: float  # [0.0, 1.0]
    char_start: int
    char_end: int
    temporal_context: Optional[str] = None  # "from last year", "for 5 years"

@dataclass
class NERResult:
    entities: list[ExtractedEntity] = field(default_factory=list)
    language_detected: str = "en"  # "en" hoặc "vi"
    processing_time_ms: float = 0.0

class NERPipeline:
    """
    NER pipeline chạy song song với Tier 1 RAG retrieval.
    Chỉ xử lý user messages — KHÔNG chạy trên AI-generated turns.
    Nhận scrubbed text từ PII Scrubber.
    """

    ENTITY_LABELS = [
        "medical condition",
        "medication name",
        "demographic information",
        "lifestyle factor",
        "chronic symptom",
        "biomarker preference",
        "temporal context",
    ]

    LABEL_TO_ENTITY_TYPE = {
        "medical condition": EntityType.CONDITION,
        "medication name": EntityType.MEDICATION,
        "demographic information": EntityType.DEMOGRAPHIC,
        "lifestyle factor": EntityType.LIFESTYLE_FACTOR,
        "chronic symptom": EntityType.SYMPTOM_CHRONIC,
        "biomarker preference": EntityType.BIOMARKER_PREFERENCE,
        "temporal context": EntityType.TEMPORAL_CONTEXT,
    }

    def __init__(self, model_path: str, normalizer: "EntityNormalizer"):
        # GLiNER model được host trên Elfie NER inference service
        self.model = gliner.GLiNER.from_pretrained(model_path)
        self.normalizer = normalizer

    def extract(self, scrubbed_text: str, is_ai_turn: bool = False) -> NERResult:
        """
        CRITICAL: is_ai_turn=True → skip hoàn toàn, trả về empty result.
        NER không bao giờ chạy trên AI-generated turns.
        """
        if is_ai_turn:
            return NERResult()

        import time
        start = time.monotonic()

        raw_entities = self.model.predict_entities(
            scrubbed_text,
            self.ENTITY_LABELS,
            threshold=0.40,  # threshold thấp để bắt; confidence < 0.60 sẽ vào staging
        )

        entities = []
        for ent in raw_entities:
            entity_type = self.LABEL_TO_ENTITY_TYPE[ent["label"]]
            normalized = self.normalizer.normalize(entity_type, ent["text"])

            # Apply temperature scaling calibration
            calibrated_score = self.normalizer.calibrate_confidence(
                entity_type, ent["score"]
            )

            entities.append(ExtractedEntity(
                entity_type=entity_type,
                raw_value=ent["text"],
                normalized_value=normalized,
                confidence_score=calibrated_score,
                char_start=ent["start"],
                char_end=ent["end"],
            ))

        elapsed = (time.monotonic() - start) * 1000
        return NERResult(entities=entities, processing_time_ms=elapsed)


class EntityNormalizer:
    """
    Chuẩn hóa entity values về định dạng chuẩn.
    Không dùng LLM — dùng dictionary lookup + rule-based mapping.
    """

    # ICD-10 normalization dictionary (version-controlled, Medical Affairs reviewed)
    CONDITION_MAP = {
        # Tiếng Việt
        "tiểu đường": "diabetes mellitus",
        "tiểu đường type 2": "type 2 diabetes mellitus",
        "đái tháo đường": "diabetes mellitus",
        "cao huyết áp": "hypertension",
        "tăng huyết áp": "hypertension",
        "huyết áp cao": "hypertension",
        "mỡ máu": "dyslipidemia",
        "tim mạch": "cardiovascular disease",
        # English aliases
        "high blood pressure": "hypertension",
        "t2dm": "type 2 diabetes mellitus",
        "htn": "hypertension",
        "bp": None,  # ambiguous — không normalize
    }

    # INN normalization (brand name → generic name)
    MEDICATION_MAP = {
        "glucophage": "metformin",
        "amlor": "amlodipine",
        "concor": "bisoprolol",
        "novamet": "metformin",
        "januvia": "sitagliptin",
    }

    def normalize(self, entity_type: EntityType, raw_value: str) -> str:
        raw_lower = raw_value.lower().strip()
        if entity_type == EntityType.CONDITION:
            return self.CONDITION_MAP.get(raw_lower, raw_lower)
        if entity_type == EntityType.MEDICATION:
            return self.MEDICATION_MAP.get(raw_lower, raw_lower)
        if entity_type == EntityType.DEMOGRAPHIC:
            return self._normalize_demographic(raw_value)
        return raw_lower

    def _normalize_demographic(self, raw_value: str) -> str:
        """Chuyển về SI units: kg, cm, years"""
        import re
        # "68 kg" → "68.0"
        kg_match = re.search(r'(\d+\.?\d*)\s*kg', raw_value.lower())
        if kg_match:
            return str(float(kg_match.group(1)))
        # "1m62" hoặc "162 cm" → "162.0"
        cm_match = re.search(r'(\d+\.?\d*)\s*cm', raw_value.lower())
        if cm_match:
            return str(float(cm_match.group(1)))
        m_match = re.search(r'1[.,](\d{2})\s*m?', raw_value.lower())
        if m_match:
            return str(100 + float(m_match.group(1)))
        # "45 tuổi" / "45 years old"
        age_match = re.search(r'(\d+)\s*(tuổi|years?)', raw_value.lower())
        if age_match:
            return age_match.group(1)
        return raw_value

    def calibrate_confidence(self, entity_type: EntityType, raw_score: float) -> float:
        """
        Temperature scaling calibration.
        ECE (Expected Calibration Error) phải ≤ 0.05 sau khi calibrate.
        Params được load từ file version-controlled, không hardcode.
        """
        # Trong production: load calibration_params từ config store
        # calibration_params = load_calibration_params(entity_type, model_version)
        # return apply_temperature_scaling(raw_score, calibration_params.temperature)
        #
        # Demo placeholder:
        return min(1.0, max(0.0, raw_score))
```

### 3.4 Lưu ý quan trọng về entity attribution

```python
# ĐÚNG: entity luôn được gán cho active_profile_id từ session token
def attribute_entities_to_profile(entities: list[ExtractedEntity], session: Session) -> list[ExtractedEntity]:
    """
    Entity extraction KHÔNG cố gắng đoán subject từ ngôn ngữ.
    "Mẹ tôi bị cao huyết áp" → entity vẫn gán cho active_profile_id (người đang chat).
    Lý do: subject detection từ ngôn ngữ tự nhiên không đủ độ tin cậy cho health data.
    """
    # Không có logic phân tích chủ ngữ ở đây — đây là intentional design
    return entities  # tất cả đều thuộc session.active_profile_id
```

---

## 4. Bước 3 — Profile Store (PostgreSQL)

### 4.1 Schema (append-only)

```sql
-- migration: create_user_health_profile_entries.sql

CREATE TYPE field_group_enum AS ENUM (
    'DEMOGRAPHICS', 'CONDITIONS', 'MEDICATIONS',
    'LIFESTYLE', 'BIOMARKER_PREFERENCES', 'SYMPTOMS_CHRONIC'
);

CREATE TABLE user_health_profile_entries (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id            UUID NOT NULL REFERENCES accounts(id),
    profile_id            UUID NOT NULL REFERENCES profiles(id),
    field_group           field_group_enum NOT NULL,
    field_key             VARCHAR(64) NOT NULL,
    field_value           JSONB NOT NULL,
    confidence_score      FLOAT NOT NULL CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    confirmed             BOOLEAN NOT NULL DEFAULT FALSE,
    source_conversation_id UUID NOT NULL,   -- session token, không phải user identity
    source_turn_index     INTEGER NOT NULL,
    extracted_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confirmed_at          TIMESTAMPTZ,
    version               INTEGER NOT NULL DEFAULT 1,
    superseded_by         UUID REFERENCES user_health_profile_entries(id)
);

-- CRITICAL: Index đầu tiên phải là (profile_id, field_key) để enforce isolation
CREATE INDEX idx_profile_entries_profile_id ON user_health_profile_entries (profile_id);
CREATE INDEX idx_profile_entries_lookup ON user_health_profile_entries (profile_id, field_key, extracted_at DESC);
CREATE INDEX idx_profile_entries_active ON user_health_profile_entries (profile_id, field_group)
    WHERE superseded_by IS NULL;

-- Staging table cho low-confidence extractions (< 0.60)
CREATE TABLE pending_profile_extractions (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id                UUID NOT NULL REFERENCES accounts(id),
    profile_id                UUID NOT NULL REFERENCES profiles(id),
    field_group               field_group_enum NOT NULL,
    field_key                 VARCHAR(64) NOT NULL,
    field_value               JSONB NOT NULL,
    confidence_score          FLOAT NOT NULL,
    source_conversation_id    UUID NOT NULL,
    extracted_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at                TIMESTAMPTZ NOT NULL GENERATED ALWAYS AS (extracted_at + INTERVAL '30 days') STORED,
    confirmation_prompt_sent  BOOLEAN NOT NULL DEFAULT FALSE,
    conflict_flag             BOOLEAN NOT NULL DEFAULT FALSE
);

-- Row Level Security: application role chỉ có INSERT + SELECT, không có UPDATE/DELETE
-- trực tiếp lên user_health_profile_entries
REVOKE UPDATE, DELETE ON user_health_profile_entries FROM app_role;
GRANT INSERT, SELECT ON user_health_profile_entries TO app_role;
```

### 4.2 Profile Store Service

```python
# profile_store.py
import uuid
from datetime import datetime, timezone
from typing import Optional
import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel

class ProfileEntry(BaseModel):
    profile_id: uuid.UUID
    account_id: uuid.UUID
    field_group: str
    field_key: str
    field_value: dict
    confidence_score: float
    confirmed: bool = False
    source_conversation_id: uuid.UUID
    source_turn_index: int

class ProfileSnapshot(BaseModel):
    """Profile đã được resolve về active values."""
    profile_id: uuid.UUID
    fields: dict[str, dict]  # field_key → {value, confidence, confirmed, extracted_at}

class ProfileStoreService:
    """
    Service layer cho profile store.
    Application role: INSERT + SELECT only — không có UPDATE/DELETE.
    """

    def __init__(self, db_pool: psycopg.AsyncConnectionPool):
        self.db = db_pool

    async def write_extraction(
        self,
        entry: ProfileEntry,
        session_profile_id: uuid.UUID,
    ) -> uuid.UUID:
        """
        Ghi entity extraction vào profile store.
        Tự động handle versioning và supersession.

        SECURITY: session_profile_id phải match entry.profile_id.
        Cross-profile write là P0 security violation.
        """
        if entry.profile_id != session_profile_id:
            raise SecurityError(
                f"Profile ID mismatch: session={session_profile_id}, "
                f"entry={entry.profile_id}"
            )

        # Chỉ ghi nếu confidence >= 0.60
        if entry.confidence_score < 0.60:
            raise ValueError(
                "Confidence < 0.60: use write_to_staging() instead"
            )

        async with self.db.connection() as conn:
            async with conn.transaction():
                # Tìm entry hiện tại cho cùng field_key
                current = await conn.fetchrow(
                    """
                    SELECT id, version
                    FROM user_health_profile_entries
                    WHERE profile_id = $1
                      AND field_key = $2
                      AND superseded_by IS NULL
                    ORDER BY extracted_at DESC
                    LIMIT 1
                    """,
                    entry.profile_id,
                    entry.field_key,
                )

                new_version = (current["version"] + 1) if current else 1

                # INSERT entry mới
                new_id = await conn.fetchval(
                    """
                    INSERT INTO user_health_profile_entries (
                        account_id, profile_id, field_group, field_key,
                        field_value, confidence_score, confirmed,
                        source_conversation_id, source_turn_index,
                        version
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                    """,
                    entry.account_id, entry.profile_id, entry.field_group,
                    entry.field_key, entry.field_value, entry.confidence_score,
                    entry.confirmed, entry.source_conversation_id,
                    entry.source_turn_index, new_version,
                )

                # Supersede entry cũ (nếu có)
                # KHÔNG dùng UPDATE trực tiếp — chỉ set superseded_by
                if current:
                    await conn.execute(
                        """
                        UPDATE user_health_profile_entries
                        SET superseded_by = $1
                        WHERE id = $2
                        """,
                        new_id, current["id"],
                    )
                    # Lưu ý: đây là UPDATE duy nhất được phép — chỉ set superseded_by
                    # Không bao giờ UPDATE field_value, confidence_score, v.v.

                return new_id

    async def get_snapshot(
        self,
        profile_id: uuid.UUID,
        session_profile_id: uuid.UUID,
    ) -> ProfileSnapshot:
        """
        Lấy active profile values cho một profile.

        SECURITY: profile_id PHẢI luôn được truyền vào và match session.
        Không bao giờ query mà không có WHERE profile_id = ...
        """
        if profile_id != session_profile_id:
            raise SecurityError("Cross-profile read attempt blocked")

        async with self.db.connection() as conn:
            rows = await conn.fetch(
                """
                SELECT field_key, field_group, field_value,
                       confidence_score, confirmed, extracted_at
                FROM user_health_profile_entries
                WHERE profile_id = $1          -- CRITICAL: always filter by profile_id
                  AND superseded_by IS NULL    -- only active entries
                  AND (
                      confirmed = TRUE
                      OR confidence_score >= 0.60
                  )
                ORDER BY field_key, extracted_at DESC
                """,
                profile_id,
                row_factory=dict_row,
            )

        fields = {}
        seen_keys = set()
        for row in rows:
            key = row["field_key"]
            if key not in seen_keys:
                # Active value resolution: confirmed OR confidence >= 0.85 → fact
                # 0.60 ≤ confidence < 0.85, unconfirmed → provisional
                fields[key] = {
                    "value": row["field_value"],
                    "confidence": row["confidence_score"],
                    "confirmed": row["confirmed"],
                    "extracted_at": row["extracted_at"].isoformat(),
                    "field_group": row["field_group"],
                    "is_fact": row["confirmed"] or row["confidence_score"] >= 0.85,
                }
                seen_keys.add(key)

        return ProfileSnapshot(profile_id=profile_id, fields=fields)

    async def write_to_staging(self, entry: ProfileEntry) -> uuid.UUID:
        """Ghi low-confidence extraction (< 0.60) vào pending_profile_extractions."""
        async with self.db.connection() as conn:
            entry_id = await conn.fetchval(
                """
                INSERT INTO pending_profile_extractions (
                    account_id, profile_id, field_group, field_key,
                    field_value, confidence_score, source_conversation_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                entry.account_id, entry.profile_id, entry.field_group,
                entry.field_key, entry.field_value, entry.confidence_score,
                entry.source_conversation_id,
            )
        return entry_id


class SecurityError(Exception):
    pass
```

---

## 5. Bước 4 — Profile Gap Analyzer

### 5.1 Tại sao là rule-based, không phải ML?

- **Predictable**: output xác định, dễ audit và test
- **No latency**: ≤ 20ms P95 (so với LLM call ~1-3s)
- **Medical Affairs controlled**: intent map được Medical Affairs review và version-control
- **No hallucination risk**: ML model có thể đề xuất câu hỏi không phù hợp hoặc nhạy cảm

### 5.2 Code Gap Analyzer

```python
# gap_analyzer.py
from dataclasses import dataclass
from enum import Enum

class QueryIntent(str, Enum):
    BLOOD_PRESSURE_QUERY = "blood_pressure_query"
    GLUCOSE_QUERY = "glucose_query"
    MEDICATION_ADHERENCE_QUERY = "medication_adherence_query"
    WEIGHT_GOAL_QUERY = "weight_goal_query"
    SLEEP_QUERY = "sleep_query"
    EXERCISE_QUERY = "exercise_query"
    GENERAL_TREND_QUERY = "general_trend_query"
    LAB_RESULT_QUERY = "lab_result_query"
    SYMPTOM_INTERPRETATION_QUERY = "symptom_interpretation_query"

@dataclass
class GapField:
    field_key: str
    field_group: str
    priority_rank: int  # 1 = highest priority

# Intent → Required Profile Fields mapping
# Version-controlled, Medical Affairs reviewed
INTENT_REQUIRED_FIELDS: dict[QueryIntent, list[str]] = {
    QueryIntent.BLOOD_PRESSURE_QUERY: [
        "age_years", "condition_name", "medication_name", "smoking_status"
    ],
    QueryIntent.GLUCOSE_QUERY: [
        "condition_name", "medication_name", "weight_kg", "biological_sex"
    ],
    QueryIntent.MEDICATION_ADHERENCE_QUERY: [
        "medication_name", "condition_name"
    ],
    QueryIntent.WEIGHT_GOAL_QUERY: [
        "weight_kg", "height_cm", "age_years", "biological_sex"
    ],
    QueryIntent.SLEEP_QUERY: [
        "sleep_hours_avg", "condition_name", "exercise_frequency_per_week"
    ],
    QueryIntent.EXERCISE_QUERY: [
        "exercise_frequency_per_week", "age_years", "condition_name"
    ],
    QueryIntent.GENERAL_TREND_QUERY: [
        "age_years", "biological_sex", "condition_name"
    ],
    QueryIntent.LAB_RESULT_QUERY: [
        "condition_name", "medication_name", "age_years", "biological_sex"
    ],
    QueryIntent.SYMPTOM_INTERPRETATION_QUERY: [
        "condition_name", "medication_name", "symptom_name"
    ],
}

# Mỗi field_key thuộc field_group nào
FIELD_GROUP_MAP: dict[str, str] = {
    "age_years": "DEMOGRAPHICS",
    "biological_sex": "DEMOGRAPHICS",
    "height_cm": "DEMOGRAPHICS",
    "weight_kg": "DEMOGRAPHICS",
    "condition_name": "CONDITIONS",
    "medication_name": "MEDICATIONS",
    "medication_dose": "MEDICATIONS",
    "exercise_frequency_per_week": "LIFESTYLE",
    "smoking_status": "LIFESTYLE",
    "alcohol_status": "LIFESTYLE",
    "sleep_hours_avg": "LIFESTYLE",
    "diet_type": "LIFESTYLE",
    "personal_target": "BIOMARKER_PREFERENCES",
    "symptom_name": "SYMPTOMS_CHRONIC",
    "symptom_frequency": "SYMPTOMS_CHRONIC",
}

class ProfileGapAnalyzer:
    """
    Rule-based component: so sánh query intent vs profile hiện tại.
    Output: ordered list ≤ 2 gap fields cho Context Assembler.
    Performance: ≤ 20ms P95.
    """

    MAX_GAP_OUTPUT = 2
    ACTIVE_CONFIDENCE_THRESHOLD = 0.40  # field với bất kỳ entry ≥ 0.40 → không hỏi lại

    def analyze(
        self,
        intent: QueryIntent,
        profile_snapshot: "ProfileSnapshot",
    ) -> list[GapField]:
        """
        Trả về danh sách field đang thiếu hoặc low-confidence,
        sắp xếp theo độ liên quan đến intent hiện tại.
        """
        required_fields = INTENT_REQUIRED_FIELDS.get(intent, [])
        gaps = []

        for rank, field_key in enumerate(required_fields, start=1):
            profile_entry = profile_snapshot.fields.get(field_key)

            if profile_entry is None:
                # Hoàn toàn không có → highest priority gap
                gaps.append(GapField(
                    field_key=field_key,
                    field_group=FIELD_GROUP_MAP.get(field_key, "UNKNOWN"),
                    priority_rank=rank,
                ))
            elif (
                not profile_entry["confirmed"]
                and profile_entry["confidence"] < self.ACTIVE_CONFIDENCE_THRESHOLD
            ):
                # Có entry nhưng quá thấp confidence → vẫn là gap, nhưng lower priority
                gaps.append(GapField(
                    field_key=field_key,
                    field_group=FIELD_GROUP_MAP.get(field_key, "UNKNOWN"),
                    priority_rank=rank + 100,  # lower priority than absent fields
                ))

        # Sort: absent fields trước, provisional fields sau, cùng rank → giữ order
        gaps.sort(key=lambda g: g.priority_rank)

        # Hard limit: tối đa 2 gaps
        return gaps[:self.MAX_GAP_OUTPUT]
```

---

## 6. Bước 5 — Proactive RAG: Query Expansion

### 6.1 Tư duy thiết kế

Query expansion là bước **làm giàu câu hỏi** trước khi tìm kiếm vector. Thay vì chỉ tìm với câu hỏi gốc, ta thêm context từ profile (conditions đã biết, medications đang dùng) để retrieval có liên quan hơn.

**Không dùng LLM cho query expansion** — dùng versioned expansion map để tránh latency và hallucination.

```python
# query_expander.py

# Expansion map: condition/medication → related search terms
# Version-controlled, Medical Affairs reviewed, không chứa diagnostic language
CONDITION_EXPANSION_MAP: dict[str, list[str]] = {
    "hypertension": [
        "blood pressure", "systolic", "diastolic", "antihypertensive",
        "sodium restriction", "DASH diet", "cardiovascular risk"
    ],
    "type 2 diabetes mellitus": [
        "blood glucose", "HbA1c", "glycemic control", "insulin resistance",
        "metformin", "carbohydrate intake", "fasting glucose"
    ],
    "dyslipidemia": [
        "LDL cholesterol", "HDL", "triglycerides", "statin",
        "cardiovascular risk", "lipid profile"
    ],
    "cardiovascular disease": [
        "heart health", "cardiac", "blood pressure", "cholesterol",
        "antiplatelet", "coronary"
    ],
}

MEDICATION_EXPANSION_MAP: dict[str, list[str]] = {
    "metformin": [
        "type 2 diabetes", "blood glucose", "HbA1c", "renal function",
        "lactic acidosis", "gastrointestinal"
    ],
    "amlodipine": [
        "blood pressure", "calcium channel blocker", "hypertension",
        "edema", "heart rate"
    ],
    "bisoprolol": [
        "heart rate", "beta blocker", "blood pressure", "heart failure",
        "bradycardia"
    ],
}

MAX_EXPANSION_TOKENS = 50  # spec: original query + ≤ 50 profile-derived tokens

class ProfileAwareQueryExpander:
    """
    Làm giàu query vector search bằng profile context.
    Không dùng LLM — dùng lookup table.
    Latency target: ≤ 10ms P95.
    """

    def expand(
        self,
        original_query: str,
        profile_snapshot: "ProfileSnapshot",
    ) -> str:
        """
        Trả về query đã được expand với profile terms.
        Không bao giờ thêm diagnostic language.
        """
        expansion_terms = []

        # Lấy conditions đã confirmed từ profile
        condition_entry = profile_snapshot.fields.get("condition_name")
        if condition_entry and condition_entry["is_fact"]:
            condition = condition_entry["value"].get("value", "")
            terms = CONDITION_EXPANSION_MAP.get(condition, [])
            expansion_terms.extend(terms)

        # Lấy medications đã confirmed
        medication_entry = profile_snapshot.fields.get("medication_name")
        if medication_entry and medication_entry["is_fact"]:
            medication = medication_entry["value"].get("value", "")
            terms = MEDICATION_EXPANSION_MAP.get(medication, [])
            expansion_terms.extend(terms)

        if not expansion_terms:
            return original_query  # empty profile → không expand

        # Cap at MAX_EXPANSION_TOKENS
        expansion_text = " ".join(expansion_terms)
        # Rough token counting (trong production dùng tiktoken)
        words = expansion_text.split()[:MAX_EXPANSION_TOKENS]
        expansion_capped = " ".join(words)

        return f"{original_query} {expansion_capped}".strip()
```

---

## 7. Bước 6 — Proactive RAG: Profile-Aware Reranking

### 7.1 Công thức reranking

```
final_score = (0.7 × cosine_similarity) + (0.3 × profile_relevance_score)
```

**Profile relevance score:**
- `1.0` — chunk chứa term trùng với condition hoặc medication trong profile
- `0.5` — chunk chứa term thuộc parent category của condition
- `0.0` — không có match nào

### 7.2 Code Reranker

```python
# reranker.py
from dataclasses import dataclass

@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    cosine_similarity: float
    metadata: dict
    final_score: float = 0.0

class ProfileAwareReranker:
    """
    Rerank top-10 pgvector candidates trước khi pass top-5 vào Context Assembler.
    Không gọi LLM — pure scoring algorithm.
    """

    COSINE_WEIGHT = 0.7
    PROFILE_WEIGHT = 0.3
    MIN_COSINE_THRESHOLD = 0.75  # chunks dưới threshold này bị loại từ đầu

    # Parent category mapping để partial match
    CONDITION_PARENT_CATEGORIES: dict[str, list[str]] = {
        "hypertension": ["cardiovascular", "blood pressure", "heart disease"],
        "type 2 diabetes mellitus": ["diabetes", "metabolic", "endocrine"],
        "dyslipidemia": ["cardiovascular", "cholesterol", "lipid"],
    }

    def rerank(
        self,
        candidates: list[RetrievedChunk],
        profile_snapshot: "ProfileSnapshot",
    ) -> list[RetrievedChunk]:
        """
        Input: top-10 chunks từ pgvector cosine similarity search
        Output: top-5 chunks sau khi rerank theo profile relevance
        """
        # Lấy active terms từ profile
        profile_terms = self._extract_profile_terms(profile_snapshot)

        if not profile_terms:
            # Empty profile → pure cosine similarity (identical to Component 1)
            scored = sorted(candidates, key=lambda c: c.cosine_similarity, reverse=True)
            for chunk in scored:
                chunk.final_score = chunk.cosine_similarity
            return scored[:5]

        # Tính final score cho từng chunk
        for chunk in candidates:
            profile_score = self._compute_profile_relevance(
                chunk.content, profile_terms
            )
            chunk.final_score = (
                self.COSINE_WEIGHT * chunk.cosine_similarity
                + self.PROFILE_WEIGHT * profile_score
            )

        # Sort và trả về top-5
        reranked = sorted(candidates, key=lambda c: c.final_score, reverse=True)
        return reranked[:5]

    def _extract_profile_terms(self, snapshot: "ProfileSnapshot") -> dict:
        """Trích xuất terms và parent categories từ profile để match."""
        terms = {"exact": set(), "parent": set()}

        condition = snapshot.fields.get("condition_name")
        if condition and condition["is_fact"]:
            cond_value = condition["value"].get("value", "").lower()
            terms["exact"].add(cond_value)
            parents = self.CONDITION_PARENT_CATEGORIES.get(cond_value, [])
            terms["parent"].update(parents)

        medication = snapshot.fields.get("medication_name")
        if medication and medication["is_fact"]:
            terms["exact"].add(medication["value"].get("value", "").lower())

        return terms

    def _compute_profile_relevance(
        self, content: str, profile_terms: dict
    ) -> float:
        content_lower = content.lower()

        # Exact match: condition name hoặc medication name trong chunk
        for term in profile_terms["exact"]:
            if term in content_lower:
                return 1.0  # exact match → highest score, stop searching

        # Parent category match
        for parent in profile_terms["parent"]:
            if parent in content_lower:
                return 0.5

        return 0.0
```

---

## 8. Bước 7 — Context Assembly với Profile Injection

### 8.1 Thứ tự lắp ghép context

Context Assembler tạo final LLM prompt theo thứ tự cố định:

```
1. System Prompt Block       (static, version-controlled)
2. Profile Summary Block     (≤ 200 tokens, được tạo không dùng LLM)
3. Tier 1 Data Block         (7 ngày dữ liệu structured: vitals, meds, labs)
4. Retrieved Documents Block (top-5 chunks đã rerank)
5. Conversation Buffer Block (N turns gần nhất)
6. Current User Message
```

### 8.2 Code Context Assembler

```python
# context_assembler.py
import json
from datetime import datetime, timezone, timedelta
import tiktoken

MAX_PROFILE_TOKENS = 200
MIN_PROFILE_TOKENS = 100  # không được truncate xuống dưới mức này

SYSTEM_PROMPT = """
Bạn là Elfie AI Health Coach — trợ lý sức khỏe cá nhân hóa.

Nguyên tắc bắt buộc:
1. Chỉ sử dụng dữ liệu sức khỏe từ Elfie và kiến thức y tế đã được xác minh. Không tạo ra thông tin y tế mới.
2. Profile data được đánh dấu 'unconfirmed' là những gì người dùng đã đề cập trong hội thoại — hãy xem đây là self-reported context, không phải hồ sơ y tế đã xác minh.
3. Dữ liệu Profile KHÔNG ĐƯỢC dùng để chẩn đoán, gợi ý chẩn đoán, hoặc suy luận về bệnh lý người dùng chưa nói rõ ràng.
4. Khi đề cập đến condition trong profile, luôn dùng: "Vì bạn có đề cập rằng bạn bị [bệnh]..." — không bao giờ nói "Vì bạn bị [bệnh]..." như thể là chẩn đoán lâm sàng.
5. Với dữ liệu provisional (unconfirmed): dùng ngôn ngữ hedged — "Dựa trên những gì bạn đã chia sẻ..."

Nhúng follow-up question khi Gap Analyzer cung cấp gap fields:
- Tối đa 2 câu hỏi, lồng tự nhiên vào response
- Không hỏi lại thông tin đã biết
- Câu hỏi phải conversational, không phải dạng form lâm sàng
""".strip()

class ContextAssembler:
    """
    Lắp ghép final LLM prompt từ các nguồn khác nhau.
    Không gọi LLM — pure text assembly.
    Latency target: ≤ 15ms P95.
    """

    def __init__(self, encoding_name: str = "cl100k_base"):
        self.tokenizer = tiktoken.get_encoding(encoding_name)

    def assemble(
        self,
        profile_snapshot: "ProfileSnapshot",
        tier1_data: dict,                    # structured health data từ Elfie DB
        retrieved_chunks: list["RetrievedChunk"],
        conversation_buffer: list[dict],     # list of {"role": "user"|"assistant", "content": "..."}
        current_message: str,
        gap_fields: list["GapField"],
        context_window_limit: int = 8000,    # tính bằng tokens
    ) -> str:
        """Tạo final prompt cho LLM."""

        # 1. System prompt
        system_block = SYSTEM_PROMPT

        # 2. Profile summary block
        profile_block = self._build_profile_summary(profile_snapshot, gap_fields)

        # 3. Tier 1 data block
        tier1_block = self._build_tier1_block(tier1_data)

        # 4. Retrieved documents block
        docs_block = self._build_docs_block(retrieved_chunks)

        # 5. Conversation buffer block
        conv_block = self._build_conv_block(conversation_buffer)

        # 6. Current message
        current_block = f"**Tin nhắn hiện tại của người dùng:**\n{current_message}"

        # Assemble và truncate nếu cần
        blocks = [
            ("system", system_block),
            ("profile", profile_block),
            ("tier1", tier1_block),
            ("docs", docs_block),
            ("conversation", conv_block),
            ("current", current_block),
        ]
        return self._assemble_with_truncation(blocks, context_window_limit)

    def _build_profile_summary(
        self,
        snapshot: "ProfileSnapshot",
        gap_fields: list,
    ) -> str:
        """
        Tạo profile summary block ≤ 200 tokens.
        Áp dụng hedging rules theo AC 1.6.
        Không gọi LLM.
        """
        if not snapshot.fields:
            return ""  # empty profile → block bị omit hoàn toàn

        lines = ["**Hồ sơ sức khỏe người dùng (từ hội thoại):**"]
        now = datetime.now(timezone.utc)

        for field_key, entry in snapshot.fields.items():
            value_str = json.dumps(entry["value"], ensure_ascii=False)
            age_days = self._calculate_age_days(entry["extracted_at"], now)

            # Staleness rules (AC 1.7)
            stale_note = ""
            is_stale_field = field_key in {"weight_kg", "medication_name", "medication_dose",
                                           "exercise_frequency_per_week", "smoking_status",
                                           "alcohol_status", "sleep_hours_avg", "diet_type"}
            stale_threshold = 180 if is_stale_field else 365
            very_stale_threshold = 180 if is_stale_field else 730

            if age_days > very_stale_threshold:
                stale_note = f" [CÓ THỂ OUTDATED - cập nhật {age_days // 30} tháng trước]"
            elif age_days > stale_threshold:
                stale_note = " [có thể đã thay đổi]"

            # Hedging rules (AC 1.6)
            if entry["confirmed"] or entry["confidence"] >= 0.85:
                lines.append(f"- {field_key}: {value_str}{stale_note}")
            elif 0.60 <= entry["confidence"] < 0.85:
                lines.append(
                    f"- {field_key}: {value_str} (chưa xác nhận — "
                    f"người dùng đã đề cập){stale_note}"
                )
            # confidence < 0.60 → không đưa vào context

        summary = "\n".join(lines)

        # Truncate về MAX_PROFILE_TOKENS nếu cần
        tokens = self.tokenizer.encode(summary)
        if len(tokens) > MAX_PROFILE_TOKENS:
            # Truncate từ cuối, giữ header
            header_tokens = self.tokenizer.encode(lines[0])
            remaining = MAX_PROFILE_TOKENS - len(header_tokens)
            body_tokens = tokens[len(header_tokens):][:remaining]
            summary = self.tokenizer.decode(header_tokens + body_tokens)

        return summary

    def _build_tier1_block(self, tier1_data: dict) -> str:
        if not tier1_data:
            return ""
        return (
            "**Dữ liệu sức khỏe 7 ngày gần nhất (Elfie):**\n"
            + json.dumps(tier1_data, ensure_ascii=False, indent=2)
        )

    def _build_docs_block(self, chunks: list) -> str:
        if not chunks:
            return ""
        parts = ["**Tài liệu tham khảo liên quan:**"]
        for i, chunk in enumerate(chunks, 1):
            parts.append(f"[{i}] {chunk.content}")
        return "\n\n".join(parts)

    def _build_conv_block(self, turns: list[dict]) -> str:
        if not turns:
            return ""
        parts = ["**Lịch sử hội thoại:**"]
        for turn in turns:
            role_label = "Người dùng" if turn["role"] == "user" else "Elfie"
            parts.append(f"{role_label}: {turn['content']}")
        return "\n".join(parts)

    def _assemble_with_truncation(
        self, blocks: list[tuple[str, str]], limit: int
    ) -> str:
        """
        Truncation priority:
        1. Conversation buffer (first to trim)
        2. Retrieved documents (trim from bottom)
        3. Profile summary (never below MIN_PROFILE_TOKENS if non-empty)
        4. Tier 1 data (NEVER truncated)
        """
        block_dict = dict(blocks)
        assembled = "\n\n".join(v for _, v in blocks if v)
        total_tokens = len(self.tokenizer.encode(assembled))

        if total_tokens <= limit:
            return assembled

        # Step 1: Trim conversation buffer
        conv = block_dict.get("conversation", "")
        if conv:
            conv_tokens = self.tokenizer.encode(conv)
            excess = total_tokens - limit
            if len(conv_tokens) > excess:
                trimmed = self.tokenizer.decode(conv_tokens[excess:])
                block_dict["conversation"] = trimmed
            else:
                block_dict["conversation"] = ""

        assembled = "\n\n".join(v for v in block_dict.values() if v)
        total_tokens = len(self.tokenizer.encode(assembled))

        if total_tokens <= limit:
            return assembled

        # Step 2: Trim retrieved documents từ bottom
        docs = block_dict.get("docs", "")
        if docs:
            doc_lines = docs.split("\n\n")
            while len(doc_lines) > 1:
                doc_lines.pop()
                block_dict["docs"] = "\n\n".join(doc_lines)
                assembled = "\n\n".join(v for v in block_dict.values() if v)
                if len(self.tokenizer.encode(assembled)) <= limit:
                    break

        return "\n\n".join(v for v in block_dict.values() if v)

    def _calculate_age_days(self, extracted_at_iso: str, now: datetime) -> int:
        extracted = datetime.fromisoformat(extracted_at_iso)
        return (now - extracted).days
```

---

## 9. Bước 8 — Embedded Follow-up Questions

### 9.1 Luồng xử lý

```
Gap Analyzer output (0-2 gap fields)
          │
          ▼
System Prompt chứa gap fields + phrasing guidance
          │
          ▼
LLM tạo response + nhúng câu hỏi
          │
          ▼
Post-generation Validator (stripping rules)
          │
          ▼
2-Stage Safety Classifier
          │
          ▼
Final Response
```

### 9.2 Code Post-Generation Validator

```python
# question_validator.py
import re
from dataclasses import dataclass

@dataclass
class ValidationResult:
    cleaned_response: str
    questions_stripped: int
    strip_reasons: list[str]

class PostGenerationQuestionValidator:
    """
    Chạy SAU khi LLM tạo response, TRƯỚC khi đưa vào Safety Classifier.
    Strip các câu hỏi vi phạm hard rules.
    """

    MAX_QUESTIONS = 2
    MAX_QUESTIONS_FOR_LONG_RESPONSE = 1
    LONG_RESPONSE_WORD_COUNT = 200

    # Phrasing bị cấm (clinical-form style)
    PROHIBITED_PATTERNS = [
        r'please state your',
        r'enter your',
        r'what is your \w+ \?',  # "What is your age?" style
        r'fill in',
        r'please provide your',
    ]

    # Acute symptom patterns bị cấm
    ACUTE_SYMPTOM_PATTERNS = [
        r'are you currently (feeling|experiencing)',
        r'do you (have|feel) (chest pain|shortness of breath|severe|acute)',
        r'bạn có đang (cảm thấy|bị) .{0,30} (ngay lúc này|hiện tại)',
    ]

    def validate(
        self,
        response: str,
        gap_fields: list["GapField"],
        known_profile_fields: set[str],
        is_escalation_response: bool,
        is_safety_blocked: bool,
    ) -> ValidationResult:
        stripped = 0
        reasons = []

        # Rule: no questions in escalation or safety-blocked responses
        if is_escalation_response or is_safety_blocked:
            cleaned = self._strip_all_questions(response)
            return ValidationResult(
                cleaned_response=cleaned,
                questions_stripped=self._count_questions(response) - self._count_questions(cleaned),
                strip_reasons=["escalation_or_safety_block"],
            )

        # Detect questions in response
        questions = self._extract_questions(response)
        valid_questions = []

        for q in questions:
            # Check prohibited phrasing
            if self._matches_patterns(q, self.PROHIBITED_PATTERNS):
                stripped += 1
                reasons.append(f"prohibited_phrasing: {q[:50]}")
                continue

            # Check acute symptom patterns
            if self._matches_patterns(q, self.ACUTE_SYMPTOM_PATTERNS):
                stripped += 1
                reasons.append(f"acute_symptom: {q[:50]}")
                continue

            # Check re-ask known data (AC 1.4 rule 2)
            # Nếu question liên quan đến field đã có trong profile → strip
            if self._is_re_asking_known_field(q, known_profile_fields):
                stripped += 1
                reasons.append(f"re_ask_known_field: {q[:50]}")
                continue

            valid_questions.append(q)

        # Check question count limit
        word_count = len(response.split())
        max_questions = (
            self.MAX_QUESTIONS_FOR_LONG_RESPONSE
            if word_count > self.LONG_RESPONSE_WORD_COUNT
            else self.MAX_QUESTIONS
        )

        if len(valid_questions) > max_questions:
            excess = valid_questions[max_questions:]
            for q in excess:
                stripped += 1
                reasons.append(f"exceeded_max_questions: {q[:50]}")
            valid_questions = valid_questions[:max_questions]

        # Rebuild response with only valid questions
        cleaned = self._rebuild_with_questions(response, valid_questions)

        return ValidationResult(
            cleaned_response=cleaned,
            questions_stripped=stripped,
            strip_reasons=reasons,
        )

    def _extract_questions(self, text: str) -> list[str]:
        """Tách câu hỏi khỏi response (câu kết thúc bằng ?)."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip().endswith('?')]

    def _count_questions(self, text: str) -> int:
        return len(self._extract_questions(text))

    def _matches_patterns(self, text: str, patterns: list[str]) -> bool:
        text_lower = text.lower()
        return any(re.search(p, text_lower) for p in patterns)

    def _is_re_asking_known_field(
        self, question: str, known_fields: set[str]
    ) -> bool:
        """
        Kiểm tra xem câu hỏi có hỏi về field đã biết không.
        Sử dụng keyword matching đơn giản — đủ cho hard rule enforcement.
        """
        field_keywords = {
            "age_years": ["tuổi", "age", "years old", "bao nhiêu tuổi"],
            "biological_sex": ["giới tính", "sex", "gender", "nam", "nữ"],
            "weight_kg": ["cân nặng", "weight", "kg", "kilograms"],
            "condition_name": ["bệnh", "condition", "diagnosis", "diagnosed"],
            "medication_name": ["thuốc", "medication", "drug", "medicine"],
        }
        question_lower = question.lower()
        for field, keywords in field_keywords.items():
            if field in known_fields:
                if any(kw in question_lower for kw in keywords):
                    return True
        return False

    def _strip_all_questions(self, text: str) -> str:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        non_questions = [s for s in sentences if not s.strip().endswith('?')]
        return ' '.join(non_questions).strip()

    def _rebuild_with_questions(
        self, original: str, valid_questions: list[str]
    ) -> str:
        """Rebuild response chỉ giữ valid questions."""
        all_questions = self._extract_questions(original)
        stripped_questions = set(all_questions) - set(valid_questions)

        result = original
        for q in stripped_questions:
            result = result.replace(q, '').strip()
        return result
```

---

## 10. Bước 9 — Low-Confidence Confirmation Flow

### 10.1 Luồng xác nhận

```
Conversation N (extraction xảy ra)
     │  NER: confidence < 0.60
     ▼
pending_profile_extractions table
     │  expires_at = extracted_at + 30 days
     ▼
Conversation N+1 (session khác, next time user chat)
     │  Gap Analyzer phát hiện pending extraction liên quan
     ▼
Confirmation prompt (tối đa 1 prompt/session)
"Lần trước bạn có nhắc đến [giá trị] — mình hiểu đúng không?"
     │
     ├── User confirms → move to user_health_profile_entries
     │                    (confirmed=true, confidence=0.90)
     │
     └── User denies  → delete staging entry + audit record
```

```python
# confirmation_flow.py
import uuid
from datetime import datetime, timezone

class LowConfidenceConfirmationFlow:
    """
    Xử lý flow xác nhận cho low-confidence extractions.
    Tối đa 1 confirmation prompt mỗi session.
    """

    def __init__(self, db_pool, profile_store: "ProfileStoreService"):
        self.db = db_pool
        self.profile_store = profile_store

    async def get_pending_for_session(
        self,
        profile_id: uuid.UUID,
        current_intent: "QueryIntent",
        session_id: uuid.UUID,
        max_one_per_session: bool = True,
    ) -> list[dict]:
        """
        Lấy pending extractions liên quan đến current intent.
        Đã lọc: chưa được prompt trong session này, chưa expired.
        """
        async with self.db.connection() as conn:
            # Lấy fields relevant với intent hiện tại
            relevant_fields = INTENT_REQUIRED_FIELDS.get(current_intent, [])
            if not relevant_fields:
                return []

            rows = await conn.fetch(
                """
                SELECT id, field_key, field_value, confidence_score, conflict_flag
                FROM pending_profile_extractions
                WHERE profile_id = $1
                  AND field_key = ANY($2)
                  AND expires_at > NOW()
                  AND confirmation_prompt_sent = FALSE
                ORDER BY confidence_score DESC
                LIMIT $3
                """,
                profile_id,
                relevant_fields,
                1 if max_one_per_session else 10,
            )
        return [dict(r) for r in rows]

    async def build_confirmation_prompt(self, pending_entry: dict) -> str:
        """
        Tạo confirmation prompt conversational.
        Ví dụ: "Lần trước bạn có nhắc đến bạn bị tiểu đường type 2 — mình hiểu đúng không?"
        """
        field_key = pending_entry["field_key"]
        value = pending_entry["field_value"].get("value", "")
        conflict = pending_entry["conflict_flag"]

        if conflict:
            prompt = (
                f"Lần trước bạn có nhắc đến {value} cho {field_key}, "
                f"nhưng điều này có vẻ khác với thông tin mình đã có trước đó. "
                f"Bạn muốn cập nhật lại không?"
            )
        else:
            prompt = (
                f"Lần trước bạn có nhắc đến {value} — mình hiểu đúng không?"
            )

        # Mark as sent
        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE pending_profile_extractions SET confirmation_prompt_sent = TRUE WHERE id = $1",
                pending_entry["id"],
            )

        return prompt

    async def handle_confirmation(
        self,
        pending_id: uuid.UUID,
        confirmed: bool,
        profile_id: uuid.UUID,
        session_profile_id: uuid.UUID,
        session_conversation_id: uuid.UUID,
        account_id: uuid.UUID,
    ) -> None:
        """Xử lý user confirm hoặc deny."""
        async with self.db.connection() as conn:
            pending = await conn.fetchrow(
                "SELECT * FROM pending_profile_extractions WHERE id = $1 AND profile_id = $2",
                pending_id, profile_id,
            )
            if not pending:
                raise ValueError("Pending entry not found or wrong profile")

            if confirmed:
                # Move to main profile store với confirmed=True, confidence=0.90
                from profile_store import ProfileEntry
                entry = ProfileEntry(
                    profile_id=profile_id,
                    account_id=account_id,
                    field_group=pending["field_group"],
                    field_key=pending["field_key"],
                    field_value=dict(pending["field_value"]),
                    confidence_score=0.90,
                    confirmed=True,
                    source_conversation_id=session_conversation_id,
                    source_turn_index=0,
                )
                await self.profile_store.write_extraction(entry, session_profile_id)

            # Xóa khỏi staging (cả confirm lẫn deny)
            await conn.execute(
                "DELETE FROM pending_profile_extractions WHERE id = $1",
                pending_id,
            )
            # Ghi audit log (không lưu health data trong audit log)
            await conn.execute(
                """
                INSERT INTO audit_log (event_type, profile_id_hash, occurred_at)
                VALUES ($1, encode(sha256($2::bytea), 'hex'), NOW())
                """,
                "CONFIRMATION_ACCEPTED" if confirmed else "CONFIRMATION_DENIED",
                str(profile_id).encode(),
            )
```

---

## 11. Bước 10 — Agentic RAG (v2): LangGraph State Machine

> **Lưu ý MVP:** Agentic RAG dùng LangGraph là tính năng v2. MVP dùng Agentic Orchestrator rule-based. Phần này là roadmap để chuẩn bị architecture sẵn.

### 11.1 Tư duy thiết kế Agentic RAG

Sự khác biệt lớn nhất với Proactive RAG:
- **Proactive RAG**: Chạy qua pipeline một lần, profile làm giàu input
- **Agentic RAG**: Có thể chạy nhiều vòng. Sau mỗi vòng, agent **tự đánh giá**: "Tôi đã có đủ thông tin để trả lời chưa?" Nếu chưa → lấy thêm thông tin, điều chỉnh query

### 11.2 State Machine Design

```
                    START
                      │
                      ▼
             [plan_retrieval]     ← Phân tích intent, quyết định retrieval tools
                      │
           ┌──────────┼──────────┐
           ▼          ▼          ▼
    [vector_search] [db_lookup] [graph_search]  ← Chạy song song
           │          │          │
           └──────────┴──────────┘
                      │
                      ▼
              [reflect_sufficiency]  ← "Đủ ngữ cảnh chưa?" (max 3 vòng)
                      │
              ┌───────┴────────┐
              ▼ (NOT enough)   ▼ (enough hoặc max iterations)
     [refine_query]      [assemble_context]
              │                 │
              └────────►────────┘ (loop back)
                                │
                                ▼
                         [generate_response]
                                │
                                ▼
                               END
```

### 11.3 Code LangGraph Agentic RAG

```python
# agentic_rag.py
# v2 feature — requires: langgraph >= 0.1.0, langchain >= 0.2.0

from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import operator

class AgenticRAGState(TypedDict):
    """State được chia sẻ qua tất cả nodes trong graph."""
    # Input
    user_message: str
    profile_snapshot: dict          # serialized ProfileSnapshot
    session_profile_id: str         # profile isolation
    intent: str

    # Retrieval state
    iteration_count: int
    retrieved_chunks: list[dict]
    tier1_data: dict
    graph_context: dict             # v3: GraphRAG results

    # Reflection state
    sufficiency_score: float        # 0.0–1.0: đủ ngữ cảnh?
    reflection_reasoning: str
    refinement_history: list[str]   # queries đã thử

    # Output
    final_context: str
    response: str

    # Messages (LangGraph convention)
    messages: Annotated[list, add_messages]

# Sufficiency threshold: khi nào agent quyết định đủ context
SUFFICIENCY_THRESHOLD = 0.75
MAX_ITERATIONS = 3

def plan_retrieval_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    Phân tích intent và quyết định retrieval strategy.
    Trong v2: dùng LLM để lập kế hoạch.
    """
    intent = state["intent"]
    iteration = state.get("iteration_count", 0)

    # Iteration đầu tiên: dùng câu hỏi gốc
    if iteration == 0:
        refined_query = state["user_message"]
    else:
        # Iteration tiếp theo: dùng refinement query từ reflect node
        refined_query = state["refinement_history"][-1] if state["refinement_history"] else state["user_message"]

    # Trong production: LLM call để decompose query thành sub-queries
    # Ví dụ: "Thuốc metformin có tác dụng phụ gì với người bị thận yếu?"
    # → sub-query 1: "metformin side effects renal impairment"
    # → sub-query 2: "metformin contraindications kidney disease"

    return {
        **state,
        "iteration_count": iteration + 1,
        "current_query": refined_query,
    }

def vector_search_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    pgvector semantic search với profile-aware expansion + reranking.
    Chạy song song với db_lookup_node (LangGraph supports parallel edges).
    """
    from query_expander import ProfileAwareQueryExpander
    from reranker import ProfileAwareReranker
    from profile_store import ProfileSnapshot

    query = state.get("current_query", state["user_message"])
    profile = ProfileSnapshot(**state["profile_snapshot"])

    # Expand query với profile context
    expander = ProfileAwareQueryExpander()
    expanded_query = expander.expand(query, profile)

    # Vector search (production: async pgvector call)
    # results = await pgvector_client.search(expanded_query, top_k=10, threshold=0.75)

    # Rerank với profile relevance
    reranker = ProfileAwareReranker()
    # top5 = reranker.rerank(results, profile)

    # Demo placeholder
    new_chunks = state.get("retrieved_chunks", [])  # accumulate across iterations

    return {**state, "retrieved_chunks": new_chunks}

def db_lookup_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    Tier 1 RAG: direct DB fetch của structured health data.
    Luôn chạy, không phụ thuộc vào sufficiency.
    """
    # production: await elfie_db.get_recent_health_data(profile_id, days=7)
    tier1 = state.get("tier1_data", {})
    return {**state, "tier1_data": tier1}

def reflect_sufficiency_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    "Agentic Reflector" — đánh giá xem đã có đủ context để trả lời chưa.
    
    Trong v2: dùng LLM call ngắn để đánh giá.
    Prompt: "Với câu hỏi: [question] và context: [retrieved], 
             bạn có thể trả lời đầy đủ và chính xác không? 
             Trả lời: SUFFICIENT hoặc NEED_MORE [reason]"
    """
    iteration = state["iteration_count"]
    chunks = state.get("retrieved_chunks", [])

    # Demo: simple heuristic (production: LLM-based reflection)
    has_chunks = len(chunks) > 0
    score = 0.80 if has_chunks else 0.30

    # Force sufficient sau MAX_ITERATIONS
    if iteration >= MAX_ITERATIONS:
        score = 1.0

    return {
        **state,
        "sufficiency_score": score,
        "reflection_reasoning": f"Iteration {iteration}, chunks={len(chunks)}",
    }

def route_after_reflection(state: AgenticRAGState) -> Literal["refine_query", "assemble_context"]:
    """
    Conditional routing: đủ context → assemble, chưa đủ → refine và lấy thêm.
    """
    if state["sufficiency_score"] >= SUFFICIENCY_THRESHOLD:
        return "assemble_context"
    if state["iteration_count"] >= MAX_ITERATIONS:
        return "assemble_context"  # force finish
    return "refine_query"

def refine_query_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    Tạo refined query dựa trên reflection reasoning.
    Trong v2: LLM call để rephrase query và bổ sung context còn thiếu.
    """
    original = state["user_message"]
    reasoning = state.get("reflection_reasoning", "")

    # production: LLM call để refine
    refined = f"{original} [refined iteration {state['iteration_count']}]"

    history = state.get("refinement_history", [])
    return {**state, "refinement_history": [*history, refined]}

def assemble_context_node(state: AgenticRAGState) -> AgenticRAGState:
    """Lắp ghép final context từ tất cả các nguồn đã retrieved."""
    from context_assembler import ContextAssembler
    from profile_store import ProfileSnapshot

    assembler = ContextAssembler()
    profile = ProfileSnapshot(**state["profile_snapshot"])

    # Build gap fields (simplified)
    gap_fields = []

    final_context = assembler.assemble(
        profile_snapshot=profile,
        tier1_data=state.get("tier1_data", {}),
        retrieved_chunks=state.get("retrieved_chunks", []),
        conversation_buffer=[],
        current_message=state["user_message"],
        gap_fields=gap_fields,
    )
    return {**state, "final_context": final_context}

def generate_response_node(state: AgenticRAGState) -> AgenticRAGState:
    """Final LLM call để generate response từ assembled context."""
    # production: await anthropic_client.messages.create(...)
    response = f"[Generated response based on {len(state.get('retrieved_chunks', []))} chunks]"
    return {**state, "response": response}

def build_agentic_rag_graph() -> StateGraph:
    """Xây dựng LangGraph state machine cho Agentic RAG."""
    graph = StateGraph(AgenticRAGState)

    # Add nodes
    graph.add_node("plan_retrieval", plan_retrieval_node)
    graph.add_node("vector_search", vector_search_node)
    graph.add_node("db_lookup", db_lookup_node)
    graph.add_node("reflect_sufficiency", reflect_sufficiency_node)
    graph.add_node("refine_query", refine_query_node)
    graph.add_node("assemble_context", assemble_context_node)
    graph.add_node("generate_response", generate_response_node)

    # Entry point
    graph.set_entry_point("plan_retrieval")

    # Edges
    # Sau plan_retrieval: chạy song song vector_search và db_lookup
    graph.add_edge("plan_retrieval", "vector_search")
    graph.add_edge("plan_retrieval", "db_lookup")

    # Sau khi cả hai search xong → reflect
    graph.add_edge("vector_search", "reflect_sufficiency")
    graph.add_edge("db_lookup", "reflect_sufficiency")

    # Conditional routing từ reflect
    graph.add_conditional_edges(
        "reflect_sufficiency",
        route_after_reflection,
        {
            "refine_query": "refine_query",
            "assemble_context": "assemble_context",
        }
    )

    # Sau refine_query → quay lại plan_retrieval (loop)
    graph.add_edge("refine_query", "plan_retrieval")

    # Final path
    graph.add_edge("assemble_context", "generate_response")
    graph.add_edge("generate_response", END)

    return graph.compile()

# Usage:
# agentic_graph = build_agentic_rag_graph()
# result = await agentic_graph.ainvoke({
#     "user_message": "Metformin có tác dụng phụ gì?",
#     "profile_snapshot": profile.dict(),
#     "session_profile_id": str(session.active_profile_id),
#     "intent": "medication_adherence_query",
#     "iteration_count": 0,
#     "retrieved_chunks": [],
#     "tier1_data": {},
#     "refinement_history": [],
#     "messages": [],
# })
```

---

## 12. Bước 11 — Full Pipeline Integration

### 12.1 Orchestrator chính (MVP — rule-based)

```python
# pipeline.py — Full MVP pipeline
import asyncio
import uuid
from dataclasses import dataclass

@dataclass
class ConversationSession:
    session_token: str
    account_id: uuid.UUID
    active_profile_id: uuid.UUID
    profile_locked: bool = True  # immutable for conversation duration

@dataclass
class PipelineInput:
    user_message: str
    session: ConversationSession
    turn_index: int
    conversation_history: list[dict]
    is_ai_turn: bool = False  # must be False for user messages

@dataclass
class PipelineOutput:
    response: str
    profile_was_updated: bool
    questions_embedded: int
    chunks_used: int

class ProactiveRAGPipeline:
    """
    MVP Pipeline: Proactive RAG với Progressive Profiling.
    Tất cả components chạy theo thứ tự xác định.
    """

    def __init__(
        self,
        pii_scrubber: "PIIScrubber",
        intent_classifier,           # Component 1 — kế thừa
        ner_pipeline: "NERPipeline",
        profile_store: "ProfileStoreService",
        gap_analyzer: "ProfileGapAnalyzer",
        query_expander: "ProfileAwareQueryExpander",
        reranker: "ProfileAwareReranker",
        context_assembler: "ContextAssembler",
        question_validator: "PostGenerationQuestionValidator",
        llm_client,                  # Anthropic / OpenAI client
        safety_classifier,           # Component 1 — kế thừa
        tier1_retriever,             # Elfie DB client
        vector_store,                # pgvector client
        confirmation_flow: "LowConfidenceConfirmationFlow",
    ):
        self.pii_scrubber = pii_scrubber
        self.intent_classifier = intent_classifier
        self.ner = ner_pipeline
        self.profile_store = profile_store
        self.gap_analyzer = gap_analyzer
        self.expander = query_expander
        self.reranker = reranker
        self.assembler = context_assembler
        self.validator = question_validator
        self.llm = llm_client
        self.safety = safety_classifier
        self.tier1 = tier1_retriever
        self.vector_store = vector_store
        self.confirmation = confirmation_flow

    async def process(self, input: PipelineInput) -> PipelineOutput:
        profile_id = input.session.active_profile_id

        # ── Point A: PII Scrub ────────────────────────────────────────
        scrub_result = self.pii_scrubber.scrub(input.user_message)
        scrubbed_text = scrub_result.scrubbed_text

        # ── Parallel: Intent Classification + NER + Tier 1 RAG ───────
        intent_task = asyncio.create_task(
            self.intent_classifier.classify(scrubbed_text)
        )
        ner_task = asyncio.create_task(
            asyncio.to_thread(
                self.ner.extract,
                scrubbed_text,
                is_ai_turn=False,   # always False for user messages
            )
        )
        tier1_task = asyncio.create_task(
            self.tier1.fetch_recent(profile_id, days=7)
        )

        intent, ner_result, tier1_data = await asyncio.gather(
            intent_task, ner_task, tier1_task
        )

        # ── Update Profile Store ──────────────────────────────────────
        profile_updated = False
        for entity in ner_result.entities:
            try:
                if entity.confidence_score >= 0.60:
                    from profile_store import ProfileEntry
                    entry = ProfileEntry(
                        profile_id=profile_id,
                        account_id=input.session.account_id,
                        field_group=self._entity_type_to_field_group(entity.entity_type),
                        field_key=self._entity_type_to_field_key(entity.entity_type),
                        field_value={"value": entity.normalized_value, "raw": entity.raw_value},
                        confidence_score=entity.confidence_score,
                        source_conversation_id=uuid.UUID(input.session.session_token),
                        source_turn_index=input.turn_index,
                    )
                    await self.profile_store.write_extraction(entry, profile_id)
                    profile_updated = True
                else:
                    # confidence < 0.60 → staging
                    staging_entry = ProfileEntry(
                        profile_id=profile_id,
                        account_id=input.session.account_id,
                        field_group=self._entity_type_to_field_group(entity.entity_type),
                        field_key=self._entity_type_to_field_key(entity.entity_type),
                        field_value={"value": entity.normalized_value},
                        confidence_score=entity.confidence_score,
                        source_conversation_id=uuid.UUID(input.session.session_token),
                        source_turn_index=input.turn_index,
                    )
                    await self.profile_store.write_to_staging(staging_entry)
            except Exception:
                pass  # profile update failures do not block response

        # ── Get Updated Profile Snapshot ─────────────────────────────
        profile_snapshot = await self.profile_store.get_snapshot(profile_id, profile_id)

        # ── Profile Gap Analysis ──────────────────────────────────────
        gap_fields = self.gap_analyzer.analyze(intent, profile_snapshot)

        # ── Check for Pending Confirmations ──────────────────────────
        pending = await self.confirmation.get_pending_for_session(
            profile_id, intent, uuid.UUID(input.session.session_token)
        )

        # ── Proactive RAG: Expand + Vector Search + Rerank ───────────
        expanded_query = self.expander.expand(scrubbed_text, profile_snapshot)
        raw_candidates = await self.vector_store.search(
            expanded_query, top_k=10, threshold=0.75
        )
        top_chunks = self.reranker.rerank(raw_candidates, profile_snapshot)

        # ── Context Assembly ──────────────────────────────────────────
        known_profile_fields = set(profile_snapshot.fields.keys())

        # Add confirmation prompt if relevant
        if pending:
            confirmation_prompt = await self.confirmation.build_confirmation_prompt(pending[0])
            gap_fields_with_confirm = gap_fields  # confirmation goes into system prompt separately
        else:
            confirmation_prompt = None

        assembled_context = self.assembler.assemble(
            profile_snapshot=profile_snapshot,
            tier1_data=tier1_data,
            retrieved_chunks=top_chunks,
            conversation_buffer=input.conversation_history,
            current_message=scrubbed_text,
            gap_fields=gap_fields,
        )

        # ── Point B: PII Scrub before LLM ────────────────────────────
        final_context = self.pii_scrubber.scrub(assembled_context).scrubbed_text

        # ── LLM Generation ────────────────────────────────────────────
        raw_response = await self.llm.generate(final_context)

        # ── Post-generation Validation ────────────────────────────────
        validation = self.validator.validate(
            response=raw_response,
            gap_fields=gap_fields,
            known_profile_fields=known_profile_fields,
            is_escalation_response=False,
            is_safety_blocked=False,
        )

        # ── 2-Stage Safety Classifier ─────────────────────────────────
        safe_response = await self.safety.classify_and_rewrite(
            validation.cleaned_response
        )

        return PipelineOutput(
            response=safe_response,
            profile_was_updated=profile_updated,
            questions_embedded=len(gap_fields) - validation.questions_stripped,
            chunks_used=len(top_chunks),
        )

    def _entity_type_to_field_group(self, entity_type: "EntityType") -> str:
        mapping = {
            "CONDITION": "CONDITIONS",
            "MEDICATION": "MEDICATIONS",
            "DEMOGRAPHIC": "DEMOGRAPHICS",
            "LIFESTYLE_FACTOR": "LIFESTYLE",
            "SYMPTOM_CHRONIC": "SYMPTOMS_CHRONIC",
            "BIOMARKER_PREFERENCE": "BIOMARKER_PREFERENCES",
        }
        return mapping.get(entity_type.value, "DEMOGRAPHICS")

    def _entity_type_to_field_key(self, entity_type: "EntityType") -> str:
        mapping = {
            "CONDITION": "condition_name",
            "MEDICATION": "medication_name",
            "DEMOGRAPHIC": "age_years",  # simplified; production: more granular
            "LIFESTYLE_FACTOR": "exercise_frequency_per_week",
            "SYMPTOM_CHRONIC": "symptom_name",
            "BIOMARKER_PREFERENCE": "personal_target",
        }
        return mapping.get(entity_type.value, "unknown")
```

---

## 13. Checklist Triển Khai

### Phase 1 — Foundation (tuần 1–2)

- [ ] Database schema migration (`user_health_profile_entries`, `pending_profile_extractions`)
- [ ] Row Level Security: REVOKE UPDATE/DELETE cho app_role
- [ ] Profile isolation test: cross-profile read attempt → 0 rows returned
- [ ] PII Scrubber integration (kế thừa Component 1 — verify 2-point deployment)
- [ ] Session token schema update: thêm `profile_id` và `profile_locked: true`

### Phase 2 — NER + Profile Store (tuần 3–4)

- [ ] GLiNER model deployment trên Elfie NER inference service
- [ ] NER test suite ≥ 200 labeled messages (English MVP)
- [ ] F1 ≥ 0.85 per entity type trước khi ship
- [ ] Temperature scaling calibration (ECE ≤ 0.05)
- [ ] Normalization dictionary: ≥ 50 condition aliases, INN medication mapping
- [ ] NER latency test: ≤ 150ms P95 tại 500 req/min
- [ ] Verify: NER không chạy trên AI-generated turns
- [ ] Verify: NER không chạy khi user chưa consent Checkbox B

### Phase 3 — Proactive RAG (tuần 5–6)

- [ ] Profile Gap Analyzer: unit tests tất cả 9 intent × 4 profile states
- [ ] Gap Analyzer latency: ≤ 20ms P95
- [ ] Query Expansion: expansion map ≥ 10 conditions, ≥ 5 drug classes
- [ ] Reranking formula: unit test (profile-conditioned chunk > non-profile chunk)
- [ ] Retrieval regression gate: NDCG@5 ≥ baseline − 0.02 (empty profile)
- [ ] Retrieval lift gate: profile-aware NDCG@5 ≥ baseline + 5pp
- [ ] Context Assembler: profile summary ≤ 200 tokens; truncation priority test

### Phase 4 — Questions + Confirmation (tuần 7)

- [ ] Post-generation validator: test tất cả 6 strip rules
- [ ] Adversarial test suite ≥ 50 cases
- [ ] Confirmation flow: confirm path, deny path, expiry cleanup
- [ ] Confirmation prompt ≤ 1 per session với 3 pending extractions
- [ ] Gamification: PROFILE_FIRST_CONFIRMATION + PROFILE_COMPLETENESS_50 events (idempotent)

### Phase 5 — Privacy + Consent (tuần 8)

- [ ] Combined consent modal: Checkbox B unchecked by default
- [ ] Two independent consent records sau submit
- [ ] AI Health Coach functional khi chỉ Checkbox A
- [ ] Profile deletion pipeline: hard-delete within 72h SLA
- [ ] JSON export (48h expiry link)
- [ ] Settings → Privacy → AI Health Profile UI (7 functions)
- [ ] PDPA Thailand + PDPD Vietnam compliance checklist sign-off
- [ ] Medical Affairs + Legal sign-off on consent modal copy

### Phase 6 — Agentic RAG v2 (future sprint)

- [ ] LangGraph state machine implementation
- [ ] Latency profiling: agentic loop ≤ 3 iterations
- [ ] Agentic Reflector LLM call design (sufficiency scoring prompt)
- [ ] Fallback: nếu LangGraph fails → degrade gracefully về MVP rule-based pipeline

---

## Tài Liệu Tham Khảo

- [Spec: Proactive RAG with Progressive Profiling](../specs/04-proactive-rag-progressive-profiling.md)
- [Elfie Platform Context](../elfie-platform-context.md)
- [Architecture Rules](../rules/01-architecture.md)
- [Security Rules](../rules/02-security.md)
- GLiNER paper: [Zero-Shot Named Entity Recognition](https://arxiv.org/abs/2311.08526)
- LangGraph documentation: https://langchain-ai.github.io/langgraph/
- pgvector: https://github.com/pgvector/pgvector
