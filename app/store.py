"""Game service: SQLite persistence, round lifecycle, and role-based views.

One global lock keeps things simple and safe for ~50 users. Role rules live in
`effective_roles` and in the `view_*` functions, so the browser never receives
data its role may not see.
"""
from __future__ import annotations

import hmac
import json
import os
import secrets
import sqlite3
import threading
import time

from . import engine as E
from . import forecast as F

BOT_NAME = "AI baseline"
BOT_MODES = {"tee": "sea", "coat": "sea", "dress": "nearshore", "viral": "nearshore"}


class GameError(Exception):
    def __init__(self, code: str, status: int = 400, **extra):
        super().__init__(code)
        self.code, self.status, self.extra = code, status, extra


SCHEMA = """
CREATE TABLE IF NOT EXISTS game(id INTEGER PRIMARY KEY CHECK(id=1), round INT, phase TEXT, seed INT,
  public_board INT, deadline REAL, auto_close INT, round_seconds INT);
CREATE TABLE IF NOT EXISTS players(token TEXT PRIMARY KEY, name TEXT, team_id INT, roles TEXT, is_admin INT, created REAL);
CREATE TABLE IF NOT EXISTS teams(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE COLLATE NOCASE, state TEXT, bot INT);
CREATE TABLE IF NOT EXISTS orders(team_id INT, round INT, qty TEXT, modes TEXT, approved INT, cost REAL,
  PRIMARY KEY(team_id, round));
"""


class Game:
    def __init__(self, db_path: str, class_pin: str, admin_password: str):
        self.lock = threading.RLock()
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(SCHEMA)
        self.class_pin, self.admin_password = class_pin, admin_password
        self._scn: dict | None = None
        self._scn_seed: int | None = None
        self._fc_cache: dict = {}
        if not self.db.execute("SELECT 1 FROM game").fetchone():
            self.db.execute("INSERT INTO game VALUES(1,0,'lobby',?,0,NULL,0,150)", (secrets.randbelow(10**6),))
            self.db.commit()
            self._ensure_bot()

    # ------------------------------------------------------------- helpers
    def _g(self) -> sqlite3.Row:
        return self.db.execute("SELECT * FROM game").fetchone()

    def _set(self, **kv) -> None:
        cols = ", ".join(f"{k}=?" for k in kv)
        self.db.execute(f"UPDATE game SET {cols}", tuple(kv.values()))
        self.db.commit()

    def scn(self) -> dict:
        seed = self._g()["seed"]
        if self._scn_seed != seed:
            self._scn, self._scn_seed = E.make_scenario(seed), seed
            self._fc_cache.clear()
        return self._scn

    def _teams(self) -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM teams ORDER BY bot DESC, id").fetchall()

    def _ensure_bot(self) -> None:
        if not self.db.execute("SELECT 1 FROM teams WHERE bot=1").fetchone():
            self.db.execute("INSERT INTO teams(name,state,bot) VALUES(?,?,1)",
                            (BOT_NAME, json.dumps(E.new_team_state(self.scn())),))
            self.db.commit()

    def _members(self, tid: int) -> list[dict]:
        rows = self.db.execute("SELECT name, roles FROM players WHERE team_id=? AND is_admin=0 ORDER BY created", (tid,))
        return [{"name": r["name"], "roles": r["roles"].split(",")} for r in rows]

    def effective_roles(self, player: sqlite3.Row) -> set[str]:
        """Own roles + any role nobody in the team holds (covers groups of 2 and no-shows)."""
        if player["is_admin"]:
            return {"admin"}
        mine = set(player["roles"].split(","))
        held = set()
        for m in self._members(player["team_id"]):
            held |= set(m["roles"])
        return mine | (set(E.ROLES) - held)

    def _order(self, tid: int, rnd: int) -> dict:
        r = self.db.execute("SELECT * FROM orders WHERE team_id=? AND round=?", (tid, rnd)).fetchone()
        if not r:
            return {"qty": {}, "modes": {}, "approved": False, "cost": 0.0}
        return {"qty": json.loads(r["qty"]), "modes": json.loads(r["modes"]),
                "approved": bool(r["approved"]), "cost": r["cost"]}

    def _save_order(self, tid: int, rnd: int, o: dict) -> None:
        self.db.execute("INSERT OR REPLACE INTO orders VALUES(?,?,?,?,?,?)",
                        (tid, rnd, json.dumps(o["qty"]), json.dumps(o["modes"]), int(o["approved"]), o["cost"]))
        self.db.commit()

    def _save_state(self, tid: int, state: dict) -> None:
        self.db.execute("UPDATE teams SET state=? WHERE id=?", (json.dumps(state), tid))

    # ---------------------------------------------------------------- auth
    def _new_player(self, name, team_id, roles, is_admin) -> str:
        token = secrets.token_urlsafe(24)
        self.db.execute("INSERT INTO players VALUES(?,?,?,?,?,?)",
                        (token, name, team_id, ",".join(roles), int(is_admin), time.time()))
        self.db.commit()
        return token

    def join(self, name: str, pin: str, team_name: str, roles: list[str]) -> str:
        with self.lock:
            if not hmac.compare_digest(pin.strip().encode(), self.class_pin.encode()):
                raise GameError("bad_pin", 403)
            name, team_name = name.strip()[:30], team_name.strip()[:24]
            roles = [r for r in E.ROLES if r in roles]
            if not name or not team_name or not roles:
                raise GameError("missing_fields")
            if team_name.lower() == BOT_NAME.lower():
                raise GameError("reserved_name")
            team = self.db.execute("SELECT * FROM teams WHERE name=?", (team_name,)).fetchone()
            if not team:
                if self._g()["phase"] != "lobby":
                    raise GameError("game_started")
                cur = self.db.execute("INSERT INTO teams(name,state,bot) VALUES(?,?,0)",
                                      (team_name, json.dumps(E.new_team_state(self.scn()))))
                self.db.commit()
                tid = cur.lastrowid
            else:
                tid = team["id"]
            same = self.db.execute("SELECT token FROM players WHERE team_id=? AND lower(name)=lower(?) AND is_admin=0",
                                   (tid, name)).fetchone()
            if same:                      # same person coming back (new browser, refresh)
                return same["token"]
            taken = set()
            for m in self._members(tid):
                taken |= set(m["roles"])
            clash = [r for r in roles if r in taken]
            if clash:
                raise GameError("role_taken", 409, roles=clash)
            return self._new_player(name, tid, roles, False)

    def admin_login(self, password: str) -> str:
        with self.lock:
            if not hmac.compare_digest(password.encode(), self.admin_password.encode()):
                raise GameError("bad_password", 403)
            return self._new_player("admin", None, ["admin"], True)

    def player(self, token: str | None) -> sqlite3.Row:
        with self.lock:
            row = self.db.execute("SELECT * FROM players WHERE token=?", (token or "",)).fetchone()
            if not row:
                raise GameError("unauthorized", 401)
            return row

    # ----------------------------------------------------------- lifecycle
    def _maybe_autoclose(self) -> None:
        g = self._g()
        if g["auto_close"] and g["phase"] == "open" and g["deadline"] and time.time() > g["deadline"] + 2:
            self.close_round()

    def start_round(self) -> None:
        with self.lock:
            g = self._g()
            if g["phase"] == "open":
                raise GameError("round_already_open")
            if g["round"] >= E.N_ROUNDS:
                raise GameError("game_finished")
            rnd = g["round"] + 1
            for t in self._teams():
                st = json.loads(t["state"])
                E.open_round(st, rnd)
                self._save_state(t["id"], st)
                if t["bot"]:
                    self._bot_order(t["id"], st, rnd)
            deadline = time.time() + g["round_seconds"] if g["round_seconds"] else None
            self._set(round=rnd, phase="open", deadline=deadline)

    def close_round(self) -> None:
        with self.lock:
            g = self._g()
            if g["phase"] != "open":
                raise GameError("round_not_open")
            rnd = g["round"]
            for t in self._teams():
                st = json.loads(t["state"])
                E.close_round(st, rnd, self.scn(), self._order(t["id"], rnd))
                self._save_state(t["id"], st)
            self.db.commit()
            self._set(phase="finished" if rnd >= E.N_ROUNDS else "closed", deadline=None)

    def reset(self, seed: int | None = None) -> None:
        with self.lock:
            self.db.execute("DELETE FROM teams")
            self.db.execute("DELETE FROM orders")
            self.db.execute("DELETE FROM players WHERE is_admin=0")
            self._set(round=0, phase="lobby", deadline=None,
                      seed=seed if seed is not None else secrets.randbelow(10**6))
            self._ensure_bot()

    def settings(self, public_board=None, auto_close=None, round_seconds=None) -> None:
        with self.lock:
            kv = {}
            if public_board is not None:
                kv["public_board"] = int(bool(public_board))
            if auto_close is not None:
                kv["auto_close"] = int(bool(auto_close))
            if round_seconds is not None:
                kv["round_seconds"] = max(0, min(900, int(round_seconds)))
            if kv:
                self._set(**kv)

    # ----------------------------------------------------------------- bot
    def forecasts(self, hist_n: int) -> dict:
        key = (self._g()["seed"], hist_n)
        if key not in self._fc_cache:
            scn = self.scn()
            self._fc_cache[key] = {s: F.forecast([int(x) for x in scn["demand"][s][:hist_n]]) for s in E.SKUS}
        return self._fc_cache[key]

    def _bot_order(self, tid: int, st: dict, rnd: int) -> None:
        fc = self.forecasts(E.N_HISTORY + rnd - 1)
        qty, modes = {}, {}
        for sku in E.SKUS:
            mode = BOT_MODES[sku]
            lead = E.MODES[mode]["lead"]
            target = sum(fc[sku][k]["p50"] for k in range(1, lead + 1))
            target += F.quantile_at(fc[sku][lead + 1], E.critical_ratio(sku, mode))
            position = st["inv"][sku] + sum(p["qty"] for p in st["pipeline"] if p["sku"] == sku)
            qty[sku], modes[sku] = max(0, int(round(target - position))), mode
            if rnd + lead > E.N_ROUNDS:          # would arrive after the season ends
                qty[sku] = 0
        cost = E.order_cost(qty, modes)
        if cost > st["cash"]:
            qty = {s: 0 for s in qty}
            cost = 0.0
        self._save_order(tid, rnd, {"qty": qty, "modes": modes, "approved": True, "cost": cost})

    # -------------------------------------------------------------- player actions
    def _require(self, token: str, role: str, need_open: bool = True):
        p = self.player(token)
        if p["is_admin"] or role not in self.effective_roles(p):
            raise GameError("forbidden", 403)
        if need_open and self._g()["phase"] != "open":
            raise GameError("round_not_open")
        return p

    def set_proposal(self, token: str, qty: dict) -> None:
        with self.lock:
            p = self._require(token, "planner")
            rnd = self._g()["round"]
            qty = {s: (int(q) if isinstance(q, (int, float)) and not isinstance(q, bool) else -1) for s, q in qty.items()}
            err = E.validate_order(qty, {s: "sea" for s in qty})
            if err:
                raise GameError("bad_order", detail=err)
            o = self._order(p["team_id"], rnd)
            o.update(qty={s: qty.get(s, 0) for s in E.SKUS}, approved=False, cost=0.0)
            self._save_order(p["team_id"], rnd, o)

    def set_modes(self, token: str, modes: dict) -> None:
        with self.lock:
            p = self._require(token, "logistics")
            if any(m not in E.MODES for m in modes.values()) or any(s not in E.SKUS for s in modes):
                raise GameError("bad_order")
            rnd = self._g()["round"]
            o = self._order(p["team_id"], rnd)
            o.update(modes=modes, approved=False, cost=0.0)
            self._save_order(p["team_id"], rnd, o)

    def approve(self, token: str, approve: bool) -> None:
        with self.lock:
            p = self._require(token, "finance")
            rnd, tid = self._g()["round"], p["team_id"]
            o = self._order(tid, rnd)
            if not approve:
                o.update(approved=False, cost=0.0)
            else:
                qty = {s: q for s, q in o["qty"].items() if q > 0}
                if not qty:
                    raise GameError("empty_order")
                err = E.validate_order(qty, o["modes"])
                if err:
                    raise GameError("modes_missing", detail=err)
                cost = E.order_cost(qty, o["modes"])
                cash = json.loads(self.db.execute("SELECT state FROM teams WHERE id=?", (tid,)).fetchone()["state"])["cash"]
                if cost > cash:
                    raise GameError("over_budget", cost=cost, cash=cash)
                o.update(approved=True, cost=cost)
            self._save_order(tid, rnd, o)

    # ------------------------------------------------------------------ views
    def _history_n(self, g) -> int:
        shown = g["round"] if g["phase"] in ("closed", "finished") else max(g["round"] - 1, 0)
        return E.N_HISTORY + shown

    def _board(self) -> list[dict]:
        rows = []
        for t in self._teams():
            st = json.loads(t["state"])
            rows.append({"team": t["name"], "bot": bool(t["bot"]), "net_worth": E.net_worth(st),
                         "trend": [x["net_worth"] for x in st["log"]]})
        rows.sort(key=lambda r: -r["net_worth"])
        return rows

    def state(self, token: str) -> dict:
        with self.lock:
            p = self.player(token)
            self._maybe_autoclose()
            g = self._g()
            base = {"now": time.time(), "game": {
                "round": g["round"], "phase": g["phase"], "n_rounds": E.N_ROUNDS, "deadline": g["deadline"],
                "events": [{"round": r, "key": k} for r, k in sorted(E.EVENTS.items()) if r <= g["round"] and g["phase"] != "lobby"],
            }}
            if p["is_admin"]:
                return {**base, "role": "admin", "admin": self._admin_view(g)}
            return {**base, **self._player_view(p, g)}

    def _player_view(self, p, g) -> dict:
        tid, rnd = p["team_id"], g["round"]
        team = self.db.execute("SELECT * FROM teams WHERE id=?", (tid,)).fetchone()
        st = json.loads(team["state"])
        roles = self.effective_roles(p)
        order = self._order(tid, rnd) if rnd else {"qty": {}, "modes": {}, "approved": False, "cost": 0.0}
        out = {"role": "player", "me": {"name": p["name"], "roles": p["roles"].split(","),
               "effective": sorted(roles), "covering": sorted(roles - set(p["roles"].split(",")))},
               "team": {"name": team["name"], "members": self._members(tid)},
               "inventory": st["inv"], "pipeline": sorted(st["pipeline"], key=lambda x: (x["arrival"], x["sku"])),
               "order_status": {"has_qty": any(order["qty"].values()),
                                "has_modes": bool(order["modes"]) and all(order["modes"].get(s) for s, q in order["qty"].items() if q > 0),
                                "approved": order["approved"]},
               "results": [{"round": r["round"], "rows": r["rows"]} for r in st["log"]],
               "skus": list(E.SKUS)}
        if g["public_board"]:
            out["board"] = [{"team": r["team"], "net_worth": r["net_worth"]} for r in self._board()]
        hist_n = self._history_n(g)
        if "planner" in roles:
            scn = self.scn()
            out["planner"] = {"history": {s: [int(x) for x in scn["demand"][s][:hist_n]] for s in E.SKUS},
                              "n_history": E.N_HISTORY, "proposal": order["qty"],
                              "forecast": self.forecasts(hist_n) if g["phase"] == "open" else None}
        if "logistics" in roles:
            out["logistics"] = {"modes": {m: {"lead": v["lead"], "freight": v["freight"], "duty": v["duty"]}
                                          for m, v in E.MODES.items()},
                                "proposal": order["qty"], "chosen": order["modes"]}
        if "finance" in roles:
            out["finance"] = {"cash": st["cash"], "net_worth": E.net_worth(st),
                              "prices": {s: v["price"] for s, v in E.SKUS.items()},
                              "unit_costs": {s: v["cost"] for s, v in E.SKUS.items()},
                              "landed": {s: {m: E.unit_landed_cost(s, m) for m in E.MODES} for s in E.SKUS},
                              "critical_ratio": {s: {m: round(E.critical_ratio(s, m), 2) for m in E.MODES} for s in E.SKUS},
                              "order": order, "pnl": [{k: r[k] for k in ("round", "revenue", "holding", "penalty", "ordered_cost", "cash", "net_worth")}
                                                      for r in st["log"]],
                              "constants": {"holding": E.HOLDING_COST, "penalty": E.LOST_SALE_PENALTY, "salvage": E.SALVAGE}}
        return out

    def _admin_view(self, g) -> dict:
        rnd, teams = g["round"], []
        for t in self._teams():
            st = json.loads(t["state"])
            o = self._order(t["id"], rnd) if rnd else None
            teams.append({"team": t["name"], "bot": bool(t["bot"]), "members": self._members(t["id"]),
                          "cash": st["cash"], "net_worth": E.net_worth(st),
                          "ordered": bool(o and any(o["qty"].values())), "approved": bool(o and o["approved"]),
                          "trend": [x["net_worth"] for x in st["log"]]})
        scn = self.scn()
        reveal = g["phase"] in ("closed", "finished")
        shown = g["round"] if reveal else max(g["round"] - 1, 0)
        return {"teams": teams, "board": self._board(),
                "settings": {"public_board": bool(g["public_board"]), "auto_close": bool(g["auto_close"]),
                             "round_seconds": g["round_seconds"]},
                "n_players": self.db.execute("SELECT COUNT(*) c FROM players WHERE is_admin=0").fetchone()["c"],
                "demand": {s: [int(x) for x in scn["demand"][s][E.N_HISTORY:E.N_HISTORY + shown]] for s in E.SKUS}}
