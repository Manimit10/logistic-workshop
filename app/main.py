"""FastAPI entry point: JSON API + static single-page front end, one process, one URL."""
from __future__ import annotations

import os
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .store import Game, GameError

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"


def _load_dotenv() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


class Join(BaseModel):
    name: str
    pin: str
    team: str
    roles: list[str]

class Login(BaseModel):
    password: str

class Qty(BaseModel):
    qty: dict[str, float]

class Modes(BaseModel):
    modes: dict[str, str]

class Approve(BaseModel):
    approve: bool

class Settings(BaseModel):
    public_board: bool | None = None
    auto_close: bool | None = None
    round_seconds: int | None = None

class Reset(BaseModel):
    seed: int | None = None



def create_app(db_path: str | None = None) -> FastAPI:
    _load_dotenv()
    admin_pw = os.environ.get("ADMIN_PASSWORD")
    if not admin_pw:
        admin_pw = secrets.token_urlsafe(9)
        print(f"[setup] ADMIN_PASSWORD not set; using a random one for this run: {admin_pw}")
    pin = os.environ.get("CLASS_PIN", "EUM2026")
    game = Game(db_path or os.environ.get("DB_PATH", str(ROOT / "data" / "game.db")), pin, admin_pw)
    app = FastAPI(title="EUM Logistics Game", docs_url=None, redoc_url=None, openapi_url=None)

    @app.exception_handler(GameError)
    async def _err(_: Request, e: GameError):
        return JSONResponse({"error": e.code, **e.extra}, status_code=e.status)

    def token(authorization: str | None = Header(default=None)) -> str:
        return (authorization or "").removeprefix("Bearer ").strip()

    def admin(tok: str = Depends(token)) -> str:
        if not game.player(tok)["is_admin"]:
            raise GameError("forbidden", 403)
        return tok

    @app.get("/healthz")
    def health():
        return {"ok": True}

    @app.post("/api/join")
    def join(b: Join):
        return {"token": game.join(b.name, b.pin, b.team, b.roles)}

    @app.post("/api/admin/login")
    def login(b: Login):
        return {"token": game.admin_login(b.password)}

    @app.get("/api/state")
    def state(tok: str = Depends(token)):
        return game.state(tok)

    @app.post("/api/proposal")
    def proposal(b: Qty, tok: str = Depends(token)):
        game.set_proposal(tok, b.qty)
        return {"ok": True}

    @app.post("/api/modes")
    def modes(b: Modes, tok: str = Depends(token)):
        game.set_modes(tok, b.modes)
        return {"ok": True}

    @app.post("/api/approve")
    def approve(b: Approve, tok: str = Depends(token)):
        game.approve(tok, b.approve)
        return {"ok": True}

    @app.post("/api/admin/start")
    def start(_: str = Depends(admin)):
        game.start_round()
        return {"ok": True}

    @app.post("/api/admin/close")
    def close(_: str = Depends(admin)):
        game.close_round()
        return {"ok": True}

    @app.post("/api/admin/reset")
    def reset(b: Reset, _: str = Depends(admin)):
        game.reset(b.seed)
        return {"ok": True}

    @app.post("/api/admin/settings")
    def settings(b: Settings, _: str = Depends(admin)):
        game.settings(b.public_board, b.auto_close, b.round_seconds)
        return {"ok": True}

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    app.state.game = game
    return app


app = create_app() if os.environ.get("EUM_NO_AUTOAPP") != "1" else None
