class AudioFrame:
    """A snapshot of musical state, derived from already-processed audio bands.

    This sits between raw audio analysis and visual meaning: it names
    audio-domain concepts (bass/mids/highs/energy/impact/silence) without
    assigning any of them a visual purpose. Visual code decides what bass
    or impact *mean*; this object only describes what the music is doing.
    """

    def __init__(
        self,
        bass,
        mids,
        highs,
        bass_onset,
        mids_onset,
        highs_onset,
        silence_threshold=0.02,
        flux=0.0,
    ):
        self.bass = bass
        self.mids = mids
        self.highs = highs
        self.bass_onset = bass_onset
        self.mids_onset = mids_onset
        self.highs_onset = highs_onset
        self.flux = flux

        self.energy = (bass + mids + highs) / 3.0
        self.impact = max(bass_onset, mids_onset, highs_onset)
        self.is_silent = self.energy <= silence_threshold

        # Optional timing estimates are populated by the shared analysis path.
        self.rhythmic_activity = self.impact
        self.beat_confidence = 0.
        self.beat_phase = 0.
        self.beat_tick = False
        self.tempo = 0.
        self.band12 = None
        self.spectrum_frequencies = None
        self.spectrum_magnitudes = None
