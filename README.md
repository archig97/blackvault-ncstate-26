# 🛡️ bLACKVAULT  
### Big Score Track — Financial Technology & Cryptocurrency

---

## 📌 Overview

**bLACKVAULT** is a real-time financial risk intelligence platform designed to help banks detect, score, and flag malicious accounts based on transaction behavior patterns.

Built for the **Big Score (Financial Technology & Cryptocurrency)** hackathon track, the system addresses a critical institutional challenge:

> How can banks proactively identify suspicious accounts and anomalous transaction behavior before financial loss or regulatory exposure occurs?

bLACKVAULT simulates live transaction streams, computes dynamic risk scores, and surfaces actionable intelligence through a real-time monitoring dashboard.

---

## 🎯 Problem Statement

Banks process massive volumes of transactions daily. Within this activity:

- Fraudulent accounts attempt structuring and layering  
- Dormant accounts suddenly spike in activity  
- Rapid fund transfers indicate mule networks  
- Transaction velocity anomalies go undetected in real time  

Traditional monitoring systems are often:
- Batch-based instead of real-time  
- Static rule engines with limited adaptability  
- Operationally opaque  
- Poorly visualized for analysts  

bLACKVAULT closes this gap with a real-time, backend-driven detection engine.

---

## 💡 Solution

bLACKVAULT is a scalable risk detection engine built using:

- **FastAPI (Python)** for high-performance APIs  
- **Valkey** as an in-memory data store  
- A **transaction simulator** to generate realistic financial activity  
- A live **risk intelligence dashboard**

The system ingests transaction streams, updates behavioral metrics per account, calculates risk scores dynamically, and flags suspicious entities instantly.

---

## 🏗️ System Architecture

```text
Transaction Simulator
        │
        ▼
FastAPI Backend (Risk Engine)
├── Account State Manager
├── Risk Scoring Engine
├── Flagging Logic
└── REST APIs
        │
        ▼
Valkey (In-Memory Store)
        │
        ▼
Live Risk Dashboard


---

## 🔧 Core Components

### 1️⃣ Transaction Simulator

Generates synthetic banking transactions to test detection logic under realistic conditions.

Simulates:
- High-velocity transfers  
- Sudden balance spikes  
- Circular fund movement  
- Structured deposits (smurfing patterns)  
- Rapid deposit-withdrawal cycles  

This enables controlled stress-testing of risk logic.

---

### 2️⃣ FastAPI Backend (Python)

Handles:

- Transaction ingestion  
- Real-time account state updates  
- Risk score computation  
- Suspicious activity flagging  
- API endpoints for dashboard integration  

FastAPI enables:

- Asynchronous request handling  
- High throughput under concurrent load  
- Clear and structured API design  

---

### 3️⃣ Valkey (In-Memory Data Store)

Valkey serves as:

- Real-time account state storage  
- Risk score cache  
- Transaction memory layer  
- Fast lookup backend for dashboard queries  

Why Valkey:

- Sub-millisecond read/write latency  
- High concurrency support  
- Atomic operations for consistent state updates  
- Optimized for streaming financial workloads  

---

### 4️⃣ Risk Scoring Engine

Each account is evaluated against multiple behavioral signals, including:

- Transaction frequency spikes  
- Amount deviation from historical baseline  
- Cross-account fund velocity  
- Rapid withdrawal after deposit  
- Repeated structured transaction patterns  

These signals contribute to a dynamic risk score that is:

- Continuously updated  
- Threshold-based for flagging  
- Stored in Valkey for instant retrieval  

---

### 5️⃣ Live Dashboard

The dashboard provides:

- 🔴 Flagged accounts  
- 📊 Real-time risk scores  
- 💸 Live transaction feed  
- 📈 Risk trend analysis  
- 🧠 Behavioral breakdown per account  

This allows compliance teams to act immediately.

---

## 🚀 Use Cases

bLACKVAULT is applicable to:

- Retail banks  
- Digital-first neobanks  
- Payment processors  
- Cryptocurrency exchanges  
- AML and compliance teams  

It can operate as:

- A real-time fraud detection layer  
- A risk scoring microservice  
- A compliance visualization platform  

---

## 🏆 Hackathon Track Alignment  
### Big Score — Financial Technology & Cryptocurrency

The Big Score track emphasizes:

- Financial innovation  
- Scalable transaction systems  
- Secure fintech infrastructure  
- Cryptocurrency fraud detection  

bLACKVAULT aligns directly by providing:

- Real-time fraud detection capabilities  
- High-throughput backend architecture  
- Risk scoring tailored for financial ecosystems  
- Infrastructure adaptable to crypto transaction flows  

---

## 📊 Technical Highlights

- ⚡ Low-latency architecture  
- 🧵 Concurrent transaction handling  
- 📦 Docker-based deployment  
- 🧠 Extensible rule-based risk scoring  
- 🔄 Real-time state mutation using Valkey  

---

## 🧠 Design Principles

1. **Real-Time First** — Risk must be computed instantly.  
2. **Deterministic State Management** — Consistency under concurrency is critical.  
3. **Explainable Risk Signals** — Every flagged account must be auditable.  
4. **Extensible Architecture** — Detection logic can evolve over time.  

---

## 📦 Getting Started

### Run with Docker

```bash
docker compose up -d

#Backend 

http://localhost:8000

#Frontend

http://localhost:3000

