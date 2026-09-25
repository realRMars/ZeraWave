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

    def map_frame(self, frame):
        return self.map(
            bass=frame.bass,
            mids=frame.mids,
            highs=frame.highs,
            bass_onset=frame.bass_onset,
            mids_onset=frame.mids_onset,
            highs_onset=frame.highs_onset,
        )
