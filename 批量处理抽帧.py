# -*- coding: utf-8 -*-
"""
Created on Tue Mar 18 16:47:36 2025

@author: sml68
"""

import cv2
import tkinter as tk
from tkinter import simpledialog
from tkinter import messagebox
import os
import subprocess

# 从视频文件中按指定间隔抽取帧并保存
def extract_frames_at_interval(root, video_path, folder_1, interval_seconds=20):
    # 检查 1 文件夹是否存在，不存在则创建
    if not os.path.exists(folder_1):
        os.makedirs(folder_1)

    # 尝试使用 OpenCV 按顺序读取帧
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        messagebox.showerror("错误", f"无法打开视频文件：{video_path}")
        return

    # 获取视频的帧率
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        # 如果帧率获取失败，手动指定一个常见的帧率
        fps = 25
        print(f"无法获取视频帧率，手动指定为 {fps}")

    # 计算每间隔的帧数
    interval_frames = int(interval_seconds * fps)
    # 计算从第 20 秒开始抽取帧对应的帧数
    start_frame = int(20 * fps)
    current_frame = 0

    # 获取视频文件的名称（包含扩展名）
    video_name = os.path.basename(video_path)
    last_saved_frame = 0
    last_valid_frame = None
    last_valid_frame_number = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if current_frame >= start_frame and (current_frame - start_frame) % interval_frames == 0:
            # 缩放图像到 224x224
            resized_frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)

            # 计算当前帧对应的时间（秒）
            time_in_seconds = current_frame / fps
            # 四舍五入到个位
            rounded_time = round(time_in_seconds)
            # 构建保存的图像文件名，在视频文件名后添加 .mp4
            image_filename = os.path.join(folder_1, f"{video_name}_at_{rounded_time}_seconds.jpg")
            # 保存帧为图像文件
            cv2.imwrite(image_filename, resized_frame)
            print(f"Frame at {time_in_seconds:.2f} seconds saved as {image_filename}")
            last_saved_frame = current_frame

        last_valid_frame = frame
        last_valid_frame_number = current_frame
        current_frame += 1

    # 处理最后一帧
    if last_valid_frame is not None:
        # 缩放图像到 224x224
        resized_frame = cv2.resize(last_valid_frame, (224, 224), interpolation=cv2.INTER_AREA)

        # 计算当前帧对应的时间（秒）
        time_in_seconds = last_valid_frame_number / fps
        # 四舍五入到个位
        rounded_time = round(time_in_seconds)
        # 构建保存的图像文件名，在视频文件名后添加 .mp4
        image_filename = os.path.join(folder_1, f"{video_name}_at_{rounded_time}_seconds.jpg")
        # 保存帧为图像文件
        cv2.imwrite(image_filename, resized_frame)
        print(f"Last frame at {time_in_seconds:.2f} seconds saved as {image_filename}")

    cap.release()

    # 如果 OpenCV 抽取失败，尝试使用 FFmpeg
    if last_saved_frame == 0:
        try:
            output_folder = os.path.dirname(video_path)
            ffmpeg_command = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"fps=1/{interval_seconds}",
                f"{output_folder}/frame_%04d.jpg"
            ]
            subprocess.run(ffmpeg_command, check=True)
            print(f"使用 FFmpeg 成功从 {video_path} 抽取帧")
        except subprocess.CalledProcessError as e:
            print(f"使用 FFmpeg 抽取帧失败: {e}")


# 创建根窗口并隐藏
root = tk.Tk()
root.withdraw()

# 让用户输入要遍历的包含视频文件的目录路径
video_directory = simpledialog.askstring("输入目录路径", "请输入包含视频文件的目录路径：")

if video_directory:
    # 定义常见的视频文件扩展名
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv')
    # 遍历指定目录及其子目录
    for root_dir, _, files in os.walk(video_directory):
        for file in files:
            # 检查文件是否为视频文件
            if file.lower().endswith(video_extensions):
                # 构建完整的视频文件路径
                video_path = os.path.join(root_dir, file)
                # 构建保存 1 类图片的文件夹路径
                folder_1 = os.path.join(root_dir, "1")
                # 对当前视频文件进行抽帧处理
                extract_frames_at_interval(root, video_path, folder_1, interval_seconds=20)

    # 所有视频处理完毕后弹出提示框
    messagebox.showinfo("提示", "目录下视频已全部抽帧完毕")
else:
    messagebox.showinfo("提示", "未输入目录路径，程序退出。")

# 销毁根窗口，结束程序
root.destroy()
    