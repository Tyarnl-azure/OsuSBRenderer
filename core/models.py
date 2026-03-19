from typing import List, Dict

class Command:
    def __init__(self, cmd_type: str, easing: int, start_time: float, end_time: float, start_val: tuple, end_val: tuple):
        self.cmd_type = cmd_type
        self.easing = easing
        self.start_time = start_time
        self.end_time = end_time
        self.start_val = start_val
        self.end_val = end_val

class LoopGroup:
    def __init__(self, start_time: float, repeat_count: int):
        self.start_time = start_time
        self.repeat_count = max(0, repeat_count - 1) + 1  
        self.commands: List[Command] = []
        
    def get_duration(self) -> float:
        if not self.commands: return 0
        return max(cmd.end_time for cmd in self.commands)

class VideoObject:
    def __init__(self, path: str, start_time: float):
        self.path = path.replace('\\', '/')
        self.start_time = start_time

class Sprite:
    def __init__(self, layer: str, origin: str, path: str, default_x: float, default_y: float):
        self.layer = layer
        self.origin = origin
        self.path = path.replace('\\', '/')
        self.default_x = default_x
        self.default_y = default_y
        
        self.commands: Dict[str, List[Command]] = {
            'F': [], 'S': [], 'V': [], 'R': [], 'M': [], 
            'MX': [], 'MY': [], 'C': [], 'P': []
        }
        self.loops: List[LoopGroup] = []
        self.start_time = 1e18
        self.end_time = -1e18

    def add_command(self, cmd: Command):
        self.commands[cmd.cmd_type].append(cmd)

    def unroll_loops(self):
        for loop in self.loops:
            loop_duration = loop.get_duration()
            for iteration in range(loop.repeat_count):
                time_offset = loop.start_time + iteration * loop_duration
                for cmd in loop.commands:
                    abs_cmd = Command(cmd.cmd_type, cmd.easing, time_offset + cmd.start_time, 
                                      time_offset + cmd.end_time, cmd.start_val, cmd.end_val)
                    self.add_command(abs_cmd)
        self.loops.clear()

    def finalize(self):
        self.unroll_loops()
        has_commands = False
        
        for cmd_list in self.commands.values():
            if cmd_list:
                has_commands = True
                for cmd in cmd_list:
                    self.start_time = min(self.start_time, cmd.start_time)
                    self.end_time = max(self.end_time, cmd.end_time)

        if not has_commands:
            if self.layer == "Background":
                self.start_time = -1e18
                self.end_time = 1e18
            else:
                self.start_time = 0
                self.end_time = 0
        
        for cmd_type in self.commands:
            self.commands[cmd_type].sort(key=lambda c: c.start_time)

class Animation(Sprite):
    def __init__(self, layer: str, origin: str, path: str, default_x: float, default_y: float, frame_count: int, frame_delay: float, loop_type: str):
        super().__init__(layer, origin, path, default_x, default_y)
        self.frame_count = frame_count
        self.frame_delay = frame_delay
        self.loop_type = loop_type

    def get_frame_index(self, time: float) -> int:
        if time < self.start_time: return 0
        elapsed = time - self.start_time
        if self.frame_delay <= 0: return 0
        frame = int(elapsed / self.frame_delay)
        if self.loop_type == "LoopForever":
            return frame % self.frame_count
        else:
            return min(frame, self.frame_count - 1)