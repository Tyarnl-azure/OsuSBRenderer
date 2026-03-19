"""
Main entry point for OsuSBRenderer.
Handles CLI, multi-processing orchestration, and frame-by-frame rendering sequence.
Uses ProcessPoolExecutor for parallel rendering and FFmpeg for video encoding.
"""
import sys
import os
import gc
import re
import time
import glob
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import tkinter as tk
from tkinter import filedialog

os.environ["OPENCV_LOG_LEVEL"] = "0"
os.environ['PNGC_LIBPNG_WARNINGS'] = '0'
import warnings
warnings.filterwarnings("ignore")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from core.parser import StoryboardParser
from core.timeline import TimelineEvaluator
from graphics.renderer import Renderer
from video.exporter import VideoExporter

_worker_renderer = None
_worker_layers = None
_worker_evaluators = None

def worker_init(input_dir, layers, video_obj, res_w, res_h, fps, mem_limit_bytes):
    """子进程初始化函数"""
    import config
    import ctypes
    if os.name == 'nt':
        ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002)
        try:
            null_fd = os.open(os.devnull, os.O_RDWR)
            os.dup2(null_fd, 2) 
        except: pass

    config.update_config(res_w, res_h, fps)
    
    global _worker_renderer, _worker_layers, _worker_evaluators
    _worker_renderer = Renderer(input_dir, mem_limit_bytes=mem_limit_bytes)
    _worker_renderer.init_video(video_obj)
    _worker_layers = layers
    
    _worker_evaluators = {s: TimelineEvaluator(s) for layer in layers.values() for s in layer}

def worker_render(frame_idx, current_time_ms):
    """执行单帧渲染"""
    global _worker_renderer, _worker_layers, _worker_evaluators
    img = _worker_renderer.render_frame(_worker_layers, _worker_evaluators, current_time_ms)
    return frame_idx, img

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

class OsuCLI:
    def __init__(self):
        if os.name == 'nt': os.system("")
        self.input_dir = ""
        self.output_dir = "" 
        self.res_w = 1920
        self.res_h = 1080
        self.fps = 60
        self.mem_limit_mb = 4096 
        self.render_bg = False
        self.root = tk.Tk()
        self.root.withdraw()

    def run(self):
        while True:
            clear_screen()
            print("=== OSU! Storyboard Renderer ===")
            print(f"Config: {self.res_w}x{self.res_h}@{self.fps}FPS | Mem Limit: {self.mem_limit_mb}MB")
            print(f"Render BG: {'YES' if self.render_bg else 'NO'}")
            print(f"Export Dir: {self.output_dir if self.output_dir else 'Auto'}")
            print("---------------------------------")
            print("[1] Render a new Storyboard")
            print("[2] Set export path")
            print("[3] Set rendering parameters")
            print("[4] Exit")

            choice = input("\nSelect: ")
            if choice == '1':
                folder = filedialog.askdirectory()
                if folder: self.start_render(folder)
            elif choice == '2':
                folder = filedialog.askdirectory()
                if folder: self.output_dir = folder
            elif choice == '3': self.set_parameters()
            elif choice == '4': break

    def set_parameters(self):
        clear_screen()
        print("Resolution: [1]1080P [2]1440P [3]2160P")
        res = input("Select: ")
        if res == '1': self.res_w, self.res_h = 1920, 1080
        elif res == '2': self.res_w, self.res_h = 2560, 1440
        elif res == '3': self.res_w, self.res_h = 3840, 2160
        print("\nFPS: [1]30 [2]60 [3]120")
        f_choice = input("Select: ")
        if f_choice == '1': self.fps = 30
        elif f_choice == '2': self.fps = 60
        elif f_choice == '3': self.fps = 120
        print("\nRender static Beatmap BG? [1]No [2]Yes")
        self.render_bg = (input("Select: ") == '2')
        print(f"\nMax RAM Limit (Current {self.mem_limit_mb}MB):")
        mem = input("Enter size in MB: ").strip()
        if mem.isdigit(): self.mem_limit_mb = int(mem)

    def start_render(self, input_dir):
        config.update_config(self.res_w, self.res_h, self.fps)
        
        print("\nParsing storyboard...")
        parser = StoryboardParser(render_bg=self.render_bg)
        layers, video_obj = parser.parse_folder(input_dir)
        
        safe_title = re.sub(r'[\\/*?:"<>|]', "", parser.title).strip() or "Rendered_MV"
        out_dir = self.output_dir if self.output_dir else input_dir
        output_file = os.path.join(out_dir, f"{safe_title}.mp4").replace("\\", "/")

        max_end_time = max((s.end_time for layer in layers.values() for s in layer if s.end_time != float('inf')), default=0)

        print(f"\nStoryboard Max Duration: {max_end_time:.1f} ms")
        try:
            s_in = input("Start Time (ms) [Default 0]: ").strip()
            start_ms = float(s_in) if s_in else 0.0
            e_in = input(f"End Time (ms) [Default {max_end_time:.1f}]: ").strip()
            end_ms = float(e_in) if e_in else max_end_time
        except ValueError:
            print("Invalid time input.")
            time.sleep(2); return

        duration_ms = end_ms - start_ms
        if duration_ms <= 0: 
            print("Duration is zero or negative."); time.sleep(2); return

        audio_files = glob.glob(os.path.join(input_dir, "*.mp3")) + glob.glob(os.path.join(input_dir, "*.ogg"))
        audio_path = audio_files[0] if audio_files else None

        ms_per_frame = 1000.0 / config.FPS
        total_frames = int(duration_ms / ms_per_frame) + 1

        print(f"\nInitializing FFmpeg...")
        try:
            exporter = VideoExporter(output_file, audio_path, start_time_ms=start_ms, duration_ms=duration_ms)
        except Exception as e:
            print(f"FFmpeg Error: {e}"); input("Press Enter..."); return

        print(f"Starting Render: {total_frames} frames...")

        cpu_count = multiprocessing.cpu_count()
        max_workers = max(1, cpu_count - 2)
        if self.res_w > 2000: max_workers = max(1, cpu_count // 2)
        
        worker_mem_bytes = (self.mem_limit_mb * 1024 * 1024) // max_workers
        WINDOW_SIZE = max_workers * 2 

        frame_buffer = {}
        next_submit = 0
        next_write = 0
        start_real = time.time()

        try:
            with ProcessPoolExecutor(max_workers=max_workers, initializer=worker_init, 
                                     initargs=(input_dir, layers, video_obj, self.res_w, self.res_h, self.fps, worker_mem_bytes)) as pool:
                active_futures = {}
                while next_write < total_frames:
                    while len(active_futures) < WINDOW_SIZE and next_submit < total_frames:
                        curr_ms = start_ms + next_submit * ms_per_frame
                        f = pool.submit(worker_render, next_submit, curr_ms)
                        active_futures[f] = next_submit
                        next_submit += 1

                    done_fs = [f for f in active_futures if f.done()]
                    for f in done_fs:
                        f_idx, f_img = f.result()
                        frame_buffer[f_idx] = f_img
                        del active_futures[f]

                    while next_write in frame_buffer:
                        img = frame_buffer.pop(next_write)
                        exporter.write_frame(img)
                        del img
                        next_write += 1
                        elapsed = time.time() - start_real
                        sys.stdout.write(f"\rProgress: {next_write}/{total_frames} | {int(elapsed//60)}m{int(elapsed%60)}s | Workers: {max_workers}  ")
                        sys.stdout.flush()
                    
                    time.sleep(0.001)

        except Exception as e:
            print(f"\nRender Error: {e}")
            input("Press Enter to see traceback...")
            raise e
        finally:
            exporter.close()

        print("\nRender Complete!")
        input("Press Enter to return to menu...")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    OsuCLI().run()