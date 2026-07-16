import sys
import os

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False


def create_icon_image(color='#4CAF50'):
    size = 64
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.ellipse([4, 4, size-4, size-4], fill=color, outline='white', width=2)

    draw.ellipse([20, 20, 30, 30], fill='white')
    draw.ellipse([34, 20, 44, 30], fill='white')

    draw.arc([18, 28, 46, 48], 0, 180, fill='white', width=2)

    return image


class SystemTray:
    def __init__(self, agent_callback=None):
        self.agent = agent_callback
        self.tray = None
        self.is_running = False

        if not HAS_TRAY:
            print("[INFO] pystray not installed. System tray disabled.")
            print("[INFO] Install with: pip install pystray")
            return

    def start(self):
        if not HAS_TRAY:
            return

        menu = pystray.Menu(
            pystray.MenuItem('Employee Monitor', None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Status: Running', None, enabled=False),
            pystray.MenuItem('Take Screenshot Now', self._on_screenshot),
            pystray.MenuItem('Show Status', self._on_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Pause Monitoring', self._on_pause),
            pystray.MenuItem('Resume Monitoring', self._on_resume),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', self._on_exit)
        )

        self.tray = pystray.Icon(
            'EmployeeMonitor',
            create_icon_image(),
            'Employee Monitor - Running',
            menu
        )

        self.is_running = True
        self.tray.run()

    def stop(self):
        if self.tray:
            self.is_running = False
            self.tray.stop()

    def update_status(self, status, color='#4CAF50'):
        if self.tray:
            self.tray.icon = create_icon_image(color)
            self.tray.title = f'Employee Monitor - {status}'

    def _on_screenshot(self, icon, item):
        if self.agent:
            self.agent.take_screenshot_now()

    def _on_status(self, icon, item):
        if self.agent:
            stats = self.agent.get_status()
            print(f"\n=== Agent Status ===")
            print(f"Server: {stats.get('server', 'Unknown')}")
            print(f"Screenshots taken: {stats.get('screenshots', 0)}")
            print(f"Last screenshot: {stats.get('last_screenshot', 'Never')}")
            print(f"Uptime: {stats.get('uptime', 'Unknown')}")

    def _on_pause(self, icon, item):
        if self.agent:
            self.agent.pause()
            self.update_status('Paused', '#FF9800')

    def _on_resume(self, icon, item):
        if self.agent:
            self.agent.resume()
            self.update_status('Running', '#4CAF50')

    def _on_exit(self, icon, item):
        if self.agent:
            self.agent.stop()
        self.stop()
