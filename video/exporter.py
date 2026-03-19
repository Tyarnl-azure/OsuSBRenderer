# Pipes raw BGR24 frames directly into FFmpeg stdin to avoid massive temporary disk usage.
import subprocess
import os
import config

class VideoExporter:
    def __init__(self, output_path: str, audio_path: str = None, start_time_ms: float = 0, duration_ms: float = 0):
        self.output_path = output_path
        self.process = None
        
        command = [
            'ffmpeg',
            '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}',
            '-pix_fmt', 'bgr24',
            '-r', str(config.FPS),
            '-i', '-'
        ]
        
        if audio_path and os.path.exists(audio_path):
            start_sec = start_time_ms / 1000.0
            duration_sec = duration_ms / 1000.0
            command.extend(['-ss', str(start_sec), '-t', str(duration_sec), '-i', audio_path])
            
        command.extend([
            '-c:v', 'h264_nvenc',
            '-preset', 'p4',
            '-cq', '18',
            '-b:v', '0',
            '-pix_fmt', 'yuv420p',
        ])
        
        if audio_path and os.path.exists(audio_path):
            command.extend(['-c:a', 'aac', '-b:a', '192k'])
            
        command.append(output_path)
        
        try:
            self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            raise RuntimeError("未找到 ffmpeg！")

    def write_frame(self, frame):
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(frame.tobytes())
            except:
                pass

    def close(self):
        if self.process:
            if self.process.stdin:
                self.process.stdin.close()
            self.process.wait()