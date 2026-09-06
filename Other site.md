# Supplementary Singapore Data Sources & Platforms for Real Estate Multi-Agent Engine

This document outlines official Singapore government data sources, statutory board portals, and market intelligence APIs to enrich the **End-to-End Real Estate Lead-Generation & Intelligence Multi-Agent System**.

---

## 1. Urban Planning, Master Plan & Private Property Data

### **[URA Space & URA Developer APIs](https://www.ura.gov.sg/maps/api/) / [REALIS](https://www.ura.gov.sg/maps/)**
* **Primary Data Types**:
  * **Private Residential Property Transactions**: Median PSF, transaction prices, and historical transaction volume across CCR (Core Central Region), RCR (Rest of Central Region), and OCR (Outside Central Region).
  * **Developer Launch Data**: Monthly launched vs. unsold developer inventory and buyer demographic breakdowns (Singaporean vs. PR vs. Foreigner).
  * **Master Plan Zoning & Plot Ratio**: Allowable Gross Plot Ratio (GPR), zoning changes, building height limits, and future development land parcels.
  * **Rental Contracts**: Registered private leasing contracts and gross rental yields by project.
* **Multi-Agent Use Cases**:
  * **Agent 2 & 3 (Whitespace Analysis)**: Detects projects with high unsold inventory where developers/agencies are spending heavily on ads or where buyer demand outpaces supply.
  * **Agent 4 & 5 (Content Gen & Market Reports)**: Auto-generates quarterly price trend reports and investment yield analyses.

---

## 2. Upgrader Triggers & Public Housing Data

### **[HDB Map Services](https://services2.hdb.gov.sg/webapp/BB33MAPS/) & [HDB Resale Portal](https://www.hdb.gov.sg/)**
* **Primary Data Types**:
  * Block-level HDB resale transactions and median prices by town.
  * **BTO Completion & MOP (Minimum Occupation Period) Dates**: Year of completion for every HDB precinct.
* **Multi-Agent Use Cases (High-Value Lead-Gen Trigger 🎯)**:
  * **MOP Upgrader Targeting Engine**: When an HDB estate reaches its **5-year MOP** (e.g., Canberra, Punggol, Tengah), owners become eligible to sell and upgrade to an Executive Condominium (EC) or private condominium. Identifying MOP clusters provides a prime seller/upgrader lead pool.

---

## 3. Geospatial, School Catchments & Infrastructure

### **[OneMap API (Singapore Land Authority - SLA)](https://www.onemap.gov.sg/docs/)**
* **Primary Data Types**:
  * High-precision reverse geocoding and planning area boundaries.
  * **1km / 2km Primary School Catchment Circles**: Essential for Singapore school balloting (Phase 2C distance rules).
  * Hawker centres, parks, childcare centres, and community amenities.

### **[LTA DataMall (Land Transport Authority)](https://datamall.lta.gov.sg/)**
* **Primary Data Types**:
  * Existing and upcoming MRT lines/stations (Thomson-East Coast Line, Cross Island Line, Jurong Region Line).
  * Bus stop density, bus arrival routes, and ERP gantry locations.
* **Multi-Agent Use Cases**:
  * **Agent 1 & 3 (Property Scoring Engine)**: Calculates an **Amenity & Transport Accessibility Score** (Distance to nearest MRT, Top-10 Primary Schools within 1km) for any project.
  * **Agent 3 (LPAMA Inbound Bot)**: Answers lead queries like: *"Is Project X within 1km of ACS Primary or Tao Nan School?"*

---

## 4. Demographics & Household Wealth Mapping

### **[SingStat Table Builder (Department of Statistics Singapore)](https://tablebuilder.singstat.gov.sg/)**
* **Primary Data Types**:
  * Resident population demographics broken down by Planning Area and Subzone.
  * Household monthly income brackets, population age profiles, and housing type distribution (percentage residing in private vs. HDB).
* **Multi-Agent Use Cases**:
  * **Agent 2 & 3 (Audience Persona Profiling)**: Matches high-income planning subzones (e.g., Bukit Timah, Marine Parade, Bishan) with target ad copy and luxury property positioning.

---

## 5. Mortgage, Interest Rates & Affordability Rules

### **[MAS Financial & Banking Statistics](https://eservices.mas.gov.sg/statistics/)**
* **Primary Data Types**:
  * Benchmark interest rates (**SORA — Singapore Overnight Rate Average** 1M/3M compounded rates).
  * Regulatory thresholds: **TDSR** (Total Debt Servicing Ratio: 55%), **MSR** (Mortgage Servicing Ratio: 30% for HDB/EC), and **LTV** (Loan-to-Value) caps.
* **Multi-Agent Use Cases**:
  * **Agent 3 (WhatsApp LPAMA Qualification Bot)**: Real-time affordability calculator: estimates maximum loan eligibility and monthly mortgage instalments based on live SORA floating vs. fixed bank rates.

---

## 6. Competitor Advertising & Market Demand Signals

### **[Meta Ad Library API (Singapore Region)](https://www.facebook.com/ads/library/api/)**
* **Primary Data Types**: All active and inactive sponsored Facebook/Instagram ads run by Singapore property agents and agencies.
* **Multi-Agent Use Cases (Phase 2 Milestone)**:
  * Analyzes which new launches are saturated with ads and flags projects where top agents have zero ad presence (**Ad Whitespace Gap**).

### **[Google Trends & Keyword Planner](https://trends.google.com/)**
* **Primary Data Types**: Real-time Singapore search volume for project names (e.g., *"Norwood Grand price"*, *"Chuan Park launch date"*).
* **Multi-Agent Use Cases**:
  * Detects surging consumer search interest before sales gallery previews start.

---

## 📊 Summary Integration Matrix

| Platform | Primary Data Type | Integration Method | Multi-Agent Subsystem |
|---|---|---|---|
| **URA APIs / REALIS** | Private transactions, developer sales, master plan zoning | REST API / CSV | Agent 1 (Enrichment) & Agent 2 (Whitespace) |
| **HDB Services** | Resale transactions & 5-year MOP completion clusters | Scraper / Open API | Lead-Gen Trigger (Upgrader Engine) |
| **OneMap API** | 1km/2km school zones, planning boundaries, geocoding | REST API | Scoring Engine & Agent 3 (Inbound Bot) |
| **SingStat** | Subzone household income & demographic profiles | REST API / JSON | Audience Profiling & Copywriting |
| **MAS Statistics** | SORA interest rates, TDSR/MSR regulatory thresholds | REST API / Scraper | Agent 3 (LPAMA Financial Qualifier) |
| **Meta Ad Library** | Live property agent ad creatives & audience targeting | Meta Graph API | Phase 2 (Ad Transparency Engine) |
