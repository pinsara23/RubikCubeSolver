from flask import Flask, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from twophase import solve
from flask import request

# Initialize the Flask App
app = Flask(__name__)
CORS(app) # This allows your HTML frontend to talk to this Python backend

def classify_color(bgr_pixel):
    """Converts a BGR pixel to HSV and classifies it into a string name."""
    hsv_pixel = cv2.cvtColor(np.uint8([[bgr_pixel]]), cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = hsv_pixel

    if s < 60 and v > 150: return "White"
    if (h >= 0 and h <= 2) or (h >= 165 and h <= 180): return "Red"
    elif 2 < h <= 25: return "Orange"
    elif 25 < h <= 40: return "Yellow"
    elif 40 < h <= 85: return "Green"
    elif 85 < h <= 135: return "Blue"
    else: return "Unknown"

# Define the API endpoint
@app.route('/api/cube-colors', methods=['GET'])
def get_cube_colors():
    # 1. Read the image (Ensure 'rub.jpeg' is in the same folder as app.py)
    image = cv2.imread("rubbt3.jpeg") 
    
    if image is None:
        return jsonify({"error": "Image not found"}), 404

    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) 
    blurred = cv2.GaussianBlur(image_gray, (5, 5), 0)
    
    mask = cv2.Canny(blurred, 20, 100) 
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated_mask = cv2.dilate(mask, kernel, iterations=2) 
    
    contours, _ = cv2.findContours(dilated_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE) 
    
    detected_cubes = []
    accepted_centers = [] 

    # 2. Extract Data
    for contour in contours:
        area = cv2.contourArea(contour)
        if 1000 < area < 150000: 
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            extent = float(area) / (w * h)
            
            if 0.75 <= aspect_ratio <= 1.25 and extent > 0.65:
                center_x = x + (w // 2)
                center_y = y + (h // 2)
                
                is_duplicate = any(((center_x - cx)**2 + (center_y - cy)**2)**0.5 < 20 for cx, cy in accepted_centers)
                if is_duplicate: continue
                
                accepted_centers.append((center_x, center_y))
                
                patch_radius = 5 
                y_start, y_end = max(0, center_y - patch_radius), min(image.shape[0], center_y + patch_radius)
                x_start, x_end = max(0, center_x - patch_radius), min(image.shape[1], center_x + patch_radius)
                
                avg_bgr = np.mean(image[y_start:y_end, x_start:x_end], axis=(0, 1))
                color_name = classify_color(avg_bgr)
                
                detected_cubes.append({
                    "color": color_name,
                    "center_coordinates": {"x": int(center_x), "y": int(center_y)}
                })

    # 3. Spatial Sorting (Group by rows, then sort Left-to-Right)
    if not detected_cubes:
        return jsonify([])

    cubes_sorted_y = sorted(detected_cubes, key=lambda c: c['center_coordinates']['y'])
    rows = []
    current_row = [cubes_sorted_y[0]]
    # Using a fixed tolerance (approx half a block) for safety
    y_tolerance = 40 

    for cube in cubes_sorted_y[1:]:
        if abs(cube['center_coordinates']['y'] - current_row[0]['center_coordinates']['y']) < y_tolerance:
            current_row.append(cube)
        else:
            rows.append(current_row)
            current_row = [cube]
    rows.append(current_row)

    final_sorted_cubes = []
    block_number = 1
    for row in rows:
        row_sorted_x = sorted(row, key=lambda c: c['center_coordinates']['x'])
        for cube in row_sorted_x:
            cube['id'] = block_number
            final_sorted_cubes.append(cube)
            block_number += 1

    # 4. Return the JSON array to the frontend
    return jsonify(final_sorted_cubes)


@app.route('/api/solve', methods=['POST'])
def solve_cube_api():
    # Get the 54-character string from the frontend
    data = request.json
    cube_string = data.get("cube_string")
    
    if not cube_string or len(cube_string) != 54:
        return jsonify({"error": "Invalid cube string. Must be 54 characters."}), 400
        
    try:
        # Ask Kociemba to solve it
        solution = solve(cube_string)
        # Convert "U R2 F B'" into ["U", "R2", "F", "B'"]
        moves = solution.split(" ")
        return jsonify({"moves": moves})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    


if __name__ == '__main__':
    # Run the server on port 5000
    app.run(debug=True, port=5000)


# @app.route('/api/solve', methods=['POST'])
# def solve_cube_api():
#     data = request.json
#     cube_string = data.get("cube_string")
    
#     if not cube_string or len(cube_string) != 54:
#         return jsonify({"error": "Invalid cube string."}), 400
        
#     try:
#         # 1. Calculate the solution
#         solution = solve(cube_string)
#         moves = solution.split(" ")
        
#         # ==========================================
#         # --- NEW: SEND COMMANDS TO ESP32 ROBOT ---
#         # ==========================================
#         # IMPORTANT: Change this to the exact IP address of your ESP32!
#         esp32_url = "http://192.168.1.150/execute" 
        
#         try:
#             # Send the JSON payload to the ESP32. 
#             # We use a 2-second timeout so your Flask app doesn't freeze if the robot is turned off!
#             print(f"Sending {len(moves)} moves to Robot...")
#             robot_response = requests.post(esp32_url, json={"moves": moves}, timeout=2)
            
#             if robot_response.status_code == 200:
#                 print("Robot received the commands successfully!")
#             else:
#                 print(f"Robot returned an error: {robot_response.status_code}")
                
#         except requests.exceptions.RequestException as e:
#             print(f"WARNING: Could not reach the ESP32 robot. Is it powered on? (Error: {e})")
#         # ==========================================
        
#         # 2. Return the moves to the 3D Frontend so it can animate
#         return jsonify({"moves": moves})
        
#     except ValueError as e:
#         return jsonify({"error": str(e)}), 400