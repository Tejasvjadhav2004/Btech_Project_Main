# AI-Powered Supplier Management System

LSTM + LangChain + FastAPI + PostgreSQL + Streamlit

---

## Tech Stack

| Layer | Tech |
|---|---|
| UI | Streamlit |
| API | FastAPI + Uvicorn |
| Database | PostgreSQL |
| Deep Learning | PyTorch LSTM |
| LLM Agent | LangChain + OpenAI GPT |

---

## Project Structure

```
app/
├── main.py                 # FastAPI entry point
├── config.py               # Loads settings from .env
├── streamlit_app.py        # Streamlit UI
├── requirements.txt        # Python dependencies
├── .env.example            # Template — copy to .env and fill in values
├── agents/
│   ├── supplier_agent.py   # Core AI agent (LSTM + LangChain)
│   └── invetory_agent.py   # Inventory agent
├── api/
│   ├── supplier_routes.py  # /supplier/* endpoints
│   ├── inventory_routes.py # /inventory/* endpoints
│   └── security.py         # API key authentication
├── database/
│   ├── db.py               # PostgreSQL connection
│   └── models.py           # Database tables
├── models/
│   └── lstm_model.py       # LSTM reliability predictor
└── schemas/
    └── supplier_schema.py  # Request/response schemas
```

---

## Setup (First Time)

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO/app
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### 4. Create your .env file
```bash
cp .env.example .env
```
Fill in `.env` with values received from the project admin:
```dotenv
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/supplier_db
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-3.5-turbo
APP_API_KEYS=                   # leave empty for local dev
```

---

## Running the App

Requires **two terminals**.

**Terminal 1 — Backend**
```bash
source venv/bin/activate
venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
API: http://localhost:8000  
Docs: http://localhost:8000/docs

**Terminal 2 — UI**
```bash
source venv/bin/activate
venv/bin/streamlit run streamlit_app.py --server.port 8501
```
UI: http://localhost:8501

**First run:** Open UI → Dashboard → click **Refresh Metrics** to seed 15 suppliers into the database.

---

## Stopping the Servers

```bash
pkill -f "uvicorn main:app"
pkill -f "streamlit run"
```

---

## API Endpoints

All endpoints require header: `X-API-Key: your-key`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/supplier/list` | All suppliers |
| POST | `/supplier/recommend` | AI recommendations |
| POST | `/supplier/search` | Search by product name |
| GET | `/supplier/performance/{id}` | Performance report + charts |
| POST | `/supplier/update-metrics` | Recalculate scores |
| POST | `/supplier/reset-reseed` | Clear and re-seed DB |
| POST | `/supplier/ask` | Chat with AI agent (GPT) |
| GET | `/inventory/find-supplier` | Find supplier for a product |

---

## Security

- All API endpoints are protected by `X-API-Key` header
- `.env` is in `.gitignore` — never uploaded to GitHub
- Only `.env.example` (with placeholder values) is committed

**Admin: generate a key for a new team member**
```bash
python3 -c "import secrets; print('key-' + secrets.token_hex(12))"
```
Add it to `APP_API_KEYS` in `.env` (comma-separated), then restart the server.  
To revoke: remove their key and restart.
