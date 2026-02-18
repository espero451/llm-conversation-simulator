# LLM Conversation Simulator

## Overview
This project simulates restaurant conversations between a waiter and customers, stores the results in database, and provides a simple dashboard with a chatbot UI.

Key capabilities:
- Generate simulated conversations and persist them.
- Browse the latest simulations, diet counts, and top foods.
- Export simulations as JSON or CSV.
- Chat with a waiter-style bot.

## Tech Stack
- Django 5+ (backend, templates)
- PostgreSQL (database)
- OpenAI API (LLM generation)
- Gunicorn + WhiteNoise (serving)
- Docker / docker-compose

## Endpoints

UI:
- `GET /dashboard/` Dashboard UI (Basic Auth required)
- `GET /chatbot/` Chatbot UI (Basic Auth required)

API:
- `POST /api/chatbot/` Chatbot reply (Basic Auth required, JSON: `{"message": "..."}`)
- `GET /api/vegetarians/` Vegetarian/vegan summary (Basic Auth required)
- `GET /api/simulations/latest/?format=json|csv&limit=100` Export latest simulations (Basic Auth required)
- `POST /api/simulations/run/` Run simulations (Basic Auth required, form field `count`, optional `diet-mode` = `self|rules|llm`)

Example curl:
```bash
# Chatbot API
curl -u "$API_USER:$API_PASSWORD" -X POST \
  -H "Content-Type: application/json" \
  -d '{"message":"Hi"}' \
  http://localhost:8000/api/chatbot/

# Vegetarian/vegan summary
curl -u "$API_USER:$API_PASSWORD" \
  http://localhost:8000/api/vegetarians/

# Latest simulations (JSON or CSV)
curl -u "$API_USER:$API_PASSWORD" \
  "http://localhost:8000/api/simulations/latest/?format=json&limit=5"
curl -u "$API_USER:$API_PASSWORD" \
  "http://localhost:8000/api/simulations/latest/?format=csv&limit=5"

# Run simulations with diet mode
curl -u "$API_USER:$API_PASSWORD" -X POST \
  -d "count=50" -d "diet-mode=rules" \
  http://localhost:8000/api/simulations/run/
```

## Configuration
Set these environment variables (create `.env` file for local defaults):
- `OPENAI_API_KEY` Required for simulations and chatbot.
- `OPENAI_MODEL` Optional, default `gpt-4.1`.
- `API_USER` / `API_PASSWORD` Basic Auth for protected endpoints.
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` Database config.

## Running (Docker)
```bash
docker-compose up --build
```
Open:
- Dashboard: `http://localhost:8000/dashboard/`
- Chatbot UI: `http://localhost:8000/chatbot/`

## Manual Simulation
```bash
python app/manage.py simulate_conversations --count 100 --diet-mode self
```

## Diet Validation Modes
Simulations support three diet modes via `--diet-mode`:
- `self` The customer self-declares a diet in the JSON response. No validation, lowest cost, reflects self‑declared diet.
- `rules` Diet is derived from a lightweight ruleset that checks foods for meat/fish or animal products. No extra LLM calls, deterministic heuristic, low cost, may miss ambiguous dishes.
- `llm` Diet is validated by an extra LLM call using favorite foods and ordered dishes. Extra LLM validation, more nuanced but higher cost.

Use the mode that balances accuracy and cost for your needs.

## Todo / Limitations
- Simulations are triggered synchronously from the web request; consider moving them to a background job with a message broker (Redis/RabbitMQ + Celery), but for now they run inline.
