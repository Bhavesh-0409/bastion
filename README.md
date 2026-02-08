# 🛡️ Bastion - LLM Security Layer

A model-agnostic pre-prompt security layer for locally deployed LLMs.

## Quick Start

### Installation
```bash
pip install -r requirements.txt
cp .env.example .env
```

### Run Backend (API)
```bash
python backend/bastion_api.py
```
API runs on `http://localhost:8000`

### Run UI (Dashboard)
```bash
streamlit run ui/app.py
```
UI runs on `http://localhost:8501`

## Architecture

- **Backend**: FastAPI server with security endpoints
- **Rules**: Rule-based threat detection (regex, keywords)
- **ML**: Machine learning classifier for advanced detection
- **UI**: Streamlit dashboard for monitoring

## Project Structure

```
bastion/
├── backend/          # FastAPI application
├── rules/            # Rule-based detection
├── ml/               # ML classifier
├── ui/               # Streamlit dashboard
├── logs/             # Security logs
├── data/             # Data storage
└── requirements.txt  # Dependencies
```

## API Endpoints

- `GET /health` - Health check
- `POST /prompt/check` - Check prompt security
- `GET /logs` - Retrieve security logs

## TODO

- [ ] Implement ML classifier
- [ ] Add log persistence
- [ ] Implement rules management UI
- [ ] Add model-specific security profiles
