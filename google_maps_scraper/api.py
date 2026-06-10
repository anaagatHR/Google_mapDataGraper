import asyncio
import io
import json
import os
import uuid

import pandas as pd
from fastapi import FastAPI, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from scraper_logic import run_scraper, JOB_STATES, CITY_AREAS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Models ────────────────────────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    searches: str
    total: int
    output_folder: str = "output"
    no_website_only: bool = False

class ControlRequest(BaseModel):
    job_id: str
    action: str  # pause | resume | stop

class SaveRequest(BaseModel):
    filepath: str
    data: list

class RenameRequest(BaseModel):
    old_path: str
    new_name: str


# ── Scrape ────────────────────────────────────────────────────────────────────

@app.post("/api/scrape")
def scrape_endpoint(req: ScrapeRequest, background_tasks: BackgroundTasks):
    search_list = [s.strip() for s in req.searches.split('\n') if s.strip()]
    job_id = str(uuid.uuid4())
    JOB_STATES[job_id] = {'status': 'pending', 'progress': 'Queued...', 'data': [], 'log': []}
    background_tasks.add_task(
        run_scraper, job_id, search_list,
        req.total, req.output_folder, req.no_website_only
    )
    return {"status": "success", "job_id": job_id}


# ── SSE stream — live log lines ───────────────────────────────────────────────

@app.get("/api/stream/{job_id}")
async def stream_job(job_id: str):
    async def generate():
        sent = 0
        while True:
            await asyncio.sleep(0.4)
            state = JOB_STATES.get(job_id, {})
            log_list = state.get('log', [])

            while sent < len(log_list):
                safe = log_list[sent].replace('\n', ' ').replace('\r', '')
                yield f"data: {safe}\n\n"
                sent += 1

            status = state.get('status', 'pending')
            if status in ('completed', 'stopped', 'error'):
                yield f"data: __DONE__{status}\n\n"
                return

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Status (polling fallback + data updates) ──────────────────────────────────

@app.get("/api/status/{job_id}")
def get_status(job_id: str):
    if job_id not in JOB_STATES:
        return JSONResponse(status_code=404,
                            content={"status": "error", "message": "Job not found"})
    state = JOB_STATES[job_id]
    return {
        "status":      state['status'],
        "progress":    state['progress'],
        "data_length": len(state['data']),
        "data":        state['data'],
    }


# ── Control (pause / resume / stop) ──────────────────────────────────────────

@app.post("/api/control")
def control_job(req: ControlRequest):
    if req.job_id not in JOB_STATES:
        return JSONResponse(status_code=404,
                            content={"status": "error", "message": "Job not found"})
    action = req.action
    if action == 'resume':
        JOB_STATES[req.job_id]['status'] = 'running'
    elif action == 'pause':
        JOB_STATES[req.job_id]['status'] = 'paused'
    elif action == 'stop':
        JOB_STATES[req.job_id]['status'] = 'stopped'
    else:
        return JSONResponse(status_code=400,
                            content={"status": "error", "message": "Invalid action"})
    return {"status": "success", "job_status": JOB_STATES[req.job_id]['status']}


# ── Cities list (for frontend autocomplete) ───────────────────────────────────

@app.get("/api/cities")
def cities():
    return sorted(CITY_AREAS.keys())


# ── File management ───────────────────────────────────────────────────────────

@app.get("/api/files")
def list_files(folder: str = "output"):
    if not os.path.exists(folder):
        return {"status": "success", "files": []}
    files = []
    for f in os.listdir(folder):
        if f.endswith('.json'):
            path = os.path.join(folder, f)
            files.append({"name": f, "path": path, "size": os.path.getsize(path)})
    return {"status": "success", "files": files}


@app.post("/api/save_file")
def save_file(req: SaveRequest):
    try:
        if not req.filepath.endswith('.json'):
            return JSONResponse(status_code=400,
                                content={"status": "error", "message": "Can only save JSON files"})
        os.makedirs(os.path.dirname(req.filepath) or '.', exist_ok=True)
        with open(req.filepath, 'w', encoding='utf-8') as f:
            json.dump(req.data, f, indent=4, ensure_ascii=False)
        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.get("/api/read_file")
def read_file(filepath: str):
    try:
        if not os.path.exists(filepath):
            return JSONResponse(status_code=404,
                                content={"status": "error", "message": "File not found"})
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {"status": "success", "data": data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.post("/api/rename_file")
def rename_file(req: RenameRequest):
    try:
        if not os.path.exists(req.old_path):
            return JSONResponse(status_code=404,
                                content={"status": "error", "message": "File not found"})
        dir_name = os.path.dirname(req.old_path)
        new_path = os.path.join(dir_name, req.new_name)
        if not new_path.endswith('.json'):
            new_path += '.json'
        os.rename(req.old_path, new_path)
        return {"status": "success", "new_path": new_path}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.post("/api/import")
def import_excel(file: UploadFile = File(...)):
    try:
        contents = file.file.read()
        df = pd.read_excel(io.BytesIO(contents))
        df = df.fillna("")
        data = df.to_dict(orient="records")
        return {"status": "success", "data": data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ── Root ──────────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    print("Server running at http://127.0.0.1:8080")
    uvicorn.run(app, host="127.0.0.1", port=8080)
