# LLM Conversation Simulator

## Overview
This project simulates restaurant conversations between a waiter and customers, stores the results in database, and provides a simple dashboard with a chatbot UI.

Key capabilities:
- Generate simulated conversations and persist them.
- Browse the latest simulations, diet counts, and top foods.
- Export simulations as JSON or CSV.
- Chat with a waiter-style bot.

## Tech Stack
- Django 5+ (backend, templates, session authentication)
- Django REST Framework (API layer, serializers, permissions, CSRF integration)
- PostgreSQL (database)
- OpenAI API (LLM generation)
- Gunicorn + WhiteNoise (serving)
- Docker / docker-compose

## Endpoints

UI:
- `GET /dashboard/` Dashboard UI
- `GET /chatbot/` Chatbot UI

API:
- `POST /api/chatbot/` Chatbot reply
- `GET /api/vegetarians/` Vegetarians / vegans summary
- `GET /api/simulations/latest/?format=json|csv&limit=100` Export latest simulations
- `POST /api/simulations/run/` Run simulations (form field `count`, optional `diet-mode` = `self|rules|llm`)

## Authentication & Security

- Django session-based authentication.
- All UI and API endpoints require an authenticated user.
- CSRF protection is enforced for all unsafe HTTP methods (POST, PUT, PATCH, DELETE).
- Permissions are enforced via Django's built-in permission system.

## Configuration
Set these environment variables (create `.env` file for local defaults):
- `OPENAI_API_KEY` Required for simulations and chatbot.
- `OPENAI_MODEL` Optional, default `gpt-4.1`.
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` Database config.

## Running (Docker)
```bash
docker-compose up --build
```

Add user:
`docker compose exec web python3 manage.py createsuperuser`

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
