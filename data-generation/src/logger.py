import logging
from datetime import datetime
import os

# Define the path for the logs folder using the relative path
logfile_path = os.path.join(os.path.dirname(__file__), "..", "logs")
if not os.path.exists(logfile_path):
    os.makedirs(logfile_path)

# Get the current timestamp for the log file name
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Full log file path with timestamp
log_file = os.path.join(logfile_path, f"{timestamp}.log")
print(f"Log file: {log_file}")
# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),  # Save log in the generated log file
        logging.StreamHandler()  # Print to console as well
    ]
)

# Create logger instance
logger = logging.getLogger(__name__)