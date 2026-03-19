from core.models import Sprite, Animation
from core.easing import interpolate

class SpriteState:
    def __init__(self):
        self.x: float = 0.0
        self.y: float = 0.0
        self.scale: float = 1.0
        self.vector_scale_x: float = 1.0
        self.vector_scale_y: float = 1.0
        self.rotation: float = 0.0
        self.color: tuple = (255, 255, 255)
        self.alpha: float = 1.0
        
        self.flip_h: bool = False
        self.flip_v: bool = False
        self.additive: bool = False
        
        self.frame_index: int = 0

class MockCmd:
    def __init__(self, cmd_type, easing, start_time, end_time, start_val, end_val):
        self.cmd_type = cmd_type
        self.easing = easing
        self.start_time = start_time
        self.end_time = end_time
        self.start_val = start_val
        self.end_val = end_val

class TimelineEvaluator:
    def __init__(self, sprite: Sprite):
        self.sprite = sprite
        
        self.x_commands = []
        self.y_commands = []
        
        for cmd in sprite.commands['M']:
            self.x_commands.append(self._mock_cmd('MX', cmd, 0))
            self.y_commands.append(self._mock_cmd('MY', cmd, 1))
            
        for cmd in sprite.commands['MX']:
            self.x_commands.append(self._mock_cmd('MX', cmd, 0))
        for cmd in sprite.commands['MY']:
            self.y_commands.append(self._mock_cmd('MY', cmd, 0))
            
        self.x_commands.sort(key=lambda c: c.start_time)
        self.y_commands.sort(key=lambda c: c.start_time)

    def _mock_cmd(self, type_name, original_cmd, index):
        return MockCmd(
            cmd_type=type_name,
            easing=original_cmd.easing,
            start_time=original_cmd.start_time,
            end_time=original_cmd.end_time,
            start_val=original_cmd.start_val[index],
            end_val=original_cmd.end_val[index]
        )

    def _evaluate_property(self, commands, time: float, default_value):
        if not commands:
            return default_value

        current_val = commands[0].start_val
        active_cmd = None
        last_ended_cmd = None

        for cmd in commands:
            if time >= cmd.end_time:
                if last_ended_cmd is None or cmd.end_time >= last_ended_cmd.end_time:
                    last_ended_cmd = cmd
                    current_val = cmd.end_val
            elif cmd.start_time <= time < cmd.end_time:
                active_cmd = cmd
                
        if active_cmd is not None:
            current_val = interpolate(
                time, 
                active_cmd.start_val, active_cmd.end_val, 
                active_cmd.start_time, active_cmd.end_time, 
                active_cmd.easing
            )

        return current_val

    def _evaluate_color(self, commands, time: float):
        if not commands:
            return (255, 255, 255)
        
        current_val = commands[0].start_val
        active_cmd = None
        last_ended_cmd = None

        for cmd in commands:
            if time >= cmd.end_time:
                if last_ended_cmd is None or cmd.end_time >= last_ended_cmd.end_time:
                    last_ended_cmd = cmd
                    current_val = cmd.end_val
            elif cmd.start_time <= time < cmd.end_time:
                active_cmd = cmd

        if active_cmd is not None:
            r = interpolate(time, active_cmd.start_val[0], active_cmd.end_val[0], active_cmd.start_time, active_cmd.end_time, active_cmd.easing)
            g = interpolate(time, active_cmd.start_val[1], active_cmd.end_val[1], active_cmd.start_time, active_cmd.end_time, active_cmd.easing)
            b = interpolate(time, active_cmd.start_val[2], active_cmd.end_val[2], active_cmd.start_time, active_cmd.end_time, active_cmd.easing)
            current_val = (r, g, b)

        return current_val

    def _evaluate_parameter(self, commands, time: float, param_type: str) -> bool:
        param_commands = [c for c in commands if c.start_val[0] == param_type]
        if not param_commands:
            return False

        current_val = False
        for cmd in param_commands:
            if time >= cmd.start_time:
                if time < cmd.end_time:
                    current_val = True
                else:
                    current_val = (cmd.start_time == cmd.end_time)
        return current_val

    def evaluate(self, time: float) -> SpriteState:
        state = SpriteState()
        
        state.x = self._evaluate_property(self.x_commands, time, self.sprite.default_x)
        state.y = self._evaluate_property(self.y_commands, time, self.sprite.default_y)
        
        state.scale = self._evaluate_property(
            [self._mock_cmd('S', c, 0) for c in self.sprite.commands['S']], time, 1.0)
        
        state.vector_scale_x = self._evaluate_property(
            [self._mock_cmd('V', c, 0) for c in self.sprite.commands['V']], time, 1.0)
        state.vector_scale_y = self._evaluate_property(
            [self._mock_cmd('V', c, 1) for c in self.sprite.commands['V']], time, 1.0)
            
        state.rotation = self._evaluate_property(
            [self._mock_cmd('R', c, 0) for c in self.sprite.commands['R']], time, 0.0)
            
        state.alpha = self._evaluate_property(
            [self._mock_cmd('F', c, 0) for c in self.sprite.commands['F']], time, 1.0)
            
        state.color = self._evaluate_color(self.sprite.commands['C'], time)
        
        state.flip_h = self._evaluate_parameter(self.sprite.commands['P'], time, "H")
        state.flip_v = self._evaluate_parameter(self.sprite.commands['P'], time, "V")
        state.additive = self._evaluate_parameter(self.sprite.commands['P'], time, "A")
        
        if isinstance(self.sprite, Animation):
            state.frame_index = self.sprite.get_frame_index(time)
            
        return state