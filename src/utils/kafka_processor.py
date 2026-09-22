import sys
import os
import json
from confluent_kafka import Producer, Consumer

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

producer = Producer({'bootstrap.servers': '127.0.0.1:9092'})

def submit_audio_task(file_path, session_id):
    task = {"file_path": file_path, "session_id": session_id}
    producer.produce('audio_recognize', key=session_id, value=json.dumps(task))
    producer.flush()
    print(f"【Producer】已发送任务: {task}")
    return f"任务已提交: {session_id}"

consumer = Consumer({
    'bootstrap.servers': '127.0.0.1:9092',
    'group.id': 'recognize-workers-final', 
    'auto.offset.reset': 'earliest'        
})
consumer.subscribe(['audio_recognize'])

def process_audio_worker():
    """消费者：从队列取任务 执行指纹提取和匹配"""
    from src.utils.fingerprint import fingerprint_file
    from src.db.database import get_db
    from src.db.matcher import match_song
    from src.utils.cache import save_session
    
    print("Worker 已启动 等待任务...")
    while True:
        msg = consumer.poll(1.0) 
        if msg is None:
            continue
        if msg.error():
            print(f"【Consumer 报错】: {msg.error()}")
            continue
            
        task = json.loads(msg.value().decode('utf-8'))
        print(f"\n【Kafka收到消息】: {task}")
        print(f"正在处理任务: {task['session_id']}")
        
        try:
            hashes = fingerprint_file(task['file_path'])
            db = next(get_db())
            result = match_song(db, hashes)
            
            save_session(task['session_id'], {
                "status": "completed",
                "result": result
            })
            print(f"任务完成: {task['session_id']}")
        except Exception as e:
            print(f"【Worker 真实报错】: {repr(e)}")
            save_session(task['session_id'], {
                "status": "error",
                "error": str(e)
            })

if __name__ == '__main__':
    process_audio_worker()