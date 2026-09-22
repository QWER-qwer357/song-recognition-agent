from prometheus_client import Counter, Histogram, Gauge, start_http_server

# 评估
RECOGNIZE_TOTAL = Counter('recognize_total', 'Total recognize requests')
RECOGNIZE_SUCCESS = Counter('recognize_success', 'Successful recognitions')
RECOGNIZE_LATENCY = Histogram('recognize_latency_seconds', 'Recognition latency')
TOOL_CALL_TOTAL = Counter('tool_call_total', 'Tool calls', ['tool_name'])
TOOL_CALL_ERROR = Counter('tool_call_error', 'Tool call errors', ['tool_name'])
AGENT_STEPS = Histogram('agent_steps', 'Steps per agent run')
ACTIVE_SESSIONS = Gauge('active_sessions', 'Active user sessions')

def start_metrics():
    # 启动一个 HTTP 服务器 暴露指标
    start_http_server(9999)
    print("Metrics 服务器已启动: http://localhost:9999/metrics")