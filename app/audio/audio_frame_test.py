from audio_frame import AudioFrame


def main():
    print("ZeraWave AudioFrame Test")
    print("-------------------------")

    quiet = AudioFrame(0.0, 0.01, 0.0, 0.0, 0.0, 0.0)
    assert quiet.is_silent
    assert quiet.energy == (0.0 + 0.01 + 0.0) / 3.0
    assert quiet.impact == 0.0
    assert quiet.rhythmic_activity == quiet.impact
    print(f"Quiet   -> energy={quiet.energy:.3f} silent={quiet.is_silent}")

    normal = AudioFrame(0.5, 0.4, 0.3, 0.2, 0.1, 0.0)
    assert not normal.is_silent
    assert normal.energy == (0.5 + 0.4 + 0.3) / 3.0
    assert normal.impact == 0.2
    print(f"Normal  -> energy={normal.energy:.3f} impact={normal.impact:.2f}")

    impact = AudioFrame(0.9, 0.7, 0.5, 0.8, 0.4, 0.6)
    assert impact.impact == 0.8
    assert impact.rhythmic_activity == 0.8
    assert not impact.is_silent
    print(f"Impact  -> energy={impact.energy:.3f} impact={impact.impact:.2f}")

    # Deterministic: identical inputs produce identical derived fields.
    repeat = AudioFrame(0.9, 0.7, 0.5, 0.8, 0.4, 0.6)
    assert repeat.energy == impact.energy
    assert repeat.impact == impact.impact
    assert repeat.is_silent == impact.is_silent

    default_flux = AudioFrame(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert default_flux.flux == 0.0

    with_flux = AudioFrame(
        0.5, 0.4, 0.3, 0.0, 0.0, 0.0, flux=1.25
    )
    assert with_flux.flux == 1.25

    print("\nAudioFrame assertions passed.")


if __name__ == "__main__":
    main()
