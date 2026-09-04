---
name: cea-data-pipeline
description: Workflow cheatsheet and operations manual for ingesting, querying, and verifying CEA property transactions and agent rankings.
---

# CEA Data Pipeline Operations Skill

Use this skill when managing, inspecting, or extending Agent 1 (CEA Ranking & Ingestion Engine).

## 1. Quick API Commands

### Check System Health & Metrics
```bash
curl -s http://127.0.0.1:8000/api/v1/health | jq
```

### Query Top Agents by Segment
```bash
# Overall Top 10
curl -s "http://127.0.0.1:8000/api/v1/agent-rankings?segment=overall&limit=10" | jq

# New Sale Top 10
curl -s "http://127.0.0.1:8000/api/v1/agent-rankings?segment=new_sale&limit=10" | jq

# Resale Top 10
curl -s "http://127.0.0.1:8000/api/v1/agent-rankings?segment=resale&limit=10" | jq

# Rental Top 10
curl -s "http://127.0.0.1:8000/api/v1/agent-rankings?segment=rental&limit=10" | jq
```

### Inspect Single Agent Profile
```bash
curl -s "http://127.0.0.1:8000/api/v1/agents/R0331148Q" | jq
```

### Trigger On-Demand Ingestion
```bash
curl -s -X POST "http://127.0.0.1:8000/api/v1/ingest/trigger" \
  -H "Content-Type: application/json" \
  -d '{"sample_size": 150, "use_fixtures": true}' | jq
```

## 2. Test Execution
```bash
python3 -m pytest tests/ -v
```
