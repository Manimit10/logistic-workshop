# Deployment guide (for you, Mani)

Goal: one public URL that 40 students open on laptops or phones, no registration.
Order of work: **1. run locally → 2. push to GitHub → 3. deploy → 4. rehearse on the real URL.**
Do steps 1-3 on **Wednesday**, step 4 the same evening. Nothing here needs Docker on your computer.

> Tested in the build environment: the 17 automated tests pass on a clean install of `requirements.txt`; a 40-student load test
> (median 4 ms, p95 8 ms, no errors); a full 3-round game in a headless browser. **Not tested there: the Dockerfile build and the
> cloud hosts themselves** (no Docker daemon, no cloud access). Step 4 is how you test them.

---

## 1. Run it on your computer (Windows, PowerShell, ~5 min)

Prerequisites: Python 3.11+ (3.13 was used) and Git. You have Miniconda; plain `python` from it works.

```powershell
cd path\to\eum-logistics-game
python -m venv .venv
.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements-dev.txt
copy .env.example .env              # then open .env and set CLASS_PIN and ADMIN_PASSWORD
pytest                              # expect: 17 passed
uvicorn app.main:app --reload
```

Open <http://localhost:8000>.
- Students: name + PIN + team name + role(s) → **Join**.
- You: **Instructor login** (bottom right of the join card) → the password from `.env`.

Try it yourself in 4 browser windows (use one normal and 2-3 private windows so sessions don't mix): admin, planner, logistics, finance.
Full UI check by script (optional): `python scripts/e2e_browser.py http://localhost:8000 <admin_password>` after `playwright install chromium`.

**Phone on the same Wi-Fi (optional):** run `uvicorn app.main:app --host 0.0.0.0` and open `http://<your-PC-IP>:8000`
(find the IP with `ipconfig`). Windows Firewall may ask to allow Python. Campus Wi-Fi often blocks device-to-device traffic, so don't rely on this on the day.

---

## 2. Put it on GitHub

Create an empty **private** repo (e.g. `eum-logistics-game`) on github.com, **without** README/.gitignore/licence (the project already has them). Then:

```powershell
git init -b main
git add .
git status                           # CHECK: .env and data/ must NOT be listed
git commit -m "EUM supply chain game: first version"
git remote add origin https://github.com/<your-user>/eum-logistics-game.git
git push -u origin main
```

With the GitHub CLI instead: `gh repo create eum-logistics-game --private --source . --push`.

`.gitignore` already excludes `.env`, the SQLite database, virtual environments and caches.
`artifacts/forecast_models.joblib` (376 KB) **is** committed on purpose, so the server doesn't retrain at startup.
Never put the class PIN or the admin password in a committed file; they are set in the host's dashboard (below).

---

## 3. Deploy: choose one

| | **A. Render (free)** recommended | **B. Google Cloud Run** | **C. Plan B: your laptop + tunnel** |
|---|---|---|---|
| Cost | Free web service | Inside the free tier for one class; billing account required | Free |
| Sign-up | GitHub login; it may ask for a payment method (reports differ, check) | Google Cloud billing account (card) | none for a quick tunnel |
| Sleeps when idle | **Yes, after 15 min; wake-up ≈ 1 min** | scales to zero (set 1 minimum instance for the day) | n/a |
| Risk on the day | slow wake-up, small CPU | misconfiguring "max instances" (see below) | your laptop, Wi-Fi, battery |

Free-tier facts below come from Render's docs and third-party reviews of Render, Cloud Run and others, as of November 2026; they change, so check each pricing page before you rely on them.
Hugging Face Spaces is **not** an option: Docker Spaces need a paid plan.

### A. Render (free)

1. render.com → sign up with GitHub → **New + → Web Service** → pick the repo.
   (Alternative: **New + → Blueprint**, which reads `render.yaml` and fills everything in.)
2. **Runtime: Docker**. **Instance type: Free**. Health check path: `/healthz`.
3. **Environment variables**: `CLASS_PIN` (what students type, e.g. `LOG2026`) and `ADMIN_PASSWORD` (long, only for you).
4. **Create**. The first build takes several minutes (scikit-learn). When the log says the service is live, open the `https://…onrender.com` URL.
5. Every `git push` to `main` redeploys automatically.

Things to know about the free instance:
- It **sleeps after 15 minutes without traffic** and takes about a minute to wake. **Open the URL 5-10 minutes before the workshop**, and again right before you start. During class the students' polling keeps it awake.
- The disk is **ephemeral**: if the service restarts mid-game, the game state is lost and students get "session expired, join again". Rare, but it is why Plan C exists.
- Reported limits: 512 MB RAM (the app uses ≈ 180 MB under load) and a small CPU share (≈ 0.1 vCPU). The app does little work per request, but this is exactly what the rehearsal in step 4 tests.
- 750 free instance hours per month: more than enough for one always-on service.

### B. Google Cloud Run (more headroom, needs a billing account)

Install the `gcloud` CLI, run `gcloud auth login`, create or pick a project with billing enabled, then from the repo folder:

```powershell
gcloud run deploy eum-logistics-game --source . --region europe-west1 --allow-unauthenticated `
  --max-instances 1 --min-instances 1 --memory 1Gi --cpu 1 `
  --set-env-vars "CLASS_PIN=LOG2026,ADMIN_PASSWORD=<long-password>"
```

- **`--max-instances 1` is mandatory.** Game state lives in one process's SQLite file; two instances would give two different games.
- `--min-instances 1` avoids cold starts; it is billed, so after the event run
  `gcloud run services update eum-logistics-game --region europe-west1 --min-instances 0` (or delete the service).
- The command prints the service URL. Free-tier amounts (2 M requests, 180 k vCPU-seconds per month for request-based billing) are far above one class.

### C. Plan B: run on your laptop and expose it

If the cloud misbehaves on the day: run `uvicorn app.main:app --host 0.0.0.0` and create a public tunnel, for example Cloudflare's
quick tunnel: `cloudflared tunnel --url http://localhost:8000` (it prints a `https://….trycloudflare.com` URL). **Try this once at home beforehand**: campus networks and
laptop sleep settings can break it. Keep the laptop on power and disable sleep.

---

## 4. Rehearse on the real URL (Wednesday night)

1. Open the URL; confirm the join page loads. Log in as instructor.
2. From your computer: `python scripts/loadtest.py https://<your-url> <ADMIN_PASSWORD> 40 <CLASS_PIN>`
   (simulates 40 students for ~2 minutes and resets the game when it starts; expect "5xx errors: 0" and a p95 well under 1000 ms on free Render).
3. Join from your **phone on mobile data** (not the Wi-Fi), to see what students on 4G will see.
4. **Reset the game** in the admin screen. Write down the URL, the PIN, and the admin password where you can read them on the day.
5. Make a QR code for the projector: `python scripts/make_qr.py https://<your-url>` → `qr.png`.

## Day-of checklist

- [ ] T-30 min: open the URL on the classroom computer (wakes the free instance), log in as instructor, **Reset**
- [ ] Settings: seconds per round **150** (use 180 for round 1), "auto-close" **on**, "students can see ranking" **off** (turn on for the debrief)
- [ ] URL + PIN visible on the projector (QR code on a slide)
- [ ] Plan B tab ready (tunnel command tested), and printed role cards in case the network dies
- [ ] Browser zoom for the presenter view: Ctrl +

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Page takes ~1 min to load | Free instance waking up. Wait; it won't repeat while the class is active |
| "Wrong class PIN" | PIN is case-sensitive only in your `.env`/dashboard value; check for trailing spaces |
| "Session expired, join again" | Server restarted (state lost) or you pressed Reset. Students re-join with the same names |
| "Role already taken" | Someone else in the team has that role. Same person returning: use the same name and team (case doesn't matter) |
| Student forgot the laptop | They sit with a team; in a team of 2 each takes two roles |
| `pip install` fails on scikit-learn | Use Python 3.11-3.13 (64-bit) |
| Port 8000 busy | `uvicorn app.main:app --port 8001` |

## Changing the app later (VS Code + Claude Code)

Open the repo in VS Code and start Claude Code in it; it reads `CLAUDE.md` automatically (project rules, commands, ready-made prompts per stage), so you don't need to re-explain anything. Run `pytest` before every commit; `git push` redeploys.

## Sources for the hosting facts
- Render docs, free web services: <https://render.com/docs/free>
- Render plan changes (Aug 2026): <https://jwatte.com/blog/render-com-platform-review.md>
- Free Docker hosting comparison: <https://flywp.com/blog/9769/best-free-docker-hosting-platforms>
- Cloud Run pricing: <https://cloud.google.com/run/pricing>
- Hugging Face Spaces overview: <https://huggingface.co/docs/hub/spaces-overview>
