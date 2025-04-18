import os
import tempfile
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import io
from PIL import Image
from typing import List, Tuple, Dict, Any, Optional

from verification import verify_environmental_task, calculate_distance #local code.

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "ok", "message": "Environmental verification service is running"}), 200

@app.route('/api/verify', methods=['POST'])
def verify_task():
    """
    API endpoint to verify environmental tasks.
    
    Expected JSON body:
    {
        "images": {
            "before": "base64_encoded_image_string",
            "after": "base64_encoded_image_string"
        },
        "coordinates": {
            "before": [latitude, longitude],
            "after": [latitude, longitude]
        },
        "task_type": "trash_cleanup" | "afforestation" | "water_body_cleaning" | null
    }
    """
    try:
        # Parse request data
        data = request.json
        
        if not data or 'images' not in data or 'coordinates' not in data:
            return jsonify({
                "error": "Missing required fields",
                "details": "Request must include 'images' and 'coordinates'"
            }), 400
            
        # Extract images
        try:
            before_image_b64 = data['images'].get('before')
            after_image_b64 = data['images'].get('after')
            
            if not before_image_b64 or not after_image_b64:
                return jsonify({
                    "error": "Missing images",
                    "details": "Both 'before' and 'after' images are required"
                }), 400
                
            # Decode base64 images to PIL Images
            before_image = decode_base64_to_image(before_image_b64)
            after_image = decode_base64_to_image(after_image_b64)
            
        except Exception as e:
            return jsonify({
                "error": "Invalid image data",
                "details": str(e)
            }), 400
            
        # Extract coordinates
        try:
            before_coords = tuple(data['coordinates'].get('before', [0, 0]))
            after_coords = tuple(data['coordinates'].get('after', [0, 0]))
            
            if not all(isinstance(c, (int, float)) for c in before_coords + after_coords):
                return jsonify({
                    "error": "Invalid coordinates",
                    "details": "Coordinates must be numeric values"
                }), 400
                
        except Exception as e:
            return jsonify({
                "error": "Invalid coordinates data",
                "details": str(e)
            }), 400
            
        # Extract optional task_type
        task_type = data.get('task_type')
        
        # Call verification function
        verification_result = verify_environmental_task(
            images=[before_image, after_image],
            coordinates=[before_coords, after_coords],
            task_type=task_type
        )
        
        # Return the result
        return jsonify({
            "success": True,
            "result": verification_result
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Server error",
            "details": str(e)
        }), 500

def decode_base64_to_image(base64_str: str) -> Image.Image:
    """Convert a base64 string to a PIL Image."""
    # Remove data URL prefix if present
    if ',' in base64_str:
        base64_str = base64_str.split(',', 1)[1]
        
    image_data = base64.b64decode(base64_str)
    image = Image.open(io.BytesIO(image_data))
    return image

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) # we're running this on port number 5000.
    
    app.run(host='0.0.0.0', port=port, debug=False)