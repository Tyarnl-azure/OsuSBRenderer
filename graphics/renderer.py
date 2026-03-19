import os
import cv2
import numpy as np
import math
from collections import OrderedDict
import config
from core.models import Sprite, Animation

ORIGIN_MAP = {
    "TopLeft": (0.0, 0.0),      "TopCentre": (0.5, 0.0),      "TopRight": (1.0, 0.0),
    "CentreLeft": (0.0, 0.5),   "Centre": (0.5, 0.5),         "CentreRight": (1.0, 0.5),
    "BottomLeft": (0.0, 1.0),   "BottomCentre": (0.5, 1.0),   "BottomRight": (1.0, 1.0)
}

class Renderer:
    def __init__(self, beatmap_dir: str, mem_limit_bytes: float = 512 * 1024 * 1024):
        self.beatmap_dir = beatmap_dir
        self.mem_limit_bytes = mem_limit_bytes
        self.current_mem_bytes = 0
        self.texture_cache = OrderedDict()
        
        self.black_frame = np.zeros((config.SCREEN_HEIGHT, config.SCREEN_WIDTH, 3), dtype=np.uint8)
        self.video_cap = None
        self.video_obj = None
        self.last_v_time = -1

    def init_video(self, video_obj):
        self.video_obj = video_obj
        if video_obj:
            vid_path = os.path.normpath(os.path.join(self.beatmap_dir, video_obj.path))
            if os.path.exists(vid_path):
                self.video_cap = cv2.VideoCapture(vid_path)

    def load_texture(self, path: str):
        normalized_path = os.path.normpath(os.path.join(self.beatmap_dir, path))

        if normalized_path in self.texture_cache:
            self.texture_cache.move_to_end(normalized_path)
            return self.texture_cache[normalized_path]
            
        if not os.path.exists(normalized_path):
            self.texture_cache[normalized_path] = None
            return None
            
        img = cv2.imread(normalized_path, cv2.IMREAD_UNCHANGED)
        
        if img is not None:
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
            elif img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        
        img_size = img.nbytes if img is not None else 0
        
        while self.current_mem_bytes + img_size > self.mem_limit_bytes and self.texture_cache:
            old_path, old_img = self.texture_cache.popitem(last=False)
            if old_img is not None:
                self.current_mem_bytes -= old_img.nbytes
                del old_img
                
        self.texture_cache[normalized_path] = img
        self.current_mem_bytes += img_size
        return img

    def get_sprite_texture(self, sprite: Sprite, state):
        if isinstance(sprite, Animation):
            base, ext = os.path.splitext(sprite.path)
            frame_path = f"{base}{state.frame_index}{ext}"
            return self.load_texture(frame_path)
        return self.load_texture(sprite.path)

    def draw_video(self, frame_bg, time_ms):
        if not self.video_cap or time_ms < self.video_obj.start_time:
            return
            
        elapsed_ms = time_ms - self.video_obj.start_time
        self.video_cap.set(cv2.CAP_PROP_POS_MSEC, elapsed_ms)
        ret, v_frame = self.video_cap.read()
        
        if ret and v_frame is not None:
            resized = cv2.resize(v_frame, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            frame_bg[:, :] = resized

    # Uses OpenCV WarpAffine for hardware-accelerated rotation, scaling, and positioning.
    # Handles additive blending and color transformations.
    def draw_sprite(self, frame_bg: np.ndarray, sprite: Sprite, state):
        if state.alpha <= 0.001 or state.scale == 0 or state.vector_scale_x == 0 or state.vector_scale_y == 0:
            return 
            
        img = self.get_sprite_texture(sprite, state)
        if img is None: return
            
        if state.flip_h or state.flip_v:
            flip_code = -1 if (state.flip_h and state.flip_v) else (1 if state.flip_h else 0)
            img = cv2.flip(img, flip_code)

        img_h, img_w = img.shape[:2]
        final_scale_x = state.scale * state.vector_scale_x * config.GLOBAL_SCALE
        final_scale_y = state.scale * state.vector_scale_y * config.GLOBAL_SCALE
        
        if (img_w <= 5 or img_h <= 5) and (final_scale_x > 2 or final_scale_y > 2):
            new_w = max(1, int(img_w * final_scale_x))
            new_h = max(1, int(img_h * final_scale_y))
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            img_w, img_h = new_w, new_h
            final_scale_x, final_scale_y = 1.0, 1.0
        
        screen_x = state.x * config.GLOBAL_SCALE + config.WIDESCREEN_OFFSET_X
        screen_y = state.y * config.GLOBAL_SCALE
        anchor_ratio_x, anchor_ratio_y = ORIGIN_MAP.get(sprite.origin, (0.0, 0.0))
        
        T1 = np.array([[1, 0, -img_w * anchor_ratio_x], [0, 1, -img_h * anchor_ratio_y], [0, 0, 1]])
        S = np.array([[final_scale_x, 0, 0], [0, final_scale_y, 0], [0, 0, 1]])
        cos_r, sin_r = math.cos(state.rotation), math.sin(state.rotation)
        R = np.array([[cos_r, -sin_r, 0], [sin_r, cos_r, 0], [0, 0, 1]])
        T2 = np.array([[1, 0, screen_x], [0, 1, screen_y], [0, 0, 1]])
        
        M = T2 @ R @ S @ T1
        
        corners = np.array([[0, 0, 1], [img_w, 0, 1], [0, img_h, 1], [img_w, img_h, 1]]).T
        transformed_corners = M @ corners
        min_x, max_x = int(np.floor(np.min(transformed_corners[0]))), int(np.ceil(np.max(transformed_corners[0])))
        min_y, max_y = int(np.floor(np.min(transformed_corners[1]))), int(np.ceil(np.max(transformed_corners[1])))
        
        intersect_min_x, intersect_max_x = max(0, min_x), min(config.SCREEN_WIDTH, max_x)
        intersect_min_y, intersect_max_y = max(0, min_y), min(config.SCREEN_HEIGHT, max_y)
        
        roi_w = intersect_max_x - intersect_min_x
        roi_h = intersect_max_y - intersect_min_y
        if roi_w <= 0 or roi_h <= 0: return  
            
        M[0, 2] -= intersect_min_x
        M[1, 2] -= intersect_min_y
        
        warped_img = cv2.warpAffine(img, M[:2], (roi_w, roi_h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
        
        color_bgr = np.array([state.color[2], state.color[1], state.color[0]], dtype=np.float32) / 255.0
        
        src_bgr = warped_img[:, :, :3].astype(np.float32)
        src_a = (warped_img[:, :, 3].astype(np.float32) / 255.0) * state.alpha
            
        src_bgr = src_bgr * color_bgr
        src_a_3d = np.expand_dims(src_a, axis=-1)
        
        dst_roi = frame_bg[intersect_min_y:intersect_max_y, intersect_min_x:intersect_max_x].astype(np.float32)
        
        if state.additive:
            blended = dst_roi + (src_bgr * src_a_3d)
            np.clip(blended, 0, 255, out=blended)
        else:
            blended = (src_bgr * src_a_3d) + dst_roi * (1.0 - src_a_3d)
            
        frame_bg[intersect_min_y:intersect_max_y, intersect_min_x:intersect_max_x] = blended.astype(np.uint8)

    def render_frame(self, layers: dict, evaluators: dict, time_ms: float) -> np.ndarray:
        frame = self.black_frame.copy()

        self.draw_video(frame, time_ms)
        
        layer_order = ["Background", "Fail", "Pass", "Foreground", "Overlay"]
        
        for layer_name in layer_order:
            if layer_name not in layers: continue
            for sprite in layers[layer_name]:
                if time_ms < sprite.start_time or time_ms > sprite.end_time:
                    continue
                
                evaluator = evaluators.get(sprite)
                if not evaluator: continue
                
                state = evaluator.evaluate(time_ms)
                self.draw_sprite(frame, sprite, state)
                
        return frame