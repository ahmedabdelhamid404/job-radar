import subprocess, smtplib, requests
from email.mime.text import MIMEText

def send_telegram(cfg, text):
    a = cfg["alerts"]
    if not (a.get("telegram") and a.get("telegram_token") and a.get("telegram_chat_id")):
        return False, "telegram off or unconfigured"
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{a['telegram_token']}/sendMessage",
            data={"chat_id": a["telegram_chat_id"], "text": text,
                  "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=15)
        return r.ok, r.text[:200]
    except Exception as e:
        return False, str(e)

def send_desktop(cfg, title, body):
    if not cfg["alerts"].get("desktop_popup"):
        return False, "off"
    try:
        subprocess.run(["notify-send", "-a", "Job Radar", title, body], check=False)
        return True, "ok"
    except Exception as e:
        return False, str(e)

def send_email(cfg, subject, body_html):
    a = cfg["alerts"]
    if not a.get("email"):
        return False, "off"
    try:
        msg = MIMEText(body_html, "html")
        msg["Subject"] = subject
        msg["From"] = a.get("smtp_user", "")
        msg["To"] = a.get("email_to", "")
        s = smtplib.SMTP(a["smtp_host"], int(a.get("smtp_port", 587)), timeout=20)
        s.starttls()
        s.login(a["smtp_user"], a["smtp_pass"])
        s.send_message(msg)
        s.quit()
        return True, "ok"
    except Exception as e:
        return False, str(e)
