"""
notifier.py – Benachrichtigt den Nutzer auf zwei Wegen:
1. send_desktop_notification: native System-Benachrichtigung (best effort,
   plattformabhängig: notify-send / osascript / plyer).
2. show_alert_window: kleines eigenständiges Tkinter-Fenster, das offen
   bleibt, bis der Nutzer auf "OK" klickt – läuft in einem eigenen Thread,
   damit der Scraping-Loop nicht blockiert wird.
"""

import platform
import subprocess
import shutil
import threading


def send_desktop_notification(title, message):
    system = platform.system()
    try:
        if system == "Linux" and shutil.which("notify-send"):
            subprocess.run(["notify-send", title, message])
        elif system == "Darwin":
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script])
        elif system == "Windows":
            try:
                from plyer import notification
                notification.notify(title=title, message=message, timeout=10)
            except ImportError:
                print(f"[Notification] {title}: {message}")
        else:
            print(f"[Notification] {title}: {message}")
    except Exception as e:
        print(f"Konnte Systembenachrichtigung nicht senden: {e}")


def show_alert_window(title, message):
    """
    Öffnet ein kleines, immer-im-Vordergrund-Fenster mit der Alarmmeldung.
    Gibt den Thread zurück, damit der Aufrufer bei Bedarf darauf warten kann
    (z.B. im --once-Modus, damit der Prozess nicht sofort beendet wird).
    """

    def _run():
        import tkinter as tk

        root = tk.Tk()
        root.title(title)
        root.attributes("-topmost", True)
        root.geometry("420x180")
        tk.Label(root, text=title, font=("Helvetica", 14, "bold"), fg="#b30000").pack(pady=(15, 5))
        tk.Label(root, text=message, font=("Helvetica", 11), wraplength=380, justify="center").pack(pady=5)
        tk.Button(root, text="OK", command=root.destroy, width=10).pack(pady=15)
        root.mainloop()

    thread = threading.Thread(target=_run, daemon=False)
    thread.start()
    return thread
