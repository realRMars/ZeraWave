class VisualParameterMapper:
    def map(self, bass, mids, highs, bass_onset, mids_onset, highs_onset):
        return {
            "scale": bass,
            "movement": mids,
            "sparkle": highs,
            "impact": max(
                bass_onset,
                mids_onset,
                highs_onset,
            ),
        }