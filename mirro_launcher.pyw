# -*- coding: utf-8 -*-
"""
Mirro Launcher — программа-загрузчик Mirro.
Запускает сервер одной кнопкой, следит за статусом и открывает сайт.
tkinter, только stdlib.
"""
import os, sys, time, socket, subprocess, threading, webbrowser
from pathlib import Path

MIRRO = r"D:\Mirro"
CORE = os.path.join(MIRRO, "core", "mirro_core.py")
PORT = 3443
URL = f"http://127.0.0.1:{PORT}"
LOG_OUT = os.path.join(MIRRO, "logs", "mirro_out.log")
LOG_ERR = os.path.join(MIRRO, "logs", "mirro_err.log")
INDEX_CACHE = os.path.join(MIRRO, "models", "index_cache.pkl")
RAG_INDEX = os.path.join(MIRRO, "models", "rag_index")

import tkinter as tk
from tkinter import scrolledtext, messagebox


def find_python():
    exe = sys.executable or "python"
    if exe.lower().endswith("pythonw.exe"):
        exe = exe[:-4] + ".exe"
    if not os.path.exists(exe):
        for cand in [r"C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe",
                     r"C:\Python314\python.exe", r"C:\Python312\python.exe", "python"]:
            if os.path.exists(cand) or cand == "python":
                exe = cand
                break
    return exe


class MirroLauncher:
    C = {
        "bg": "#0e0e12", "panel": "#181820", "panel2": "#21212b",
        "border": "#2a2a36", "text": "#e6e6ee", "text2": "#a0a0b0",
        "muted": "#6b6b7a", "accent": "#6c5ce7", "accent2": "#a29bfe",
        "accent_dim": "#2a2440", "success": "#2ecc8f", "warn": "#f0b94e",
        "danger": "#e1605a",
    }

    def __init__(self, root):
        self.root = root
        self.proc = None
        self.monitoring = False
        self.auto_open = tk.BooleanVar(value=True)

        root.title("Mirro — Загрузчик")
        root.geometry("560x760")
        root.configure(bg=self.C["bg"])
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_menu()
        self._build_ui()
        self._update_status()

    def _build_menu(self):
        menubar = tk.Menu(self.root, bg=self.C["panel"], fg=self.C["text"], activebackground=self.C["accent_dim"], activeforeground=self.C["text"])
        m_file = tk.Menu(menubar, tearoff=0, bg=self.C["panel"], fg=self.C["text"], activebackground=self.C["accent_dim"])
        m_file.add_command(label="Запустить Mirro", command=self.start)
        m_file.add_command(label="Остановить Mirro", command=self.stop)
        m_file.add_separator()
        m_file.add_command(label="Открыть сайт", command=self.open_browser)
        m_file.add_separator()
        m_file.add_command(label="Выход", command=self.on_close)
        menubar.add_cascade(label="Файл", menu=m_file)

        m_srv = tk.Menu(menubar, tearoff=0, bg=self.C["panel"], fg=self.C["text"], activebackground=self.C["accent_dim"])
        m_srv.add_command(label="Перезапустить сервер", command=self.restart)
        m_srv.add_separator()
        m_srv.add_command(label="Пересобрать индекс (полностью)", command=self.rebuild_index)
        m_srv.add_command(label="Пересобрать RAG-индекс", command=self.rebuild_rag)
        m_srv.add_separator()
        m_srv.add_command(label="Открыть логи", command=lambda: self._open_file(LOG_OUT))
        m_srv.add_command(label="Открыть папку Mirro", command=lambda: self._open_file(MIRRO))
        menubar.add_cascade(label="Сервер", menu=m_srv)

        m_help = tk.Menu(menubar, tearoff=0, bg=self.C["panel"], fg=self.C["text"], activebackground=self.C["accent_dim"])
        m_help.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Помощь", menu=m_help)
        self.root.config(menu=menubar)

    def _build_ui(self):
        header = tk.Frame(self.root, bg=self.C["panel"], height=72)
        header.pack(fill="x")
        header.pack_propagate(False)

        logo = tk.Canvas(header, width=46, height=46, bg=self.C["panel"], highlightthickness=0)
        logo.pack(side="left", padx=(18, 12), pady=13)
        self._draw_vortex(logo)

        tk.Label(header, text="Mirro", font=("Segoe UI", 20, "bold"),
                 fg=self.C["text"], bg=self.C["panel"]).pack(side="left", anchor="s", pady=(10, 0))
        tk.Label(header, text="эволюционная нейросеть", font=("Segoe UI", 9),
                 fg=self.C["muted"], bg=self.C["panel"]).pack(side="left", anchor="s", pady=(10, 2), padx=(6, 0))

        self.status_dot = tk.Canvas(header, width=16, height=16, bg=self.C["panel"], highlightthickness=0)
        self.status_dot.pack(side="right", padx=18)
        self.dot = self.status_dot.create_oval(2, 2, 14, 14, fill="#555", outline="")

        self.lbl_status = tk.Label(self.root, text="Проверка...", font=("Segoe UI", 12),
                                   fg=self.C["text2"], bg=self.C["bg"])
        self.lbl_status.pack(pady=(16, 2))
        self.lbl_sub = tk.Label(self.root, text="", font=("Segoe UI", 9),
                                fg=self.C["muted"], bg=self.C["bg"])
        self.lbl_sub.pack()

        self.btn_main = tk.Button(self.root, text="ЗАПУСТИТЬ MIRRO", font=("Segoe UI", 14, "bold"),
                                  bg=self.C["accent"], fg="#ffffff", activebackground=self.C["accent2"],
                                  activeforeground="#ffffff", relief="flat", bd=0, cursor="hand2",
                                  height=2, command=self.toggle)
        self.btn_main.pack(fill="x", padx=36, pady=(18, 8))

        self.progress = tk.Canvas(self.root, height=5, bg=self.C["panel"], highlightthickness=0)
        self.progress.pack(fill="x", padx=36)
        self.progress_bar = self.progress.create_rectangle(0, 0, 0, 5, fill=self.C["accent"], outline="")

        opt = tk.Frame(self.root, bg=self.C["bg"])
        opt.pack(fill="x", padx=36, pady=(10, 0))
        tk.Checkbutton(opt, text="Открывать сайт автоматически", variable=self.auto_open,
                       font=("Segoe UI", 9), fg=self.C["text2"], bg=self.C["bg"],
                       selectcolor=self.C["panel2"], activebackground=self.C["bg"],
                       activeforeground=self.C["text"], cursor="hand2").pack(side="left")

        row = tk.Frame(self.root, bg=self.C["bg"])
        row.pack(fill="x", padx=36, pady=10)

        self.btn_open = tk.Button(row, text="Открыть сайт", font=("Segoe UI", 10),
                                  bg=self.C["panel2"], fg=self.C["accent2"], relief="flat", bd=0,
                                  activebackground="#2a2a36", cursor="hand2", state="disabled",
                                  command=self.open_browser)
        self.btn_open.pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=6)

        self.btn_logs = tk.Button(row, text="Показать логи", font=("Segoe UI", 10),
                                  bg=self.C["panel2"], fg=self.C["text2"], relief="flat", bd=0,
                                  activebackground="#2a2a36", cursor="hand2", command=self.toggle_logs)
        self.btn_logs.pack(side="left", fill="x", expand=True, padx=(5, 0), ipady=6)

        self.txt_log = scrolledtext.ScrolledText(self.root, height=16, bg="#0a0a10",
                                                 fg="#9ecaed", insertbackground=self.C["text"],
                                                 font=("Consolas", 9), relief="flat", state="disabled")
        self.txt_log.pack(fill="both", expand=True, padx=18, pady=(4, 6))
        self.txt_log.pack_forget()

        tk.Label(self.root, text="Первый запуск — индексация 3-5 минут.\nДалее старт за 30-60 секунд.",
                 font=("Segoe UI", 9), fg=self.C["muted"], bg=self.C["bg"]).pack(pady=(0, 12))

    def _draw_vortex(self, cv):
        cx, cy = 23, 23
        for r, op in [(20, 1.0), (14, 0.7), (8, 0.45)]:
            for a in range(0, 360, 8):
                import math
                x1 = cx + r * math.cos(math.radians(a))
                y1 = cy + r * math.sin(math.radians(a))
                x2 = cx + r * math.cos(math.radians(a + 40))
                y2 = cy + r * math.sin(math.radians(a + 40))
                cv.create_line(x1, y1, x2, y2, fill=self.C["accent2"], width=1.6, capstyle="round")
        cv.create_oval(cx - 3.5, cy - 3.5, cx + 3.5, cy + 3.5, fill="#7cc4ff", outline="")

    def _log(self, msg):
        try:
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", msg + "\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        except Exception:
            pass

    def toggle_logs(self):
        if self.txt_log.winfo_ismapped():
            self.txt_log.pack_forget()
            self.root.geometry("560x760")
            self.btn_logs.config(text="Показать логи")
        else:
            self.txt_log.pack(fill="both", expand=True, padx=18, pady=(4, 6))
            self.root.geometry("560x900")
            self.btn_logs.config(text="Скрыть логи")
            self._tail_logs()

    def _tail_logs(self):
        try:
            with open(LOG_OUT, "r", encoding="utf-8", errors="replace") as f:
                data = f.read()
            self.txt_log.configure(state="normal")
            self.txt_log.delete("1.0", "end")
            self.txt_log.insert("end", data[-4000:])
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        except Exception:
            pass

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

    def _health(self):
        try:
            import urllib.request, json
            with urllib.request.urlopen(f"{URL}/health", timeout=4) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            return None

    def _set_progress(self, frac):
        w = 488
        self.progress.coords(self.progress_bar, 0, 0, int(w * max(0, min(1, frac))), 5)

    def start(self):
        if self._server_alive():
            self._log("[i] Сервер уже запущен")
            self._on_ready()
            return
        self._log("[i] Освобождаю порт...")
        self._kill_port_users()
        time.sleep(1)
        self._log("[i] Запускаю Mirro...")
        os.makedirs(os.path.dirname(LOG_OUT), exist_ok=True)
        py = find_python()
        self._log(f"[i] Python: {py}")
        self._set_state_starting()
        try:
            self.proc = subprocess.Popen(
                [py, "-u", CORE], cwd=MIRRO,
                stdout=open(LOG_OUT, "w", encoding="utf-8", errors="replace"),
                stderr=open(LOG_ERR, "w", encoding="utf-8", errors="replace"),
                creationflags=subprocess.CREATE_NO_WINDOW)
            self._log(f"[i] PID: {self.proc.pid}")
        except Exception as e:
            self._log(f"[!] Ошибка запуска: {e}")
            messagebox.showerror("Mirro", f"Не удалось запустить сервер:\n{e}")
            self._set_state_stopped()
            return
        self.monitoring = True
        threading.Thread(target=self._monitor, daemon=True).start()

    def _monitor(self):
        waited = 0
        while self.monitoring and waited < 600:
            h = self._health()
            if h:
                self.root.after(0, lambda: self._on_ready(h))
                self._log(f"[+] Сервер готов через {waited}s")
                self.root.after(0, self._set_progress, 1.0)
                return
            self.root.after(0, self._set_progress, min(0.95, waited / 300.0))
            self.root.after(0, lambda w=waited: self.lbl_sub.config(
                text=f"Индексация и запуск... {w}s (первый раз 3-5 мин)"))
            time.sleep(5)
            waited += 5
        if self.monitoring:
            self._log("[!] Таймаут ожидания сервера")
            self.root.after(0, self._set_state_stopped)

    def _on_ready(self, health=None):
        self.monitoring = False
        self._set_state_running()
        self._set_progress(1.0)
        if health:
            ex = health.get("total_examples", 0)
            self.lbl_sub.config(text=f"{ex:,} примеров в базе · {URL}")
        if self.auto_open.get():
            self._log("[i] Открываю сайт...")
            webbrowser.open(URL)

    def stop(self):
        self.monitoring = False
        self._log("[i] Останавливаю Mirro...")
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=6)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
        self.proc = None
        self._kill_port_users()
        self._log("[i] Остановлена")
        self._set_state_stopped()

    def restart(self):
        self._log("[i] Перезапуск...")
        self.stop()
        time.sleep(1)
        self.start()

    def toggle(self):
        if self._server_alive() or (self.proc and self.proc.poll() is None):
            self.stop()
        else:
            self.start()

    def open_browser(self):
        webbrowser.open(URL)
        self._log(f"[i] Открываю {URL}")

    def rebuild_index(self):
        if not messagebox.askyesno("Mirro", "Полностью пересобрать индекс?\nЭто займёт 5-10 минут и 6-8 ГБ RAM."):
            return
        self._log("[i] Удаляю кэш индекса...")
        try:
            os.remove(INDEX_CACHE)
        except OSError:
            pass
        self._log("[i] Перезапускаю с пересборкой...")
        threading.Thread(target=self._restart_thread, daemon=True).start()

    def rebuild_rag(self):
        if not messagebox.askyesno("Mirro", "Пересобрать RAG-индекс на диске?\nЭто займёт ~3 минуты."):
            return
        self._log("[i] Пересобираю RAG-индекс...")
        threading.Thread(target=self._rag_thread, daemon=True).start()

    def _restart_thread(self):
        self.root.after(0, self.stop)
        time.sleep(2)
        self.root.after(0, self.start)

    def _rag_thread(self):
        try:
            py = find_python()
            code = (
                "import shutil, os\n"
                f"shutil.rmtree(r'{RAG_INDEX}', ignore_errors=True)\n"
                "os.makedirs(r'" + RAG_INDEX + "', exist_ok=True)\n"
                "import sys; sys.path.insert(0, r'" + MIRRO + "')\n"
                "from scripts.rag import MirroRAG\n"
                "rag = MirroRAG(); rag.rebuild_all()\n"
                "print('RAG OK')"
            )
            r = subprocess.run([py, "-c", code], capture_output=True, text=True, timeout=900)
            self.root.after(0, self._log, "[i] RAG: " + (r.stdout.strip()[-200:] or r.stderr.strip()[-200:]))
        except Exception as e:
            self.root.after(0, self._log, f"[!] RAG: {e}")

    def _kill_port_users(self):
        try:
            r = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
            for line in r.stdout.splitlines():
                if f":{PORT}" in line and "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    if pid.isdigit() and pid != "0":
                        subprocess.run(["taskkill", "/f", "/pid", pid], capture_output=True)
        except Exception:
            pass

    def _set_state_starting(self):
        self.btn_main.config(text="ОСТАНОВИТЬ", bg=self.C["danger"], activebackground="#d9534f")
        self.lbl_status.config(text="Запуск...", fg=self.C["warn"])
        self.status_dot.itemconfig(self.dot, fill=self.C["warn"])
        self.btn_open.config(state="disabled")
        self._set_progress(0.02)

    def _set_state_running(self):
        self.btn_main.config(text="ОСТАНОВИТЬ", bg=self.C["danger"], activebackground="#d9534f")
        self.lbl_status.config(text="Работает", fg=self.C["success"])
        self.status_dot.itemconfig(self.dot, fill=self.C["success"])
        self.btn_open.config(state="normal")
        self._set_progress(1.0)

    def _set_state_stopped(self):
        self.btn_main.config(text="ЗАПУСТИТЬ MIRRO", bg=self.C["accent"], activebackground=self.C["accent2"])
        self.lbl_status.config(text="Не запущена", fg=self.C["muted"])
        self.status_dot.itemconfig(self.dot, fill="#555")
        self.btn_open.config(state="disabled")
        self.lbl_sub.config(text="")
        self._set_progress(0.0)

    def _update_status(self):
        h = self._health()
        if h:
            self._set_state_running()
            self.lbl_sub.config(text=f"{h.get('total_examples', 0):,} примеров в базе · {URL}")
        else:
            if not (self.proc and self.proc.poll() is None) and not self.monitoring:
                self._set_state_stopped()
        self.root.after(3000, self._update_status)

    def _open_file(self, path):
        os.startfile(path)

    def show_about(self):
        messagebox.showinfo("О программе",
            "Mirro — эволюционная нейросеть знаний\n\n"
            "Собственные алгоритмы, без внешних API.\n"
            f"Сервер: {URL}\n"
            "Загрузчик: запуск одной кнопкой,\n"
            "статус, логи и меню управления.")

    def on_close(self):
        if messagebox.askokcancel("Mirro", "Закрыть загрузчик?\nСервер продолжит работать в фоне."):
            self.monitoring = False
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MirroLauncher(root)
    root.mainloop()