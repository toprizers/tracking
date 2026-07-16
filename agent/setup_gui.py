import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import subprocess
import threading


class SetupGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Employee Monitor - Setup")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        self.create_widgets()
        self.load_existing_config()

    def create_widgets(self):
        header = tk.Frame(self.root, bg="#1a1a2e", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="Employee Monitor", font=("Segoe UI", 18, "bold"),
                fg="white", bg="#1a1a2e").pack(pady=10)
        tk.Label(header, text="Setup Configuration", font=("Segoe UI", 10),
                fg="#aaa", bg="#1a1a2e").pack()

        form = tk.Frame(self.root, padx=30, pady=20)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Server URL:", font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
        self.server_entry = tk.Entry(form, font=("Segoe UI", 11), width=50)
        self.server_entry.pack(pady=(0, 10), ipady=4)
        self.server_entry.insert(0, "http://")

        tk.Label(form, text="Agent Key:", font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
        self.key_entry = tk.Entry(form, font=("Segoe UI", 11), width=50)
        self.key_entry.pack(pady=(0, 10), ipady=4)

        tk.Label(form, text="Employee Name (optional):", font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
        self.name_entry = tk.Entry(form, font=("Segoe UI", 11), width=50)
        self.name_entry.pack(pady=(0, 15), ipady=4)

        btn_frame = tk.Frame(form)
        btn_frame.pack(fill="x")

        self.test_btn = tk.Button(btn_frame, text="Test Connection", font=("Segoe UI", 10),
                                  bg="#ffc107", fg="black", padx=15, pady=8, command=self.test_connection)
        self.test_btn.pack(side="left")

        self.save_btn = tk.Button(btn_frame, text="Save & Start", font=("Segoe UI", 10, "bold"),
                                  bg="#198754", fg="white", padx=20, pady=8, command=self.save_and_start)
        self.save_btn.pack(side="right")

        self.status_label = tk.Label(form, text="", font=("Segoe UI", 9))
        self.status_label.pack(pady=10)

        self.progress = ttk.Progressbar(form, mode='indeterminate')

    def load_existing_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            self.server_entry.delete(0, tk.END)
            self.server_entry.insert(0, config.get('server_url', 'http://'))
            self.key_entry.delete(0, tk.END)
            self.key_entry.insert(0, config.get('agent_key', ''))

    def test_connection(self):
        server = self.server_entry.get().strip()
        key = self.key_entry.get().strip()

        if not server or not key:
            messagebox.showwarning("Warning", "Please enter Server URL and Agent Key")
            return

        self.status_label.config(text="Testing connection...", fg="#666")
        self.test_btn.config(state="disabled")

        def do_test():
            try:
                import requests
                resp = requests.post(f"{server}/api/agent/heartbeat",
                                   json={"agent_key": key}, timeout=5)
                if resp.status_code == 200:
                    self.status_label.config(text="Connected successfully!", fg="green")
                else:
                    self.status_label.config(text="Connection failed - check credentials", fg="red")
            except Exception as e:
                self.status_label.config(text=f"Error: {str(e)[:50]}", fg="red")
            finally:
                self.test_btn.config(state="normal")

        threading.Thread(target=do_test, daemon=True).start()

    def save_and_start(self):
        server = self.server_entry.get().strip()
        key = self.key_entry.get().strip()

        if not server or not key:
            messagebox.showwarning("Warning", "Please enter Server URL and Agent Key")
            return

        config = {
            "server_url": server,
            "agent_key": key,
            "screenshot_interval": 1800,
            "idle_threshold": 900,
            "activity_check_interval": 60,
            "input_test_interval": 300,
            "max_retries": 3,
            "retry_delay": 10
        }

        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)

        self.status_label.config(text="Config saved! Starting agent...", fg="green")
        self.progress.pack(fill="x", pady=5)
        self.progress.start()

        def start_agent():
            try:
                main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
                subprocess.Popen([sys.executable, main_py],
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                self.root.after(1000, lambda: messagebox.showinfo("Success",
                    "Agent started successfully!\n\nYou can close this window.\nAgent is running in background."))
                self.root.after(1500, self.root.destroy)
            except Exception as e:
                self.status_label.config(text=f"Error starting agent: {e}", fg="red")
                self.progress.stop()

        threading.Thread(target=start_agent, daemon=True).start()

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = SetupGUI()
    app.run()
