# Workspace Rules: Multi-Agent Execution Guardrails

## 1. Phased Roadmap Execution Guardrails
- Under no circumstances should downstream code (Phase 2 to Phase 5) be written or scaffolded until the preceding phase is verified and signed off.
- **Phase 1**: Agent 1 (CEA Ranking & Ingestion Engine)
- **Phase 2**: Agent 2 & Agent 3 (Meta Ad Library Scraper & Whitespace Opportunity Detection)
- **Phase 3**: Conversational Inbound Engine (WhatsApp Business API & LPAMA auto-qualification)
- **Phase 4**: Frontend UI & PWA Packaging
- **Phase 5**: Downstream Content & Funnel Agents (Agents 4, 6, 7, 8)

## 2. Documentation Standards
- Every phase must produce three markdown documents in the `Doc/` directory:
  1. `Doc/Phase_N_Spec.md`
  2. `Doc/Phase_N_Report.md`
  3. `Doc/Phase_N_Workflow.md`
