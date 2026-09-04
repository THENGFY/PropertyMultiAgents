# Real Estate Lead-Gen Multi-Agent Engine — Phase 1: Agent 1

> **Agent 1: CEA Ranking & Transaction Ingestion Engine (Singapore Real Estate)**

---

## Quickstart

### 1. Run the Application & Developer Dashboard
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- **Developer Test Dashboard UI**: [http://localhost:8000/](http://localhost:8000/) (or `/portal`, `/dashboard`)
- **Interactive OpenAPI / Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 2. Run the Full Test Suite & Performance Benchmarks
```bash
python3 -m pytest tests/ -v
```

---

## Phase 1 Documentation

All Phase 1 architectural, verification, and engineering workflow documents are located in the [`Doc/`](file:///home/mille/TFYProject/PropertyMultiAgents/Doc/) directory:
* [`Doc/Phase_1_Spec.md`](file:///home/mille/TFYProject/PropertyMultiAgents/Doc/Phase_1_Spec.md): Functional and technical architecture specification.
* [`Doc/Phase_1_Report.md`](file:///home/mille/TFYProject/PropertyMultiAgents/Doc/Phase_1_Report.md): Benchmark results, visual ASCII charts, and edge-case logs.
* [`Doc/Phase_1_Workflow.md`](file:///home/mille/TFYProject/PropertyMultiAgents/Doc/Phase_1_Workflow.md): Development steps, engineering decisions, and Phase 2 alignment.
