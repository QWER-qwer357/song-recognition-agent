from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, tempfile, uvicorn, hashlib, time
from uuid import uuid4

from src.utils.fingerprint import fingerprint_file
from src.db.database import init_db, get_db
from src.db.matcher import store_fingerprints, match_song
from src.utils.cache import get_cached_result, cache_song_result, redis_lock, increment_song_play, get_session
from src.utils.kafka_processor import submit_audio_task

from src.utils.metrics import (
    RECOGNIZE_TOTAL, RECOGNIZE_SUCCESS, RECOGNIZE_LATENCY, start_metrics
)

app = FastAPI(title="听歌识曲", version="1.0")
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/ui")
async def ui():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    start_metrics() 
    print("API 服务已启动，监控端口: http://localhost:9999/metrics")

@app.get("/")
def root():
    return {"status": "ok", "message": "听歌识曲 Agent API"}

@app.post("/fingerprint")
async def add_song(file: UploadFile = File(...), song_name: str = "unknown"):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    shutil.copyfileobj(file.file, tmp)
    tmp.close()
    try:
        hashes = fingerprint_file(tmp.name)
        db = next(get_db())
        song_id = store_fingerprints(db, song_name, hashes, tmp.name)
        return {"song_id": song_id, "song_name": song_name, "hashes_count": len(hashes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp.name)


@app.post("/recognize")
async def recognize(file: UploadFile = File(...)):
   
    RECOGNIZE_TOTAL.inc()
    start_time = time.time()

    content = await file.read()
    file_hash = hashlib.md5(content).hexdigest()

    cached = get_cached_result(file_hash)
    if cached:
        RECOGNIZE_SUCCESS.inc() 
        RECOGNIZE_LATENCY.observe(time.time() - start_time)  
        return {"result": cached, "cached": True}

    session_id = str(uuid4())
    file_path = f"data/uploads/{session_id}.wav"
    os.makedirs("data/uploads", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    submit_audio_task(file_path, session_id)
    return {"session_id": session_id, "status": "processing"}


@app.get("/result/{session_id}")
def get_result(session_id: str):
    result = get_session(session_id)
    if result:
        return result
    return {"status": "processing"}

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8010, ws="none")