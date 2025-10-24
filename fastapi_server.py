from fastapi import FastAPI
from pydantic import BaseModel, Field
import uvicorn

from handler import process_image


# --- Interface B: FastAPI Server (for Local Testing) ---
app = FastAPI()


class InputSource(BaseModel):
    type: str = Field(..., description="Input type, 'url' or 'base64'")
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


@app.post("/process")
async def process_endpoint(request: APIRequest):
    """The main processing endpoint for local testing."""
    # Convert the Pydantic model to the dict format our core logic expects
    job_input = request.dict()
    return process_image(job_input)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Server is ready to accept requests."}


# ===================================================================================
# 4. LAUNCHER (Decides whether to start Runpod or FastAPI)
# ===================================================================================
if __name__ == "__main__":
    print("--> Starting FastAPI server for local testing...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
