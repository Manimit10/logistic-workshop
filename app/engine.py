"""Game engine: demand scenario, economics and round resolution.

Pure functions, no I/O, no web framework. Everything here is a *teaching
simplification*, not Shein's real numbers. Money is in euros, one round = two
weeks of sales.
"""
from __future__ import annotations

import copy
import math

import numpy as np

N_HISTORY = 8          # rounds of sales history shown before round 1
N_ROUNDS = 6           # rounds of the game
START_CASH = 10_000.0
HOLDING_COST = 0.5     # EUR per unit left in stock at the end of a round
LOST_SALE_PENALTY = 5.0  # EUR per unmet unit (brand damage)
SALVAGE = 0.5          # leftover stock is valued at 50% of its base cost
ROLES = ("planner", "logistics", "finance")

SKUS = {
    "tee":   {"price": 15.0, "cost": 6.0,  "base": 100},
    "dress": {"price": 30.0, "cost": 9.0,  "base": 60},
    "coat":  {"price": 60.0, "cost": 20.0, "base": 80},
    "viral": {"price": 22.0, "cost": 7.0,  "base": 20},
}

# lead = rounds between ordering and arrival. duty applies per unit because air
# parcels go to the consumer (EU flat duty of EUR 3 per item category, Jul 2026).
MODES = {
    "sea":       {"lead": 3, "freight": 1.0, "duty": 0.0, "cost_mult": 1.0},
    "nearshore": {"lead": 2, "freight": 2.5, "duty": 0.0, "cost_mult": 1.15},
    "air":       {"lead": 1, "freight": 5.0, "duty": 3.0, "cost_mult": 1.0},
}

# Round -> event key. The viral spike is NOT announced: teams must notice it.
EVENTS = {2: "port_delay"}
VIRAL_MULT = {3: 5.0, 4: 6.0, 5: 4.0, 6: 2.5}   # game round -> multiplier on "viral"


def unit_landed_cost(sku: str, mode: str) -> float:
    m = MODES[mode]
    return round(SKUS[sku]["cost"] * m["cost_mult"] + m["freight"] + m["duty"], 2)


def critical_ratio(sku: str, mode: str) -> float:
    """Newsvendor service level Cu / (Cu + Co) for a SKU shipped by `mode`."""
    landed = unit_landed_cost(sku, mode)
    cu = SKUS[sku]["price"] - landed + LOST_SALE_PENALTY
    co = landed - SALVAGE * SKUS[sku]["cost"] + HOLDING_COST
    cu, co = max(cu, 0.01), max(co, 0.01)
    return cu / (cu + co)


# --------------------------------------------------------------------------
# Demand scenario
# --------------------------------------------------------------------------
def series_means(sku: str, n: int, phase: float = 0.0) -> np.ndarray:
    t = np.arange(n)
    base = SKUS[sku]["base"]
    if sku == "tee":
        return np.full(n, float(base))
    if sku == "dress":
        return base * 1.07 ** t
    if sku == "coat":
        return base * (1 + 0.45 * np.sin(2 * math.pi * t / 12 + phase))
    if sku == "viral":
        m = np.full(n, float(base))
        m[3] *= 2.0   # a small bump in the history so students see spikes exist
        for rnd, mult in VIRAL_MULT.items():
            if N_HISTORY + rnd - 1 < n:
                m[N_HISTORY + rnd - 1] *= mult
        return m
    raise KeyError(sku)


SIGMA = {"tee": 0.10, "dress": 0.20, "coat": 0.12, "viral": 0.25}


def make_scenario(seed: int) -> dict:
    """Return {'means': {sku: array}, 'demand': {sku: array}} for history + game."""
    rng = np.random.default_rng(seed)
    n = N_HISTORY + N_ROUNDS
    phase = float(rng.uniform(-0.5, 0.5))
    means, demand = {}, {}
    for sku in SKUS:
        means[sku] = series_means(sku, n, phase)
        noise = rng.lognormal(0.0, SIGMA[sku], n)
        demand[sku] = np.maximum(0, np.rint(means[sku] * noise)).astype(int)
    return {"means": means, "demand": demand}


def history_upto(scn: dict, sku: str, rnd: int) -> list[int]:
    """Demand the teams may see at the start of game round `rnd` (rounds < rnd)."""
    return [int(x) for x in scn["demand"][sku][: N_HISTORY + rnd - 1]]


# --------------------------------------------------------------------------
# Team state
# --------------------------------------------------------------------------
def new_team_state(scn: dict) -> dict:
    inv, pipeline = {}, []
    for sku in SKUS:
        m = scn["means"][sku]
        inv[sku] = int(round(m[N_HISTORY]))
        for k in (1, 2):   # shipments already at sea when the game starts
            pipeline.append({"sku": sku, "qty": int(round(m[N_HISTORY + k])),
                             "arrival": 1 + k, "mode": "sea"})
    return {"cash": START_CASH, "inv": inv, "pipeline": pipeline, "log": []}


def net_worth(state: dict) -> float:
    stock = sum(q * SKUS[s]["cost"] for s, q in state["inv"].items())
    stock += sum(p["qty"] * SKUS[p["sku"]]["cost"] for p in state["pipeline"])
    return round(state["cash"] + SALVAGE * stock, 2)


def apply_event(state: dict, rnd: int) -> None:
    """Mutates `state` for the event that fires when round `rnd` opens."""
    if EVENTS.get(rnd) == "port_delay":
        for p in state["pipeline"]:
            if p["mode"] == "sea" and p["arrival"] > rnd:
                p["arrival"] += 1


def open_round(state: dict, rnd: int) -> None:
    """Event first, then deliveries due this round."""
    apply_event(state, rnd)
    keep = []
    for p in state["pipeline"]:
        if p["arrival"] <= rnd:
            state["inv"][p["sku"]] += p["qty"]
        else:
            keep.append(p)
    state["pipeline"] = keep


def order_cost(qty: dict, modes: dict) -> float:
    return round(sum(q * unit_landed_cost(s, modes[s]) for s, q in qty.items() if q > 0), 2)


def validate_order(qty: dict, modes: dict) -> str | None:
    for s, q in qty.items():
        if s not in SKUS:
            return f"unknown sku {s}"
        if not isinstance(q, int) or q < 0 or q > 5000:
            return f"bad quantity for {s}"
        if q > 0 and modes.get(s) not in MODES:
            return f"choose a shipping mode for {s}"
    return None


def close_round(state: dict, rnd: int, scn: dict, order: dict | None) -> dict:
    """Sell, charge holding/penalty, then charge and ship the approved order."""
    idx = N_HISTORY + rnd - 1
    rows, revenue, holding, penalty = {}, 0.0, 0.0, 0.0
    for sku, info in SKUS.items():
        d = int(scn["demand"][sku][idx])
        sold = min(state["inv"][sku], d)
        lost = d - sold
        state["inv"][sku] -= sold
        revenue += sold * info["price"]
        holding += HOLDING_COST * state["inv"][sku]
        penalty += LOST_SALE_PENALTY * lost
        rows[sku] = {"demand": d, "sold": sold, "lost": lost, "end_stock": state["inv"][sku]}
    spent = 0.0
    if order and order.get("approved"):
        qty, modes = order["qty"], order["modes"]
        spent = order_cost(qty, modes)
        if spent <= state["cash"] + revenue:
            for sku, q in qty.items():
                if q > 0:
                    state["pipeline"].append({"sku": sku, "qty": q, "mode": modes[sku],
                                              "arrival": rnd + MODES[modes[sku]]["lead"]})
        else:
            spent = 0.0
    state["cash"] = round(state["cash"] + revenue - holding - penalty - spent, 2)
    res = {"round": rnd, "rows": rows, "revenue": round(revenue, 2), "holding": round(holding, 2),
           "penalty": round(penalty, 2), "ordered_cost": round(spent, 2),
           "cash": state["cash"], "net_worth": net_worth(state)}
    state["log"].append(res)
    return res


def clone(state: dict) -> dict:
    return copy.deepcopy(state)
