"""Drive the real UI with Playwright: 3 students + admin play 3 rounds. Dev tool, not needed to run the app.
Usage: python scripts/e2e_browser.py http://localhost:8000 <admin_password> [screenshot_dir]"""
import sys
from playwright.sync_api import sync_playwright

URL, ADMIN_PW = sys.argv[1], sys.argv[2]
SHOTS = sys.argv[3] if len(sys.argv) > 3 else None
errors = []

def shot(page, name):
    if SHOTS:
        page.screenshot(path=f"{SHOTS}/{name}.png", full_page=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    def new(name, **kw):
        ctx = b.new_context(**kw); pg = ctx.new_page()
        pg.on("pageerror", lambda e, n=name: errors.append(f"{n}: {e}"))
        pg.on("console", lambda m, n=name: m.type == "error" and errors.append(f"{n}: console {m.text}"))
        pg.goto(URL); return pg
    adm = new("admin", viewport={"width": 1280, "height": 900})
    adm.click("#staff-btn"); adm.fill("#a-pw", ADMIN_PW); adm.click("#login-btn"); adm.wait_for_selector("#start")
    team = {}
    for name, role in (("Ana", "planner"), ("Bru", "logistics"), ("Cai", "finance")):
        pg = new(name, viewport={"width": 1100, "height": 900} if role != "finance" else {"width": 390, "height": 844})
        pg.fill("#j-name", name); pg.fill("#j-pin", "EUM2026"); pg.fill("#j-team", "Team Rocket")
        pg.check(f"input[name=role][value={role}]"); pg.click("#join-btn"); team[role] = pg
    for pg in team.values(): pg.wait_for_selector(".banner")
    shot(team["planner"], "01_lobby_planner")
    for rnd in range(1, 4):
        adm.click("#start"); 
        team["planner"].wait_for_selector("#q-tee:not([disabled])", timeout=8000)
        team["logistics"].wait_for_selector("#m-tee:not([disabled])", timeout=8000)
        pl = team["planner"]
        for sku, q in (("tee", 100), ("dress", 120), ("coat", 70), ("viral", 30)): pl.fill(f"#q-{sku}", str(q))
        if rnd == 1: shot(pl, "02_planner_open")
        pl.click("#save-qty"); pl.wait_for_selector("text=Saved")
        lg = team["logistics"]
        team["logistics"].wait_for_function("document.querySelector('#m-tee') && true")
        lg.wait_for_function("document.querySelector('table')")
        # logistics sees planner quantities after its next poll
        lg.wait_for_function("[...document.querySelectorAll('td')].some(td => td.textContent.trim()==='100')", timeout=8000)
        for sku, m in (("tee", "sea"), ("dress", "nearshore"), ("coat", "sea"), ("viral", "air")): lg.select_option(f"#m-{sku}", m)
        if rnd == 1: shot(lg, "03_logistics_open")
        lg.click("#save-modes"); lg.wait_for_selector("text=Saved")
        fi = team["finance"]
        fi.wait_for_function("document.querySelector('#approve') && !document.querySelector('#approve').disabled", timeout=8000)
        if rnd == 1: shot(fi, "04_finance_mobile")
        fi.click("#approve"); fi.wait_for_selector("text=Approved")
        adm.wait_for_function("document.body.innerText.includes('✓')", timeout=8000)
        if rnd == 1: shot(adm, "05_admin_round_open")
        adm.click("#close"); adm.wait_for_function("document.querySelector('#start') && !document.querySelector('#start').disabled")
        team["planner"].wait_for_selector("text=closed", timeout=8000)
        if rnd == 2: shot(team["planner"], "06_planner_after_round2"); shot(adm, "07_admin_after_round2")
    adm.click("#present"); shot(adm, "08_presenter")
    adm.click("#present"); adm.check("#s-public"); adm.click("#s-apply")
    team["finance"].wait_for_selector("text=Ranking", timeout=8000); shot(team["finance"], "09_finance_with_board_mobile")
    team["planner"].click("#lang"); shot(team["planner"], "10_planner_spanish")
    b.close()
print("UI errors:", errors or "none")
