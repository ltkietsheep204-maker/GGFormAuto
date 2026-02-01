"""
Test submission worker để tìm lỗi
"""
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import worker
from gui_app_v3 import SubmissionWorker

# Fake data để test
form_url = "https://docs.google.com/forms/d/e/1FAIpQLSeGyknkHM24lN1xlYvvM9j8xaz3CFwK_huh_aazNGl15o8ZBA/viewform"

# Fake questions
questions = [
    {"index": 0, "title": "Test Q1", "type": "short_answer", "options": []},
    {"index": 1, "title": "Test Q2", "type": "multiple_choice", "options": [{"text": "Option 1"}, {"text": "Option 2"}]}
]

# Fake answers
answers = {
    0: "Test answer",
    1: "Option 1"
}

logger.info("="*80)
logger.info("TESTING SUBMISSION WORKER")
logger.info("="*80)

# Create worker
worker = SubmissionWorker(
    form_url=form_url,
    answers=answers,
    count=1,  # Chỉ test 1 response
    questions=questions,
    max_parallel=1  # Sequential mode
)

def on_progress(msg):
    logger.info(f"PROGRESS: {msg}")

def on_count(n):
    logger.info(f"COUNT: {n}")

def on_finished():
    logger.info("FINISHED!")

def on_error(err):
    logger.error(f"ERROR: {err}")

worker.progress.connect(on_progress)
worker.count_progress.connect(on_count)
worker.finished.connect(on_finished)
worker.error.connect(on_error)

logger.info("Starting worker...")
worker.start()

# Wait for completion
worker.wait()

logger.info("Worker completed!")
