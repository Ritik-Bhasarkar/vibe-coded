"""Config loading for aiwatch.

Searches for aiwatch.toml in:
  1. Current working directory  (./aiwatch.toml)
  2. User home directory        (~/.aiwatch.toml)

The first file found wins.  Missing keys fall back to defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


# Default patterns that indicate the AI tool is waiting for human input.
# These are matched (case-insensitive) against the last few lines of output.
DEFAULT_PROMPT_PATTERNS: List[str] = [
    # Claude Code permission / approval prompts
    r"\(y\b",                    # (y/n), (Y/n), etc.
    r"\by/n\b",                  # y/n anywhere
    r"\byes/no\b",               # yes/no
    r"\ballow\b.*\bdeny\b",      # Allow ... Deny
    r"\bdeny\b.*\ballow\b",      # Deny ... Allow
    r"\balways allow\b",         # Always allow
    r"\bdo you want\b",          # Do you want to ...
    r"\?\s*$",                   # Line ending with ?
    r"\bproceed\b.*\?",          # "proceed?" prompts
    r"\bconfirm\b.*\?",          # "confirm?" prompts
    r"\bapprove\b",              # approve prompts
    r"\bwait(?:ing)?\s+for\b.*\binput\b",  # "waiting for input"
    # Generic interactive prompts
    r">\s*$",                    # Line ending with >
    r"❯\s*$",                    # Line ending with ❯
    r"\$\s*$",                   # Line ending with $
    r"\binput\b.*:\s*$",         # "Input:" style prompts
    r"press\s+(?:enter|any\s+key)",  # Press enter / any key
]


@dataclass
class SoundConfig:
    enabled: bool = True
    # Empty string → use auto-generated bell in ~/.aiwatch/bell.wav
    file: str = ""


@dataclass
class WindowConfig:
    # Bring terminal to foreground when prompt is detected
    auto_maximize: bool = True


@dataclass
class Config:
    sound: SoundConfig = field(default_factory=SoundConfig)
    window: WindowConfig = field(default_factory=WindowConfig)
    # Fire bell after this many seconds of no screen activity
    silence_timeout: float = 5.0
    # Regex patterns that indicate the tool is waiting for human input.
    # Bell only fires when silence follows output matching one of these.
    prompt_patterns: List[str] = field(
        default_factory=lambda: list(DEFAULT_PROMPT_PATTERNS)
    )


def load_config() -> Config:
    config = Config()

    for path in [Path("./aiwatch.toml"), Path.home() / ".aiwatch.toml"]:
        if path.exists():
            _apply_toml(config, path)
            break

    return config


def _apply_toml(config: Config, path: Path) -> None:
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # pip install tomli
        except ImportError:
            return  # silently use defaults

    try:
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
    except Exception:
        return

    if sound := data.get("sound", {}):
        if "enabled" in sound:
            config.sound.enabled = bool(sound["enabled"])
        if "file" in sound:
            config.sound.file = str(sound["file"])

    if window := data.get("window", {}):
        if "auto_maximize" in window:
            config.window.auto_maximize = bool(window["auto_maximize"])

    if "silence_timeout" in data:
        config.silence_timeout = float(data["silence_timeout"])

    if "prompt_patterns" in data:
        patterns = data["prompt_patterns"]
        if isinstance(patterns, list):
            config.prompt_patterns = [str(p) for p in patterns]
