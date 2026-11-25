from flask import Flask, jsonify, Response, request
from flask_cors import CORS
import cv2
import numpy as np
from twophase import solve

app = Flask(__name__)
CORS(app) 

# Initialize the webcam globally
camera = cv2.VideoCapture(0)
current_cubes_global = [] # This will hold the live JSON data

def classify_color(bgr_pixel):
    hsv_pixel = cv2.cvtColor(np.uint8([[bgr_pixel]]), cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = hsv_pixel

    if s < 60 and v > 150: return "White"
    if (h >= 0 and h <= 2) or (h >= 165 and h <= 180): return "Red"
    elif 2 < h <= 25: return "Orange"
    elif 25 < h <= 40: return "Yellow"
    elif 40 < h <= 85: return "Green"
    elif 85 < h <= 135: return "Blue"
    else: return "Unknown"

def generate_frames():
    global current_cubes_global
    
    while True:
        success, frame = camera.read()
        if not success:
            break
            
        #frame = cv2.flip(frame, 1) # Mirror effect
        
        image_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
        blurred = cv2.GaussianBlur(image_gray, (5, 5), 0)
        mask = cv2.Canny(blurred, 20, 100) 
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated_mask = cv2.dilate(mask, kernel, iterations=2) 
        contours, _ = cv2.findContours(dilated_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE) 
        
        contour_image = frame.copy()
        detected_cubes = []
        accepted_centers = [] 

        for contour in contours:
            area = cv2.contourArea(contour)
            if 1000 < area < 150000: 
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                extent = float(area) / (w * h)
                
                if 0.75 <= aspect_ratio <= 1.25 and extent > 0.65:
                    center_x, center_y = x + (w // 2), y + (h // 2)
                    
                    is_duplicate = any(((center_x - cx)**2 + (center_y - cy)**2)**0.5 < 20 for cx, cy in accepted_centers)
                    if is_duplicate: continue
                    
                    accepted_centers.append((center_x, center_y))
                    
                    patch_radius = 5 
                    y_start, y_end = max(0, center_y - patch_radius), min(frame.shape[0], center_y + patch_radius)
                    x_start, x_end = max(0, center_x - patch_radius), min(frame.shape[1], center_x + patch_radius)
                    
                    avg_bgr = np.mean(frame[y_start:y_end, x_start:x_end], axis=(0, 1))
                    color_name = classify_color(avg_bgr)
                    
                    detected_cubes.append({
                        "color": color_name,
                        "center_coordinates": {"x": int(center_x), "y": int(center_y)}
                    })
                    
                    cv2.rectangle(contour_image, (x, y), (x + w, y + h), (0, 255, 0), 4)
                    cv2.putText(contour_image, color_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Update the global variable so the Scan button can grab it instantly
        current_cubes_global = detected_cubes
        
        # Encode the frame as a JPEG
        ret, buffer = cv2.imencode('.jpg', contour_image)
        frame = buffer.tobytes()
        
        # Yield the frame to the Flask HTTP stream
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# --- ROUTES ---

@app.route('/video_feed')
def video_feed():
    """This route streams the live OpenCV video to your HTML img tag."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/cube-colors', methods=['GET'])
def get_cube_colors():
    """This route triggers when you click 'Scan Current View'."""
    global current_cubes_global
    detected_cubes = current_cubes_global
    
    if not detected_cubes or len(detected_cubes) < 9:
        return jsonify({"error": f"Only detected {len(detected_cubes)} blocks. Please hold the cube clearly in frame."}), 400

    # Sort cubes Top-to-Bottom, Left-to-Right
    cubes_sorted_y = sorted(detected_cubes, key=lambda c: c['center_coordinates']['y'])
    rows = []
    current_row = [cubes_sorted_y[0]]
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

    # Return exactly the first 9 sorted blocks
    return jsonify(final_sorted_cubes[:9])


@app.route('/api/solve', methods=['POST'])
def solve_cube_api():
    data = request.json
    cube_string = data.get("cube_string")
    
    if not cube_string or len(cube_string) != 54:
        return jsonify({"error": "Invalid cube string."}), 400
        
    try:
        solution = solve(cube_string)
        moves = solution.split(" ")
        return jsonify({"moves": moves})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    # use_reloader=False prevents the webcam from crashing if you save this file while running
    app.run(debug=True, port=5000, use_reloader=False)