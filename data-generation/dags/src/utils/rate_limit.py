import time
from collections import deque
from src.logger import logger

class RateLimiter:
    
    """A rate limiter to restrict the number of requests per minute and per day."""

    def __init__(self, max_requests_per_minute, max_request_per_day):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_request_per_day = max_request_per_day
        self.timestamps = deque()
        self.num_requests = 0
        self.start_time = None

    def request(self):
        """Handles request rate limiting by enforcing both per-minute and per-day constraints.
        
        Returns:
            bool: True if the request is allowed, False if the limit is exceeded.
        """

        current_time = time.time()
        if self.num_requests == 0:
            self.start_time = current_time

        if current_time < self.start_time + 86400 and self.num_requests + 1 < self.max_request_per_day:
            self.num_requests += 1
        else:
            logger.warning("Exceeded max Open Router API requests for the day")
            return False
        
        # Remove timestamps older than 1 minute
        while self.timestamps and self.timestamps[0] <= current_time - 60:
            self.timestamps.popleft()
        
        if len(self.timestamps) >= self.max_requests_per_minute:
            # reached the limit, wait until the next minute
            wait_time = 60
            logger.warning(f"Rate limit exceeded for OpenRouter API. Waiting for {wait_time:.2f} seconds.")
            time.sleep(wait_time)
        
        # Record the current request time
        self.timestamps.append(current_time)

        return True