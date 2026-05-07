# UBID-Sync: Interoperability Middleware Prototype

## 🎯 Main Goal
The **UBID-Sync Interoperability Middleware** is designed to demonstrate a lightweight, non-invasive solution for bidirectional data synchronization between a central **Single Window System (SWS)** and various **Legacy Department Systems** (e.g., Factory & Boilers, Shops & Establishments).

The core objective is to ensure that a change made in any system (like a business address update or a contact name change) is automatically propagated to all other relevant systems using the **Unique Business Identifier (UBID)** as the common key, without requiring expensive re-engineering of the legacy databases.

---

## 🛠️ How it Works (The Architecture)
The project consists of three main layers:

### 1. Mock Ecosystem (The Simulation)
Since we cannot access real government databases, the backend simulates:
- **SWS**: The modern, citizen-facing portal.
- **Factory Department**: A legacy system with its own naming conventions (e.g., `factory_addr` instead of `registered_address`).
- **Shop Department**: Another legacy system with a different schema.

### 2. Middleware Core (The Intelligence)
The middleware runs as a background service within the FastAPI backend:
- **Polling Engine**: Every 5 seconds, it checks each system for "last updated" timestamps.
- **Schema Mapping**: It translates fields between systems (e.g., `business_name` in SWS ↔ `establishment_name` in Factory).
- **Conflict Resolution**: If two systems update the same record simultaneously, it applies a "Latest Timestamp Wins" policy.
- **Idempotency & Retries**: Uses a `request_id` ledger to prevent duplicate updates and a `RetryQueue` to handle temporary network failures.

### 3. Admin Dashboard (The Visualization)
A React-based frontend that provides:
- **Live Audit Trail**: Watch data propagate in real-time.
- **System Health**: Monitor the status of connected departments.
- **Conflict Monitoring**: View and track resolved data conflicts.

---

## 🔄 Workflow Summary
1. **Change Detected**: A user updates their business name in the SWS portal.
2. **Poll & Detect**: The Middleware Polling Engine detects the `updated_at` change in the SWS database.
3. **Registry Lookup**: The middleware uses the `UBIDRegistry` to find corresponding record IDs in the Factory and Shop systems.
4. **Translation & Propagation**: 
   - It maps `business_name` to `establishment_name` for the Factory system.
   - It sends an internal "update" request to the Mock Factory API.
5. **Audit Log**: Every step is recorded in the `audit_logs` table for full transparency.

---

## 🚀 How to Run

### Prerequisites
- Python 3.9+
- Node.js 18+

### 1. Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
The backend will start at `http://localhost:8000`. It automatically seeds the database with initial mock data.

### 2. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
The dashboard will be available at `http://localhost:5173`.

---

## 📁 Project Structure
- `backend/app/main.py`: Entry point and scheduler initialization.
- `backend/app/models.py`: Database schemas for systems and middleware.
- `backend/app/middleware/polling_engine.py`: The "brain" that handles synchronization.
- `backend/app/mock_systems/`: Logic simulating the SWS and department APIs.
- `frontend/src/`: React components and API hooks for the dashboard.

---

## ⚖️ Key Features for Hackathon
- **Zero-Invasive**: Works alongside existing systems via polling.
- **Bidirectional**: Syncs SWS → Dept AND Dept → SWS.
- **Robustness**: Handles conflicts, retries, and deduplication.
- **Traceability**: Comprehensive audit trail for every single field change.
