# CLAUDE.md: project context for Claude Code

EUM supply chain game: FastAPI + SQLite + plain-JS front end, one process, one URL. Read `README.md` for the layout.

## Commands
- Run: `uvicorn app.main:app --reload` (needs `.env`, copy from `.env.example`)
- Test: `pytest` (must stay green; 17 tests)
- Load test: `python scripts/loadtest.py http://localhost:8000 <admin_pw> 40 <pin>`
- UI test: `python scripts/e2e_browser.py http://localhost:8000 <admin_pw> [screenshot_dir]`
- Retrain forecasts: `python -m app.forecast` then commit `artifacts/forecast_models.joblib`

## Rules that must not break
1. **RBAC is server-side.** Role views are built in `Game._player_view`. Never add data to a view the role shouldn't see (planner: no costs/cash; logistics: no forecasts/cash; finance: no forecasts).
2. **Never leak future demand.** Students only get history for rounds already played (`_history_n`). Admin sees demand only after a round closes.
3. **Rules live in `engine.py` only** (constants at the top). The UI text lives in the `I18N` object in `app/static/app.js`; add every string in **both** `en` and `es`.
4. Single instance only (SQLite + one global lock). Don't add background workers or multi-process settings.
5. No secrets in git: `CLASS_PIN` and `ADMIN_PASSWORD` come from the environment/.env.
6. Keep the front end build-free (no npm). Keep `requirements.txt` pinned.

## Stage prompts (copy, fill the brackets, paste into Claude Code)

**Change the balance:** "In engine.py change [constant/rule]. Then re-run the strategy comparison idea in docs/FACILITATOR_GUIDE.md (bot vs naive vs bridging) over 12 seeds, update the reference numbers there, and run pytest."

**Add an item, mode or event:** "Add [SKU/mode/event] to engine.py (economics, demand, event hook), expose it in store.py views for the right roles only, render it in app.js with en+es strings, add a test in tests/test_game.py, run pytest and scripts/e2e_browser.py."

**Tweak the UI or text:** "In app/static/app.js change [screen/text]. Keep en+es in sync, keep mobile layout (390px wide) working, then run scripts/e2e_browser.py and show me the screenshot."

**Fix a deployment problem:** "Here is the Render/Cloud Run log: [paste]. Find the cause using the Dockerfile, requirements.txt and app/main.py. Propose the smallest fix; don't change game logic."

**Prepare a rerun for another class:** "Add a [theme] scenario selectable by env var SCENARIO without changing the default; update tests and docs/FACILITATOR_GUIDE.md."
