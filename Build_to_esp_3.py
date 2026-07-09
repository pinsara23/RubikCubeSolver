from flask import Flask, jsonify, Response, request
from flask_cors import CORS
import cv2
import numpy as np
from twophase import solve
import serial
import time
import threading

app = Flask(__name__)
CORS(app) 

# ==========================================
# --- USB SERIAL SETUP ---
# ==========================================
COM_PORT = 'COM8'  # Check Arduino IDE if this changes
BAUD_RATE = 115200

print(f"Connecting to robot on {COM_PORT}...")
try:
    esp32 = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) 
    print("SUCCESS: USB Robot Connected!")
except serial.SerialException:
    esp32 = None
    print(f"WARNING: Could not connect to {COM_PORT}.")

# ==========================================
# --- HARDWARE DICTIONARY (RACK & PINION) ---
# ==========================================
CALIB = {
    # THE BLUE MOTORS (Rotators: 3-point calibration for imperfect servos)
    # You must find the exact physical 90-degree turn numbers for each!
    "rotF_center": 90, "rotF_cw": 180, "rotF_ccw": 0,
    "rotB_center": 90, "rotB_cw": 180, "rotB_ccw": 0,
    "rotL_center": 80, "rotL_cw": 170, "rotL_ccw": -8,
    "rotR_center": 85, "rotR_cw": 175, "rotR_ccw": -5,  
    
    # THE BOTTOM MOTORS (Sliders: pushing/pulling the linear track)
    # retract = pulled safely away from cube | extend = flush against cube
    "gripF_retract": 50, "gripF_extend": 90,
    "gripB_retract": 50, "gripB_extend": 90,
    "gripL_retract": 40, "gripL_extend": 80, 
    "gripR_retract": 45, "gripR_extend": 85   
}

# ==========================================
# --- ROBOT KINEMATICS ---
# ==========================================
def move_servo(motor_name, angle):
    if esp32 and esp32.is_open:
        esp32.write(f"{motor_name}:{angle}\n".encode('utf-8'))
        time.sleep(0.3) # Wait for physical movement

def flip_cube_forward():
    """Tumbles the entire cube forward by 90 degrees (U face becomes F face)"""
    print(" -> Tumbling Cube Forward")
    
    # 1. Slide Left and Right tracks back so cube can spin
    move_servo("gripL", CALIB["gripL_retract"])
    move_servo("gripR", CALIB["gripR_retract"])
    time.sleep(0.2)
    
    # 2. Twist Front and Back blue motors 90 degrees to tumble the whole cube
    # (Note: Check physically if cw/ccw tumble it the correct direction)
    move_servo("rotF", CALIB["rotF_ccw"]) 
    move_servo("rotB", CALIB["rotB_cw"])  
    time.sleep(0.5)
    
    # 3. Slide Left and Right tracks forward to lock the cube in its new position
    move_servo("gripL", CALIB["gripL_extend"])
    move_servo("gripR", CALIB["gripR_extend"])
    time.sleep(0.2)
    
    # 4. Slide Front and Back tracks back (letting go of the old faces)
    move_servo("gripF", CALIB["gripF_retract"])
    move_servo("gripB", CALIB["gripB_retract"])
    time.sleep(0.2)
    
    # 5. Untwist the empty Front and Back cups back to standard center
    move_servo("rotF", CALIB["rotF_center"])
    move_servo("rotB", CALIB["rotB_center"])
    time.sleep(0.4)
    
    # 6. Slide Front and Back tracks forward to grab the new faces
    move_servo("gripF", CALIB["gripF_extend"])
    move_servo("gripB", CALIB["gripB_extend"])
    time.sleep(0.2)

def execute_face_turn(motor_name, kociemba_move):
    """Executes a single face turn using the rack and pinion mechanism"""
    grip_name = motor_name.replace("rot", "grip")
    
    center_pos = CALIB[f"{motor_name}_center"]
    cw_pos     = CALIB[f"{motor_name}_cw"]
    ccw_pos    = CALIB[f"{motor_name}_ccw"]

    # 1. Slide track forward to lock cup onto cube
    move_servo(grip_name, CALIB[f"{grip_name}_extend"])
    time.sleep(0.2)

    # 2. Twist the blue motor (turning only the face)
    if len(kociemba_move) == 1:
        move_servo(motor_name, cw_pos)
    elif kociemba_move[1] == "'":
        move_servo(motor_name, ccw_pos)
    elif kociemba_move[1] == "2":
        move_servo(motor_name, cw_pos) 
        time.sleep(0.3)
        move_servo(motor_name, ccw_pos) 
    
    time.sleep(0.2)
    
    # 3. Slide track backward, pulling cup off the cube
    move_servo(grip_name, CALIB[f"{grip_name}_retract"])
    time.sleep(0.3)
    
    # 4. Untwist the empty cup back to center
    move_servo(motor_name, center_pos) 
    time.sleep(0.3)
    
    # 5. Slide track forward to lock cube for the next arm's move
    move_servo(grip_name, CALIB[f"{grip_name}_extend"])
    time.sleep(0.2)

def run_robot_motors(moves_array):
    if esp32 and esp32.is_open:
        print("\n--- INITIATING SOLVE SEQUENCE ---")
        for move in moves_array:
            print(f"Executing: {move}")
            face = move[0]
            
            # Map Kociemba notation to the physical arms
            if face == 'F': execute_face_turn("rotF", move)
            elif face == 'B': execute_face_turn("rotB", move)
            elif face == 'L': execute_face_turn("rotL", move)
            elif face == 'R': execute_face_turn("rotR", move)
            elif face in ['U', 'D']:
                # Tumble the cube so U/D face the F/B arms
                flip_cube_forward()
                if face == 'U': execute_face_turn("rotF", move)
                else: execute_face_turn("rotB", move)
            
            time.sleep(0.5) # Vibration buffer between moves
        print("--- SOLVE COMPLETE ---\n")

# ==========================================
# --- OPENCV SCANNER ---
# ==========================================
camera = cv2.VideoCapture(0)
current_cubes_global = [] 

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
        if not success: break
            
        # Standardize physical camera orientation (Mirror Flip)
        #frame = cv2.flip(frame, 1) 
        
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

        current_cubes_global = detected_cubes
        ret, buffer = cv2.imencode('.jpg', contour_image)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# ==========================================
# --- API ROUTES ---
# ==========================================
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/cube-colors', methods=['GET'])
def get_cube_colors():
    global current_cubes_global
    detected_cubes = current_cubes_global
    
    if not detected_cubes or len(detected_cubes) < 9:
        return jsonify({"error": f"Detected {len(detected_cubes)}/9 blocks."}), 400

    cubes_sorted_y = sorted(detected_cubes, key=lambda c: c['center_coordinates']['y'])
    rows = []
    current_row = [cubes_sorted_y[0]]
    for cube in cubes_sorted_y[1:]:
        if abs(cube['center_coordinates']['y'] - current_row[0]['center_coordinates']['y']) < 40:
            current_row.append(cube)
        else:
            rows.append(current_row)
            current_row = [cube]
    rows.append(current_row)

    final_sorted_cubes = []
    block_number = 1
    for row in rows:
        for cube in sorted(row, key=lambda c: c['center_coordinates']['x']):
            cube['id'] = block_number
            final_sorted_cubes.append(cube)
            block_number += 1

    return jsonify(final_sorted_cubes[:9])

@app.route('/api/solve', methods=['POST'])
def solve_cube_api():
    cube_string = request.json.get("cube_string")
    if not cube_string or len(cube_string) != 54:
        return jsonify({"error": "Invalid cube string."}), 400
        
    try:
        moves = solve(cube_string).split(" ")
        threading.Thread(target=run_robot_motors, args=(moves,)).start()
        return jsonify({"moves": moves})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)