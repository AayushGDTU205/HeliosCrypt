import os
import google.generativeai as genai
import PIL.Image
from typing import List, Dict, Any, Tuple, Union, BinaryIO, Optional
from dotenv import load_dotenv
import io
import math
import json

# Load environment variables on module import
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# Configure Gemini API
genai.configure(api_key=API_KEY)

def load_image_from_path(image_path: str) -> PIL.Image.Image:
    """Load an image from a file path."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    return PIL.Image.open(image_path)

def load_image_from_bytes(image_bytes: Union[bytes, BinaryIO]) -> PIL.Image.Image:
    """Load an image from bytes or file-like object."""
    return PIL.Image.open(io.BytesIO(image_bytes) if isinstance(image_bytes, bytes) else image_bytes)

def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calculate distance between two latitude/longitude points in meters using the Haversine formula.
    
    Args:
        coord1: (latitude, longitude) of first point
        coord2: (latitude, longitude) of second point
        
    Returns:
        Distance in meters
    """
    # Earth radius in meters
    R = 6371000
    
    # Convert degrees to radians
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    
    # Differences
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Haversine formula
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

def verify_environmental_task(
    images: List[Union[str, bytes, BinaryIO, PIL.Image.Image]],
    coordinates: List[Tuple[float, float]],
    task_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify completion of environmental tasks (trash cleanup, afforestation, water body cleaning)
    using Gemini Vision API.
    
    Args:
        images: List of before/after images (can be paths, bytes, file-like objects, or PIL Images)
        coordinates: List of (latitude, longitude) tuples for each image
        task_type: Optional specification of the task type ('trash_cleanup', 'afforestation', 
                  'water_body_cleaning', or None for automatic detection)
    
    Returns:
        Dictionary with verification results
    """
    if len(images) != 2 or len(coordinates) != 2:
        raise ValueError("Exactly 2 images and 2 coordinate pairs are required for verification")
    
    # Calculate distance between coordinates
    distance = calculate_distance(coordinates[0], coordinates[1])
    
    # If distance is already >= 500m, we can return early
    if distance >= 500:
        return {
            "task_verified": False,
            "reason": f"Coordinates are {distance:.1f}m apart, which exceeds the 500m threshold",
            "distance": distance,
            "llm_analysis": None
        }
    
    # Convert all images to PIL.Image objects
    pil_images = []
    for img in images:
        if isinstance(img, str):
            pil_images.append(load_image_from_path(img))
        elif isinstance(img, (bytes, BinaryIO)):
            pil_images.append(load_image_from_bytes(img))
        elif isinstance(img, PIL.Image.Image):
            pil_images.append(img)
        else:
            raise TypeError(f"Unsupported image type: {type(img)}")
    
    # Preference order of models
    available_models = [
        'gemini-2.0-flash-thinking-exp-01-21',
        'gemini-2.0-flash',
        'gemini-1.5-pro',
    ]
    
    model = None
    model_error = None
    
    # Try each model until one works
    for model_name in available_models:
        try:
            model = genai.GenerativeModel(model_name)
            # Test with a simple generation to make sure it works
            _ = model.generate_content("Hello")
            print(f"Successfully connected to model: {model_name}")
            break
        except Exception as e:
            model_error = str(e)
            print(f"Failed to use model {model_name}: {e}")
            continue
    
    if model is None:
        raise RuntimeError(f"Could not find a working Gemini model. Last error: {model_error}")
    
    # Format coordinates for the prompt
    coord_str = "\n".join([f"Image {i+1}: Latitude {coords[0]}, Longitude {coords[1]}" 
                         for i, coords in enumerate(coordinates)])
    
    # Base system prompt for environmental task verification
    system_prompt = """You will be given latitudes, longitudes, and 2 images (before and after) related to an environmental task. 
    Your task is to verify the completion of the environmental task based on the images and the geographic coordinates provided.
    
    The environmental task could be one of the following:
    - Trash cleanup (removing litter, waste, garbage from an area)
    - Afforestation (planting trees or other vegetation)
    - Water body cleaning (removing pollution, trash, or contaminants from water)
    
    Verification rules:
    1. If the latitude and longitude vary by >= 500m, return false
    2. If the task has not been visibly completed based on the images, return false
    3. If the task has been completed and the geographic coordinates are within 500m, return true
    
    Analyze both images carefully, comparing the 'before' and 'after' states. Look for clear evidence of environmental improvement
    such as removed trash, newly planted vegetation, or cleaner water. Determine which type of environmental task was performed.
    
    Your response should be in JSON format with the following structure:
    {
      "verification_result": "true" or "false",
      "distance_between_points_meters": [calculated distance],
      "distance_acceptable": true or false,
      "task_type_detected": "trash cleanup" or "afforestation" or "water body cleaning",
      "evidence_of_completion": [detailed description of visual evidence between before/after images],
      "explanation": [detailed reasoning for your verification decision]
    }"""
    
    # Add task type guidance if specified
    task_guidance = ""
    if task_type:
        if task_type.lower() == "trash_cleanup":
            task_guidance = "\n\nThe user has specified this as a TRASH CLEANUP task. Look specifically for evidence of litter, garbage, or waste being removed between the before and after images."
        elif task_type.lower() == "afforestation":
            task_guidance = "\n\nThe user has specified this as an AFFORESTATION task. Look specifically for evidence of new plants, trees, or vegetation being added between the before and after images."
        elif task_type.lower() == "water_body_cleaning":
            task_guidance = "\n\nThe user has specified this as a WATER BODY CLEANING task. Look specifically for evidence of water pollution, trash, or contaminants being removed between the before and after images."
    
    # Combine system prompt with coordinates and task guidance
    full_prompt = f"{system_prompt}{task_guidance}\n\nImage Coordinates:\n{coord_str}\nDistance between points: {distance:.1f} meters"
    
    try:
        # Generate content with images and prompt
        response = model.generate_content([full_prompt, *pil_images])
        
        # Parse the JSON response
        try:
            # Try to extract JSON from the response
            response_text = response.text
            
            # Some LLMs wrap JSON in code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                # Handle case where code block is present but without json specifier
                json_str = response_text.split("```")[1].strip()
            else:
                # Find the first { and the last }
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start >= 0 and end > 0:
                    json_str = response_text[start:end]
                else:
                    json_str = response_text
                    
            # Parse the JSON
            parsed_response = json.loads(json_str)
            
            # Get verification result
            task_verified = parsed_response.get("verification_result") == "true"
            
            return {
                "task_verified": task_verified,
                "distance": distance,
                "llm_analysis": response.text,
                "parsed_result": parsed_response
            }
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            # Fallback to simple string check
            return {
                "task_verified": '"verification_result": "true"' in response.text,
                "distance": distance,
                "llm_analysis": response.text,
                "parse_error": str(e)
            }
            
    except Exception as e:
        print(f"Error generating content: {e}")
        raise

def main():
    """Example usage for local testing."""
    # Example inputs for environmental task verification
    before_image_path = "verification/waterbefore.jpeg"  # Path to image before task completion
    after_image_path = "verification/waterafter.jpeg"    # Path to image after task completion
    
    # Example coordinates (should be less than 500m apart for a valid task)
    coordinates = [(28.684629, 77.208069), (28.686425, 77.210112)]  # ~300m apart
    
    try:
        # Example 1: Let the model automatically detect the task type
        result = verify_environmental_task(
            images=[before_image_path, after_image_path],
            coordinates=coordinates
        )
        
        # Example 2: Specify a task type
        # result = verify_environmental_task(
        #     images=[before_image_path, after_image_path],
        #     coordinates=coordinates,
        #     task_type="trash_cleanup"  # or "afforestation" or "water_body_cleaning"
        # )
        
        if "parsed_result" in result:
            verification_status = "VERIFIED" if result["task_verified"] else "NOT VERIFIED"
            print(f"Verification Result: {verification_status}")
            print(f"Task Type: {result['parsed_result'].get('task_type_detected', 'Unknown')}")
            print(f"Distance between points: {result['distance']:.1f} meters")
            print(f"Evidence: {result['parsed_result'].get('evidence_of_completion', 'Not provided')}")
            print(f"Explanation: {result['parsed_result'].get('explanation', 'Not provided')}")
        else:
            print("Verification Result:", "VERIFIED" if result["task_verified"] else "NOT VERIFIED")
            print(f"Distance between points: {result['distance']:.1f} meters")
            if "parse_error" in result:
                print(f"Warning: Could not parse JSON response - {result['parse_error']}")
        
        print("\nDetailed Analysis:")
        print(result["llm_analysis"])
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()