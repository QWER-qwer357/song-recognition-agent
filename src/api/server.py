from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
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

app = FastAPI(title="听歌识曲", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/ui")
async def ui():
    return FileResponse("static/index.html")

@app.on_event("startup")
def startup():
    init_db()
    start_metrics()
    print("API 服务已启动，监控端口: http://localhost:9090/metrics")

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
    os.makedirs("data/uploads", exist_ok=True)

    raw_path = f"data/uploads/{session_id}_raw"
    wav_path = f"data/uploads/{session_id}.wav"
    with open(raw_path, "wb") as f:
        f.write(content)

    from pydub import AudioSegment
    try:
        audio = AudioSegment.from_file(raw_path)
        # 强制截取前 30 秒，避免长音频处理超时
        audio = audio[:30000]
        audio.export(wav_path, format="wav")
        print(f"【转码成功】原格式已转为标准 WAV，时长 {len(audio)/1000:.1f} 秒")
    except Exception as e:
        print(f"【转码失败】{e}，尝试直接使用原文件")
        shutil.copy(raw_path, wav_path)
    finally:
        if os.path.exists(raw_path):
            os.unlink(raw_path)

    submit_audio_task(wav_path, session_id)
    return {"session_id": session_id, "status": "processing"}

@app.get("/result/{session_id}")
def get_result(session_id: str):
    result = get_session(session_id)
    return result if result else {"status": "processing"}

class ChatRequest(BaseModel):
    message: str
    current_song: str = "" 

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        from src.agents.orchestrator import app as agent_app
        
        user_input = request.message
        if request.current_song:
            user_input = f"【当前正在聊的歌曲是《{request.current_song}》】\n{request.message}"
        
        config = {"configurable": {"thread_id": "web_user_1"}}
        result = agent_app.invoke({"user_input": user_input}, config)
        return {"reply": result.get("final_answer", "抱歉，我没有理解您的意思。")}
    except Exception as e:
        return {"reply": f"Agent 处理出错：{str(e)}"}

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8010, ws="none")