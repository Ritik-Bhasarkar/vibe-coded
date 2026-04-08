"""Core watcher: monitor child process output for silence → bell + window focus.

Architecture (Windows)
----------------------
aiwatch spawns the child process inside a ConPTY (via pywinpty).
All output is read from the ConPTY and forwarded to the real stdout.
When output stops for `silence_timeout` seconds → bell + window focus.

The outer terminal is put in raw mode so that keystrokes are forwarded
immediately to the child (no double-echo, no line buffering).

Bell logic
----------
- After the child produces at least some output and then goes silent
  for `silence_timeout` seconds, the bell fires.
- After firing, the bell is disarmed until new output appears.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
import threading
from typing import List

from .config import Config, load_config
from .notifier import play_bell
from .window_manager import maybe_maximize_window


# Strip ANSI escape codes
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b\][^\x07]*\x07|\x1b.")

# How many characters of trailing output to keep for prompt detection
_TAIL_BUFFER_SIZE = 2000

# Module-level debug flag, set by run_watcher
_debug = False


def _dbg(msg: str) -> None:
    if _debug:
        print(f"[aiwatch-debug] {msg}", file=sys.stderr, flush=True)


def _clean(text: str) -> str:
    return ANSI_RE.sub("", text)


def _looks_like_prompt(tail: str, patterns: list[re.Pattern]) -> bool:
    """Check if the tail of output matches any prompt pattern."""
    cleaned = _clean(tail)
    # Check the last few non-empty lines
    lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
    last_lines = "\n".join(lines[-5:]) if lines else ""
    if not last_lines:
        return False
    for pat in patterns:
        if pat.search(last_lines):
            return True
    return False


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def _resolve_cmd(cmd: List[str]) -> List[str]:
    """Resolve the first element to a full path so subprocess can find it."""
    if cmd and not os.path.isabs(cmd[0]):
        resolved = shutil.which(cmd[0])
        if resolved:
            return [resolved] + cmd[1:]
    return cmd


def run_watcher(cmd: List[str], debug: bool = False) -> int:
    """Spawn *cmd*, monitor for halts, return exit code."""
    global _debug
    _debug = debug

    config = load_config()
    cmd = _resolve_cmd(cmd)

    print(
        f"[aiwatch] Monitoring: {' '.join(cmd)}",
        file=sys.stderr,
    )

    if sys.platform == "win32":
        return _monitor_windows(cmd, config)
    else:
        try:
            import pty  # noqa: F401
            return _pty_unix(cmd, config)
        except ImportError:
            return _pipe_fallback(cmd, config)


def run_test() -> None:
    """Test bell sound and window focus independently."""
    config = load_config()

    print("[aiwatch] Testing bell sound...", file=sys.stderr)
    # Play bell synchronously for testing
    from .notifier import _default_bell_path, _play_wav
    bell_path = _default_bell_path()
    print(f"[aiwatch] Bell file: {bell_path}", file=sys.stderr)
    try:
        _play_wav(bell_path)
        print("[aiwatch] Bell: OK", file=sys.stderr)
    except Exception as e:
        print(f"[aiwatch] Bell: FAILED - {e}", file=sys.stderr)

    time.sleep(1.5)  # let sound finish

    print("[aiwatch] Testing window focus...", file=sys.stderr)
    maybe_maximize_window(config)
    print("[aiwatch] Window focus: attempted", file=sys.stderr)

    # Diagnostic info
    print("\n[aiwatch] Diagnostics:", file=sys.stderr)
    print(f"  silence_timeout: {config.silence_timeout}s", file=sys.stderr)
    print(f"  sound.enabled: {config.sound.enabled}", file=sys.stderr)
    print(f"  sound.file: {config.sound.file or '(auto-generated)'}", file=sys.stderr)
    print(f"  window.auto_maximize: {config.window.auto_maximize}", file=sys.stderr)
    print(f"  prompt_patterns: {len(config.prompt_patterns)} patterns", file=sys.stderr)

    if sys.platform == "win32":
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        stdin_h = ctypes.windll.kernel32.GetStdHandle(0xFFFFFFF6)  # STD_INPUT_HANDLE
        mode = ctypes.c_ulong()
        has_console = ctypes.windll.kernel32.GetConsoleMode(stdin_h, ctypes.byref(mode))
        print(f"  console window: {'yes' if hwnd else 'no (mintty/ConPTY)'}", file=sys.stderr)
        print(f"  real console mode: {'yes' if has_console else 'no'}", file=sys.stderr)
        try:
            from winpty import PTY  # noqa: F401
            print("  pywinpty: available", file=sys.stderr)
        except ImportError:
            print("  pywinpty: NOT AVAILABLE (install with: pip install pywinpty)", file=sys.stderr)


# ---------------------------------------------------------------------------
# Windows: ConPTY monitoring via pywinpty
# ---------------------------------------------------------------------------

def _build_conpty_cmd(cmd: List[str]) -> tuple[str, str | None]:
    """Build (appname, cmdline) for ConPTY spawn.

    For .cmd/.bat files, wraps with cmd.exe /c.
    Returns (appname, cmdline_args_string_or_None).
    """
    exe = cmd[0]
    args = cmd[1:]
    ext = os.path.splitext(exe)[1].lower()

    if ext in ('.cmd', '.bat'):
        sysroot = os.environ.get('SYSTEMROOT', r'C:\Windows')
        appname = os.path.join(sysroot, 'System32', 'cmd.exe')
        # /c "path\to\file.cmd" arg1 arg2 ...
        parts = ['/c', f'"{exe}"'] + [_quote_arg(a) for a in args]
        return appname, ' '.join(parts)
    else:
        appname = exe
        if args:
            return appname, ' '.join(_quote_arg(a) for a in args)
        return appname, None


def _quote_arg(arg: str) -> str:
    """Quote a command-line argument if needed."""
    if ' ' in arg or '"' in arg or '&' in arg or '^' in arg:
        return f'"{arg}"'
    return arg


def _set_raw_mode() -> tuple | None:
    """Put outer terminal in raw mode. Returns state for restoration."""
    if not sys.stdin.isatty():
        return None

    # Try stty (works in Git Bash, mintty, MSYS2)
    try:
        result = subprocess.run(
            ['stty', '-g'],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            old = result.stdout.strip()
            subprocess.run(['stty', 'raw', '-echo'], check=False, timeout=5)
            _dbg("Raw mode set via stty")
            return ('stty', old)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try Windows console mode
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(0xFFFFFFF6)  # STD_INPUT_HANDLE
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            old_mode = mode.value
            # Clear ENABLE_ECHO_INPUT (4), ENABLE_LINE_INPUT (2), ENABLE_PROCESSED_INPUT (1)
            new_mode = old_mode & ~0x0007
            # Add ENABLE_VIRTUAL_TERMINAL_INPUT (0x0200)
            new_mode |= 0x0200
            kernel32.SetConsoleMode(handle, new_mode)
            _dbg(f"Raw mode set via SetConsoleMode (0x{old_mode:04x} → 0x{new_mode:04x})")
            return ('console', (handle, old_mode))
    except Exception:
        pass

    _dbg("Could not set raw mode")
    return None


def _restore_tty(state: tuple | None) -> None:
    """Restore terminal to previous mode."""
    if state is None:
        return

    kind, data = state
    if kind == 'stty':
        try:
            subprocess.run(['stty', data], check=False, timeout=5)
            _dbg("Terminal restored via stty")
        except Exception:
            pass
    elif kind == 'console':
        try:
            import ctypes
            handle, old_mode = data
            ctypes.windll.kernel32.SetConsoleMode(handle, old_mode)
            _dbg(f"Terminal restored via SetConsoleMode (0x{old_mode:04x})")
        except Exception:
            pass


def _enable_vt_output() -> tuple | None:
    """Enable VT processing on stdout (for real Windows console)."""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(0xFFFFFFF5)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            old_mode = mode.value
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            new_mode = old_mode | 0x0004
            if kernel32.SetConsoleMode(handle, new_mode):
                _dbg("VT output processing enabled")
                return ('console_out', (handle, old_mode))
    except Exception:
        pass
    return None


def _restore_vt_output(state: tuple | None) -> None:
    if state is None:
        return
    try:
        import ctypes
        _, (handle, old_mode) = state
        ctypes.windll.kernel32.SetConsoleMode(handle, old_mode)
    except Exception:
        pass


def _monitor_windows(cmd: List[str], config: Config) -> int:
    """Launch command in ConPTY and monitor output for silence."""
    try:
        from winpty import PTY
    except ImportError:
        print(
            "[aiwatch] pywinpty not available, falling back to pipe mode.",
            file=sys.stderr,
        )
        return _pipe_fallback(cmd, config)

    # Get terminal size
    try:
        ts = os.get_terminal_size()
        cols, rows = ts.columns, ts.lines
    except Exception:
        cols, rows = 120, 30

    _dbg(f"Terminal size: {cols}x{rows}")

    # Create ConPTY
    pty = PTY(cols, rows)

    # Build command
    appname, cmdline_args = _build_conpty_cmd(cmd)
    _dbg(f"Spawning: appname={appname!r} cmdline={cmdline_args!r}")

    try:
        pty.spawn(appname, cmdline=cmdline_args)
    except Exception as e:
        print(f"[aiwatch] Failed to spawn in ConPTY: {e}", file=sys.stderr)
        print("[aiwatch] Falling back to direct execution.", file=sys.stderr)
        return _direct_fallback(cmd, config)

    _dbg(f"Child PID: {pty.pid}")

    # Put outer terminal in raw mode
    old_tty = _set_raw_mode()
    vt_state = _enable_vt_output()

    silence_timeout = config.silence_timeout
    compiled_patterns = [re.compile(p, re.IGNORECASE) for p in config.prompt_patterns]
    print(
        f"\r\n[aiwatch] Bell will ring after {silence_timeout}s when waiting for input.\r\n",
        file=sys.stderr, flush=True,
    )

    state = {
        'last_output': time.time(),
        'bell_armed': True,
        'has_output': False,
        'tail_buffer': '',
    }

    # -- Silence checker thread --
    def silence_checker() -> None:
        while pty.isalive():
            now = time.time()
            elapsed = now - state['last_output']
            if (
                state['has_output']
                and state['bell_armed']
                and elapsed > silence_timeout
                and pty.isalive()
                and _looks_like_prompt(state['tail_buffer'], compiled_patterns)
            ):
                state['bell_armed'] = False
                _dbg(f"Silence for {elapsed:.1f}s + prompt detected — ringing bell")
                play_bell(config)
                maybe_maximize_window(config)
            elif (
                state['has_output']
                and state['bell_armed']
                and elapsed > silence_timeout
                and pty.isalive()
            ):
                _dbg(f"Silence for {elapsed:.1f}s but no prompt pattern — skipping bell")
            time.sleep(0.3)

    threading.Thread(target=silence_checker, daemon=True).start()

    # -- Stdin forwarding thread --
    def stdin_reader() -> None:
        fd = sys.stdin.fileno()
        while pty.isalive():
            try:
                data = os.read(fd, 4096)
                if data:
                    pty.write(data.decode('utf-8', errors='replace'))
                else:
                    break
            except OSError:
                break

    threading.Thread(target=stdin_reader, daemon=True).start()

    # -- Terminal resize checker thread --
    def resize_checker() -> None:
        cur_cols, cur_rows = cols, rows
        while pty.isalive():
            try:
                ts = os.get_terminal_size()
                if ts.columns != cur_cols or ts.lines != cur_rows:
                    cur_cols, cur_rows = ts.columns, ts.lines
                    pty.set_size(cur_cols, cur_rows)
                    _dbg(f"Resized to {cur_cols}x{cur_rows}")
            except Exception:
                pass
            time.sleep(1)

    threading.Thread(target=resize_checker, daemon=True).start()

    # -- Main loop: read ConPTY output, forward to stdout --
    try:
        while pty.isalive():
            try:
                data = pty.read(blocking=False)
            except Exception:
                if not pty.isalive():
                    break
                time.sleep(0.05)
                continue

            if data:
                sys.stdout.write(data)
                sys.stdout.flush()
                state['last_output'] = time.time()
                state['bell_armed'] = True
                state['has_output'] = True
                # Keep a rolling tail buffer for prompt detection
                state['tail_buffer'] = (state['tail_buffer'] + data)[-_TAIL_BUFFER_SIZE:]
            else:
                time.sleep(0.05)

        # Drain remaining output
        try:
            data = pty.read(blocking=False)
            if data:
                sys.stdout.write(data)
                sys.stdout.flush()
        except Exception:
            pass

    except KeyboardInterrupt:
        try:
            pty.write('\x03')
            time.sleep(0.5)
        except Exception:
            pass
    finally:
        _restore_tty(old_tty)
        _restore_vt_output(vt_state)

    return pty.get_exitstatus() or 0


# ---------------------------------------------------------------------------
# Direct fallback: no monitoring, just run the command
# ---------------------------------------------------------------------------

def _direct_fallback(cmd: List[str], config: Config) -> int:
    """Run command directly when ConPTY is unavailable. No monitoring."""
    print("[aiwatch] Warning: running without monitoring.", file=sys.stderr)
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
    return proc.returncode or 0


# ---------------------------------------------------------------------------
# Unix PTY  (Linux / macOS)
# ---------------------------------------------------------------------------

def _pty_unix(cmd: List[str], config: Config) -> int:
    import pty
    import select
    import termios
    import tty

    old_settings = None
    stdin_fd = sys.stdin.fileno()

    if sys.stdin.isatty():
        old_settings = termios.tcgetattr(stdin_fd)
        tty.setraw(stdin_fd)

    master_fd, slave_fd = pty.openpty()

    try:
        import fcntl, struct
        ts = os.get_terminal_size()
        winsize = struct.pack("HHHH", ts.lines, ts.columns, 0, 0)
        fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)
    except Exception:
        pass

    proc = subprocess.Popen(
        cmd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        preexec_fn=os.setsid,
        close_fds=True,
    )
    os.close(slave_fd)

    bell_state = {
        "armed": True, "last_output": time.time(),
        "has_output": False, "tail_buffer": "",
    }
    stdout_fd = sys.stdout.fileno()
    silence_timeout = config.silence_timeout
    compiled_patterns = [re.compile(p, re.IGNORECASE) for p in config.prompt_patterns]

    def _silence_checker() -> None:
        while proc.poll() is None:
            if (
                bell_state["has_output"]
                and bell_state["armed"]
                and (time.time() - bell_state["last_output"]) > silence_timeout
                and _looks_like_prompt(bell_state["tail_buffer"], compiled_patterns)
            ):
                bell_state["armed"] = False
                play_bell(config)
                maybe_maximize_window(config)
            time.sleep(0.3)

    threading.Thread(target=_silence_checker, daemon=True).start()

    try:
        while True:
            try:
                readable, _, _ = select.select([master_fd, stdin_fd], [], [], 0.1)
            except Exception:
                break

            if master_fd in readable:
                try:
                    data = os.read(master_fd, 4096)
                except OSError:
                    break
                if not data:
                    break
                os.write(stdout_fd, data)
                text = data.decode("utf-8", errors="replace")
                bell_state["last_output"] = time.time()
                bell_state["armed"] = True
                bell_state["has_output"] = True
                bell_state["tail_buffer"] = (bell_state["tail_buffer"] + text)[-_TAIL_BUFFER_SIZE:]

            if stdin_fd in readable:
                try:
                    chunk = os.read(stdin_fd, 1024)
                    if chunk:
                        os.write(master_fd, chunk)
                except OSError:
                    break

            if proc.poll() is not None:
                break
    finally:
        if old_settings:
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)
        try:
            os.close(master_fd)
        except Exception:
            pass

    return proc.returncode or 0


# ---------------------------------------------------------------------------
# Pipe fallback  (no PTY – colours may be lost)
# ---------------------------------------------------------------------------

def _pipe_fallback(cmd: List[str], config: Config) -> int:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE,
        bufsize=0,
    )

    bell_state = {
        "armed": True, "last_output": time.time(),
        "has_output": False, "tail_buffer": "",
    }
    silence_timeout = config.silence_timeout
    compiled_patterns = [re.compile(p, re.IGNORECASE) for p in config.prompt_patterns]

    def _silence_checker() -> None:
        while proc.poll() is None:
            if (
                bell_state["has_output"]
                and bell_state["armed"]
                and (time.time() - bell_state["last_output"]) > silence_timeout
                and _looks_like_prompt(bell_state["tail_buffer"], compiled_patterns)
            ):
                bell_state["armed"] = False
                play_bell(config)
                maybe_maximize_window(config)
            time.sleep(0.3)

    threading.Thread(target=_silence_checker, daemon=True).start()

    def _forward_stdin() -> None:
        while proc.poll() is None:
            try:
                line = sys.stdin.readline()
                if line and proc.stdin:
                    proc.stdin.write(line.encode())
                    proc.stdin.flush()
            except Exception:
                break

    threading.Thread(target=_forward_stdin, daemon=True).start()

    assert proc.stdout
    for chunk in iter(lambda: proc.stdout.read(1024), b""):
        text = chunk.decode("utf-8", errors="replace")
        sys.stdout.write(text)
        sys.stdout.flush()
        bell_state["last_output"] = time.time()
        bell_state["armed"] = True
        bell_state["has_output"] = True
        bell_state["tail_buffer"] = (bell_state["tail_buffer"] + text)[-_TAIL_BUFFER_SIZE:]

    proc.wait()
    return proc.returncode or 0
