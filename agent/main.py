import json
import time
import os
import sys
import signal
import logging
import threading
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_persistent_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_bundled_config_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'config.json')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')


def get_persistent_config_path():
    return os.path.join(get_persistent_dir(), 'config.json')


class MonitorAgent:
    def __init__(self, config_path):
        from capture import ScreenCapture
        from activity import ActivityTracker
        from uploader import ServerUploader

        self.running = False
        self.paused = False
        self.config = self.load_config(config_path)
        self.setup_dirs()

        self.capture = ScreenCapture(save_dir=self.screenshot_dir)
        self.tracker = ActivityTracker(
            idle_threshold=self.config.get('idle_threshold', 900)
        )
        self.uploader = ServerUploader(
            server_url=self.config['server_url'],
            agent_key=self.config['agent_key']
        )

        self.screenshot_count = 0
        self.start_time = datetime.now()
        self.last_screenshot_time = None
        self.tray = None
        self.live_screen_enabled = True

    def load_config(self, path):
        with open(path, 'r') as f:
            return json.load(f)

    def setup_dirs(self):
        base = get_persistent_dir()
        self.screenshot_dir = os.path.join(base, 'screenshots')
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def test_connection(self):
        logger.info("Testing server connection...")
        if self.uploader.test_connection():
            logger.info("Server connection successful!")
            return True
        else:
            logger.error("Cannot connect to server!")
            return False

    def capture_and_upload(self):
        if self.paused:
            return

        logger.info("Taking screenshot...")
        filepath = self.capture.take_screenshot()
        if filepath:
            self.capture.compress_screenshot(filepath)
            logger.info(f"Screenshot saved: {filepath}")
            if self.uploader.upload_screenshot(filepath):
                logger.info("Screenshot uploaded successfully!")
                self.screenshot_count += 1
                self.last_screenshot_time = datetime.now()
            else:
                logger.warning("Screenshot upload failed, will retry later")

    def report_activity(self):
        if self.paused:
            return

        stats = self.tracker.get_stats()
        window = self.tracker.get_active_window()
        if self.uploader.report_activity(stats, window):
            logger.info(f"Activity reported: clicks={stats['mouse_clicks']}, "
                       f"keys={stats['keystrokes']}, idle={stats['idle_time']}s")
        self.tracker.reset_stats()

    def check_input_devices(self):
        if self.paused:
            return

        results = self.tracker.test_input_devices()
        self.uploader.report_input_status(
            mouse_works=results['mouse_works'],
            keyboard_works=results['keyboard_works']
        )

    def capture_live_screen(self):
        if self.paused or not self.live_screen_enabled:
            return
        buf = self.capture.take_screenshot_bytes()
        if buf:
            self.uploader.upload_live_screen(buf.getvalue())

    def take_screenshot_now(self):
        logger.info("Manual screenshot triggered")
        self.capture_and_upload()

    def get_status(self):
        uptime = datetime.now() - self.start_time
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        return {
            'server': self.config['server_url'],
            'screenshots': self.screenshot_count,
            'last_screenshot': str(self.last_screenshot_time) if self.last_screenshot_time else 'Never',
            'uptime': f"{hours}h {minutes}m",
            'paused': self.paused
        }

    def pause(self):
        self.paused = True
        logger.info("Agent paused")

    def resume(self):
        self.paused = False
        logger.info("Agent resumed")

    def run(self):
        if not self.test_connection():
            logger.error("Fix server connection and try again.")
            return

        self.running = True
        self.tracker.start()
        self.uploader.report_status('active')

        screenshot_interval = self.config.get('screenshot_interval', 1800)
        activity_interval = self.config.get('activity_check_interval', 60)
        input_interval = self.config.get('input_test_interval', 300)
        heartbeat_interval = 60
        live_screen_interval = 5

        last_screenshot = 0
        last_activity = 0
        last_input_check = 0
        last_heartbeat = 0
        last_live_screen = 0

        logger.info(f"Agent started! Screenshot every {screenshot_interval}s, "
                    f"Live screen every {live_screen_interval}s, "
                    f"Activity check every {activity_interval}s")

        try:
            while self.running:
                if self.paused:
                    time.sleep(1)
                    continue

                now = time.time()

                if now - last_heartbeat >= heartbeat_interval:
                    self.uploader.heartbeat()
                    last_heartbeat = now

                if now - last_screenshot >= screenshot_interval:
                    self.capture_and_upload()
                    last_screenshot = now

                if now - last_activity >= activity_interval:
                    self.report_activity()
                    last_activity = now

                if now - last_input_check >= input_interval:
                    self.check_input_devices()
                    last_input_check = now

                if now - last_live_screen >= live_screen_interval:
                    self.capture_live_screen()
                    last_live_screen = now

                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Agent stopped by user")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        self.tracker.stop()
        self.uploader.report_status('offline')
        logger.info("Agent stopped")


def install_autostart():
    if sys.platform == 'win32':
        import winreg
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "EmployeeMonitor"
        app_path = os.path.abspath(sys.argv[0])

        is_exe = getattr(sys, 'frozen', False)
        cmd = app_path if is_exe else f'python "{app_path}"'

        try:
            reg_key = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, cmd)
            winreg.CloseKey(reg_key)
            print("[OK] Auto-start enabled in Windows Registry")
        except Exception as e:
            print(f"[ERROR] Failed to set auto-start: {e}")

    elif sys.platform == 'linux':
        autostart_dir = os.path.expanduser('~/.config/autostart')
        os.makedirs(autostart_dir, exist_ok=True)

        desktop_file = f"""[Desktop Entry]
Type=Application
Name=EmployeeMonitor
Exec=python3 {os.path.abspath(sys.argv[0])}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
        filepath = os.path.join(autostart_dir, 'employee-monitor.desktop')
        with open(filepath, 'w') as f:
            f.write(desktop_file)
        os.chmod(filepath, 0o755)
        print(f"[OK] Auto-start enabled: {filepath}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--install-autostart':
        install_autostart()
        return

    persistent_config = get_persistent_config_path()
    bundled_config = get_bundled_config_path()

    if os.path.exists(persistent_config):
        agent = MonitorAgent(persistent_config)
    elif os.path.exists(bundled_config):
        import shutil
        shutil.copy2(bundled_config, persistent_config)
        agent = MonitorAgent(persistent_config)
    else:
        print("ERROR: config.json not found!")
        print("Please configure server_url and agent_key in config.json")
        return

    def signal_handler(sig, frame):
        agent.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    agent.run()


if __name__ == '__main__':
    main()
