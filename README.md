# AssetFlow Copilot

AssetFlow Copilot brings IT asset workflows into Slack. Employees can find available equipment, request an asset, check their assigned devices, and report hardware problems. Asset managers review requests through Slack actions, while a background worker sends overdue reminders.

> **Project background:** This repository continues the hackathon project created with [Mayank Padhi](https://github.com/Diclo-fenac/assetflow-copilot). The original MIT license and attribution are retained; see [LICENSE](LICENSE).

## Features

- Look up an asset by tag and search available inventory.
- Request an available asset through an interactive Slack flow.
- Approve or reject allocation requests from a Slack approval card.
- Restrict approval, rejection, and audit-start actions to AssetFlow admins and asset managers.
- View assigned assets and recent requests in the Slack App Home tab.
- Report hardware issues through the AssetFlow API.
- Receive direct-message reminders for overdue allocations.

## Architecture

- **Slack Bolt** receives events and handles Slack interactions.
- **FastAPI** exposes `/slack/events` and `/slack/interactions` and starts the reminder worker.
- **LangGraph and Gemini** handle conversational inventory questions and tool calls.
- **AssetFlow API** remains the system of record for assets and allocations. The current configuration uses one AssetFlow organization and one Slack bot installation.
- **SQLAlchemy** stores local request and account-mapping information in the configured database.

## Requirements

- Python 3.13 or newer
- [`uv`](https://docs.astral.sh/uv/)
- A running AssetFlow API
- A Slack app configured for Events API, Interactivity, and the App Home tab
- A Google AI Studio API key

## Local setup

1. Create a local environment file:

   ```bash
   cp .env.example .env
   ```

   In PowerShell, use `Copy-Item .env.example .env`.

2. Add the Slack, AssetFlow, and Google credentials to `.env`. Never commit this file or real credentials.

3. Install dependencies:

   ```bash
   uv pip install -r requirements.txt
   ```

4. Initialize the local database:

   ```bash
   uv run python seed.py
   ```

5. Start the service:

   ```bash
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

6. For local Slack development, expose port `8000` through a tunnel such as ngrok. Configure the Slack Events API URL as `<tunnel-url>/slack/events` and the Interactivity URL as `<tunnel-url>/slack/interactions`.

The root endpoint (`GET /`) and `/healthz` provide basic liveness responses. The app also needs a valid AssetFlow API organization and credentials before inventory actions will work. `seed.py` creates the local schema only; it does not insert demo identities or credentials.

## Current limitations

- The AssetFlow API URL, organization ID, and admin token are configured globally. Full per-workspace API credentials and tenant isolation are not implemented.
- Existing database schemas are initialized with SQLAlchemy `create_all`; there is not yet a migration system for changing tables in place.
- Live Slack, Gemini, and AssetFlow integration checks require dedicated non-production credentials and services.

## Configuration

See [.env.example](.env.example) for the complete list of environment variables. Required values include Slack bot/signing credentials, the AssetFlow admin token, and a Google API key. `DATABASE_URL` defaults to a local SQLite database. `LOG_LEVEL`, `OVERDUE_CHECK_INTERVAL_SECONDS`, `OVERDUE_REMINDER_COOLDOWN_HOURS`, and `ENABLE_OVERDUE_WORKER` control logging and reminder behavior.

## Project layout

```text
app/
  agent/       LangGraph assistant and inventory tools
  bot/         Slack handlers and overdue reminder worker
  core/        Application configuration
  db/          SQLAlchemy models and database setup
  services/    AssetFlow API client
seed.py        Local database initialization
tests/         Agent smoke test
```

## License and acknowledgments

This project is distributed under the MIT License. The original hackathon implementation was created with [Mayank Padhi](https://github.com/Diclo-fenac/assetflow-copilot). This repository retains the original license and attribution; later contributions should be described accurately in repository history and project notes.
