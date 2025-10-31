import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

# Assume your core logic is in `handler.py` and the function is `process_image`
from handler import process_image

# --- 1. Advanced Concurrency & Queue Control Setup ---

# The maximum number of requests allowed to access the GPU simultaneously.
# For a single GPU, this should almost always be 1.
MAX_CONCURRENT_GPU_REQUESTS = 1
semaphore = asyncio.Semaphore(MAX_CONCURRENT_GPU_REQUESTS)

# The maximum number of requests allowed to wait in the queue.
# If more requests arrive, they will be rejected immediately.
MAX_QUEUE_SIZE = 5

# How long (in seconds) a request is allowed to wait for the semaphore
# before it gives up and returns a timeout error.
REQUEST_TIMEOUT_SECONDS = 60  # 5 minutes


# --- 2. FastAPI Application and Middleware ---
app = FastAPI(
    title="DeepSeek OCR API (Production Grade)",
    description="An advanced local server for DeepSeek-OCR with queueing, timeouts, and load shedding.",
    version="1.1.0",
)


# --- NEW: A more accurate queue counter ---
class QueueManager:
    def __init__(self):
        self.waiting_requests = 0

    def get_queue_size(self):
        return self.waiting_requests

    async def __aenter__(self):
        # When entering the context, increment the waiting counter
        self.waiting_requests += 1
        if self.waiting_requests > MAX_QUEUE_SIZE:
            # If queue is too long, decrement counter and raise error immediately
            self.waiting_requests -= 1
            raise HTTPException(
                status_code=429,
                detail=f"Server is at maximum capacity with {self.waiting_requests} requests pending. Please try again later.",
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # When exiting the context, decrement the waiting counter
        self.waiting_requests -= 1


queue_manager = QueueManager()


# --- 3. Data Models (Unchanged) ---
class InputSource(BaseModel):
    type: str
    value: str


class OutputOptions(BaseModel):
    include_bounding_boxes: bool = False
    include_visualization: bool = False


class APIRequest(BaseModel):
    input_source: InputSource
    task_type: str
    prompt: str = None
    model_size: str = "Gundam"
    output_options: OutputOptions = Field(default_factory=OutputOptions)


# --- 4. API Endpoints ---
@app.post("/process")
async def process_endpoint(request: APIRequest):
    """
    Processes an OCR request with a semaphore lock, timeout, and error handling.
    """
    async with queue_manager:
        try:
            # Attempt to acquire the semaphore, but with a timeout.
            # If it takes longer than REQUEST_TIMEOUT_SECONDS to get the lock,
            # it will raise an asyncio.TimeoutError.
            async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
                async with semaphore:
                    print(
                        f"GPU access granted. Current queue size: {queue_manager.get_queue_size()}. Processing request..."
                    )

                    # Run the synchronous, blocking GPU code in a separate thread.
                    job_input = request.dict()
                    result = await asyncio.to_thread(process_image, job_input)

                    print("Processing finished. Releasing GPU access.")
                    return result

        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=408,  # Request Timeout
                detail=f"Request timed out after waiting for {REQUEST_TIMEOUT_SECONDS} seconds for an available GPU slot.",
            )
        except Exception as e:
            # Catch any other unexpected errors from the process_image function itself
            # (e.g., CUDA OOM, file errors, etc.)
            print(f"An unexpected error occurred during processing: {e}")
            raise HTTPException(
                status_code=503,  # Service Unavailable
                detail=f"An error occurred during model inference: {str(e)}",
            )


@app.get("/health")
async def health_check():
    """
    Provides a detailed health check of the service, including queue status.
    """
    # The semaphore's internal `_value` is 1 when idle, 0 when busy.
    # It's not a public API, but it's useful for monitoring.
    available_slots = semaphore._value

    return {
        "status": "ok",
        "gpu_status": "idle" if available_slots > 0 else "busy",
        "max_concurrent_gpu_tasks": MAX_CONCURRENT_GPU_REQUESTS,
        "available_gpu_slots": available_slots,
        "max_queue_size": MAX_QUEUE_SIZE,
        "current_queue_size": queue_manager.get_queue_size(),
    }


# --- 5. Server Launcher ---
if __name__ == "__main__":
    print("--> Starting FastAPI server with advanced queue management...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
