"""
Contains Osu! specific easing functions for smooth value interpolation.
"""
import math
from enum import IntEnum

class Easing(IntEnum):
    None_ = 0
    Out = 1
    In = 2
    InQuad = 3
    OutQuad = 4
    InOutQuad = 5
    InCubic = 6
    OutCubic = 7
    InOutCubic = 8
    InQuart = 9
    OutQuart = 10
    InOutQuart = 11
    InQuint = 12
    OutQuint = 13
    InOutQuint = 14
    InSine = 15
    OutSine = 16
    InOutSine = 17
    InExpo = 18
    OutExpo = 19
    InOutExpo = 20
    InCirc = 21
    OutCirc = 22
    InOutCirc = 23
    InElastic = 24
    OutElastic = 25
    OutElasticHalf = 26
    OutElasticQuarter = 27
    InOutElastic = 28
    InBack = 29
    OutBack = 30
    InOutBack = 31
    InBounce = 32
    OutBounce = 33
    InOutBounce = 34
    OutPow10 = 35

def apply_easing(easing: int, time: float) -> float:
    """
    DefaultEasingFunction
    """
    if time == 0: return 0.0
    if time == 1: return 1.0

    elastic_const = 2 * math.pi / 0.3
    elastic_const2 = 0.3 / 4
    back_const = 1.70158
    back_const2 = back_const * 1.525
    bounce_const = 1 / 2.75
    
    expo_offset = 2 ** -10
    elastic_offset_full = 2 ** -11
    elastic_offset_half = (2 ** -10) * math.sin((0.5 - elastic_const2) * elastic_const)
    elastic_offset_quarter = (2 ** -10) * math.sin((0.25 - elastic_const2) * elastic_const)
    in_out_elastic_offset = (2 ** -10) * math.sin((1 - elastic_const2 * 1.5) * elastic_const / 1.5)

    if easing == Easing.None_: return time
    elif easing in (Easing.In, Easing.InQuad): return time * time
    elif easing in (Easing.Out, Easing.OutQuad): return time * (2 - time)
    elif easing == Easing.InOutQuad:
        if time < 0.5: return time * time * 2
        time -= 1; return time * time * -2 + 1
    elif easing == Easing.InCubic: return time * time * time
    elif easing == Easing.OutCubic: time -= 1; return time * time * time + 1
    elif easing == Easing.InOutCubic:
        if time < 0.5: return time * time * time * 4
        time -= 1; return time * time * time * 4 + 1
    elif easing == Easing.InQuart: return time * time * time * time
    elif easing == Easing.OutQuart: time -= 1; return 1 - time * time * time * time
    elif easing == Easing.InOutQuart:
        if time < 0.5: return time * time * time * time * 8
        time -= 1; return time * time * time * time * -8 + 1
    elif easing == Easing.InQuint: return time ** 5
    elif easing == Easing.OutQuint: time -= 1; return time ** 5 + 1
    elif easing == Easing.InOutQuint:
        if time < 0.5: return (time ** 5) * 16
        time -= 1; return (time ** 5) * 16 + 1
    elif easing == Easing.InSine: return 1 - math.cos(time * math.pi * 0.5)
    elif easing == Easing.OutSine: return math.sin(time * math.pi * 0.5)
    elif easing == Easing.InOutSine: return 0.5 - 0.5 * math.cos(math.pi * time)
    elif easing == Easing.InExpo: return math.pow(2, 10 * (time - 1)) + expo_offset * (time - 1)
    elif easing == Easing.OutExpo: return -math.pow(2, -10 * time) + 1 + expo_offset * time
    elif easing == Easing.InOutExpo:
        if time < 0.5: return 0.5 * (math.pow(2, 20 * time - 10) + expo_offset * (2 * time - 1))
        return 1 - 0.5 * (math.pow(2, -20 * time + 10) + expo_offset * (-2 * time + 1))
    elif easing == Easing.InCirc: return 1 - math.sqrt(1 - time * time)
    elif easing == Easing.OutCirc: time -= 1; return math.sqrt(1 - time * time)
    elif easing == Easing.InOutCirc:
        time *= 2
        if time < 1: return 0.5 - 0.5 * math.sqrt(1 - time * time)
        time -= 2; return 0.5 * math.sqrt(1 - time * time) + 0.5
    elif easing == Easing.InElastic:
        return -math.pow(2, -10 + 10 * time) * math.sin((1 - elastic_const2 - time) * elastic_const) + elastic_offset_full * (1 - time)
    elif easing == Easing.OutElastic:
        return math.pow(2, -10 * time) * math.sin((time - elastic_const2) * elastic_const) + 1 - elastic_offset_full * time
    elif easing == Easing.OutElasticHalf:
        return math.pow(2, -10 * time) * math.sin((0.5 * time - elastic_const2) * elastic_const) + 1 - elastic_offset_half * time
    elif easing == Easing.OutElasticQuarter:
        return math.pow(2, -10 * time) * math.sin((0.25 * time - elastic_const2) * elastic_const) + 1 - elastic_offset_quarter * time
    elif easing == Easing.InOutElastic:
        time *= 2
        if time < 1:
            time -= 1
            return -0.5 * (math.pow(2, 10 * time) * math.sin((1 - elastic_const2 * 1.5 - time) * elastic_const / 1.5) - in_out_elastic_offset * (1 - time))
        time -= 1
        return 0.5 * (math.pow(2, -10 * time) * math.sin((time - elastic_const2 * 1.5) * elastic_const / 1.5) - in_out_elastic_offset * time) + 1
    elif easing == Easing.InBack:
        return time * time * ((back_const + 1) * time - back_const)
    elif easing == Easing.OutBack:
        time -= 1; return time * time * ((back_const + 1) * time + back_const) + 1
    elif easing == Easing.InOutBack:
        time *= 2
        if time < 1: return 0.5 * time * time * ((back_const2 + 1) * time - back_const2)
        time -= 2; return 0.5 * (time * time * ((back_const2 + 1) * time + back_const2) + 2)
    elif easing in (Easing.InBounce, Easing.OutBounce, Easing.InOutBounce):
        def out_bounce(t):
            if t < bounce_const: return 7.5625 * t * t
            if t < 2 * bounce_const: t -= 1.5 * bounce_const; return 7.5625 * t * t + 0.75
            if t < 2.5 * bounce_const: t -= 2.25 * bounce_const; return 7.5625 * t * t + 0.9375
            t -= 2.625 * bounce_const; return 7.5625 * t * t + 0.984375

        if easing == Easing.OutBounce: return out_bounce(time)
        if easing == Easing.InBounce: return 1 - out_bounce(1 - time)
        if easing == Easing.InOutBounce:
            if time < 0.5: return 0.5 - 0.5 * out_bounce(1 - time * 2)
            return out_bounce((time - 0.5) * 2) * 0.5 + 0.5
    elif easing == Easing.OutPow10:
        time -= 1; return time * math.pow(abs(time), 9) + 1

    return time

def interpolate(time: float, start_val: float, end_val: float, start_time: float, end_time: float, easing: int) -> float:
    if start_time == end_time:
        return start_val
    if time <= start_time:
        return start_val
    if time >= end_time:
        return end_val
    
    duration = end_time - start_time
    progress = (time - start_time) / duration
    eased_progress = apply_easing(easing, progress)
    
    return start_val + eased_progress * (end_val - start_val)