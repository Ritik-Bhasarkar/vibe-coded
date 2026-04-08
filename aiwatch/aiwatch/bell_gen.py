"""Generate a kitchen bell WAV sound programmatically."""

import math
import struct
import wave
from pathlib import Path


def generate_bell_wav(output_path: Path, duration: float = 1.6) -> None:
    """
    Generate a bright kitchen-bell / service-bell ding.

    Uses inharmonic partials (like a real struck bell) with exponential
    decay.  No external dependencies required.
    """
    sample_rate = 44100
    n_samples = int(duration * sample_rate)

    # (frequency_hz, relative_amplitude, decay_rate)
    # Inharmonic ratios give the characteristic bell timbre.
    partials = [
        (1318.5, 1.00, 4.0),   # fundamental  (~E6)
        (2637.0, 0.55, 6.5),   # 2nd partial
        (4186.0, 0.30, 9.0),   # 3rd partial
        (5274.0, 0.15, 13.0),  # 4th partial
    ]

    samples = []
    peak = sum(amp for _, amp, _ in partials)

    for i in range(n_samples):
        t = i / sample_rate
        value = 0.0
        for freq, amp, decay in partials:
            envelope = math.exp(-t * decay)
            value += amp * envelope * math.sin(2.0 * math.pi * freq * t)

        # Normalize, scale to 16-bit range with slight headroom
        sample = int((value / peak) * 29000)
        samples.append(max(-32768, min(32767, sample)))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)   # 16-bit PCM
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{n_samples}h", *samples))
