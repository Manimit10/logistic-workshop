import os

os.environ["EUM_NO_AUTOAPP"] = "1"
os.environ["CLASS_PIN"] = "PIN1"
os.environ["ADMIN_PASSWORD"] = "secret-admin"

import pytest
from fastapi.testclient import TestClient

from app import engine as E
from app import forecast as F
from app.main import create_app


@pytest.fixture()
def c():
    return TestClient(create_app(":memory:"))


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


def join(c, name, team, roles, pin="PIN1"):
    return c.post("/api/join", json={"name": name, "pin": pin, "team": team, "roles": roles})


def admin(c):
    return H(c.post("/api/admin/login", json={"password": "secret-admin"}).json()["token"])


def team_of_three(c, team="Alpha"):
    t = {}
    for name, role in (("Ana", "planner"), ("Bru", "logistics"), ("Cai", "finance")):
        t[role] = H(join(c, name, team, [role]).json()["token"])
    return t


# ---------------------------------------------------------------- engine
def test_unit_economics_make_air_uneconomic_for_cheap_tee():
    assert E.critical_ratio("tee", "air") < 0.5 < E.critical_ratio("tee", "sea")
    assert E.unit_landed_cost("tee", "air") == 6 + 5 + 3


def test_port_delay_shifts_sea_only():
    scn = E.make_scenario(1)
    st = E.new_team_state(scn)
    st["pipeline"].append({"sku": "tee", "qty": 5, "mode": "air", "arrival": 3})
    E.open_round(st, 1)
    before = [(p["mode"], p["arrival"]) for p in st["pipeline"]]
    E.open_round(st, 2)                      # the port-delay event fires when round 2 opens
    after = {(p["mode"], p["arrival"]) for p in st["pipeline"]}
    assert all(m != "sea" or a >= 4 for m, a in after), (before, after)
    assert ("air", 3) in after               # air is not delayed


def test_scenario_is_deterministic_and_viral_spikes():
    a, b = E.make_scenario(7), E.make_scenario(7)
    assert (a["demand"]["viral"] == b["demand"]["viral"]).all()
    assert a["means"]["viral"][E.N_HISTORY + 3] > 4 * a["means"]["viral"][E.N_HISTORY]


def test_forecast_is_monotone_and_calibrated_enough():
    fc = F.forecast([100, 98, 105, 99, 101, 100, 97, 103])
    for h, v in fc.items():
        assert v["p50"] <= v["p80"] <= v["p95"]
    assert 80 < fc[1]["p50"] < 120


# ---------------------------------------------------------------- auth & RBAC
def test_wrong_pin_and_admin_password(c):
    assert join(c, "x", "T", ["planner"], pin="nope").status_code == 403
    assert c.post("/api/admin/login", json={"password": "bad"}).status_code == 403


def test_state_requires_token(c):
    assert c.get("/api/state").status_code == 401
    assert c.get("/api/state", headers=H("garbage")).status_code == 401


def test_students_cannot_use_admin_endpoints(c):
    t = team_of_three(c)
    for path in ("start", "close", "reset", "settings"):
        r = c.post(f"/api/admin/{path}", json={}, headers=t["planner"])
        assert r.status_code == 403, path


def test_role_views_hide_data(c):
    t = team_of_three(c)
    adm = admin(c)
    c.post("/api/admin/start", headers=adm)
    p = c.get("/api/state", headers=t["planner"]).json()
    l = c.get("/api/state", headers=t["logistics"]).json()
    f = c.get("/api/state", headers=t["finance"]).json()
    assert "planner" in p and "finance" not in p and "logistics" not in p
    assert "logistics" in l and "planner" not in l and "finance" not in l
    assert "finance" in f and "planner" not in f
    assert "board" not in p            # leaderboard is private by default
    assert "admin" not in p


def test_role_actions_are_enforced(c):
    t = team_of_three(c)
    c.post("/api/admin/start", headers=admin(c))
    assert c.post("/api/proposal", json={"qty": {"tee": 10}}, headers=t["finance"]).status_code == 403
    assert c.post("/api/modes", json={"modes": {"tee": "sea"}}, headers=t["planner"]).status_code == 403
    assert c.post("/api/approve", json={"approve": True}, headers=t["logistics"]).status_code == 403


def test_role_taken_and_rejoin(c):
    team_of_three(c)
    r = join(c, "Dan", "Alpha", ["planner"])
    assert r.status_code == 409
    again = join(c, "ana", "Alpha", ["planner"])        # same person, any case
    assert again.status_code == 200


def test_uncovered_role_is_covered_by_teammates(c):
    a = H(join(c, "Ana", "Duo", ["planner"]).json()["token"])
    b = H(join(c, "Bru", "Duo", ["logistics"]).json()["token"])
    c.post("/api/admin/start", headers=admin(c))
    assert c.post("/api/proposal", json={"qty": {"tee": 50}}, headers=a).status_code == 200
    assert c.post("/api/modes", json={"modes": {"tee": "sea"}}, headers=b).status_code == 200
    assert c.post("/api/approve", json={"approve": True}, headers=b).status_code == 200   # finance uncovered


# ---------------------------------------------------------------- workflow
def play_order(c, t, qty, modes):
    assert c.post("/api/proposal", json={"qty": qty}, headers=t["planner"]).status_code == 200
    assert c.post("/api/modes", json={"modes": modes}, headers=t["logistics"]).status_code == 200
    return c.post("/api/approve", json={"approve": True}, headers=t["finance"])


def test_order_needs_modes_and_budget(c):
    t = team_of_three(c)
    c.post("/api/admin/start", headers=admin(c))
    c.post("/api/proposal", json={"qty": {"tee": 10}}, headers=t["planner"])
    assert c.post("/api/approve", json={"approve": True}, headers=t["finance"]).json()["error"] == "modes_missing"
    r = play_order(c, t, {"coat": 5000}, {"coat": "air"})
    assert r.json()["error"] == "over_budget"


def test_editing_after_approval_revokes_it(c):
    t = team_of_three(c)
    c.post("/api/admin/start", headers=admin(c))
    assert play_order(c, t, {"tee": 20}, {"tee": "sea"}).status_code == 200
    assert c.get("/api/state", headers=t["planner"]).json()["order_status"]["approved"] is True
    c.post("/api/proposal", json={"qty": {"tee": 30}}, headers=t["planner"])
    assert c.get("/api/state", headers=t["planner"]).json()["order_status"]["approved"] is False


def test_full_game_and_demand_not_leaked(c):
    t = team_of_three(c)
    adm = admin(c)
    for rnd in range(1, E.N_ROUNDS + 1):
        c.post("/api/admin/start", headers=adm)
        p = c.get("/api/state", headers=t["planner"]).json()
        assert len(p["planner"]["history"]["tee"]) == E.N_HISTORY + rnd - 1       # no peeking at today's demand
        assert p["planner"]["forecast"] is not None
        play_order(c, t, {"tee": 100, "dress": 50}, {"tee": "sea", "dress": "nearshore"})
        assert c.post("/api/admin/close", headers=adm).status_code == 200
    s = c.get("/api/state", headers=adm).json()
    assert s["game"]["phase"] == "finished"
    assert len(s["admin"]["board"]) == 2                          # our team + the AI baseline
    assert c.post("/api/admin/start", headers=adm).status_code == 400


def test_late_new_team_blocked_and_reset_works(c):
    team_of_three(c)
    adm = admin(c)
    c.post("/api/admin/start", headers=adm)
    assert join(c, "Zed", "Brand New", ["planner"]).json()["error"] == "game_started"
    assert join(c, "Zed", "Alpha", ["planner"]).json()["error"] == "role_taken"
    c.post("/api/admin/reset", json={}, headers=adm)
    assert join(c, "Zed", "Brand New", ["planner"]).status_code == 200
    assert c.get("/api/state", headers=adm).json()["game"]["phase"] == "lobby"


def test_public_board_toggle(c):
    t = team_of_three(c)
    adm = admin(c)
    c.post("/api/admin/settings", json={"public_board": True}, headers=adm)
    c.post("/api/admin/start", headers=adm)
    assert "board" in c.get("/api/state", headers=t["planner"]).json()


def test_bot_is_sensible():
    """The AI baseline should not lose money on a full game."""
    c = TestClient(create_app(":memory:"))
    adm = admin(c)
    for _ in range(E.N_ROUNDS):
        c.post("/api/admin/start", headers=adm)
        c.post("/api/admin/close", headers=adm)
    bot = [r for r in c.get("/api/state", headers=adm).json()["admin"]["board"] if r["bot"]][0]
    assert bot["net_worth"] > E.START_CASH
