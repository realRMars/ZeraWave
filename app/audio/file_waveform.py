"""Bounded read-only file overview; no playback, analysis or stream ownership."""
import numpy as np
from studio_transport import Decoder


def envelope(path, cancelled, buckets=2048):
    decoder=Decoder(path)
    try:
        size=min(buckets,decoder.frames)
        lows=np.full(size,np.inf,dtype=np.float32);highs=-lows.copy();position=0
        while position<decoder.frames:
            if cancelled.is_set():return None
            pcm=decoder.raw(min(65536,decoder.frames-position))
            if not len(pcm):raise ValueError('File ended before its declared duration.')
            if not np.isfinite(pcm).all():raise ValueError('Nonfinite audio in waveform.')
            indices=(np.arange(position,position+len(pcm),dtype=np.int64)*size//decoder.frames)
            np.minimum.at(lows,indices,pcm.min(axis=1));np.maximum.at(highs,indices,pcm.max(axis=1))
            position+=len(pcm)
        return dict(path=decoder.path,duration=decoder.duration,peaks=np.column_stack((lows,highs)).tolist())
    finally:decoder.close()
