import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests_per_minute, max_request_per_day):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_request_per_day = max_request_per_day
        self.timestamps = deque()
        self.num_requests = 0
        self.start_time = None

    def request(self):
        current_time = time.time()
        if self.num_requests == 0:
            self.start_time = current_time

        # check if allowed to make next request for the day max 200
        # 86400 seconds in a day
        if current_time < self.start_time + 86400 and self.num_requests + 1 < self.max_request_per_day:
            self.num_requests += 1
        else:
            print("Exceeded max requests for the day")
            return False
        # Remove timestamps older than 1 minute
        while self.timestamps and self.timestamps[0] <= current_time - 60:
            self.timestamps.popleft()
        
        if len(self.timestamps) >= self.max_requests_per_minute:
            # reached the limit, wait until the next minute
            wait_time = 60 - (current_time - self.timestamps[0])
            print(f"Rate limit exceeded. Waiting for {wait_time:.2f} seconds.")
            time.sleep(wait_time)
        
        # Record the current request time
        self.timestamps.append(current_time)

        return True