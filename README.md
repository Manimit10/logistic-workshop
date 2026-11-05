# EUM Supply Chain Game

A 45-minute classroom game for logistics students: teams of three (**Demand Planner, Logistics Manager, Finance & Customs**) plan orders for
four products over six rounds, using demand forecasts, shipping options (sea / near-shore / air) and the EU's new customs duty on small parcels.
An **AI baseline bot** plays alongside and shows what a quantile forecast plus the newsvendor rule achieves.

- No registration: students enter a name, a class PIN, a team name and their role(s).
- Role-based access control **enforced on the server**: each role only receives the data its job needs.
- The ranking is **private to the instructor** by default (one switch shares it with students for the debrief).
- English / Spanish toggle. Works on phones. One process, one URL.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
cp .env.example .env                                   # Windows: copy .env.example .env  (then edit it)
pytest                                                 # 17 tests
uvicorn app.main:app --reload                          # http://localhost:8000
```
Deploying and running the class: `docs/DEPLOYMENT.md` and `docs/FACILITATOR_GUIDE.md`.

## How it works
```
app/engine.py     rules: demand scenario, costs, lead times, events, round resolution (pure functions)
app/forecast.py   gradient-boosted quantile models (P50/P80/P95, horizons 1-4), trained on synthetic series
app/store.py      SQLite persistence, round lifecycle, role permissions and per-role views, AI baseline bot
app/main.py       FastAPI routes + static hosting
app/static/       single-page front end (plain JS, no build step)
artifacts/        pre-trained forecast models (committed so the server starts fast)
tests/            engine, forecasting, RBAC, workflow, full-game tests
scripts/          loadtest.py (40 simulated students), e2e_browser.py (Playwright), make_qr.py
```
Retrain the forecast models with `python -m app.forecast` (about 30 s).

## Honest limits
All numbers are teaching simplifications, not Shein's or anyone's real data. Game state lives in one SQLite file on one server process;
do not run more than one instance. Student sessions are random tokens, not accounts. The class PIN is a shared secret, so keep the URL private until class.
