# LLM Conversation Simulator

## Overview
This project simulates restaurant conversations between a waiter and customers, stores the results, and provides a simple dashboard with a chatbot UI.

Key capabilities:
- Generate simulated conversations and persist them.
- Browse the latest simulations, diet counts, and top foods.
- Export simulations as JSON or CSV.
- Chat with a waiter-style bot.

## Tech Stack
- Django 5 (backend, templates)
- PostgreSQL (database)
- OpenAI API (LLM generation)
- Gunicorn + WhiteNoise (serving)
- Docker / docker-compose (local orchestration)

## Endpoints

UI:
- `GET /dashboard/` Dashboard UI (Basic Auth required)
- `GET /chatbot/` Chatbot UI

API:
- `POST /api/chatbot/` Chatbot reply (JSON: `{"message": "..."}`)
- `GET /api/vegetarians/` Vegetarian/vegan summary (Basic Auth required)
- `GET /api/simulations/latest/?format=json|csv&limit=100` Export latest simulations (Basic Auth required)
- `POST /api/simulations/run/` Run simulations (Basic Auth required, form field `count`, max 100)

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
python app/manage.py simulate_conversations --count 100
```
