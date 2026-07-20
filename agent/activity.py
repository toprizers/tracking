import time
import threading

try:
    from pynput import mouse, keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

import platform
import subprocess


class ActivityTracker:
    def __init__(self, idle_threshold=900):
        self.idle_threshold = idle_threshold
        self.mouse_clicks = 0
        self.keystrokes = 0
        self.mouse_movement = 0.0
        self.last_activity_time = time.time()
        self.last_mouse_pos = (0, 0)
        self.is_tracking = False
        self.mouse_listener = None
        self.keyboard_listener = None

    def start(self):
        if not HAS_PYNPUT:
            print("[WARNING] pynput not available. Activity tracking disabled.")
            return

        self.is_tracking = True

        self.mouse_listener = mouse.Listener(
            on_click=self._on_click,
            on_move=self._on_move
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press
        )

        self.mouse_listener.start()
        self.keyboard_listener.start()

    def stop(self):
        self.is_tracking = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

    def _on_click(self, x, y, button, pressed):
        if pressed:
            self.mouse_clicks += 1
            self.last_activity_time = time.time()

    def _on_move(self, x, y):
        if self.last_mouse_pos != (0, 0):
            dx = abs(x - self.last_mouse_pos[0])
            dy = abs(y - self.last_mouse_pos[1])
            self.mouse_movement += (dx + dy)
            if (dx + dy) > 5:
                self.last_activity_time = time.time()
        self.last_mouse_pos = (x, y)

    def _on_key_press(self, key):
        self.keystrokes += 1
        self.last_activity_time = time.time()

    def get_idle_time(self):
        return int(time.time() - self.last_activity_time)

    def is_idle(self):
        return self.get_idle_time() >= self.idle_threshold

    def get_stats(self):
        idle_time = self.get_idle_time()
        stats = {
            'mouse_clicks': self.mouse_clicks,
            'keystrokes': self.keystrokes,
            'mouse_movement': round(self.mouse_movement, 2),
            'idle_time': idle_time,
            'is_idle': idle_time >= self.idle_threshold
        }
        return stats

    def reset_stats(self):
        self.mouse_clicks = 0
        self.keystrokes = 0
        self.mouse_movement = 0.0

    def get_active_window(self):
        try:
            if platform.system() == 'Windows':
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                return buff.value
            elif platform.system() == 'Linux':
                result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'],
                                       capture_output=True, text=True)
                return result.stdout.strip()
            elif platform.system() == 'Darwin':
                result = subprocess.run(['osascript', '-e',
                                        'tell application "System Events" to get name of first application process whose frontmost is true'],
                                       capture_output=True, text=True)
                return result.stdout.strip()
        except Exception:
            pass
        return "Unknown"

    def test_input_devices(self):
        results = {'mouse_works': True, 'keyboard_works': True}

        if not HAS_PYNPUT:
            results['mouse_works'] = False
            results['keyboard_works'] = False
            return results

        if self.mouse_listener:
            results['mouse_works'] = self.mouse_listener.is_alive()
        if self.keyboard_listener:
            results['keyboard_works'] = self.keyboard_listener.is_alive()

        return results
