# coding=utf-8
import os
import cv2


frame_count = 0 # 保存帧的索引
frame_index = 0 # 原视频的帧索引，与 interval*frame_count = frame_index 


src_video_path = 'E:/Documents/SynologyDrive/AdaHOI/user_study/sample.mp4'
dst_dir = os.path.join(os.path.dirname(src_video_path), os.path.basename(src_video_path).split('.')[0])

cap = cv2.VideoCapture(src_video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

interval = fps // 2 # 保存时的帧数间隔

if cap.isOpened():
    success = True
else:
    success = False
    print("读取失败!")

while(success):
    success, frame = cap.read()
    if success is False:
        print("---> 第%d帧读取失败:" % frame_index)
        break
        
    print("---> 正在读取第%d帧:" % frame_index, success)
    if frame_index % interval == 0:
    	os.makedirs(dst_dir, exist_ok=True)
    	cv2.imwrite(f"{dst_dir}/{frame_count:04d}.png", frame)
    	print(f"Save pic to {dst_dir}/{frame_count:04d}.png")
    	frame_count += 1
    frame_index += 1
