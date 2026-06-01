# Agentic Patient Summary — Technical Feasibility Research

**Component:** Agentic Patient Summary  
**Research date:** 2026-06-01

---

## Kiến trúc tổng thể

```
Trigger (automatic)
  Event: appointment_scheduled (from appointment reminder system)
  Fallback: manual trigger từ bác sĩ trong ElfieCare
        │
        ▼
[Data Collector Agent]
  Pull from Elfie data store:
  - Vitals readings (since last visit)
  - Medication adherence logs
  - Wearable sync (steps, sleep, HRV)
  - Symptom logs (free-text + tags)
  - Lab results (uploaded)
  - Coin events (as proxy for engagement)
  - Doctor notes from last visit (if in ElfieCare)
        │
        ▼
[Delta Analyzer]
  Compare current period vs. previous period:
  - Trend direction per metric
  - Anomaly detection (value outside expected range)
  - Adherence rate calculation
  - Engagement score
        │
        ▼
[Summary Generator (LLM)]
  Input: structured delta analysis + patient context
  Output: structured clinical narrative (SOAP-like format)
  Template: doctor-configurable (full detail vs. brief overview)
        │
        ▼
[Compliance & Privacy Gate]
  - Verify patient opt-in for data sharing
  - Strip/redact if consent scope exceeded
  - Audit log entry
        │
        ▼
[Delivery]
  → Push to ElfieCare doctor's patient queue (pre-visit pending)
  → Or: export PDF for paper-based clinics
  → Or: HL7 FHIR document for EHR integration
```

---

## Trigger System

### Appointment detection

| Trigger source | Method | Coverage |
|---|---|---|
| Elfie appointment reminders | Native (app feature) | High — users who schedule via Elfie |
| iCal/Google Calendar integration | OAuth read | Medium — users who connect calendar |
| Manual trigger by doctor | ElfieCare UI button | Always available as fallback |
| Scheduled (e.g., every 30 days) | Cron job | Catch-all for regular chronic patients |

**Recommended MVP:** Manual trigger (doctor pulls) + 30-day scheduled push. Appointment auto-detection = v2.

---

## Data Collection & Normalization

### Data period selection

```python
def determine_summary_period(patient_id: str, trigger: SummaryTrigger) -> DateRange:
    last_visit = get_last_visit_date(patient_id, trigger.doctor_id)
    
    if last_visit:
        # Default: since last visit (typical: 4–12 weeks)
        return DateRange(start=last_visit, end=today())
    else:
        # First visit: default to last 30 days
        return DateRange(start=today() - timedelta(days=30), end=today())
```

### Handling sparse data

Bệnh nhân không log đều đặn → summary phải thể hiện rõ data completeness:

```
BP readings: 14 of 28 days logged (50% completeness)
Medication: 22 of 28 days logged (79% completeness)
Note: Gaps in data do not necessarily indicate non-adherence.
```

Không suy diễn "bỏ thuốc" từ "không log" — chỉ báo cáo data đã có.

---

## Summary Generator

### LLM prompt strategy

```
System: You are a clinical documentation assistant. Your job is to synthesize 
patient self-monitoring data into a concise clinical summary for a physician 
preparing for a follow-up visit. Be factual, cite numbers, avoid diagnosis. 
Use the following structure: [defined template]

Patient context:
- Primary condition: {condition}
- Treatment: {medications}
- Last visit summary: {last_visit_notes}
- Doctor's monitoring goals: {targets}

Current period data ({date_range}):
{structured_data_json}

Previous period data (for comparison):
{previous_period_json}

Generate a pre-visit summary following the template. 
Flag any values outside patient-specific targets.
Do NOT provide diagnosis, treatment recommendations, or dosage changes.
```

### Output template (configurable per doctor)

```markdown
## Pre-Visit Summary
**Patient:** [anonymized in transit] | **Period:** {date_range}
**Prepared by Elfie** | Not a medical diagnosis

### Vital Signs
| Metric | This Period (avg) | Last Period | Target | Trend |
|--------|-----------------|-------------|--------|-------|
| Blood Pressure | 142/89 mmHg | 134/84 | <140/90 | ↑ |
| Heart Rate | 72 bpm | 74 bpm | 60–80 | → |
| Weight | 82.4 kg | 81.2 kg | — | ↑ |

### Medication Adherence
- Amlodipine 5mg: **22/28 days** (79%) — missed: [dates]
- Ramipril 5mg: **25/28 days** (89%)

### Physical Activity
- Average steps: 4,200/day (↓ 38% vs last period)

### Patient-Reported Symptoms
- Morning headache: 3 occurrences
- Dizziness: 1 occurrence

### ⚠️ Flags for Discussion
- BP trending up while adherence declined — consider reviewing
- Activity drop may be relevant to BP trend
```

---

## Delivery into ElfieCare

### ElfieCare integration point

ElfieCare đã có patient queue / pre-visit section (từ Pre-Visit Agent). Agentic Summary sẽ thêm một card vào đây:

```
[Patient: Nguyen Van A — Appointment: Today 14:00]
  📋 Pre-Visit Agent: Symptom form completed ✓
  🔗 Elfie Summary: Available — 28 days of data [View]    ← NEW
  📝 Previous notes: [View]
```

### Export formats

| Format | Use case |
|---|---|
| In-app card (ElfieCare) | Default — for ElfieCare-using doctors |
| PDF download | Paper-based clinics, attach to physical file |
| HL7 FHIR R4 DocumentReference | EHR integration (v2) |
| Email (encrypted) | Doctors who don't use ElfieCare yet |

---

## Agentic orchestration

Thành phần này là **agentic** theo nghĩa: chạy autonomously theo trigger, không cần user action sau khi opt-in. Implement như scheduled job hoặc event-driven worker:

```python
# Worker (simplified)
@celery_task
def generate_patient_summary(patient_id: str, doctor_id: str, trigger: str):
    # 1. Check consent
    if not consent_service.can_share(patient_id, doctor_id, scope="pre_visit_summary"):
        logger.info(f"No consent for patient {patient_id}")
        return
    
    # 2. Collect and analyze data
    data = data_collector.fetch(patient_id, period=determine_period(patient_id, doctor_id))
    delta = delta_analyzer.analyze(data, previous_period=fetch_previous(patient_id))
    
    # 3. Generate summary
    summary = summary_generator.generate(patient=patient_context(patient_id), delta=delta)
    
    # 4. Safety gate
    summary = compliance_gate.process(summary, patient_id=patient_id)
    
    # 5. Deliver
    elfie_care_api.push_pre_visit_card(doctor_id=doctor_id, patient_id=patient_id, summary=summary)
    audit_log.record(patient_id, doctor_id, action="summary_delivered", timestamp=now())
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Trigger orchestration | Celery + Redis (existing) |
| Data fetching | Existing Elfie data services |
| Delta analysis | Python + pandas (lightweight) |
| LLM for summary | Claude 3.5 / GPT-4o (same BAA as AI Coach) |
| Template engine | Jinja2 |
| ElfieCare delivery | Internal API call |
| PDF generation | WeasyPrint / Puppeteer |
| FHIR (v2) | HAPI FHIR library |

---

## Key technical risks

| Risk | Mitigation |
|---|---|
| LLM hallucination in summary | Summary is 90% structured data; LLM only writes narrative wrapper. Data values always come from source, not generated. |
| Data staleness (patient hasn't logged recently) | Show completeness score; never extrapolate from missing data |
| Doctor not using ElfieCare | PDF/email fallback; ElfieCare adoption is separate business problem |
| Consent revocation mid-flow | Check consent at delivery time, not just at trigger time |
| EHR interoperability complexity | Out of scope for MVP; FHIR = v2 |
