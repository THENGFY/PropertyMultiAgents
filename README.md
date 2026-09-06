# Real Estate Lead-Gen Multi-Agent Engine — Phase 1: Agent 1

> **Agent 1: Multi-Source Singapore Property Intelligence & CEA Ranking Engine**

---

## Quickstart

### 1. Run the Application & Developer Dashboard
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- **Developer Test Dashboard UI**: [http://localhost:8000/](http://localhost:8000/) (or `/portal`, `/dashboard`)
- **Interactive OpenAPI / Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **HDB 5-Year MOP Clusters API**: [http://localhost:8000/api/v1/hdb/mop-clusters](http://localhost:8000/api/v1/hdb/mop-clusters)
- **URA Price Benchmarks API**: [http://localhost:8000/api/v1/market-benchmarks](http://localhost:8000/api/v1/market-benchmarks)

### 2. Run the Full Test Suite & Performance Benchmarks
```bash
python3 -m pytest tests/ -v
```

---

## Phase 1 Documentation

All Phase 1 architectural, verification, and engineering workflow documents are located in the [`Doc/`](file:///home/mille/TFYProject/PropertyMultiAgents/Doc/) directory:
* [`Doc/Phase_1_Spec.md`](file:///home/mille/TFYProject/PropertyMultiAgents/Doc/Phase_1_Spec.md): Functional and technical architecture specification for multi-source ingestion.
* [`Doc/Phase_1_Report.md`](file:///home/mille/TFYProject/PropertyMultiAgents/Doc/Phase_1_Report.md): 24/24 Test pass benchmarks, visual ASCII charts, and latency metrics.
* [`Doc/Phase_1_Workflow.md`](file:///home/mille/TFYProject/PropertyMultiAgents/Doc/Phase_1_Workflow.md): Modular adapter design, legal/data compliance rules, and Phase 2 handoff.
* [`Other site2.md`](file:///home/mille/TFYProject/PropertyMultiAgents/Other%20site2.md): Master reference of Singapore Government & Private data sources.
