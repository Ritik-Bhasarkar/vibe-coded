"""Window management: aggressively bring the terminal to the foreground.

Uses multiple techniques to bypass Windows' focus-stealing prevention:
1. Find the terminal window (console handle, or by class name)
2. AttachThreadInput to the foreground window's thread
3. Simulate Alt keypress to unlock SetForegroundWindow
4. BringWindowToTop + SetForegroundWindow
5. Flash taskbar as fallback
"""

from __future__ import annotations

import sys

from .config import Config


def maybe_maximize_window(config: Config) -> None:
    if not config.window.auto_maximize:
        return

    if sys.platform == "win32":
        _windows_focus()


def _find_terminal_window() -> int | None:
    """Find the terminal window handle.

    Tries GetConsoleWindow first (works in real console environments),
    then searches for known terminal window classes (Windows Terminal,
    mintty, ConEmu, etc.).
    """
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            return hwnd
    except Exception:
        pass

    try:
        import win32gui

        TERMINAL_CLASSES = {
            'CASCADIA_HOSTING_WINDOW_CLASS',  # Windows Terminal
            'ConsoleWindowClass',              # cmd.exe / PowerShell
            'mintty',                          # Git Bash mintty
            'VirtualConsoleClass',             # ConEmu
        }

        candidates = []

        def callback(h, _):
            try:
                if win32gui.IsWindowVisible(h):
                    cls = win32gui.GetClassName(h)
                    if cls in TERMINAL_CLASSES:
                        candidates.append(h)
            except Exception:
                pass
            return True

        win32gui.EnumWindows(callback, None)

        if candidates:
            # Prefer the foreground window if it's already a terminal
            fg = win32gui.GetForegroundWindow()
            if fg in candidates:
                return fg
            return candidates[0]
    except ImportError:
        pass

    return None


def _windows_focus() -> None:
    try:
        import ctypes
        import ctypes.wintypes
        import win32con
        import win32gui
        import win32process
    except ImportError:
        return

    try:
        hwnd = _find_terminal_window()
        if not hwnd:
            return

        # If minimized, restore first
        placement = win32gui.GetWindowPlacement(hwnd)
        if placement[1] == win32con.SW_SHOWMINIMIZED:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        # Check if already the foreground window
        if win32gui.GetForegroundWindow() == hwnd:
            return

        # --- Aggressive foreground technique ---
        # Attach our thread to the foreground window's thread,
        # which gives us permission to call SetForegroundWindow.
        foreground_hwnd = win32gui.GetForegroundWindow()
        our_tid = ctypes.windll.kernel32.GetCurrentThreadId()
        fg_tid, _ = win32process.GetWindowThreadProcessId(foreground_hwnd)

        attached = False
        if our_tid != fg_tid:
            attached = ctypes.windll.user32.AttachThreadInput(our_tid, fg_tid, True)

        try:
            # Simulate Alt key press/release — this tricks Windows into
            # allowing SetForegroundWindow from a background process.
            ctypes.windll.user32.keybd_event(0x12, 0, 0x0001, 0)  # Alt down
            ctypes.windll.user32.keybd_event(0x12, 0, 0x0003, 0)  # Alt up

            win32gui.BringWindowToTop(hwnd)
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            _flash_taskbar(hwnd)
        finally:
            if attached:
                ctypes.windll.user32.AttachThreadInput(our_tid, fg_tid, False)

    except Exception:
        pass


def _flash_taskbar(hwnd: int) -> None:
    """Flash the taskbar button as a fallback attention signal."""
    try:
        import ctypes
        import ctypes.wintypes

        class FLASHWINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize",    ctypes.c_uint),
                ("hwnd",      ctypes.wintypes.HWND),
                ("dwFlags",   ctypes.c_uint),
                ("uCount",    ctypes.c_uint),
                ("dwTimeout", ctypes.c_uint),
            ]

        FLASHW_ALL = 0x00000003
        FLASHW_TIMERNOFG = 0x0000000C

        fi = FLASHWINFO(
            cbSize=ctypes.sizeof(FLASHWINFO),
            hwnd=hwnd,
            dwFlags=FLASHW_ALL | FLASHW_TIMERNOFG,
            uCount=5,
            dwTimeout=0,
        )
        ctypes.windll.user32.FlashWindowEx(ctypes.byref(fi))
    except Exception:
        pass
