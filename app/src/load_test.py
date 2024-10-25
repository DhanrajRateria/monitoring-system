import requests
import time
import random
import threading
import logging
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"
ENDPOINTS = ['/', '/slow', '/error', '/cpu-intensive']

def make_request(endpoint):
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}{endpoint}")
        duration = time.time() - start_time
        
        logger.info(
            f"Request to {endpoint} completed with status {response.status_code} "
            f"in {duration:.2f} seconds"
        )
    except Exception as e:
        logger.error(f"Request to {endpoint} failed: {str(e)}")

def simulate_user_behavior():
    while True:
        endpoint = random.choice(ENDPOINTS)
        make_request(endpoint)
        time.sleep(random.uniform(0.1, 2))

def run_load_test(num_users=5, duration_seconds=300):
    logger.info(f"Starting load test with {num_users} concurrent users")
    
    with ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [
            executor.submit(simulate_user_behavior)
            for _ in range(num_users)
        ]
        
        time.sleep(duration_seconds)
        
    logger.info("Load test completed")

if __name__ == "__main__":
    run_load_test()