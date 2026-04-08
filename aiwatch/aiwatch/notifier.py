"""Sound notification: play the bell exactly once per pause event."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

from .config import Config


def _default_bell_path() -> Path:
    """Return path to the bundled bell WAV, generating it on first run."""
    bell_path = Path.home() / ".aiwatch" / "bell.wav"
    if not bell_path.exists():
        from .bell_gen import generate_bell_wav
        generate_bell_wav(bell_path)
    return bell_path


def play_bell(config: Config) -> None:
    """Play the bell sound asynchronously (non-blocking)."""
    if not config.sound.enabled:
        return

    def _play() -> None:
        try:
            if config.sound.file:
                path = Path(config.sound.file)
                if not path.exists():
                    print(
                        f"[aiwatch] Warning: sound file not found: {path}",
                        file=sys.stderr,
                    )
                    _fallback_beep()
                    return
            else:
                path = _default_bell_path()

            _play_wav(path)
        except Exception as exc:
            # Never crash the watcher due to audio issues
            _fallback_beep()

    threading.Thread(target=_play, daemon=True).start()


def _play_wav(path: Path) -> None:
    if sys.platform == "win32":
        try:
            import winsound
            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            return
        except Exception:
            pass

    # Cross-platform fallback (requires: pip install playsound)
    try:
        from playsound import playsound
        playsound(str(path), block=False)
    except ImportError:
        _fallback_beep()


def _fallback_beep() -> None:
    """Last-resort: OS default alert sound."""
    if sys.platform == "win32":
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            return
        except Exception:
            pass
    print("\a", end="", flush=True)  # terminal bell character
