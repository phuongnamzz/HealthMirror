import cv2
import mediapipe as mp
import numpy as np

# Khởi tạo
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture('/dev/video0')

pushup_count = 0
stage = 'waiting'  # waiting → down → up

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180.0 else angle

def get_landmark_coords(landmarks, name):
    lm = landmarks[mp_pose.PoseLandmark[name].value]    
    return [lm.x, lm.y]

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = pose.process(image)
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark

        # Lấy các điểm bên trái và phải
        right_shoulder = get_landmark_coords(landmarks, 'RIGHT_SHOULDER')
        right_elbow = get_landmark_coords(landmarks, 'RIGHT_ELBOW')
        right_wrist = get_landmark_coords(landmarks, 'RIGHT_WRIST')

        left_shoulder = get_landmark_coords(landmarks, 'LEFT_SHOULDER')
        left_elbow = get_landmark_coords(landmarks, 'LEFT_ELBOW')
        left_wrist = get_landmark_coords(landmarks, 'LEFT_WRIST')

        # Tính góc cả hai tay
        right_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
        left_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)

        # Kiểm tra độ cao vai & hông (đảm bảo thân người cũng hạ xuống)
        shoulder_y = (right_shoulder[1] + left_shoulder[1]) / 2
        hip_y = (
            landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y +
            landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y
        ) / 2

        body_vertical = hip_y - shoulder_y

        # Push-up logic nâng cao
        if right_angle < 90 and left_angle < 90 and body_vertical > 0.2:
            if stage == 'waiting':
                stage = 'down'
        elif right_angle > 160 and left_angle > 160 and stage == 'down':
            stage = 'up'
            pushup_count += 1
            stage = 'waiting'  # reset lại

        # Hiển thị
        color = (0, 255, 0) if stage == 'up' else (0, 0, 255) if stage == 'down' else (255, 255, 0)
        cv2.putText(image, f'Push-ups: {pushup_count}', (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.putText(image, f'R Angle: {int(right_angle)}', (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        cv2.putText(image, f'L Angle: {int(left_angle)}', (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        cv2.putText(image, f'Stage: {stage}', (10, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    # cv2.imshow('Smart Push-up Counter', image)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()


