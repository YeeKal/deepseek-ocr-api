"""
Image processing utilities for DeepSeek OCR
Handles image preprocessing, bounding box extraction, and coordinate conversion
"""
import re
import io
import base64
from typing import List, Dict, Tuple, Optional
import requests
from PIL import Image, ImageDraw

from .config import MAX_FILE_SIZE_MB


def load_image_from_source(input_source: Dict) -> Optional[Image.Image]:
    """
    Load image from URL or base64 data
    
    Args:
        input_source: Dictionary with 'type' and 'value' keys
        
    Returns:
        PIL Image or None if loading fails
    """
    try:
        if input_source["type"] == "url":
            resp = requests.get(input_source["value"], timeout=10)
            resp.raise_for_status()
            image_bytes = resp.content
        else:
            image_bytes = base64.b64decode(input_source["value"])
            
        if len(image_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
            return None
            
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return image
    except Exception as e:
        print(f"Image load failed: {str(e)}")
        return None


def extract_bounding_boxes(text: str, image_size: Tuple[int, int]) -> List[Dict]:
    """
    Extract bounding boxes from OCR text output along with text content

    Args:
        text: OCR text output containing bounding box annotations
        image_size: Tuple of (width, height) of the original image

    Returns:
        List of dictionaries containing bounding box information with text content
    """
    # Pattern to match the full ref-det structure: <|ref|>text<|/ref|><|det|>[[x1, y1, x2, y2]]<|/det|>
    pattern = re.compile(r'<\|ref\|>(.*?)<\|/ref\|><\|det\|\>\[\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]\]<\|/det\|>')
    matches = pattern.finditer(text)

    w_orig, h_orig = image_size
    all_boxes = []

    for match in matches:
        text_content = match.group(1).strip()
        x1, y1, x2, y2 = map(int, match.groups()[1:])

        # Convert from normalized coordinates (0-999) to pixel coordinates
        box = [
            int(x1 / 999 * w_orig),
            int(y1 / 999 * h_orig),
            int(x2 / 999 * w_orig),
            int(y2 / 999 * h_orig),
        ]

        all_boxes.append({
            "text": text_content,
            "box": box,
        })

    return all_boxes


def create_visualization(image: Image.Image, bounding_boxes: List[Dict]) -> str:
    """
    Create visualization with bounding boxes drawn on the image
    
    Args:
        image: PIL Image
        bounding_boxes: List of bounding box dictionaries
        
    Returns:
        Base64 encoded JPEG string of the visualization
    """
    if not bounding_boxes:
        return ""
    
    viz_img = image.copy()
    draw = ImageDraw.Draw(viz_img)
    
    for bbox_info in bounding_boxes:
        box = bbox_info["box"]
        draw.rectangle(box, outline="red", width=3)
    
    buffer = io.BytesIO()
    viz_img.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def extract_text_with_refs(text: str) -> str:
    """
    Clean up OCR text by removing reference markers and extracting clean text
    
    Args:
        text: Raw OCR output
        
    Returns:
        Cleaned text string
    """
    # Remove reference markers like <|ref|>text<|/ref|>
    text = re.sub(r'<\|ref\|>(.*?)<\|/ref\|>', r'\1', text)
    
    # Remove detection markers
    text = re.sub(r'<\|det\|>\[\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]\]<\|/det\|>', '', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def re_match(text):
    """
    Parse text for image and other references (for compatibility with official code)
    
    Args:
        text: OCR output text
        
    Returns:
        Tuple of (all_matches, image_matches, other_matches)
    """
    pattern = r'(<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>)'
    matches = re.findall(pattern, text, re.DOTALL)

    matches_image = []
    matches_other = []
    for a_match in matches:
        if '<|ref|>image<|/ref|>' in a_match[0]:
            matches_image.append(a_match[0])
        else:
            matches_other.append(a_match[0])
    return matches, matches_image, matches_other


def extract_coordinates_and_label(ref_text, image_width, image_height):
    """
    Extract coordinates and label from reference text
    
    Args:
        ref_text: Reference text tuple
        image_width: Width of the original image
        image_height: Height of the original image
        
    Returns:
        Tuple of (label_type, coordinates_list) or None
    """
    try:
        label_type = ref_text[1]
        cor_list = eval(ref_text[2])
    except Exception as e:
        print(e)
        return None

    return (label_type, cor_list)