# import cv2
# import time

# cap = cv2.VideoCapture('/dev/video2')
# # Ghi hình trong 60 giây
# record_duration = 60 

# prev_frame_time = 0
# new_frame_time = 0

# if cap.isOpened():

#     fps = cap.get(cv2.CAP_PROP_FPS)
#     print(f"Camera FPS: {fps}")

#     fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#     frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#     frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#     out = cv2.VideoWriter('output.mp4', fourcc, fps, (frame_width, frame_height))
    
#     start_time = time.time()
    
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break
        

#         new_frame_time = time.time()
#         fps = 1 / (new_frame_time - prev_frame_time)
#         prev_frame_time = new_frame_time
#         print(f"curent fps : {fps}")
#         out.write(frame)
        
#         # Kiểm tra nếu thời gian đã trôi qua vượt quá giới hạn
#         if time.time() - start_time > record_duration:
#             print("out record time.")
#             break
            
#     cap.release()
#     out.release()
#     print("save video.")
# else:
#     print("Camera not accessible.")



import cv2
import time

# Mở camera USB (ở đây là /dev/video2)
cap = cv2.VideoCapture("/dev/video2", cv2.CAP_V4L2)

# Ép MJPEG cho tốc độ cao
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
cap.set(cv2.CAP_PROP_FPS, 30)

# Tạo VideoWriter H.264 để lưu mp4
fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # có thể đổi thành "X264" nếu ffmpeg hỗ trợ
out = cv2.VideoWriter("output.mp4", fourcc, 30, (1024, 768))

print("🎥 Recording 10s video at 640x480 MJPEG (decode to BGR)...")

start_time = time.time()
frames = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break

    out.write(frame)
    frames += 1

    # In FPS thực tế mỗi giây
    elapsed = time.time() - start_time
    if elapsed >= 1.0:
        fps = frames / elapsed
        print(f"⚡ FPS thực tế: {fps:.2f}")
        frames = 0
        start_time = time.time()

    if elapsed > 10:  # record 10s
        break

cap.release()
out.release()
print("✅ Done, saved to output.mp4")



# from picamera2 import Picamera2
# from picamera2.encoders import H264Encoder
# from picamera2.outputs import FileOutput
# import time

# picam2 = Picamera2()

# # Ép cấu hình main stream thành YUV420
# video_config = picam2.create_video_configuration(
#     main={"size": (640, 480), "format": "NV12"}
# )

# picam2.configure(video_config)

# encoder = H264Encoder(bitrate=4_000_000)  # bitrate 4Mbps
# output = FileOutput("output.mp4")

# print("🎥 Recording 60s video at 640x480 YUV420...")
# picam2.start_recording(encoder, output)

# time.sleep(60)

# picam2.stop_recording()
# print("✅ Done, saved to output.mp4")



