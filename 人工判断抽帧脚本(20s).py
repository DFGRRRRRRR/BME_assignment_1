import cv2
import tkinter as tk
from tkinter import simpledialog
from tkinter import messagebox
import os
from PIL import Image, ImageTk
import subprocess

# 显示图片并获取用户对图片的命名选择，支持撤销操作
def show_image_and_get_name(root, image, prev_image_filename=None, is_last_frame=False, is_first_choice=False):
    result = None

    def create_window():
        nonlocal result
        # 创建一个顶层窗口用于显示图片和选择按钮
        top = tk.Toplevel(root)
        top.title("图片命名")

        # 获取屏幕的宽度和高度
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # 定义弹出窗口的宽度和高度，适当增加高度以容纳提示信息
        window_width = 350
        window_height = 450

        # 计算弹出窗口在屏幕中央的坐标
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # 设置弹出窗口的位置和大小
        top.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # 创建一个主框架，用于组织其他组件
        main_frame = tk.Frame(top)
        main_frame.pack(pady=10)

        # 直接将图像调整大小为 224x224，去掉裁剪步骤
        resized = cv2.resize(image, (224, 224))

        # 将 OpenCV 图像转换为 PIL 图像
        image_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        # 将 PIL 图像转换为 Tkinter 可用的图像对象
        top.tk_image = ImageTk.PhotoImage(image=pil_image)

        # 创建图像标签并显示图片
        image_label = tk.Label(main_frame, image=top.tk_image)
        image_label.pack(pady=5)

        # 添加标题标签，提示用户不同选择的含义
        title_label = tk.Label(main_frame, text='"0"为离床, "1"为在床')
        title_label.pack(pady=5)

        # 处理按钮点击事件，记录用户选择并关闭窗口
        def on_button_click(choice):
            nonlocal result
            result = choice
            top.destroy()

        # 处理撤销按钮点击事件
        def on_undo_click():
            nonlocal result
            if prev_image_filename and os.path.exists(prev_image_filename):
                # 删除上一次保存的文件
                os.remove(prev_image_filename)
                result = "undo"
            top.destroy()

        # 创建一个框架用于放置按钮，增加内边距以增宽选择框
        button_frame = tk.Frame(main_frame, padx=20, pady=20)
        button_frame.pack(pady=20, fill=tk.X)  # 使用 fill=tk.X 使按钮框架水平填充

        # 强制更新窗口布局，确保能获取到正确的宽度
        top.update_idletasks()

        # 创建一个子框架用于放置 "0" 和 "1" 按钮
        zero_one_frame = tk.Frame(button_frame)
        # 计算使 "1" 按钮落在中线的左边距
        button_width = 50  # 假设按钮宽度约为 50，可根据实际情况调整
        left_padding = (button_frame.winfo_width() - button_width) // 2 - button_width - 10
        # 确保 left_padding 为非负数
        left_padding = max(0, left_padding)
        zero_one_frame.pack(side=tk.LEFT, padx=(left_padding, 0))

        # 创建按钮 0，点击时调用 on_button_click 函数并传入 "0"
        button_0 = tk.Button(zero_one_frame, text="0", command=lambda: on_button_click("0"))
        button_0.pack(side=tk.LEFT, padx=10)

        # 创建按钮 1，点击时调用 on_button_click 函数并传入 "1"
        button_1 = tk.Button(zero_one_frame, text="1", command=lambda: on_button_click("1"))
        button_1.pack(side=tk.LEFT, padx=10)

        # 创建撤销按钮，点击时调用 on_undo_click 函数
        if prev_image_filename and not is_first_choice:
            undo_button = tk.Button(button_frame, text="撤回到上一步", command=on_undo_click)
            undo_button.pack(side=tk.RIGHT, padx=10)  # 偏右

        if is_last_frame:
            # 显示最后一帧的提示信息，颜色为红色，放在按钮框架下面
            last_frame_warning = tk.Label(main_frame, text="本视频最后一帧，无法撤回，请认真选择", fg="red")
            last_frame_warning.pack(pady=5)

        # 等待窗口关闭
        top.wait_window()

    create_window()
    return result

# 从视频文件中按指定间隔抽取帧并保存
def extract_frames_at_interval(root, video_path, folder_0, folder_1, interval_seconds=20):
    # 检查 0 和 1 文件夹是否存在，不存在则创建
    for folder in [folder_0, folder_1]:
        if not os.path.exists(folder):
            os.makedirs(folder)

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
    prev_image_filename = None
    last_saved_frame = 0
    is_first_choice = True
    last_valid_frame = None
    last_valid_frame_number = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if current_frame >= start_frame and (current_frame - start_frame) % interval_frames == 0:
            is_last_frame = False
            while True:
                # 显示图片并获取用户选择
                image_name = show_image_and_get_name(root, frame, prev_image_filename, is_last_frame, is_first_choice)
                if image_name == "undo":
                    # 这里由于是顺序读取，撤销操作逻辑需调整，暂不处理复杂的撤销
                    print("顺序读取模式下暂不支持撤销操作")
                    break
                elif image_name:
                    # 缩放图像到 224x224
                    resized_frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
                    # 根据用户选择的命名选择保存文件夹
                    if image_name == '0':
                        output_folder = folder_0
                    elif image_name == '1':
                        output_folder = folder_1

                    # 计算当前帧对应的时间（秒）
                    time_in_seconds = current_frame / fps
                    # 四舍五入到个位
                    rounded_time = round(time_in_seconds)
                    # 构建保存的图像文件名，在视频文件名后添加 .mp4
                    prev_image_filename = os.path.join(output_folder, f"{video_name}_at_{rounded_time}_seconds.jpg")
                    # 保存帧为图像文件
                    cv2.imwrite(prev_image_filename, resized_frame)
                    print(f"Frame at {time_in_seconds:.2f} seconds saved as {prev_image_filename}")
                    last_saved_frame = current_frame
                    is_first_choice = False
                    break

        last_valid_frame = frame
        last_valid_frame_number = current_frame
        current_frame += 1

    # 处理最后一帧
    if last_valid_frame is not None:
        is_last_frame = True
        while True:
            image_name = show_image_and_get_name(root, last_valid_frame, prev_image_filename, is_last_frame, is_first_choice)
            if image_name:
                # 缩放图像到 224x224
                resized_frame = cv2.resize(last_valid_frame, (224, 224), interpolation=cv2.INTER_AREA)
                # 根据用户选择的命名选择保存文件夹
                if image_name == '0':
                    output_folder = folder_0
                elif image_name == '1':
                    output_folder = folder_1

                # 计算当前帧对应的时间（秒）
                time_in_seconds = last_valid_frame_number / fps
                # 四舍五入到个位
                rounded_time = round(time_in_seconds/10)*10
                # 构建保存的图像文件名，在视频文件名后添加 .mp4
                prev_image_filename = os.path.join(output_folder, f"{video_name}_at_{rounded_time}_seconds.jpg")
                # 保存帧为图像文件
                cv2.imwrite(prev_image_filename, resized_frame)
                print(f"Last frame at {time_in_seconds:.2f} seconds saved as {prev_image_filename}")
                break

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
                # 构建保存 0 类图片的文件夹路径
                folder_0 = os.path.join(root_dir, "0")
                # 构建保存 1 类图片的文件夹路径
                folder_1 = os.path.join(root_dir, "1")
                # 对当前视频文件进行抽帧处理
                extract_frames_at_interval(root, video_path, folder_0, folder_1, interval_seconds=20)

    # 所有视频处理完毕后弹出提示框
    messagebox.showinfo("提示", "目录下视频已全部抽帧完毕")
else:
    messagebox.showinfo("提示", "未输入目录路径，程序退出。")

# 销毁根窗口，结束程序
root.destroy()