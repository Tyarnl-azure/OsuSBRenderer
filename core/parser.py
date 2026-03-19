"""
Parses .osu and .osb files to extract storyboard events.
Supports Variables, Sprites, Animations, and Loop groups.
"""
import os
import glob
from core.models import Sprite, Animation, Command, LoopGroup, VideoObject

class StoryboardParser:
    def __init__(self, render_bg=False):
        self.variables = {}
        self.layers = {
            "Background": [], "Fail": [], "Pass": [], "Foreground": [], "Overlay": []
        }
        self.video = None
        self.title = "Rendered_MV"
        self.render_bg = render_bg

    def parse_folder(self, folder_path: str):
        osu_files = glob.glob(os.path.join(folder_path, "*.osu"))
        osb_files = glob.glob(os.path.join(folder_path, "*.osb"))
        
        if osu_files:
            self._parse_file(osu_files[0])
        if osb_files:
            self._parse_file(osb_files[0])
            
        for layer in self.layers.values():
            for obj in layer:
                obj.finalize()
                
        return self.layers, self.video

    def _parse_file(self, filepath: str):
        if not os.path.exists(filepath): return
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()

        current_section = ""
        current_sprite = None
        current_loop = None

        for raw_line in lines:
            line = raw_line.strip('\r\n')
            if not line or line.startswith("//"): continue

            if line.startswith("[") and line.endswith("]"):
                current_section = line
                continue
            
            if current_section == "[Metadata]" and line.startswith("Title:"):
                self.title = line.split(":", 1)[1].strip()
                continue

            if current_section == "[Variables]" and "=" in line:
                key, val = line.split("=", 1)
                self.variables[key] = val
                continue

            if current_section == "[Events]":
                for var_key, var_val in self.variables.items():
                    if var_key in line: line = line.replace(var_key, var_val)

                depth = len(line) - len(line.lstrip(' _'))
                content = line[depth:]
                parts = content.split(',')

                if depth == 0:
                    current_sprite = None
                    current_loop = None
                    event_type = parts[0]

                    if event_type in ("Video", "1") and len(parts) >= 3:
                        offset = float(parts[1])
                        vid_path = parts[2].strip('"')
                        self.video = VideoObject(vid_path, offset)
                        continue

                    if event_type == "0":
                        if not self.render_bg:
                            continue
                        path = parts[2].strip('"')
                        x = float(parts[3]) if len(parts) > 3 else 320.0
                        y = float(parts[4]) if len(parts) > 4 else 240.0
                        current_sprite = Sprite("Background", "Centre", path, x, y)
                        self.layers["Background"].append(current_sprite)

                    elif event_type == "Sprite":
                        layer, origin, path, x, y = parts[1], parts[2], parts[3].strip('"'), float(parts[4]), float(parts[5])
                        current_sprite = Sprite(layer, origin, path, x, y)
                        if layer in self.layers: self.layers[layer].append(current_sprite)

                    elif event_type == "Animation":
                        layer, origin, path, x, y = parts[1], parts[2], parts[3].strip('"'), float(parts[4]), float(parts[5])
                        f_count, f_delay = int(parts[6]), float(parts[7])
                        loop_type = parts[8] if len(parts) > 8 else "LoopForever"
                        current_sprite = Animation(layer, origin, path, x, y, f_count, f_delay, loop_type)
                        if layer in self.layers: self.layers[layer].append(current_sprite)

                else:
                    if current_sprite is None: continue
                    cmd_type = parts[0]

                    if cmd_type == "L":
                        current_loop = LoopGroup(float(parts[1]), int(parts[2]))
                        current_sprite.loops.append(current_loop)
                        continue
                    if cmd_type == "T":
                        current_loop = None 
                        continue

                    easing, start_time = int(parts[1]), float(parts[2])
                    end_time = float(parts[3]) if len(parts) > 3 and parts[3] else start_time
                    start_val, end_val = [], []

                    if cmd_type in ("F", "S", "R", "MX", "MY"):
                        start_val = [float(parts[4])]
                        end_val = [float(parts[5])] if len(parts) > 5 else start_val
                    elif cmd_type in ("M", "V"):
                        start_val = [float(parts[4]), float(parts[5])]
                        end_val = [float(parts[6]), float(parts[7])] if len(parts) > 6 else start_val
                    elif cmd_type == "C":
                        start_val = [float(parts[4]), float(parts[5]), float(parts[6])]
                        end_val = [float(parts[7]), float(parts[8]), float(parts[9])] if len(parts) > 7 else start_val
                    elif cmd_type == "P":
                        start_val = end_val = [parts[4]]

                    cmd = Command(cmd_type, easing, start_time, end_time, tuple(start_val), tuple(end_val))
                    if depth == 2 and current_loop is not None:
                        current_loop.commands.append(cmd)
                    else:
                        current_sprite.add_command(cmd)