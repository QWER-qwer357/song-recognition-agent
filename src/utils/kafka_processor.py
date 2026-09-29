import sys
import os
import json
import time
from confluent_kafka import Producer, Consumer

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

KAFKA_BOOTSTRAP = 'kafka:9092'

producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP})

def submit_audio_task(file_path, session_id):
    task = {"file_path": file_path, "session_id": session_id}
    producer.produce('audio_recognize', key=session_id, value=json.dumps(task))
    producer.flush()
    return f"任务已提交: {session_id}"

def create_consumer():
    """尝试连接 Kafka，如果失败则等待并重试，直到成功"""
    while True:
        try:
            consumer = Consumer({
                'bootstrap.servers': KAFKA_BOOTSTRAP,
                'group.id': 'recognize-workers-final',
                'auto.offset.reset': 'earliest'
            })
            consumer.subscribe(['audio_recognize'])
            consumer.poll(1.0)
            print(" Worker 成功连接到 Kafka！")
            return consumer
        except Exception as e:
            print(f" Kafka 还没准备好，10 秒后重试... ({e})")
            time.sleep(10)

def process_audio_worker():
    from src.utils.fingerprint import fingerprint_file
    from src.db.database import get_db
    from src.db.matcher import match_song
    from src.utils.cache import save_session
    
    consumer = create_consumer()  
    
    print("Worker 已启动 等待任务...")
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"【Consumer 报错】: {msg.error()}")
            continue
            
        try:
            task = json.loads(msg.value().decode('utf-8'))
            print(f"\n【Kafka收到消息】: {task}")
            print(f"正在处理任务: {task['session_id']}")
            
            hashes = fingerprint_file(task['file_path'])
            db = next(get_db())
            result = match_song(db, hashes)
            
            save_session(task['session_id'], {"status": "completed", "result": result})
            print(f"任务完成: {task['session_id']}")
            
        except Exception as e:
            print(f"【Worker 真实报错】: {repr(e)}")
            if 'task' in locals():
                save_session(task['session_id'], {"status": "error", "error": str(e)})

if __name__ == '__main__':
    process_audio_worker()