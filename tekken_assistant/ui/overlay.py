from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from tekken_assistant.glossary import GLOSSARY
from tekken_assistant.models import Character, Combo, Detection
from tekken_assistant.notation import iter_segments, to_official

MODES: tuple[str, ...] = ("compact", "expanded", "monitor")
MODE_LABELS = {"compact": "Бейдж", "expanded": "Панель", "monitor": "2-й монитор"}

BG = "#0d1117"
PANEL_BG = "#131a22"
BAR_BG = "#0a0e13"
FG = "#e6e6e6"
DIM = "#8a939e"
ACCENT = "#e5a13c"
PLAYER_COLOR = "#7ec46a"
OPPONENT_COLOR = "#d9635a"
MONO_BG = "#0d1117"

BADGE_W = 260
BADGE_H = 64
PANEL_W = 470
PANEL_H = 560

PANEL_ALPHA = 0.92
FADED_ALPHA = 0.35
FADE_DELAY_MS = 8000

BTN_COLORS = {
    "btn1": ("#2f6fd0", "#ffffff"),
    "btn2": ("#d9a13c", "#141414"),
    "btn3": ("#2e9e4f", "#ffffff"),
    "btn4": ("#d0453e", "#ffffff"),
    "btnx": ("#4a5568", "#ffffff"),
}

TABS = ("Комбо", "План", "Фишки", "Противник", "Словарь")


class OverlayApp:
    def __init__(
        self,
        roster: list[str],
        width: int,
        height: int,
        offset_x: int,
        offset_y: int,
        secondary_origin: tuple[int, int],
        mode: str,
        on_pause_toggle: Callable[[], None],
        on_swap: Callable[[], None],
        on_manual_set: Callable[[str, str], None],
        on_auto_toggle: Callable[[bool], None],
        on_quit: Callable[[], None],
        on_copy: Callable[[str], None],
        on_mode_change: Callable[[str], None],
    ):
        self._on_pause_toggle = on_pause_toggle
        self._on_swap = on_swap
        self._on_manual_set = on_manual_set
        self._on_auto_toggle = on_auto_toggle
        self._on_quit = on_quit
        self._on_copy = on_copy
        self._on_mode_change = on_mode_change
        self._secondary_origin = secondary_origin

        self.root = tk.Tk()
        self.root.title("Tekken 8 Assistant")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=BG)

        self.status_var = tk.StringVar(value="Запуск…")
        self.paused = False
        self.mode = mode if mode in MODES else "compact"
        self._drag = {"x": 0, "y": 0}
        self._player_char: Character | None = None
        self._kage_combos: list[Combo] = []
        self._opponent_char: Character | None = None
        self._active_tab = 0
        self._fade_job: str | None = None

        self._build_badge()
        self._build_panel(roster)
        self._apply_mode(self.mode, initial=True)
        self._set_status("Ожидание…", DIM)

    def run(self) -> None:
        self.root.mainloop()

    # ---------- layout: compact badge ----------

    def _build_badge(self) -> None:
        self.badge = tk.Frame(self.root, bg=BAR_BG, highlightthickness=1, highlightbackground="#232b36")
        self.status_dot = tk.Label(
            self.badge, text="●", bg=BAR_BG, fg=DIM, font=("Segoe UI", 11)
        )
        self.status_dot.pack(side="left", padx=(10, 4))
        self.names_label = tk.Label(
            self.badge,
            text="Ожидание…",
            bg=BAR_BG,
            fg=FG,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        self.names_label.pack(side="left", fill="x", expand=True)
        for widget in (self.badge, self.status_dot, self.names_label):
            widget.bind("<Button-1>", self._badge_click)
            widget.bind("<Double-Button-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag_move)

    def _badge_click(self, event: tk.Event) -> None:
        self._set_mode("expanded" if self.mode == "compact" else "compact")

    # ---------- layout: expanded panel ----------

    def _build_panel(self, roster: list[str]) -> None:
        self.panel = tk.Frame(self.root, bg=BG)

        bar = tk.Frame(self.panel, bg=BAR_BG, height=34)
        bar.pack(fill="x", side="top")
        bar.bind("<Button-1>", self._drag_start)
        bar.bind("<B1-Motion>", self._drag_move)

        tk.Label(
            bar, text="TEKKEN 8", bg=BAR_BG, fg=ACCENT, font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(10, 0))
        self.mode_btn = tk.Button(
            bar,
            text="Режим",
            command=self._cycle_mode,
            bg=BAR_BG, fg=FG, relief="flat", bd=0,
            font=("Segoe UI", 9),
            activebackground=BAR_BG, activeforeground=ACCENT,
        )
        self.mode_btn.pack(side="right", padx=6)
        self.pause_btn = tk.Button(
            bar,
            text="Пауза",
            command=self._handle_pause,
            bg=BAR_BG, fg=FG, relief="flat", bd=0,
            font=("Segoe UI", 9),
            activebackground=BAR_BG, activeforeground=ACCENT,
        )
        self.pause_btn.pack(side="right", padx=6)
        tk.Button(
            bar,
            text="X",
            command=self._on_quit,
            bg=BAR_BG, fg=OPPONENT_COLOR, relief="flat", bd=0,
            font=("Segoe UI", 10, "bold"),
            activebackground=BAR_BG,
        ).pack(side="right", padx=6)
        self.status_label = tk.Label(
            bar, textvariable=self.status_var, bg=BAR_BG, fg=DIM, font=("Segoe UI", 9)
        )
        self.status_label.pack(side="right", padx=10)
        self.status_label.bind("<Button-1>", self._drag_start)
        self.status_label.bind("<B1-Motion>", self._drag_move)

        manual = tk.Frame(self.panel, bg=PANEL_BG)
        manual.pack(fill="x", side="top")
        tk.Label(
            manual, text="Вручную:", bg=PANEL_BG, fg=DIM, font=("Segoe UI", 9)
        ).pack(side="left", padx=(10, 4), pady=4)
        self.player_box = ttk.Combobox(manual, values=roster, width=15, state="readonly")
        self.player_box.pack(side="left", padx=3, pady=4)
        self.player_box.bind(
            "<<ComboboxSelected>>",
            lambda e: self._on_manual_set("player", self.player_box.get()),
        )
        self.opponent_box = ttk.Combobox(manual, values=roster, width=15, state="readonly")
        self.opponent_box.pack(side="left", padx=3, pady=4)
        self.opponent_box.bind(
            "<<ComboboxSelected>>",
            lambda e: self._on_manual_set("opponent", self.opponent_box.get()),
        )
        self.auto_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            manual,
            text="Авто",
            variable=self.auto_var,
            command=lambda: self._on_auto_toggle(self.auto_var.get()),
            bg=PANEL_BG, fg=DIM, selectcolor=BAR_BG,
            activebackground=PANEL_BG, activeforeground=FG,
            font=("Segoe UI", 9),
        ).pack(side="left", padx=8)

        self.tab_row = tk.Frame(self.panel, bg=BG)
        self.tab_row.pack(fill="x", side="top")
        self.tab_buttons: list[tk.Button] = []
        for i, tab in enumerate(TABS):
            btn = tk.Button(
                self.tab_row,
                text=tab,
                command=lambda idx=i: self.select_tab(idx),
                bg=BG, fg=DIM, relief="flat", bd=0,
                font=("Segoe UI", 10, "bold"),
                activebackground=BG,
                padx=10, pady=6,
            )
            btn.pack(side="left", fill="x", expand=True)
            self.tab_buttons.append(btn)

        body = tk.Frame(self.panel, bg=PANEL_BG)
        body.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(body)
        scrollbar.pack(side="right", fill="y")
        self.text = tk.Text(
            body, bg=PANEL_BG, fg=FG, bd=0, wrap="word",
            font=("Segoe UI", 10), yscrollcommand=scrollbar.set,
            cursor="arrow", takefocus=0, padx=10, pady=8,
        )
        self.text.pack(fill="both", expand=True)
        scrollbar.configure(command=self.text.yview)
        self._configure_tags()
        self.text.configure(state="disabled")
        self.panel.bind("<Enter>", self._on_panel_enter)
        self.panel.bind("<Leave>", self._on_panel_leave)

    def _configure_tags(self) -> None:
        text = self.text
        text.tag_configure("h1", font=("Segoe UI", 13, "bold"), foreground=FG, spacing1=2)
        text.tag_configure("h2", font=("Segoe UI", 10, "bold"), foreground=ACCENT, spacing1=10, spacing3=4)
        text.tag_configure("sub", font=("Segoe UI", 9), foreground=DIM, spacing3=6)
        text.tag_configure("body", font=("Segoe UI", 10), foreground=FG, spacing2=2)
        text.tag_configure("mono", font=("Consolas", 10), foreground="#9fd3a8", background=MONO_BG, spacing1=2, spacing3=4)
        text.tag_configure("dmg", font=("Segoe UI", 9), foreground=ACCENT)
        text.tag_configure("src", font=("Segoe UI", 8), foreground=DIM)
        text.tag_configure("warn", font=("Segoe UI", 10), foreground=OPPONENT_COLOR, spacing2=2)
        text.tag_configure("good", font=("Segoe UI", 10), foreground=PLAYER_COLOR, spacing2=2)
        text.tag_configure("term", font=("Segoe UI", 10, "bold"), foreground="#cfe3ff")
        text.tag_configure("n_dir", font=("Consolas", 11, "bold"), foreground="#6ec1ff")
        text.tag_configure("n_plus", font=("Consolas", 10), foreground=DIM)
        text.tag_configure("n_comma", font=("Consolas", 10), foreground=DIM)
        text.tag_configure("n_word", font=("Consolas", 10), foreground="#9fd3a8")
        text.tag_configure("n_sep", font=("Segoe UI", 10, "bold"), foreground=ACCENT)
        for kind, (bg, fg) in BTN_COLORS.items():
            text.tag_configure(
                "n_" + kind, font=("Consolas", 10, "bold"),
                foreground=fg, background=bg,
            )

    # ---------- modes ----------

    def _cycle_mode(self) -> None:
        idx = MODES.index(self.mode)
        self._set_mode(MODES[(idx + 1) % len(MODES)])

    def _badge_click_wrapper(self) -> None:  # kept for clarity; click handled inline
        pass

    def _set_mode(self, mode: str) -> None:
        if mode == self.mode:
            return
        self._apply_mode(mode)
        self._on_mode_change(mode)

    def _apply_mode(self, mode: str, initial: bool = False) -> None:
        self.mode = mode
        if mode == "compact":
            self._cancel_fade()
            self.root.attributes("-alpha", 1.0)
            self.panel.pack_forget()
            self.badge.pack(fill="both", expand=True)
            self.root.geometry(f"{BADGE_W}x{BADGE_H}+{self.root.winfo_screenwidth() - BADGE_W - 20}+20")
        else:
            self.badge.pack_forget()
            self.panel.pack(fill="both", expand=True)
            if mode == "monitor":
                x, y = self._secondary_origin[0] + 20, self._secondary_origin[1] + 20
            else:
                x, y = 40, 40
            self.root.geometry(f"{PANEL_W}x{PANEL_H}+{x}+{y}")
            self.root.attributes("-alpha", PANEL_ALPHA)
            self._schedule_fade()
            self.select_tab(self._active_tab)
        if not initial:
            self._set_status("Режим: " + MODE_LABELS[mode], ACCENT)

    # ---------- auto-fade ----------

    def _cancel_fade(self) -> None:
        if self._fade_job is not None:
            self.root.after_cancel(self._fade_job)
            self._fade_job = None

    def _schedule_fade(self) -> None:
        self._cancel_fade()
        self._fade_job = self.root.after(
            FADE_DELAY_MS, lambda: self.root.attributes("-alpha", FADED_ALPHA)
        )

    def _on_panel_enter(self, _event: tk.Event) -> None:
        if self.mode == "compact":
            return
        self._cancel_fade()
        self.root.attributes("-alpha", PANEL_ALPHA)

    def _on_panel_leave(self, _event: tk.Event) -> None:
        if self.mode == "compact":
            return
        self._schedule_fade()

    def cycle_mode(self) -> None:
        self.root.after(0, self._cycle_mode)

    def select_tab(self, idx: int) -> None:
        self._active_tab = idx
        for i, btn in enumerate(self.tab_buttons):
            if i == idx:
                btn.configure(fg=ACCENT, bg=PANEL_BG)
            else:
                btn.configure(fg=DIM, bg=BG)
        self._render_tab()

    # ---------- drag ----------

    def _drag_start(self, event: tk.Event) -> None:
        self._drag = {"x": event.x, "y": event.y}

    def _drag_move(self, event: tk.Event) -> None:
        x = self.root.winfo_x() + event.x - self._drag["x"]
        y = self.root.winfo_y() + event.y - self._drag["y"]
        self.root.geometry(f"+{x}+{y}")

    # ---------- actions ----------

    def _handle_pause(self) -> None:
        self._on_pause_toggle()

    def set_paused(self, paused: bool) -> None:
        self.root.after(0, lambda: self._set_paused(paused))

    def _set_paused(self, paused: bool) -> None:
        self.paused = paused
        self.pause_btn.configure(text="Пуск" if paused else "Пауза")
        if paused:
            self._set_status("Пауза", ACCENT)
        else:
            self._set_status("Слежение включено", PLAYER_COLOR)

    def set_status(self, text: str, color: str = DIM) -> None:
        self.root.after(0, lambda: self._set_status(text, color))

    def _set_status(self, text: str, color: str) -> None:
        self.status_var.set(text)
        self.status_label.configure(fg=color)
        self.status_dot.configure(fg=color)
        self.names_label.configure(fg=color) if self.mode == "compact" and not self._player_char else None

    def set_detection(self, detection: Detection) -> None:
        self.root.after(0, lambda: self._render_detection(detection))

    def _render_detection(self, detection: Detection) -> None:
        self.player_box.set(detection.player or "")
        self.opponent_box.set(detection.opponent or "")

    # ---------- content ----------

    def render_player(self, character: Character | None, kage_combos: list[Combo] | None = None) -> None:
        self._player_char = character
        self._kage_combos = kage_combos or []
        self.root.after(0, self._refresh)

    def render_opponent(self, character: Character | None) -> None:
        self._opponent_char = character
        self.root.after(0, self._refresh)

    def _refresh(self) -> None:
        self._update_badge()
        self._render_tab()

    def _update_badge(self) -> None:
        player = self._player_char.name if self._player_char else None
        opponent = self._opponent_char.name if self._opponent_char else None
        if player and opponent:
            self.names_label.configure(text=f"{player}  vs  {opponent}", fg=FG)
            self.status_dot.configure(fg=PLAYER_COLOR)
        elif player or opponent:
            self.names_label.configure(text=player or opponent, fg=FG)
            self.status_dot.configure(fg=ACCENT)
        else:
            self.names_label.configure(text="Ожидание…", fg=DIM)
            self.status_dot.configure(fg=DIM)

    def _render_tab(self) -> None:
        text = self.text
        text.configure(state="normal")
        text.delete("1.0", "end")
        text._combo_tags = {}
        tab = TABS[self._active_tab]
        if tab == "Комбо":
            self._combo_tab()
        elif tab == "План":
            self._plan_tab()
        elif tab == "Фишки":
            self._tips_tab()
        elif tab == "Словарь":
            self._glossary_tab()
        else:
            self._opponent_tab()
        text.configure(state="disabled")

    def _header(self, text: tk.Text, character: Character, color: str) -> None:
        text.insert("end", character.name + "\n", ("h1", "color_" + color))
        meta = []
        if character.archetype:
            meta.append(character.archetype)
        if character.difficulty:
            meta.append("сложность: " + character.difficulty)
        if meta:
            text.insert("end", " · ".join(meta) + "\n", "sub")
        text.tag_configure("color_" + color, foreground=color)

    def _insert_notation(self, text: tk.Text, notation: str, line_tag: str) -> str:
        official = to_official(notation) or notation
        for value, kind in iter_segments(official):
            if kind == "space":
                text.insert("end", value, (line_tag,))
            else:
                text.insert("end", value, (line_tag, "n_" + kind))
        return official

    def _combo_block(self, text: tk.Text, combos: list[Combo], title: str) -> None:
        if not combos:
            return
        text.insert("end", title + "\n", "h2")
        for i, combo in enumerate(combos):
            text.insert("end", f"◆ {combo.label}", "body")
            if combo.damage:
                text.insert("end", f"   {combo.damage}", "dmg")
            text.insert("end", "\n")
            tag = f"copy_{i}_{id(combos)}"
            official = self._insert_notation(text, combo.notation, tag)
            text.insert("end", "\n")
            if combo.note:
                text.insert("end", "note: " + combo.note + "\n", "src")
            if combo.source.startswith("kage"):
                text.insert("end", f"[{combo.source}] клик по нотации — копировать\n", "src")
            text._combo_tags[tag] = official
            text.tag_bind(tag, "<Button-1>", self._make_copier(text, tag))
            text.tag_bind(tag, "<Enter>", lambda e: text.configure(cursor="hand2"))
            text.tag_bind(tag, "<Leave>", lambda e: text.configure(cursor="arrow"))

    def _make_copier(self, text: tk.Text, tag: str) -> Callable[[tk.Event], None]:
        def handler(event: tk.Event) -> None:
            notation = text._combo_tags.get(tag, "")
            if notation:
                self.root.clipboard_clear()
                self.root.clipboard_append(notation)
                self._on_copy(notation)
        return handler

    def _bullets(self, text: tk.Text, items: tuple[str, ...] | list[str], title: str, tag: str) -> None:
        if not items:
            return
        text.insert("end", title + "\n", "h2")
        for item in items:
            text.insert("end", "• " + item + "\n", tag)

    def _combo_tab(self) -> None:
        text, character = self.text, self._player_char
        if character is None:
            text.insert("end", "КОМБО\n", "h1")
            text.insert("end", "Персонаж не определён. Выбери вручную или зайди на экран выбора.\n", "sub")
            return
        self._header(text, character, PLAYER_COLOR)
        self._combo_block(text, list(character.combos), "КОМБО")
        self._combo_block(text, self._kage_combos, "КОМБО С САЙТА (kagewebsite)")

    def _plan_tab(self) -> None:
        text, character = self.text, self._player_char
        if character is None:
            text.insert("end", "ПЛАН НА ИГРУ\n", "h1")
            text.insert("end", "Персонаж не определён.\n", "sub")
            return
        self._header(text, character, PLAYER_COLOR)
        self._bullets(text, character.game_plan, "ПЛАН НА ИГРУ", "good")

    def _tips_tab(self) -> None:
        text, character = self.text, self._player_char
        if character is None:
            text.insert("end", "ФИШКИ\n", "h1")
            text.insert("end", "Персонаж не определён.\n", "sub")
            return
        self._header(text, character, PLAYER_COLOR)
        self._bullets(text, character.tips, "ФИШКИ", "body")

    def _opponent_tab(self) -> None:
        text, character = self.text, self._opponent_char
        if character is None:
            text.insert("end", "ПРОТИВНИК\n", "h1")
            text.insert("end", "Персонаж противника не определён.\n", "sub")
            return
        self._header(text, character, OPPONENT_COLOR)
        self._bullets(text, character.threats, "ОПАСНО", "warn")
        self._bullets(text, character.weaknesses, "СЛАБОСТИ", "good")
        self._bullets(text, character.counterplay, "КАК ИГРАТЬ", "body")
        if character.key_moves:
            text.insert("end", "УДАРЫ, КОТОРЫЕ КАРАЮТ\n", "h2")
            for move in character.key_moves:
                text.insert("end", "◆ ", "body")
                self._insert_notation(text, move.input, "body")
                if move.name:
                    text.insert("end", f" — {move.name}", "dmg")
                text.insert("end", "\n")
                if move.note:
                    text.insert("end", move.note + "\n", "src")

    def _glossary_tab(self) -> None:
        text = self.text
        text.insert("end", "СЛОВАРЬ TEKKEN\n", "h1")
        text.insert("end", "Аббревиатуры и понятия файтингов\n\n", "sub")
        for category, terms in GLOSSARY.items():
            text.insert("end", category.upper() + "\n", "h2")
            for term, desc in terms:
                text.insert("end", term, "term")
                text.insert("end", " — " + desc + "\n", "sub")

    def show_error(self, message: str) -> None:
        self.set_status(message, OPPONENT_COLOR)
