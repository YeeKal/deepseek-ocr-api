# DeepSeek OCR vLLM Configuration
# This file contains configuration for the DeepSeek OCR model with vLLM

# Model configuration - Using Gundam mode as default
BASE_SIZE = 1024
IMAGE_SIZE = 640
CROP_MODE = True
MIN_CROPS = 2
MAX_CROPS = 6  # max:9; If your GPU memory is small, it is recommended to set it to 6.
MAX_CONCURRENCY = 100  # If you have limited GPU memory, lower the concurrency count.
NUM_WORKERS = 64  # image pre-process (resize/padding) workers 
PRINT_NUM_VIS_TOKENS = False
SKIP_REPEAT = True

# Model paths
# For RunPod: /runpod-volume (persistent network volume) is used for model caching
# For local: current directory or ./models is used
# The model_loader.py will automatically handle the path resolution
MODEL_PATH = '/runpod-volume/models'  # Default path, will be auto-adjusted by model_loader.py
MODEL_ID = 'deepseek-ai/DeepSeek-OCR'  # HuggingFace model ID for automatic download

# Default prompt for OCR
PROMPT = '<image>\n<|grounding|>Convert the document to markdown.'

# Commonly used prompts:
# Document OCR: '<image>\n<|grounding|>Convert the document to markdown.'
# General OCR: '<image>\n<|grounding|>OCR this image.'
# Simple OCR: '<image>\nFree OCR.'
# Figure parsing: '<image>\nParse the figure.'
# Image description: '<image>\nDescribe this image in detail.'
# Text localization: '<image>\nLocate <|ref|>{text_to_locate}<|/ref|> in the image.'

# Task type configurations
PROMPT_TEMPLATES = {
    "doc_to_markdown": "<image>\n<|grounding|>Convert the document to markdown.",
    "general_ocr": "<image>\n<|grounding|>OCR this image.",
    "simple_ocr": "<image>\nFree OCR.",
    "figure_parse": "<image>\nParse the figure.",
    "image_description": "<image>\nDescribe this image in detail.",
    "text_localization": "<image>\nLocate <|ref|>{text_to_locate}<|/ref|> in the image.",
}

# Model size configurations
SIZE_CONFIGS = {
    "Tiny": {
        "base_size": 512,
        "image_size": 512,
        "crop_mode": False,
    },
    "Small": {
        "base_size": 640,
        "image_size": 640,
        "crop_mode": False,
    },
    "Base": {
        "base_size": 1024,
        "image_size": 1024,
        "crop_mode": False,
    },
    "Large": {
        "base_size": 1280,
        "image_size": 1280,
        "crop_mode": False,
    },
    "Gundam": {
        "base_size": 1024,
        "image_size": 640,
        "crop_mode": True,
    },
}

# File size limit
MAX_FILE_SIZE_MB = 10