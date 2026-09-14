# -*- coding: utf-8 -*-
"""
Mirro Launcher — приложение с жидкой анимированной кнопкой.
Эффект: переливающийся «металл» (ртуть/гелий) через движущиеся градиентные волны.
tkinter + Canvas, только stdlib.
"""
import sys, os, time, socket, subprocess, threading, webbrowser, math
from pathlib import Path

MIRRO = r"D:\Mirro"
CORE = os.path.join(MIRRO, "core", "mirro_core.py")
PORT = 3443
URL = f"http://127.0.0.1:{PORT}"

import tkinter as tk
from tkinter import scrolledtext


class LiquidButton(tk.Canvas):
    """
    Canvas-кнопка с «жидким» переливом:
    синусоидальные волны с градиентом цветов, движущиеся по часовой,
    создают эффект ртути/гелия. Клик = команда.
    """

    PALETTES = {
        "mercury": [(108, 92, 231), (142, 116, 255), (106, 90, 205), (162, 155, 254)],
        "helium": [(0, 190, 240), (90, 220, 255), (0, 130, 220), (140, 235, 255)],
        "water": [(0, 150, 255), (80, 200, 255), (0, 100, 220), (130, 220, 255)],
    }

    def __init__(self, master, command=None, palette="mercury", text="", height=64, **kw):
        # фикс. размер: ширина основного окна - отступы
        w = kw.pop("width", 440)
        super().__init__(master, width=w, height=height, highlightthickness=0, bg="#16161c", cursor="hand2", **kw)
        self.command = command
        self.colors = self.PALETTES[palette]
        self.t = 0.0
        self.phase = 0.0
        self.text = text
        self.h = height
        self.w = w

        self.bind("<Button-1>", self._click)
        self._animate()

    def _mix(self, c1, c2, k):
        return (int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3))

    def _hex(self, rgb):
        return "#%02x%02x%02x" % tuple(rgb)

    def _draw(self):
        self.delete("all")
        n = 4                          # число волн
        base = self.h / 2
        amp = 8                        # амплитуда волны
        octave = 2 * math.pi / self.w

        # рисуем волны снизу вверх (прозрачность наложением)
        for layer in range(4):
            color = self.colors[layer % len(self.colors)]
            y_off = layer * 6
            pts = []
            for x in range(0, self.w + 2, 2):
                k = 2 if layer % 2 == 0 else 3
                y = base + y_off + amp * math.sin(x * octave * k + self.phase + layer)
                pts.extend((x, y))
            # заполнение до низа
            pts.extend((self.w, self.h))
            pts.extend((0, self.h))
            # лёгкая прозрачность через стиль outline
            self.create_polygon(*pts, fill=self._hex(color), outline="")

        # блик «жидкости» сверху
        gloss = []
        for x in range(0, self.w + 2, 2):
            y = base - 14 + 4 * math.sin(x * octave * 2 + self.phase + 1.2)
            gloss.extend((x, y))
        gloss.extend((self.w, base + 4))
        gloss.extend((0, base + 4))
        self.create_polygon(*gloss, fill="#ffffff", stipple="gray50", outline="")

        # текст по центру
        cx, cy = self.w // 2, self.h // 2
        self.create_text(cx, cy, text=self.text, font=("Segoe UI", 17, "bold"),
                         fill="#ffffff", anchor="center")

    def _animate(self):
        self.phase += 0.07
        self._draw()
        self.after(40, self._animate)

    def _click(self, _):
        if self.command:
            self.command()

    def set_text(self, text):
        self.text = text
        self._draw()


class MirroLauncher:
    def __init__(self, root):
        self.root = root
        self.proc = None
        self.monitoring = False

        root.title("Mirro — Эволюционная нейросеть")
        root.geometry("520x720")
        root.configure(bg="#16161c")
        root.resizable(False, False)

        self.colors = {
            "bg": "#16161c", "panel": "#1e1e26", "accent": "#6c5ce7",
            "accent2": "#a29bfe", "text": "#e4e4ec", "muted": "#8a8a99",
            "success": "#00b894", "danger": "#e17055", "border": "#2c2c3a",
        }

        self._build_ui()
        self._update_status()

    def _build_ui(self):
        header = tk.Frame(self.root, bg=self.colors["panel"], height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="M", font=("Segoe UI", 22, "bold"),
                 fg="white", bg=self.colors["accent"], width=2, height=1).pack(side="left", padx=(16, 10), pady=12)
        tk.Label(header, text="Mirro", font=("Segoe UI", 18, "bold"),
                 fg=self.colors["text"], bg=self.colors["panel"]).pack(side="left")
        tk.Label(header, text="v0.2", font=("Segoe UI", 10),
                 fg=self.colors["muted"], bg=self.colors["panel"]).pack(side="left", padx=6)
        self.status_dot = tk.Canvas(header, width=14, height=14, bg=self.colors["panel"], highlightthickness=0)
        self.status_dot.pack(side="right", padx=(0, 16))
        self.dot = self.status_dot.create_oval(2, 2, 12, 12, fill="#666", outline="")

        self.lbl_status = tk.Label(self.root, text="Проверка...", font=("Segoe UI", 11),
                                   fg=self.colors["muted"], bg=self.colors["bg"])
        self.lbl_status.pack(pady=(14, 4))

        # Жидкая кнопка-металл (ртуть)
        self.liquid = LiquidButton(self.root, command=self.toggle, palette="mercury",
                                   text="ЗАПУСТИТЬ MIRRO", width=440, height=72)
        self.liquid.pack(padx=40, pady=12)

        # Переключатель палитры (вода/гелий/ртуть)
        theme_row = tk.Frame(self.root, bg=self.colors["bg"])
        theme_row.pack(fill="x", padx=40, pady=(0, 6))
        tk.Label(theme_row, text="Эффект:", font=("Segoe UI", 9), fg=self.colors["muted"],
                 bg=self.colors["bg"]).pack(side="left")
        for name, palette, label in [("Ртуть", "mercury", "Ртуть"),
                                     ("Вода", "water", "Вода"),
                                     ("Гелий", "helium", "Гелий")]:
            tk.Button(theme_row, text=label, font=("Segoe UI", 9),
                      bg=self.colors["panel"], fg=self.colors["text2"],
                      activebackground="#2a2a36", relief="flat", cursor="hand2",
                      command=lambda p=palette: self.set_liquid(p)).pack(side="left", padx=4)

        row = tk.Frame(self.root, bg=self.colors["bg"])
        row.pack(fill="x", padx=40, pady=4)

        self.btn_open = tk.Button(row, text="Открыть интерфейс", font=("Segoe UI", 10),
                                  bg=self.colors["panel"], fg=self.colors["accent2"],
                                  activebackground="#2a2a36", relief="flat", cursor="hand2",
                                  state="disabled", command=self.open_browser)
        self.btn_open.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_logs = tk.Button(row, text="Логи", font=("Segoe UI", 10),
                                  bg=self.colors["panel"], fg=self.colors["muted"],
                                  activebackground="#2a2a36", relief="flat", cursor="hand2",
                                  command=self.toggle_logs)
        self.btn_logs.pack(side="left", fill="x", expand=True, padx=(4, 0))

        self.txt_log = scrolledtext.ScrolledText(self.root, height=14,
                                                 bg="#121218", fg="#9ecaed",
                                                 font=("Consolas", 9), relief="flat", state="disabled")
        self.txt_log.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        self.txt_log.pack_forget()

        tk.Label(self.root, text="Первый запуск — индексация 3-5 минут.\nДалее стартует за 40 секунд.",
                 font=("Segoe UI", 9), fg=self.colors["muted"], bg=self.colors["bg"]).pack(pady=(0, 12))

    def set_liquid(self, palette):
        self.liquid.colors = LiquidButton.PALETTES[palette]

    def _log(self, msg):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", msg + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def toggle_logs(self):
        if self.txt_log.winfo_ismapped():
            self.txt_log.pack_forget()
            self.root.geometry("520x720")
        else:
            self.txt_log.pack(fill="both", expand=True, padx=16, pady=(8, 16))
            self.root.geometry("520x860")

    def _port_free(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", PORT))
            s.close()
            return True
        except OSError:
            return False

    def _server_alive(self):
        try:
            s = socket.create_connection(("127.0.0.1", PORT), timeout=2)
            s.close()
            return True
        except OSError:
            return False

    def start(self):
        self._log("[i] Освобождаю порт...")
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if f":{PORT}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                try:
                    subprocess.run(["taskkill", "/f", "/pid", pid], capture_output=True)
                except Exception:
                    pass
        time.sleep(2)

        self._log("[i] Запускаю Mirro (индексация или загрузка из кэша)...")
        log_out = open(os.path.join(MIRRO, "logs", "mirro_out.log"), "w")
        log_err = open(os.path.join(MIRRO, "logs", "mirro_err.log"), "w")
        self.proc = subprocess.Popen(
            [sys.executable, "-u", CORE], stdout=log_out, stderr=log_err, cwd=MIRRO)

        self.liquid.set_text("ОСТАНОВИТЬ")
        self.liquid.colors = LiquidButton.PALETTES["danger"] if "danger" in LiquidButton.PALETTES else self.liquid.colors
        self.lbl_status.config(text="Запуск... (первый раз 3-5 мин)")
        self.status_dot.itemconfig(self.dot, fill="#fdcb6e")
        self.monitoring = True
        threading.Thread(target=self._monitor, daemon=True).start()

    def stop(self):
        self._log("[i] Останавливаю Mirro...")
        self.monitoring = False
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()
            self.proc = None
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if f":{PORT}" in line:
                parts = line.strip().split()
                pid = parts[-1]
                if pid.isdigit() and pid != "0":
                    try:
                        subprocess.run(["taskkill", "/f", "/pid", pid], capture_output=True)
                    except Exception:
                        pass
        self.liquid.set_text("ЗАПУСТИТЬ MIRRO")
        self.liquid.colors = LiquidButton.PALETTES["mercury"]
        self.btn_open.config(state="disabled")
        self.lbl_status.config(text="Остановлена")
        self.status_dot.itemconfig(self.dot, fill="#666")

    def toggle(self):
        if self._server_alive() or (self.proc and self.proc.poll() is None):
            self.stop()
        else:
            self.start()

    def _monitor(self):
        waited = 0
        while self.monitoring and waited < 420:
            if self._server_alive():
                self.root.after(0, self._on_ready)
                self._log(f"[+] Сервер готов после {waited}s")
                return
            time.sleep(5)
            waited += 5
            self.root.after(0, lambda w=waited: self.lbl_status.config(
                text=f"Запуск... {w}s (первый раз дольше)"))

    def _on_ready(self):
        self.lbl_status.config(text="Работает", fg=self.colors["success"])
        self.status_dot.itemconfig(self.dot, fill=self.colors["success"])
        self.liquid.set_text("ОСТАНОВИТЬ")
        self.btn_open.config(state="normal")
        self._log(f"[+] Mirro готова: {URL}")

    def open_browser(self):
        webbrowser.open(URL)
        self._log(f"[i] Открываю {URL}")

    def _update_status(self):
        if self._server_alive():
            self._on_ready()
            self.monitoring = False
        else:
            self.lbl_status.config(text="Не запущена", fg=self.colors["muted"])
            self.status_dot.itemconfig(self.dot, fill="#666")
            self.liquid.set_text("ЗАПУСТИТЬ MIRRO")
        self.root.after(3000, self._update_status)


if __name__ == "__main__":
    root = tk.Tk()
    app = MirroLauncher(root)
    root.mainloop()