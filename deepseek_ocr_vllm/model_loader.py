"""
Model initialization module for DeepSeek OCR with vLLM
Handles model downloading, caching, and initialization
"""
import os
import torch
from huggingface_hub import snapshot_download
from vllm import LLM, SamplingParams
from vllm.model_executor.models.registry import ModelRegistry

from .config import MODEL_PATH, MODEL_ID
from .process.ngram_norepeat import NoRepeatNGramLogitsProcessor


def setup_cuda_environment():
    """Set up CUDA environment variables based on CUDA version"""
    cuda_version = torch.version.cuda

    if cuda_version:
        major, minor = cuda_version.split('.')[:2]
        cuda_major = int(major)

        # Set VLLM version for compatibility
        os.environ['VLLM_USE_V1'] = '0'

        # Set CUDA_VISIBLE_DEVICES to 0 by default if not set
        if "CUDA_VISIBLE_DEVICES" not in os.environ:
            os.environ["CUDA_VISIBLE_DEVICES"] = '0'

        # Only set TRITON_PTXAS_PATH for CUDA 11.x
        if cuda_major == 11:
            cuda_path = f"/usr/local/cuda-{cuda_version}/bin/ptxas"
            if os.path.exists(cuda_path):
                os.environ["TRITON_PTXAS_PATH"] = cuda_path

    print(f"CUDA version: {cuda_version}")
    print(f"GPU available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU device: {torch.cuda.get_device_name(0)}")
        print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")


def download_model_if_needed():
    """Download model if not exists in the specified path"""
    # Ensure MODEL_PATH is /runpod-volume/models for RunPod deployment
    # or use local cache path for local development
    actual_model_path = MODEL_PATH

    # If MODEL_PATH is a HuggingFace model ID, convert to local path
    if '/' in MODEL_PATH and not MODEL_PATH.startswith('/'):
        # Use local cache directory in the current directory or /runpod-volume
        if os.path.exists('/runpod-volume'):
            actual_model_path = '/runpod-volume/models'
        else:
            actual_model_path = './models'
    else:
        actual_model_path = MODEL_PATH

    # Create directory if it doesn't exist
    if not os.path.exists(actual_model_path):
        print(f"Creating model directory: {actual_model_path}")
        os.makedirs(actual_model_path, exist_ok=True)

    # Check if model files exist (both safetensors and bin formats)
    has_model_files = False
    try:
        has_model_files = any(
            f.endswith((".bin", ".safetensors", ".pth", ".ckpt")) or
            f.startswith("config.json") or
            f.startswith("tokenizer.json")
            for f in os.listdir(actual_model_path) if os.path.isfile(os.path.join(actual_model_path, f))
        )
    except FileNotFoundError:
        has_model_files = False

    if not has_model_files:
        print(f"Downloading model {MODEL_ID} to {actual_model_path}...")
        try:
            snapshot_download(
                repo_id=MODEL_ID,
                local_dir=actual_model_path,
                local_dir_use_symlinks=False,
                resume_download=True,
            )
            print("Model download completed!")
        except Exception as e:
            print(f"Error downloading model: {e}")
            raise
    else:
        print(f"Model already cached at {actual_model_path}")

    return actual_model_path


def initialize_vllm_engine():
    """Initialize vLLM engine with DeepSeek OCR model"""
    print("--> Initializing vLLM engine for DeepSeek OCR...")

    # Set up CUDA environment
    setup_cuda_environment()

    # Register the custom model
    from .deepseek_ocr import DeepseekOCRForCausalLM
    ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)

    # Get model path
    model_path = download_model_if_needed()

    # Initialize vLLM engine
    llm = LLM(
        model=model_path,
        trust_remote_code=True,
        hf_overrides={"architectures": ["DeepseekOCRForCausalLM"]},
        enable_prefix_caching=False,
        mm_processor_cache_gb=0,
        dtype=torch.bfloat16,
        gpu_memory_utilization=0.9,
        max_model_len=8192,
        tensor_parallel_size=1,
        block_size=256,
        enforce_eager=False,
    )
    
    # Initialize sampling parameters with n-gram processor
    logits_processors = [
        NoRepeatNGramLogitsProcessor(
            ngram_size=30, 
            window_size=90, 
            whitelist_token_ids={128821, 128822}  # whitelist: <td>, </td>
        )
    ]
    
    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=8192,
        logits_processors=logits_processors,
        skip_special_tokens=False,
    )
    
    print("--> vLLM engine initialized successfully!")
    return llm, sampling_params


def get_ocr_processor():
    """Get the OCR processor for image preprocessing"""
    from .process.image_process import DeepseekOCRProcessor
    return DeepseekOCRProcessor()


# Global variables for model components
_llm_engine = None
_sampling_params = None
_ocr_processor = None


def get_model_components():
    """Get or initialize model components (lazy loading)"""
    global _llm_engine, _sampling_params, _ocr_processor
    
    if _llm_engine is None:
        download_model_if_needed()
        _llm_engine, _sampling_params = initialize_vllm_engine()
        _ocr_processor = get_ocr_processor()
    
    return _llm_engine, _sampling_params, _ocr_processor