# Workspace Rules: Data Compliance, Open Data Licensing & Web Scraping Governance

This document establishes mandatory compliance, licensing, and ethical data ingestion rules for the `PropertyMultiAgents` platform under Singapore statutory law and data governance frameworks.

---

## 1. Statutory Compliance & Singapore Legal Invariants

### A. Singapore Open Data Licence (SODL)
* **Scope**: All public datasets ingested from `data.gov.sg`, Urban Redevelopment Authority (URA), Housing & Development Board (HDB), Singapore Land Authority (SLA OneMap), and Land Transport Authority (LTA DataMall).
* **Mandate**:
  * Commercial and computational use is explicitly permitted under SODL.
  * Ingestion code and public-facing reports must maintain data attribution (e.g., *"Source: data.gov.sg / CEA / URA under the Singapore Open Data Licence"*).
  * Do not modify or alter historical government transaction figures; keep raw payloads intact in `agent_transactions.raw_payload`.

### B. Singapore Copyright Act 2021 (Computational Data Analysis Exception)
* **Statutory Basis**: Sections 243–244 of the Singapore Copyright Act 2021 (Computational Data Analysis / CDA Exception).
* **Mandate**:
  * Copying and computational extraction of publicly accessible web data for machine learning, data mining, and statistical aggregation is legally protected, provided the system has lawful access to the source.
  * Analytical data mining must not republish verbatim copyrighted creative assets without transformative analysis.

### C. Personal Data Protection Act (PDPA) Invariants
* **Business Contact Information (BCI) Exemption**:
  * CEA registration numbers (`R012345A`), estate agency licence numbers (`L3008022J`), registered agency business names, and publicly registered real estate salesperson contact details are classified as **Business Contact Information (BCI)**.
  * Ingestion and ranking of BCI for regulatory transparency and B2B analytics do **not** require individual consent.
* **Strict Consumer Privacy Ban**:
  * **Zero Ingestion of Private Consumer PII**: Under no circumstances should individual buyer/seller NRIC numbers, residential home unit numbers of private owners, or private personal phone numbers be collected, stored, or processed.

### D. Computer Misuse Act (CMA) Safeguards
* **Zero Security Circumvention**: Never bypass authentication gateways, crack CAPTCHAs, or exploit security vulnerabilities.
* **No Server Degradation**: All scrapers and API clients must adhere to strict rate limiting, exponential backoff, and polite concurrency to prevent denial-of-service or infrastructure stress.

---

## 2. Ingestion & Scraper Engineering Standards

### A. API-First Ingestion Priority
1. **Tier 1 (Mandatory First Preference)**: Official Government REST APIs (`data.gov.sg`, SLA OneMap, LTA DataMall, URA APIs).
2. **Tier 2 (Official Platform APIs)**: Official Developer Graph APIs (e.g., Meta Ad Library API with approved developer app credentials).
3. **Tier 3 (Headless / HTML Extraction)**: Used only when no public API exists, strictly governed by `robots.txt` compliance, polite request intervals, and caching layers.

### B. Resilience & Rate-Limiting Protocol
* **Exponential Backoff**: Ingestion clients must handle `429 Too Many Requests` and `5xx Server Errors` with a minimum base backoff of 0.5s multiplying up to 3 retries.
* **Request Timeout**: Individual network HTTP calls must enforce strict timeouts (maximum 5.0 seconds).
* **Deterministic Fallbacks**: Test environments and offline pipelines must default to high-fidelity synthetic fixture generators (`CEASyntheticGenerator`) to ensure 100% test reproducibility without depending on live network calls.
