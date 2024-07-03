import argparse
import subprocess
import time
import logging
import os
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import re

# Define the project root directory dynamically
project_root_dir = os.path.dirname(os.path.abspath(__file__))

# Set up argument parsing
parser = argparse.ArgumentParser(description="Watchdog for Celery with dynamic log path")
parser.add_argument("--logpath", help="Path to store the log files", default=os.path.join(project_root_dir, 'app', 'logs'))
parser.add_argument("--loglevel", help="Set the logging level", choices=['info', 'debug', 'warning', 'error', 'critical'], default='debug')
parser.add_argument("--lines", help="Number of log lines to show", type=int, default=10)
parser.add_argument("--task", help="Task to manage", default='celery')
subparsers = parser.add_subparsers(dest="command")

# Define subcommands
subparsers.add_parser("start")
subparsers.add_parser("stop")
subparsers.add_parser("restart")
subparsers.add_parser("monit")

args = parser.parse_args()

# Configure logging with dynamic path
log_file_path = os.path.join(args.logpath, 'watchdog.log')
os.makedirs(args.logpath, exist_ok=True)  # Ensure log directory exists

# Update the logger to use the file handler
file_handler = logging.FileHandler(log_file_path)
# Map the log level from string to logging constants
log_level = getattr(logging, args.loglevel.upper(), logging.DEBUG)
file_handler.setLevel(log_level)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S'))

# Add a stream handler to print logs to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S'))

# Get the root logger and add handlers
logger = logging.getLogger()
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.setLevel(log_level)

# Path to store the PID of the Celery worker process
pid_file_path = os.path.join(args.logpath, f'{args.task}_worker.pid')

def start_celery_worker():
    """
    Starts the Celery worker and saves its PID to a file.

    Raises:
    Exception: If there is an error starting the Celery worker.
    """
    try:
        logger.info("Starting Celery worker...")
        process = subprocess.Popen(
            ["celery", "-A", "app.tasks.celery_config", "worker", "--loglevel=info", "--logfile=" + os.path.join(args.logpath, 'celery.log')],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        with open(pid_file_path, 'w') as f:
            f.write(str(process.pid))
        logger.info(f"Celery worker started with PID {process.pid}")
        stream_logs(process)
    except Exception as e:
        logger.error(f"Error starting Celery worker: {e}")

def stop_celery_worker():
    """
    Stops the Celery worker by reading its PID from a file and killing the process.

    Raises:
    Exception: If there is an error stopping the Celery worker.
    """
    if os.path.exists(pid_file_path):
        with open(pid_file_path, 'r') as f:
            pid = int(f.read())
        try:
            subprocess.run(["kill", "-9", str(pid)], check=True)
            logger.info(f"Stopped Celery worker with PID {pid}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error stopping Celery worker: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        os.remove(pid_file_path)
    else:
        logger.warning("No PID file found. Celery worker is not running?")

class ChangeHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.is_directory:
            return
        if event.event_type in ['created', 'modified', 'deleted']:
            if has_non_comment_changes():
                logger.info(f"Change detected: {event.src_path}")
                logger.info("Restarting Celery worker...")
                stop_celery_worker()
                start_celery_worker()

def monitor_changes():
    """
    Monitors the project directory for changes and restarts the Celery worker if any changes are detected.
    """
    path = os.path.join(project_root_dir, 'app')
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    logger.info("Watchdog started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping Watchdog...")
        observer.stop()
    observer.join()
    stop_celery_worker()
    logger.info("Watchdog stopped.")

def show_logs(lines, loglevel):
    """
    Displays the last few lines of the Celery log with optional log level filtering.

    Args:
    lines (int): Number of log lines to show.
    loglevel (str): Log level to filter by.
    """
    log_file = os.path.join(args.logpath, 'celery.log')
    if not os.path.exists(log_file):
        logger.error("Celery log file does not exist.")
        return

    with open(log_file, 'r') as f:
        logs = f.readlines()[-lines:]
        for log in logs:
            if loglevel:
                if loglevel.upper() in log:
                    print(log, end='')
            else:
                print(log, end='')

def stream_logs(process):
    """
    Streams the logs from the Celery process to the console.

    Args:
    process (Popen): The Celery worker process.
    """
    try:
        for line in iter(process.stdout.readline, b''):
            print(line.decode().strip())
    except Exception as e:
        logger.error(f"Error streaming logs: {e}")

def has_non_comment_changes():
    """
    Checks if there are any non-comment changes in the git diff.

    Returns:
    bool: True if there are non-comment changes, False otherwise.
    """
    result = subprocess.run(['git', 'diff', '--cached'], stdout=subprocess.PIPE)
    diff = result.stdout.decode()
    changes = diff.split('\n')
    for line in changes:
        if re.match(r'^\s*#', line):  # Ignore comments
            continue
        if re.match(r'^\s*$', line):  # Ignore empty lines
            continue
        if line.startswith('-') or line.startswith('+'):
            return True
    return False

if __name__ == "__main__":
    try:
        if args.command == "start":
            start_celery_worker()
            monitor_changes()

        elif args.command == "stop":
            stop_celery_worker()

        elif args.command == "restart":
            stop_celery_worker()
            start_celery_worker()
            monitor_changes()

        elif args.command == "monit":
            show_logs(args.lines, args.loglevel)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        stop_celery_worker()

# Example usage:
# 1. Start the Celery worker and monitor for changes:
#    python watchdog_celery.py start
#
# 2. Stop the Celery worker:
#    python watchdog_celery.py stop
#
# 3. Restart the Celery worker and monitor for changes:
#    python watchdog_celery.py restart
#
# 4. Show the last 15 lines of the Celery log with info log level:
#    python watchdog_celery.py monit --lines 15 --loglevel info
