from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from packages.jarvis_core.agent import Agent
from packages.jarvis_core.browser import BrowserService
from packages.jarvis_core.config import settings
from packages.jarvis_core.memory import MemoryStore

memory = MemoryStore()
browser = BrowserService(settings.browser_headless, settings.browser_executable_path)
agent = Agent(memory)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await browser.stop()


app = FastAPI(title="JARVIS", version="0.1.0", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)


class MemoryRequest(BaseModel):
    key: str = Field(min_length=1, max_length=200)
    value: str = Field(min_length=1, max_length=10_000)
    importance: int = Field(default=5, ge=1, le=10)


class ScreenshotRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2_000)
    output_name: str = Field(default="task.png", pattern=r"^[A-Za-z0-9_.-]+$")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "jarvis"}


@app.post("/chat")
async def chat(request: ChatRequest) -> dict[str, str]:
    return {"response": await agent.respond(request.message)}


@app.post("/memory")
async def write_memory(request: MemoryRequest) -> dict[str, object]:
    item = memory.upsert(request.key, request.value, request.importance)
    return {"id": item.id, "key": item.key, "importance": item.importance}


@app.get("/memory")
async def read_memory() -> dict[str, str]:
    return {"context": memory.render_context()}


@app.post("/browser/screenshot")
async def browser_screenshot(request: ScreenshotRequest) -> dict[str, str]:
    path = str(Path("storage/screenshots") / request.output_name)
    evidence = await browser.screenshot(request.url, path)
    return {"url": evidence.url, "title": evidence.title, "screenshot": f"/screenshots/{request.output_name}"}


@app.get("/screenshots/{filename}")
async def screenshot(filename: str):
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="invalid filename")
    path = Path("storage/screenshots") / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="screenshot not found")
    return FileResponse(path)
