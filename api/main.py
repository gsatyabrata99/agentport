"""
AgentPort Management API
POST /build — accepts YAML, returns a deployable agent ZIP
"""
from __future__ import annotations

import tempfile
import traceback
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))

from agentport_engine.packager import package_yaml

app = FastAPI(title="AgentPort API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class BuildRequest(BaseModel):
    yaml: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "agentport-api"}


@app.post("/build")
def build(req: BuildRequest):
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            yaml_path = tmp / "agent.yaml"
            zip_path = tmp / "agent.zip"

            yaml_path.write_text(req.yaml)
            package_yaml(str(yaml_path), str(zip_path))

            if not zip_path.exists():
                raise HTTPException(status_code=500, detail="Build failed — ZIP not produced")

            zip_bytes = zip_path.read_bytes()

        out = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        out.write(zip_bytes)
        out.close()

        return FileResponse(
            path=out.name,
            media_type="application/zip",
            filename="agent.zip",
            headers={"Content-Disposition": "attachment; filename=agent.zip"},
        )

    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc