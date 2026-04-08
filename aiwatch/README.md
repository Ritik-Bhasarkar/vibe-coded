# aiwatch

> Never miss an AI CLI approval prompt again.

`aiwatch` wraps any AI CLI tool (aider, claude-code, open-interpreter, …) inside a PTY and plays a **kitchen bell sound** + optionally **raises your terminal window** the moment the CLI pauses waiting for your approval.

---

## How it works

```
You  ──keyboard──►  aiwatch  ──PTY──►  aider / claude / interpreter
                        │
                   scans output
                   for approval prompts
                        │
               ┌────────┴─────────┐
          plays bell          raises window
         (once per pause)    (if minimised)
```

The CLI runs inside a **Windows ConPTY** (or Unix PTY on Linux/macOS), so colours, cursor movement, and interactive prompts all work exactly as normal. `aiwatch` is invisible to the wrapped tool.

---

## Installation

### Windows (recommended)

```bat
git clone <this-repo>
cd aiwatch
install.bat
```

Or manually:

```bat
pip install -e ".[toml]"
```

### Linux / macOS

```bash
pip install -e ".[toml]"
```

> **Note:** `pywinpty` and `pywin32` are Windows-only and install automatically only on Windows.

---

## Dependencies

| Package | Platform | Purpose |
|---|---|---|
| `pywinpty` | Windows | ConPTY wrapper (full terminal fidelity) |
| `pywin32` | Windows | Window focus / tiling detection |
| `tomli` | Python < 3.11 | TOML config parsing |
| `playsound` *(optional)* | All | Play MP3 custom sounds |

---

## Usage

```bash
# Wrap any AI CLI
aiwatch run aider .
aiwatch run aider --model gpt-4o .

aiwatch run claude .

aiwatch run interpreter
aiwatch run python -m aider

# Any command works
aiwatch run python my_script.py
```

All output passes through normally — aiwatch is transparent.

---

## Configuration

Copy `aiwatch.toml` to `~/.aiwatch.toml` (user-level) or keep one in your project directory.

```toml
[sound]
# Disable the bell
enabled = true

# Custom sound file (WAV built-in; MP3 needs: pip install playsound)
file = ""   # empty = auto-generated kitchen bell

[window]
# Restore + focus the terminal if minimised when a prompt fires
# Tiled/split-screen windows are never maximised (taskbar flashes instead)
auto_maximize = true
```

### Using a custom bell sound

```toml
[sound]
file = "C:/Users/you/sounds/my-bell.wav"
```

The default bell is generated on first run and saved to `~/.aiwatch/bell.wav`. You can replace that file directly.

---

## Behaviour details

### Bell
- Fires **once** per pause event.
- Re-arms when the CLI produces new output (i.e. after you respond).
- Thread-safe; never blocks the output stream.

### Window management (Windows)
| Window state | Action |
|---|---|
| Minimised | Restore + bring to foreground |
| Off-screen (disconnected monitor) | Restore + bring to foreground |
| Tiled / split-screen (< 55% monitor area) | Flash taskbar button only |
| Visible, full-screen or near-full | Bring to foreground |

### Detected prompts (built-in patterns)
`(y/n)`, `[Y/n]`, `(yes/no)`, `Allow this action`, `Press Enter to continue`,
`Do you want to`, `Shall I`, `Approve?`, `Confirm?`, `Continue?`, `Proceed?`,
`Trust this`, `Run this command`, `Execute?`, `Ok to run`, `Permit?`

---

## Supported AI CLIs

| Tool | Command |
|---|---|
| [aider](https://aider.chat) | `aiwatch run aider .` |
| [Claude Code](https://claude.ai/code) | `aiwatch run claude .` |
| [Open Interpreter](https://openinterpreter.com) | `aiwatch run interpreter` |
| Any CLI | `aiwatch run <command> [args...]` |

---

## Troubleshooting

**Bell doesn't play**
- Run `python -c "import winsound; winsound.MessageBeep()"` – if this fails, check audio drivers.
- Check `~/.aiwatch/bell.wav` exists (delete it to regenerate).

**pywin32 errors**
- Run `pip install pywin32` then `python Scripts/pywin32_postinstall.py -install`.

**pywinpty not found (pipe mode warning)**
- Run `pip install pywinpty`.
- Requires Windows 10 version 1809 or later.

**Command not found after install**
- Make sure your Python `Scripts/` folder is in `PATH`.
- Or run directly: `python -m aiwatch run aider .`

---

## Project layout

```
aiwatch/
├── aiwatch/
│   ├── __main__.py        CLI entry point
│   ├── watcher.py         PTY wrapper + pattern detection
│   ├── notifier.py        Bell sound playback
│   ├── window_manager.py  Window focus / tiling logic (Windows)
│   ├── config.py          Config loading (aiwatch.toml)
│   └── bell_gen.py        Generates default bell.wav
├── aiwatch.toml           Example / default config
├── pyproject.toml
└── install.bat            Windows one-click installer
```
