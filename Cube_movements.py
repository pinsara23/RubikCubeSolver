import time
import serial
import keyboard

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


calibration_data = {
    "rotF_center": 92, "rotF_cw": 182, "rotF_ccw": 2,
    "rotB_center": 90, "rotB_cw": 180, "rotB_ccw": 0,
    "rotL_center": 91, "rotL_cw": 183, "rotL_ccw": 3,
    "rotR_center": 81, "rotR_cw": 178, "rotR_ccw": -7,

    "gripF_retract": 0, "gripF_extend": 93,
    "gripB_retract": -5, "gripB_extend": 73,
    "gripL_retract": -10 , "gripL_extend": 50, 
    "gripR_retract": 0, "gripR_extend": 80  
}


def run_motors(solution):
    if isinstance(solution, str):   
        move_array = solution.strip().split()
    else:
        move_array = solution
 
    is_flipped = False  # track if cube is currently flipped

    print("Executing moves on robot...")
    for i, move in enumerate(move_array):
        face = move[0]
        next_face = move_array[i + 1][0] if i + 1 < len(move_array) else None

        print(f"Executing move: {move}")

        if face == "R": execute_face_turn("rotR", move)
        elif face == "L": execute_face_turn("rotL", move)
        elif face == "F": execute_face_turn("rotF", move)
        elif face == "B": execute_face_turn("rotB", move)

        elif face == 'U':
            if not is_flipped:
                flip_cube_forward()  # U comes to F
                is_flipped = True
            execute_face_turn("rotF", move)

        elif face == 'D':
            if not is_flipped:
                flip_cube_forward()  # D comes to B
                is_flipped = True
            execute_face_turn("rotB", move)

        # After executing, check if we need to flip back
        if is_flipped and next_face not in ['U', 'D', None]:
            flip_cube_backward()  # flip back to normal
            is_flipped = False

    print("All moves executed on robot.")


def execute_face_turn(motor_name, kociemba_move):
    
    gripper_name = motor_name.replace("rot", "grip")

    center = calibration_data[f"{motor_name}_center"]
    cw = calibration_data[f"{motor_name}_cw"]
    ccw = calibration_data[f"{motor_name}_ccw"]

    move_servo(gripper_name, calibration_data[f"{gripper_name}_extend"])
    time.sleep(0.2)

    if len(kociemba_move) == 1:
        move_servo(motor_name, cw) # CW
    elif kociemba_move[1] == "'":
        move_servo(motor_name, ccw)   # CCW
    elif kociemba_move[1] == "2":
        move_servo(motor_name, cw) # 180 Double Turn
        time.sleep(0.2)
        back_to_initial_position(motor_name, gripper_name)
        time.sleep(0.2)
        move_servo(motor_name, cw) # 180 Double Turn
        
    time.sleep(0.2)
    back_to_initial_position(motor_name, gripper_name)
    time.sleep(0.2)




def move_servo(motor_name, angle):
    if esp32 and esp32.is_open:
        esp32.write(f"{motor_name}:{angle}\n".encode('utf-8'))
        time.sleep(0.3) # Wait for physical movement

def move_servo_without_delay(motor_name, angle):
    if esp32 and esp32.is_open:
        esp32.write(f"{motor_name}:{angle}\n".encode('utf-8'))
        # time.sleep(0.3) # Wait for physical movement


def back_to_initial_position(rotate_motor, gripper_motor):
    
    move_servo(gripper_motor, calibration_data[f"{gripper_motor}_retract"])
    time.sleep(0.3)

    move_servo(rotate_motor, calibration_data[f"{rotate_motor}_center"])
    time.sleep(0.3)

    move_servo(gripper_motor, calibration_data[f"{gripper_motor}_extend"])
    time.sleep(0.3)


def flip_cube_forward():

    print("Flipping cube forward...")
    move_servo("gripR", calibration_data["gripR_retract"])
    time.sleep(0.2)

    move_servo("rotR", calibration_data["rotR_cw"])
    time.sleep(0.2)

    move_servo("gripR", calibration_data["gripR_extend"])
    time.sleep(0.2)

    move_servo("gripF", calibration_data["gripF_retract"])
    move_servo("gripB", calibration_data["gripB_retract"])
    time.sleep(0.2)

    move_servo_without_delay("rotR", calibration_data["rotR_center"])
    move_servo_without_delay("rotL", calibration_data["rotL_cw"])
    time.sleep(0.4)

    move_servo("gripF", calibration_data["gripF_extend"])
    move_servo("gripB", calibration_data["gripB_extend"])
    time.sleep(0.2)

    back_to_initial_position("rotL", "gripL")
    print("Cube flipped forward successfully!")

def flip_cube_backward():

    print("Flipping cube backward...")
    move_servo("gripL", calibration_data["gripL_retract"])
    time.sleep(0.2)

    move_servo("rotL", calibration_data["rotL_cw"])
    time.sleep(0.2)

    move_servo("gripL", calibration_data["gripL_extend"])
    time.sleep(0.2)

    move_servo("gripF", calibration_data["gripF_retract"])
    move_servo("gripB", calibration_data["gripB_retract"])
    time.sleep(0.2)

    move_servo_without_delay("rotL", calibration_data["rotL_center"])
    move_servo_without_delay("rotR", calibration_data["rotR_cw"])
    time.sleep(0.4)

    move_servo("gripF", calibration_data["gripF_extend"])
    move_servo("gripB", calibration_data["gripB_extend"])
    time.sleep(0.2)

    back_to_initial_position("rotR", "gripR")
    print("Cube flipped backward successfully!")

def interactive_control(solution):
    print("\n--- Interactive Control ---")
    print("Press 'Space' to extend all grippers and start solving.")
    print("Press 'Ctrl' to retract all grippers.")
    print("Press 'Esc' to exit without solving.")
    
    while True:
        if keyboard.is_pressed('space'):
            print("\nSpace pressed: Extending all grippers...")
            move_servo_without_delay("gripF", calibration_data["gripF_extend"])
            move_servo_without_delay("gripB", calibration_data["gripB_extend"])
            move_servo_without_delay("gripL", calibration_data["gripL_extend"])
            move_servo_without_delay("gripR", calibration_data["gripR_extend"])
            time.sleep(1) # wait for physical movement
            print("Running motors...")
            run_motors(solution)
            break
        elif keyboard.is_pressed('ctrl'):
            print("\nCtrl pressed: Retracting all grippers...")
            move_servo_without_delay("gripF", calibration_data["gripF_retract"])
            move_servo_without_delay("gripB", calibration_data["gripB_retract"])
            move_servo_without_delay("gripL", calibration_data["gripL_retract"])
            move_servo_without_delay("gripR", calibration_data["gripR_retract"])
            time.sleep(0.5) # debounce
        elif keyboard.is_pressed('esc'):
            print("\nEsc pressed: Exiting...")
            break
        time.sleep(0.1)
  

def interactive_control_flip():
    print("\n--- Interactive Control ---")
    print("Press 'Space' to extend all grippers and start solving.")
    print("Press 'Ctrl' to retract all grippers.")
    print("Press 'Esc' to exit without solving.")
    
    while True:
        if keyboard.is_pressed('space'):
            print("\nSpace pressed: Extending all grippers...")
            move_servo_without_delay("gripF", calibration_data["gripF_extend"])
            move_servo_without_delay("gripB", calibration_data["gripB_extend"])
            move_servo_without_delay("gripL", calibration_data["gripL_extend"])
            move_servo_without_delay("gripR", calibration_data["gripR_extend"])
            time.sleep(1) # wait for physical movement
            print("Running motors...")
            flip_cube_forward()
            break
        elif keyboard.is_pressed('ctrl'):
            print("\nCtrl pressed: Retracting all grippers...")
            move_servo_without_delay("gripF", calibration_data["gripF_retract"])
            move_servo_without_delay("gripB", calibration_data["gripB_retract"])
            move_servo_without_delay("gripL", calibration_data["gripL_retract"])
            move_servo_without_delay("gripR", calibration_data["gripR_retract"])
            time.sleep(0.5) # debounce
        elif keyboard.is_pressed('esc'):
            print("\nEsc pressed: Exiting...")
            break
        time.sleep(0.1)

def test1():
    while True:
        move_servo_without_delay("gripF", calibration_data["gripF_extend"])
        move_servo_without_delay("gripB", calibration_data["gripB_extend"])
        move_servo_without_delay("gripL", calibration_data["gripL_extend"])
        move_servo_without_delay("gripR", calibration_data["gripR_extend"])

def test2():
    while True:
        move_servo_without_delay("gripF", calibration_data["gripF_retract"])
        move_servo_without_delay("gripB", calibration_data["gripB_retract"])
        move_servo_without_delay("gripL", calibration_data["gripL_retract"])
        move_servo_without_delay("gripR", calibration_data["gripR_retract"])


#interactive_control_flip()
#flip_cube_backward()
#interactive_control(["R", "L", "F", "B", "R'", "R2", "L'", "L2", "F'", "F2", "B'", "B2"])
#run_motors(["B2"])
#flip_cube_forward()    

#test1()