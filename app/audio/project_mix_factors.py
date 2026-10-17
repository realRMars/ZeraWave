"""Canonical authored gain/gate/balance factors; no decoding or document writes."""
from fractions import Fraction
import numpy as np

RATE = 48000

def curve_factors(recipe, frames, length):
    """Nonnegative canonical factors before the established float32 boundary."""
    parts=[np.full(len(frames), 0. if recipe['mute'] else recipe['gain'], np.float64)]
    if recipe['fade_in']:
        parts.append(np.clip(frames / recipe['fade_in'], 0, 1))
    if recipe['fade_out']:
        parts.append(np.clip((length - frames) / recipe['fade_out'], 0, 1))
    if recipe['envelope']:
        points = np.asarray(recipe['envelope'], float)
        parts.append(np.interp(frames, points[:, 0], points[:, 1]))
    return parts

def curve(recipe, frames, length):
    if recipe['mute']:
        return np.zeros(len(frames), np.float32)
    parts=curve_factors(recipe,frames,length);gain=parts[0]
    for part in parts[1:]:gain*=part
    return gain.astype(np.float32)

def balance_pcm(pcm, pan):
    """Legacy mono duplicate/center unity; linear stereo channel balance."""
    if pan > 0:
        pcm[:, 0] *= 1. - pan
    elif pan < 0:
        pcm[:, 1] *= 1. + pan
    return pcm

def eligible(track, tracks, buses):
    any_solo = any(t.get('solo', False) for t in tracks.values()) or any(b['solo'] for b in buses.values())
    return not track['audio']['mute'] and (not any_solo or track.get('solo', False) or buses.get(track.get('output'), {}).get('solo', False))

def clip_curve(item, samples, fps):
    clip = item['clip']
    local = (samples / RATE - float(Fraction(clip['start']) / fps)) * float(fps) + clip['audio_window']['offset']
    frames = samples / RATE * float(fps)
    gains = curve(clip['audio'], local, clip['audio_window']['duration'])
    for fade in item.get('transition_fades', []):
        phase = np.clip((frames - fade['start']) / fade['duration'], 0., 1.)
        gains *= phase if fade['side'] == 1 else 1. - phase
    return gains
