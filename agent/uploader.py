import requests
import time
import os
from datetime import datetime


class ServerUploader:
    def __init__(self, server_url, agent_key):
        self.server_url = server_url.rstrip('/')
        self.agent_key = agent_key
        self.session = requests.Session()
        self.session.headers.update({'X-Agent-Key': agent_key})

    def _url(self, endpoint):
        return f"{self.server_url}{endpoint}"

    def heartbeat(self):
        try:
            resp = self.session.post(
                self._url('/api/agent/heartbeat'),
                json={'agent_key': self.agent_key},
                timeout=10
            )
            return resp.status_code == 200
        except requests.RequestException as e:
            print(f"[ERROR] Heartbeat failed: {e}")
            return False

    def upload_screenshot(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                files = {'screenshot': (os.path.basename(filepath), f, 'image/png')}
                data = {'agent_key': self.agent_key}
                resp = self.session.post(
                    self._url('/api/agent/screenshot'),
                    files=files,
                    data=data,
                    timeout=30
                )
            return resp.status_code == 200
        except requests.RequestException as e:
            print(f"[ERROR] Screenshot upload failed: {e}")
            return False

    def report_activity(self, stats, active_window=None):
        try:
            payload = {
                'agent_key': self.agent_key,
                'type': 'activity',
                'mouse_clicks': stats.get('mouse_clicks', 0),
                'keystrokes': stats.get('keystrokes', 0),
                'mouse_movement': stats.get('mouse_movement', 0.0),
                'idle_time': stats.get('idle_time', 0),
                'active_window': active_window
            }
            resp = self.session.post(
                self._url('/api/agent/activity'),
                json=payload,
                timeout=10
            )
            return resp.status_code == 200
        except requests.RequestException as e:
            print(f"[ERROR] Activity report failed: {e}")
            return False

    def report_input_status(self, mouse_works=True, keyboard_works=True):
        try:
            payload = {
                'agent_key': self.agent_key,
                'mouse_works': mouse_works,
                'keyboard_works': keyboard_works
            }
            resp = self.session.post(
                self._url('/api/agent/input-status'),
                json=payload,
                timeout=10
            )
            return resp.status_code == 200
        except requests.RequestException as e:
            print(f"[ERROR] Input status report failed: {e}")
            return False

    def report_status(self, status='active'):
        try:
            payload = {
                'agent_key': self.agent_key,
                'status': status
            }
            resp = self.session.post(
                self._url('/api/agent/status'),
                json=payload,
                timeout=10
            )
            return resp.status_code == 200
        except requests.RequestException as e:
            print(f"[ERROR] Status report failed: {e}")
            return False

    def upload_live_screen(self, screenshot_bytes):
        try:
            files = {'screenshot': ('live.png', screenshot_bytes, 'image/png')}
            data = {'agent_key': self.agent_key}
            resp = self.session.post(
                self._url('/api/agent/live-screen'),
                files=files,
                data=data,
                timeout=10
            )
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def test_connection(self):
        try:
            resp = self.session.post(
                self._url('/api/agent/heartbeat'),
                json={'agent_key': self.agent_key},
                timeout=5
            )
            return resp.status_code == 200
        except requests.RequestException:
            return False
