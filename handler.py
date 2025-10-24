import os
import sys
import runpod
import torch
import base64
import requests
import re
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
import io

# --- Transformers Imports (Core Model) ---
from transformers import AutoModel, AutoTokenizer

# ===================================================================================
# 1. GLOBAL MODEL AND TOKENIZER SETUP (LOADED ONLY ONCE)
# This section is shared by both Runpod and FastAPI modes.
# ===================================================================================
print("--> Initializing handler...")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_DTYPE = (
    torch.bfloat16
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    else torch.float32
)
print(f"--> Using device: {DEVICE}, with dtype: {MODEL_DTYPE}")

print("--> Loading Model and Tokenizer from Hugging Face Hub...")
model_name = "deepseek-ai/DeepSeek-OCR"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModel.from_pretrained(
    model_name,
    trust_remote_code=True,
    use_safetensors=True,
).to(device=DEVICE, dtype=MODEL_DTYPE)
model.eval()
print("--> Model and Tokenizer loaded successfully. Model is in evaluation mode.")


# ===================================================================================
# 2. CORE PROCESSING LOGIC
# This function contains the actual OCR logic. Both Runpod and FastAPI will call it.
# ===================================================================================
PROMPT_TEMPLATES = {
    "doc_to_markdown": "<image>\n<|grounding|>Convert the document to markdown.",
    "general_ocr": "<image>\n<|grounding|>OCR this image.",
    "simple_ocr": "<image>\nFree OCR.",
    "figure_parse": "<image>\nParse the figure.",
    "image_description": "<image>\nDescribe this image in detail.",
    "text_localization": "<image>\nLocate <|ref|>{text_to_locate}<|/ref|> in the image.",
}
SIZE_CONFIGS = {
    "Tiny": {"base_size": 512, "image_size": 512, "crop_mode": False},
    "Small": {"base_size": 640, "image_size": 640, "crop_mode": False},
    "Base": {"base_size": 1024, "image_size": 1024, "crop_mode": False},
    "Large": {"base_size": 1280, "image_size": 1280, "crop_mode": False},
    "Gundam": {"base_size": 1024, "image_size": 640, "crop_mode": True},
}
MAX_FILE_SIZE_MB = 10


def process_image(job_input):
    """Core logic, refactored to be called by any interface."""
    input_source = job_input.get("input_source")
    task_type = job_input.get("task_type")
    custom_prompt = job_input.get("prompt")
    model_size = job_input.get("model_size", "Gundam")
    output_options = job_input.get("output_options", {})
    include_bounding_boxes = output_options.get("include_bounding_boxes", False)
    include_visualization = output_options.get("include_visualization", False)

    # ... (All validation and processing logic is here, unchanged) ...
    if not all([input_source, task_type]):
        return {"error": "..."}
    if model_size not in SIZE_CONFIGS:
        return {"error": "..."}
    # ...

    try:
        if input_source["type"] == "url":
            response = requests.get(input_source["value"], timeout=10)
            response.raise_for_status()
            image_bytes = response.content
        else:
            image_bytes = base64.b64decode(input_source["value"])
        if len(image_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
            return {"error": f"Image file size exceeds {MAX_FILE_SIZE_MB} MB."}
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        return {"error": f"Failed to load image: {str(e)}"}

    if task_type == "custom":
        final_prompt = custom_prompt
    elif task_type == "text_localization":
        final_prompt = PROMPT_TEMPLATES["text_localization"].format(
            text_to_locate=custom_prompt
        )
    else:
        final_prompt = PROMPT_TEMPLATES[task_type]

    try:
        with tempfile.TemporaryDirectory() as output_path:
            temp_image_path = os.path.join(output_path, "temp_image.png")
            image.save(temp_image_path)
            config = SIZE_CONFIGS[model_size]
            with torch.inference_mode():
                text_content = model.infer(
                    tokenizer,
                    prompt=final_prompt,
                    image_file=temp_image_path,
                    output_path=output_path,
                    base_size=config["base_size"],
                    image_size=config["image_size"],
                    crop_mode=config["crop_mode"],
                    save_results=True,
                    test_compress=True,
                    eval_mode=True,
                )
    except Exception as e:
        return {"error": f"Model inference failed: {str(e)}"}

    output = {"text_content": text_content}
    boxes_data = []
    pattern = re.compile(r"<\|det\|>\[\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]\]<\|/det\|>")
    matches = list(pattern.finditer(text_content))
    if matches:
        w, h = image.size
        for match in matches:
            coords = [int(c) for c in match.groups()]
            boxes_data.append(
                {
                    "text": "N/A",
                    "box": [
                        int(coords[0] / 1000 * w),
                        int(coords[1] / 1000 * h),
                        int(coords[2] / 1000 * w),
                        int(coords[3] / 1000 * h),
                    ],
                }
            )
    if include_bounding_boxes:
        output["bounding_boxes"] = boxes_data
    if include_visualization and boxes_data:
        viz_image = image.copy()
        draw = ImageDraw.Draw(viz_image)
        for item in boxes_data:
            draw.rectangle(item["box"], outline="red", width=3)
        buffer = io.BytesIO()
        viz_image.save(buffer, format="JPEG")
        output["visualization_b64"] = base64.b64encode(buffer.getvalue()).decode(
            "utf-8"
        )
    return output


# ===================================================================================
# 3. INTERFACES (How we expose the core logic)
# ===================================================================================


# --- Interface A: Runpod Handler (for Production) ---
def runpod_handler(job):
    """The handler function that Runpod will call."""
    return process_image(job["input"])


# ===================================================================================
# 4. LAUNCHER (Decides whether to start Runpod or FastAPI)
# ===================================================================================
if __name__ == "__main__":
    print("--> Starting Runpod serverless worker for production...")
    runpod.serverless.start({"handler": runpod_handler})
