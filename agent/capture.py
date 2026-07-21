import os
import time
from datetime import datetime

try:
    import mss
    import mss.tools
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class ScreenCapture:
    def __init__(self, save_dir="screenshots"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

    def take_screenshot(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.save_dir, filename)

        if HAS_MSS:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=filepath)
        elif HAS_PIL:
            import subprocess
            if os.name == 'nt':
                subprocess.run(['powershell', '-command',
                    f'Add-Type -AssemblyName System.Windows.Forms; '
                    f'[System.Windows.Forms.Screen]::PrimaryScreen | ForEach-Object {{ '
                    f'$bmp = New-Object System.Drawing.Bitmap($_.Bounds.Width, $_.Bounds.Height); '
                    f'$graphics = [System.Drawing.Graphics]::FromImage($bmp); '
                    f'$graphics.CopyFromScreen($_.Bounds.Location, [System.Drawing.Point]::Empty, $_.Bounds.Size); '
                    f'$bmp.Save("{filepath}") }}'], capture_output=True)
            else:
                subprocess.run(['scrot', filepath], capture_output=True)
        else:
            print("[ERROR] No screenshot library available. Install mss: pip install mss")
            return None

        return filepath

    def compress_screenshot(self, filepath, max_size_kb=500):
        if not HAS_PIL:
            return filepath

        from PIL import Image
        img = Image.open(filepath)

        quality = 85
        while quality > 10:
            img.save(filepath, optimize=True, quality=quality)
            if os.path.getsize(filepath) <= max_size_kb * 1024:
                break
            quality -= 10

        return filepath

    def cleanup_old_screenshots(self, max_age_hours=24):
        now = time.time()
        for filename in os.listdir(self.save_dir):
            filepath = os.path.join(self.save_dir, filename)
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > max_age_hours * 3600:
                    os.remove(filepath)

    def take_screenshot_bytes(self):
        import io
        if HAS_MSS:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                png = mss.tools.to_png(screenshot.rgb, screenshot.size)
                return io.BytesIO(png)
        elif HAS_PIL:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            buf = io.BytesIO()
            img.save(buf, format='PNG', optimize=True)
            buf.seek(0)
            return buf
        return None
