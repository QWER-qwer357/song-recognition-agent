import time
import json
from collections import defaultdict

class DeadLoopDetector:
    """检测 Agent 死循环"""
    def __init__(self, max_steps=25, max_repeats=3):
        self.max_steps = max_steps
        self.max_repeats = max_repeats
        self.step_count = 0
        self.action_history = []

    def check(self, action):
        self.step_count += 1
        if self.step_count >= self.max_steps:
            raise Exception(f"超过最大步数 {self.max_steps}，疑似死循环")
        
        self.action_history.append(action)
        recent = self.action_history[-self.max_repeats:]
        if len(recent) == self.max_repeats and len(set(recent)) == 1:
            raise Exception(f"连续重复动作 {self.max_repeats} 次，疑似死循环")
        print(f"  [死循环检测] 通过，当前步数: {self.step_count}")

class CircuitBreaker:
    """熔断器：工具连续失败自动熔断"""
    def __init__(self, threshold=5, timeout=10):
        self.failure_count = defaultdict(int)
        self.threshold = threshold
        self.timeout = timeout
        self.circuit_open = defaultdict(float)

    def call_with_retry(self, func, args, retries=3):
        name = func.__name__
        
        if self.circuit_open[name] > 0:
            if time.time() - self.circuit_open[name] < self.timeout:
                raise Exception(f"工具 {name} 已熔断，请稍后再试")
            else:
                self.circuit_open[name] = 0
                self.failure_count[name] = 0
        
        for i in range(retries):
            try:
                result = func(*args)
                self.failure_count[name] = 0
                return result
            except Exception as e:
                self.failure_count[name] += 1
                print(f"  [熔断器] 工具 {name} 第 {i+1} 次失败: {e}")
                if self.failure_count[name] >= self.threshold:
                    self.circuit_open[name] = time.time()
                    raise Exception(f"工具 {name} 达到熔断阈值，已熔断！")
                time.sleep(0.5)
        raise Exception(f"重试 {retries} 次后仍失败")

def validate_output(output, expected_schema):
    """验证 LLM 输出是否符合预期的 JSON 格式"""
    try:
        data = json.loads(output)
        for key in expected_schema:
            if key not in data:
                return False, f"缺少字段: {key}"
        return True, "验证通过"
    except json.JSONDecodeError:
        return False, "JSON 格式错误"

class SafeOperations:
    """安全操作：所有写操作需要确认 + 审计日志"""
    audit_log = []
    
    @classmethod
    def safe_delete(cls, db, model, item_id):
        """安全删除：软删除 + 审计日志"""
        item = db.query(model).filter(model.id == item_id).first()
        if not item:
            raise Exception("记录不存在")
        
        cls.audit_log.append({
            "action": "delete",
            "model": str(model),
            "id": item_id,
            "time": time.time()
        })
        
        if hasattr(item, 'is_deleted'):
            item.is_deleted = True
        else:
            db.delete(item)
        db.commit()
        print(f"  [安全操作] 已安全删除记录 {item_id}，审计日志已记录")
    if __name__ == '__main__':
            print("=== 测试 1：死循环检测 ===")
            detector = DeadLoopDetector(max_steps=5, max_repeats=3)
    try:
            for i in range(6):
                detector.check("search_song") 
    except Exception as e:
            print(f"成功拦截死循环: {e}")

    print("\n=== 测试 2：熔断器 ===")
    breaker = CircuitBreaker(threshold=3, timeout=5)
    def faulty_tool():
            raise Exception("数据库连接超时")
    try:
        breaker.call_with_retry(faulty_tool, [], retries=5)
    except Exception as e:
        print(f"成功触发熔断: {e}")

    print("\n=== 测试 3：输出验证（防幻觉） ===")
    # 测试正确的输出
    is_valid, msg = validate_output('{"song": "晴天", "artist": "周杰伦"}', ["song", "artist"])
    print(f"正确输出验证: {is_valid}, {msg}")
    # 测试缺少字段的输出
    is_valid, msg = validate_output('{"song": "晴天"}', ["song", "artist"])
    print(f"缺失字段验证: {is_valid}, {msg}")
        