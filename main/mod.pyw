import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import pyperclip
import threading
import time
from pynput import keyboard as kb

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

# ─── Minecraft 1.9+ Attack Speed Delays (seconds) ───────────────────────────
WEAPON_DELAYS: dict[str, dict[str, float]] = {
    "Sword": {
        "Wooden":    0.625,
        "Stone":     0.625,
        "Iron":      0.625,
        "Golden":    0.625,
        "Diamond":   0.625,
        "Netherite": 0.625,
    },
    "Axe": {
        "Wooden":    1.250,   # Attack Speed 0.8
        "Stone":     1.250,   # Attack Speed 0.8
        "Iron":      1.111,   # Attack Speed 0.9
        "Golden":    1.000,   # Attack Speed 1.0
        "Diamond":   1.000,   # Attack Speed 1.0
        "Netherite": 1.000,   # Attack Speed 1.0
    },
}

# ─── Catppuccin Mocha palette ────────────────────────────────────────────────
C = {
    "base":     "#1e1e2e",
    "mantle":   "#181825",
    "surface0": "#313244",
    "surface1": "#45475a",
    "overlay0": "#6c7086",
    "text":     "#cdd6f4",
    "subtext":  "#a6adc8",
    "green":    "#a6e3a1",
    "blue":     "#89b4fa",
    "peach":    "#fab387",
    "red":      "#f38ba8",
    "yellow":   "#f9e2af",
    "mauve":    "#cba6f7",
    "dark_fg":  "#11111b",
}


def _entry(parent: tk.Frame, label: str, default: str) -> tk.Entry:
    tk.Label(parent, text=label, fg=C["subtext"], bg=C["surface0"],
             font=("Consolas", 9)).pack(anchor="w", padx=12, pady=(10, 2))
    e = tk.Entry(parent, bg=C["surface1"], fg=C["text"],
                 insertbackground=C["text"], relief="flat",
                 highlightthickness=1, highlightbackground=C["surface1"],
                 highlightcolor=C["blue"])
    e.insert(0, default)
    e.pack(fill="x", padx=12, ipady=4)
    return e


def _combo(parent: tk.Frame, label: str, values: list[str],
           default: str) -> ttk.Combobox:
    tk.Label(parent, text=label, fg=C["subtext"], bg=C["surface0"],
             font=("Consolas", 9)).pack(anchor="w", padx=12, pady=(10, 2))
    var = tk.StringVar(value=default)
    cb = ttk.Combobox(parent, textvariable=var, values=values,
                      state="readonly")
    cb.pack(fill="x", padx=12)
    return cb


def _check(parent: tk.Frame, label: str, var: tk.BooleanVar,
           cmd=None) -> tk.Checkbutton:
    return tk.Checkbutton(
        parent, text=label, variable=var,
        command=cmd,
        fg=C["text"], bg=C["surface0"],
        selectcolor=C["surface1"],
        activebackground=C["surface0"],
        activeforeground=C["text"],
        font=("Consolas", 9),
    )


def _btn(parent: tk.Frame, label: str, color: str,
         cmd) -> tk.Button:
    return tk.Button(
        parent, text=label,
        font=("Consolas", 10, "bold"),
        bg=color, fg=C["dark_fg"],
        relief="flat", cursor="hand2",
        activebackground=C["overlay0"],
        activeforeground=C["text"],
        command=cmd,
    )


class StatusBar(tk.Frame):
    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=C["mantle"], height=22)
        self._label = tk.Label(self, text="Hazır", fg=C["subtext"],
                               bg=C["mantle"], font=("Consolas", 8))
        self._label.pack(side="left", padx=8)

        self._hotkey_label = tk.Label(
            self,
            text="Ctrl+O Clicker  │  Ctrl+P Typer  │  Ctrl+K Weapon  │  Ctrl+I Gizlə",
            fg=C["overlay0"], bg=C["mantle"], font=("Consolas", 8),
        )
        self._hotkey_label.pack(side="right", padx=8)

    def set(self, msg: str, color: str = C["subtext"]) -> None:
        self._label.config(text=msg, fg=color)


class ClickerTab(tk.Frame):
    def __init__(self, parent, status_cb):
        super().__init__(parent, bg=C["surface0"])
        self._status = status_cb
        self._running = False
        self._thread: threading.Thread | None = None
        self._build()

    def _build(self):
        self._cps = _entry(self, "Saniyədə Klik Sayı (CPS):", "10")

        tk.Label(self, text="Mışka Düyməsi:", fg=C["subtext"],
                 bg=C["surface0"], font=("Consolas", 9)).pack(
            anchor="w", padx=12, pady=(10, 2))
        self._btn_var = tk.StringVar(value="Sol")
        ttk.Combobox(self, textvariable=self._btn_var,
                     values=["Sol", "Sağ"],
                     state="readonly").pack(fill="x", padx=12)

        self._hold_var = tk.BooleanVar(value=False)
        _check(self, "Basılı Saxla (Hold Down)", self._hold_var).pack(
            anchor="w", padx=12, pady=(10, 0))

        self._inf_var = tk.BooleanVar(value=True)
        _check(self, "Sonsuz Klikləmə", self._inf_var,
               self._toggle_count).pack(anchor="w", padx=12, pady=(5, 0))

        self._count_lbl = tk.Label(self, text="Klik Sayı:",
                                   fg=C["subtext"], bg=C["surface0"],
                                   font=("Consolas", 9))
        self._count_entry = tk.Entry(self, bg=C["surface1"], fg=C["text"],
                                     insertbackground=C["text"], relief="flat")
        self._count_entry.insert(0, "100")

        self._btn = _btn(self, "▶  BAŞLAT  [Ctrl+O]",
                         C["green"], self.toggle)
        self._btn.pack(fill="x", padx=12, pady=15, side="bottom")

    def _toggle_count(self):
        if self._inf_var.get():
            self._count_lbl.pack_forget()
            self._count_entry.pack_forget()
        else:
            self._count_lbl.pack(anchor="w", padx=12,
                                  pady=(8, 2), before=self._btn)
            self._count_entry.pack(fill="x", padx=12, before=self._btn)

    def toggle(self):
        if not self._running:
            self._running = True
            self._btn.config(text="■  DAYANDIR  [Ctrl+O]", bg=C["red"])
            self._status("Auto Clicker işləyir", C["green"])
            self._thread = threading.Thread(
                target=self._run, daemon=True)
            self._thread.start()
        else:
            self._running = False

    def _run(self):
        try:
            cps = max(0.1, float(self._cps.get()))
        except ValueError:
            cps = 10.0
        delay = 1.0 / cps
        button = "left" if self._btn_var.get() == "Sol" else "right"
        hold = self._hold_var.get()
        infinite = self._inf_var.get()
        try:
            max_clicks = int(self._count_entry.get()) if not infinite else 0
        except ValueError:
            max_clicks = 100

        try:
            if hold:
                pyautogui.mouseDown(button=button)
                while self._running:
                    time.sleep(0.05)
                pyautogui.mouseUp(button=button)
            else:
                clicked = 0
                while self._running:
                    pyautogui.click(button=button)
                    clicked += 1
                    if not infinite and clicked >= max_clicks:
                        break
                    time.sleep(delay)
        except pyautogui.FailSafeException:
            pass
        finally:
            self._running = False
            self._btn.after(0, lambda: self._btn.config(
                text="▶  BAŞLAT  [Ctrl+O]", bg=C["green"]))
            self._btn.after(0, lambda: self._status("Hazır"))


class WeaponTab(tk.Frame):
    def __init__(self, parent, status_cb):
        super().__init__(parent, bg=C["surface0"])
        self._status = status_cb
        self._running = False
        self._build()

    def _build(self):
        self._type_cb = _combo(self, "Silah Növü:",
                                list(WEAPON_DELAYS.keys()), "Axe")
        self._type_cb.bind("<<ComboboxSelected>>", self._update_delay)

        self._mat_cb = _combo(
            self, "Material:",
            ["Wooden", "Stone", "Iron", "Golden", "Diamond", "Netherite"],
            "Golden")
        self._mat_cb.bind("<<ComboboxSelected>>", self._update_delay)

        self._delay_lbl = tk.Label(
            self, text="", fg=C["yellow"], bg=C["surface0"],
            font=("Consolas", 11, "bold"))
        self._delay_lbl.pack(pady=15)
        self._update_delay()

        self._btn = _btn(self, "▶  BAŞLAT  [Ctrl+K]",
                         C["peach"], self.toggle)
        self._btn.pack(fill="x", padx=12, pady=15, side="bottom")

    def _update_delay(self, _=None):
        w = self._type_cb.get()
        m = self._mat_cb.get()
        d = WEAPON_DELAYS.get(w, {}).get(m, 1.0)
        self._delay_lbl.config(text=f"Attack delay: {d:.3f}s")
        self._current_delay = d

    def toggle(self):
        if not self._running:
            self._running = True
            self._btn.config(text="■  DAYANDIR  [Ctrl+K]", bg=C["red"])
            self._status("Weapon Auto işləyir", C["peach"])
            threading.Thread(target=self._run, daemon=True).start()
        else:
            self._running = False

    def _run(self):
        self._update_delay()
        delay = self._current_delay
        try:
            while self._running:
                pyautogui.click(button="left")
                time.sleep(delay)
        except pyautogui.FailSafeException:
            pass
        finally:
            self._running = False
            self._btn.after(0, lambda: self._btn.config(
                text="▶  BAŞLAT  [Ctrl+K]", bg=C["peach"]))
            self._btn.after(0, lambda: self._status("Hazır"))


class TyperTab(tk.Frame):
    def __init__(self, parent, status_cb):
        super().__init__(parent, bg=C["surface0"])
        self._status = status_cb
        self._running = False
        self._build()

    def _build(self):
        self._text = _entry(self, "Yazılacaq Mətn:", "Salam!")
        self._interval = _entry(self, "İnterval (saniyə):", "1.0")

        self._inf_var = tk.BooleanVar(value=True)
        _check(self, "Sonsuza Qədər Yaz", self._inf_var,
               self._toggle_count).pack(anchor="w", padx=12, pady=(10, 0))

        self._count_lbl = tk.Label(self, text="Neçə Dəfə:",
                                   fg=C["subtext"], bg=C["surface0"],
                                   font=("Consolas", 9))
        self._count_entry = tk.Entry(self, bg=C["surface1"], fg=C["text"],
                                     insertbackground=C["text"], relief="flat")
        self._count_entry.insert(0, "5")

        self._btn = _btn(self, "▶  BAŞLAT  [Ctrl+P]",
                         C["blue"], self.toggle)
        self._btn.pack(fill="x", padx=12, pady=15, side="bottom")

    def _toggle_count(self):
        if self._inf_var.get():
            self._count_lbl.pack_forget()
            self._count_entry.pack_forget()
        else:
            self._count_lbl.pack(anchor="w", padx=12,
                                  pady=(8, 2), before=self._btn)
            self._count_entry.pack(fill="x", padx=12, before=self._btn)

    def toggle(self):
        if not self._running:
            self._running = True
            self._btn.config(text="■  DAYANDIR  [Ctrl+P]", bg=C["red"])
            self._status("Auto Typer işləyir", C["blue"])
            threading.Thread(target=self._run, daemon=True).start()
        else:
            self._running = False

    def _run(self):
        text = self._text.get()
        try:
            interval = max(0.1, float(self._interval.get()))
        except ValueError:
            interval = 1.0
        infinite = self._inf_var.get()
        try:
            max_times = int(self._count_entry.get()) if not infinite else 0
        except ValueError:
            max_times = 5

        written = 0
        time.sleep(0.5)
        try:
            while self._running:
                pyperclip.copy(text)
                pyautogui.hotkey("ctrl", "v")
                pyautogui.press("enter")
                written += 1
                if not infinite and written >= max_times:
                    break
                time.sleep(interval)
        except pyautogui.FailSafeException:
            pass
        finally:
            self._running = False
            self._btn.after(0, lambda: self._btn.config(
                text="▶  BAŞLAT  [Ctrl+P]", bg=C["blue"]))
            self._btn.after(0, lambda: self._status("Hazır"))


class DisnoModPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Disno Mod Panel")
        self.root.geometry("380x580")
        self.root.resizable(False, False)
        self.root.wm_attributes("-topmost", True)
        self.root.configure(bg=C["base"])

        self._is_visible = True
        self._build_ui()
        self._bind_hotkeys()

    def _build_ui(self):
        # ── header ──────────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=C["mantle"])
        header.pack(fill="x")
        tk.Label(header, text="⚡ DISNO MOD PANEL",
                 font=("Consolas", 13, "bold"),
                 fg=C["mauve"], bg=C["mantle"]).pack(pady=8)

        # ── notebook ────────────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=C["base"],
                         borderwidth=0, tabmargins=[0, 4, 0, 0])
        style.configure("TNotebook.Tab",
                         background=C["surface1"],
                         foreground=C["subtext"],
                         font=("Consolas", 9, "bold"),
                         padding=[12, 5])
        style.map("TNotebook.Tab",
                  background=[("selected", C["surface0"])],
                  foreground=[("selected", C["text"])])

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=6, pady=6)

        # ── status bar ──────────────────────────────────────────────────────
        self._status_bar = StatusBar(self.root)
        self._status_bar.pack(fill="x", side="bottom")

        status_cb = self._status_bar.set

        self._clicker_tab = ClickerTab(nb, status_cb)
        self._weapon_tab  = WeaponTab(nb, status_cb)
        self._typer_tab   = TyperTab(nb, status_cb)

        nb.add(self._clicker_tab, text="  Auto Clicker  ")
        nb.add(self._weapon_tab,  text="  Weapon Auto  ")
        nb.add(self._typer_tab,   text="  Auto Typer  ")

    def _bind_hotkeys(self):
        hk = kb.GlobalHotKeys({
            "<ctrl>+o": lambda: self.root.after(
                0, self._clicker_tab.toggle),
            "<ctrl>+p": lambda: self.root.after(
                0, self._typer_tab.toggle),
            "<ctrl>+k": lambda: self.root.after(
                0, self._weapon_tab.toggle),
            "<ctrl>+i": lambda: self.root.after(
                0, self._toggle_visibility),
        })
        hk.start()

    def _toggle_visibility(self):
        if self._is_visible:
            self.root.withdraw()
        else:
            self.root.deiconify()
            self.root.lift()
        self._is_visible = not self._is_visible

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    DisnoModPanel().run()
