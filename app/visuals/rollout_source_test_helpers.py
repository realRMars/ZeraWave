"""Bind reused historical source checks to the recorded rollout delta.

This inversion checks provenance, not neutral GPU pixels. Current routing has
separate numerical/native/decoded-owner tests; current shader drawing requires
the coordinated GPU evidence phase.
"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def pre_rollout_source(path,source):
    rows=json.loads((ROOT/'work/studio-audio-rollout-01/source-inverse.json').read_text(encoding='utf8'))
    row=rows[path]
    assert hashlib.sha256(source.encode('utf8')).hexdigest()==row['after_utf8_sha256'],'Source differs from reviewed inverse identity: '+path
    for hunk in reversed(row['hunks']):
        start=hunk['after_start'];end=start+len(hunk['after'])
        assert source[start:end]==hunk['after'],'Inverse source context mismatch'
        source=source[:start]+hunk['before']+source[end:]
    assert hashlib.sha256(source.encode('utf8')).hexdigest()==row['before_utf8_sha256']
    return source
