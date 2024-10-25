from  flask import Flask, Response, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, Gauge, Info
import time
import random
import psutil
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

REQUEST_COUNT = Counter(
    'app_request_count_total', 
    'Total request count of the application',
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds',
    'Request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

ACTIVE_REQUESTS = Gauge(
    'app_active_requests',
    'Number of active requests'
)

CPU_USAGE = Gauge(
    'app_cpu_usage_percent',
    'Current CPU usage percentage'
)

MEMORY_USAGE = Gauge(
    'app_memory_usage_bytes',
    'Current memory usage in bytes'
)

ERROR_COUNT = Counter(
    'app_error_count_total',
    'Total count of errors',
    ['error_type', 'endpoint']
)

APP_INFO = Info('app_build_info', 'Application build information')
APP_INFO.info({
    'version': '1.0.0',
    'build_date': '2024-10-26',
    'environment': 'production'
})

def monitor_system_metrics():
    """Background thread to update system metrics"""
    while True:
        CPU_USAGE.set(psutil.cpu_percent(interval=1))
        MEMORY_USAGE.set(psutil.Process().memory_info().rss)
        time.sleep(5)

metrics_thread = threading.Thread(target=monitor_system_metrics, daemon=True)
metrics_thread.start()

def track_requests(func):
    def wrapper(*args, **kwargs):
        ACTIVE_REQUESTS.inc()
        method = request.method
        start_time = time.time()
        
        try:
            response = func(*args, **kwargs)
            REQUEST_COUNT.labels(
                method=method,
                endpoint=func.__name__,
                http_status=response.status_code
            ).inc()
            
            return response
        except Exception as e:
            ERROR_COUNT.labels(
                error_type=type(e).__name__,
                endpoint=func.__name__
            ).inc()
            raise
        finally:
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=func.__name__
            ).observe(time.time() - start_time)
            ACTIVE_REQUESTS.dec()
            
    wrapper.__name__ = func.__name__
    return wrapper

@app.route('/')
@track_requests
def homepage():
    return jsonify(status="healthy")

@app.route('/slow')
@track_requests
def slow_request():
    time.sleep(random.uniform(0.5, 2.0))
    return jsonify(status="completed")

@app.route('/error')
@track_requests
def error_endpoint():
    if random.random() < 0.5:
        raise Exception("Random error occurred")
    return jsonify(status= "success")

@app.route('/cpu-intensive')
@track_requests
def cpu_intensive():
    start = time.time()
    while time.time() - start < 0.5:
        _ = [i ** 2 for i in range(1000)]
    return jsonify(status="completed")

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)