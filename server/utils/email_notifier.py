import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os


class EmailNotifier:
    def __init__(self, smtp_server='smtp.gmail.com', smtp_port=587,
                 sender_email=None, sender_password=None):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email or os.environ.get('SMTP_EMAIL')
        self.sender_password = sender_password or os.environ.get('SMTP_PASSWORD')
        self.enabled = bool(self.sender_email and self.sender_password)

    def send_alert(self, to_email, subject, message, screenshot_path=None):
        if not self.enabled:
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject

            html = f"""
            <html>
            <body>
                <h2 style="color: #d32f2f;">Employee Monitor Alert</h2>
                <p>{message}</p>
                <hr>
                <p><small>This is an automated alert from Employee Monitoring System</small></p>
            </body>
            </html>
            """
            msg.attach(MIMEText(html, 'html'))

            if screenshot_path and os.path.exists(screenshot_path):
                with open(screenshot_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-Disposition', 'attachment', filename='screenshot.png')
                    msg.attach(img)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"[ERROR] Email send failed: {e}")
            return False

    def send_idle_alert(self, to_email, employee_name, idle_minutes):
        subject = f"Alert: {employee_name} idle for {idle_minutes} minutes"
        message = f"<strong>{employee_name}</strong> has been idle for <strong>{idle_minutes} minutes</strong>."
        return self.send_alert(to_email, subject, message)

    def send_input_failure_alert(self, to_email, employee_name, device):
        subject = f"Critical: {employee_name}'s {device} not responding"
        message = f"<strong>{employee_name}'s {device}</strong> is not responding! Please check the system."
        return self.send_alert(to_email, subject, message)
