"""
plugin_gui.py
-------------
Main GUI for the .RESOLVED → PDF Converter Plugin.
Built with tkinter (built into Python — no extra install needed).
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import subprocess
import sys

from convert_resolved import convert_resolved_to_pdf
from usage_tracker import can_convert, get_usage_today, increment_usage, is_premium, activate_premium, FREE_DAILY_LIMIT


# ─── Color Theme ──────────────────────────────────────────────────────────────
BG         = "#1E1E2E"
SURFACE    = "#313244"
ACCENT     = "#89B4FA"
GREEN      = "#A6E3A1"
YELLOW     = "#F9E2AF"
RED        = "#F38BA8"
TEXT       = "#CDD6F4"
MUTED      = "#6C7086"
BTN_HOVER  = "#45475A"


class ResolvedPDFPlugin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Resolved → PDF Converter")
        self.geometry("600x460")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.selected_file = tk.StringVar(value="No file selected")
        self.status_text   = tk.StringVar(value="Ready")
        self._build_ui()
        self._refresh_usage_display()

    # ── UI Build ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=ACCENT, height=4)
        header.pack(fill="x")

        title_frame = tk.Frame(self, bg=BG, pady=16)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="📄  Resolved → PDF Converter",
                 bg=BG, fg=ACCENT, font=("Segoe UI", 18, "bold")).pack()
        tk.Label(title_frame, text="Convert .resolved files to beautiful PDFs instantly",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack()

        # Divider
        tk.Frame(self, bg=SURFACE, height=1).pack(fill="x", padx=24)

        # Usage badge
        self.usage_frame = tk.Frame(self, bg=BG, pady=8)
        self.usage_frame.pack(fill="x", padx=24)
        self.usage_label = tk.Label(self.usage_frame, text="",
                                    bg=BG, fg=YELLOW, font=("Segoe UI", 9))
        self.usage_label.pack(side="left")
        tk.Button(self.usage_frame, text="⭐  Upgrade to Premium",
                  bg=SURFACE, fg=YELLOW, font=("Segoe UI", 9, "bold"),
                  relief="flat", cursor="hand2", activebackground=BTN_HOVER,
                  activeforeground=YELLOW, bd=0, padx=10, pady=4,
                  command=self._open_premium_dialog).pack(side="right")

        # File picker
        file_frame = tk.Frame(self, bg=SURFACE, padx=16, pady=14)
        file_frame.pack(fill="x", padx=24, pady=(8, 0))

        tk.Label(file_frame, text="Input File", bg=SURFACE, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")

        pick_row = tk.Frame(file_frame, bg=SURFACE)
        pick_row.pack(fill="x", pady=(4, 0))

        self.file_entry = tk.Entry(pick_row, textvariable=self.selected_file,
                                   bg="#45475A", fg=TEXT, insertbackground=TEXT,
                                   relief="flat", font=("Segoe UI", 10), bd=4)
        self.file_entry.pack(side="left", fill="x", expand=True)

        tk.Button(pick_row, text="Browse", bg=ACCENT, fg=BG,
                  font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                  activebackground="#6C9EE8", activeforeground=BG,
                  bd=0, padx=12, pady=4,
                  command=self._browse_file).pack(side="right", padx=(8, 0))

        # Output folder picker
        out_frame = tk.Frame(self, bg=BG, padx=24, pady=6)
        out_frame.pack(fill="x")
        tk.Label(out_frame, text="Output folder (optional — default: same as input)",
                 bg=BG, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w")

        out_row = tk.Frame(out_frame, bg=BG)
        out_row.pack(fill="x", pady=(2, 0))
        self.out_var = tk.StringVar(value="")
        self.out_entry = tk.Entry(out_row, textvariable=self.out_var,
                                  bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                                  relief="flat", font=("Segoe UI", 9), bd=4)
        self.out_entry.pack(side="left", fill="x", expand=True)
        tk.Button(out_row, text="📁", bg=SURFACE, fg=TEXT, font=("Segoe UI", 10),
                  relief="flat", cursor="hand2", bd=0, padx=8, pady=2,
                  command=self._browse_output).pack(side="right", padx=(6, 0))

        # Convert button
        self.convert_btn = tk.Button(
            self, text="⚡  Convert to PDF",
            bg=ACCENT, fg=BG, font=("Segoe UI", 13, "bold"),
            relief="flat", cursor="hand2",
            activebackground="#6C9EE8", activeforeground=BG,
            bd=0, padx=24, pady=12,
            command=self._start_conversion
        )
        self.convert_btn.pack(pady=16)

        # Status bar
        status_frame = tk.Frame(self, bg=SURFACE, padx=16, pady=8)
        status_frame.pack(fill="x", padx=24, pady=(0, 16))
        tk.Label(status_frame, textvariable=self.status_text,
                 bg=SURFACE, fg=GREEN, font=("Segoe UI", 9)).pack(side="left")

        # Footer
        tk.Label(self, text="Free plan: 3 conversions/day  •  Upgrade for unlimited",
                 bg=BG, fg=MUTED, font=("Segoe UI", 8)).pack(pady=(0, 8))

    # ── Actions ───────────────────────────────────────────────────────────────
    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select .resolved file",
            filetypes=[("Resolved files", "*.resolved"), ("All files", "*.*")]
        )
        if path:
            self.selected_file.set(path)

    def _browse_output(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.out_var.set(folder)

    def _refresh_usage_display(self):
        if is_premium():
            self.usage_label.config(text="⭐  Premium — Unlimited conversions", fg=YELLOW)
        else:
            used = get_usage_today()
            remaining = max(0, FREE_DAILY_LIMIT - used)
            color = GREEN if remaining > 1 else (YELLOW if remaining == 1 else RED)
            self.usage_label.config(
                text=f"Free plan: {remaining}/{FREE_DAILY_LIMIT} conversions left today",
                fg=color
            )

    def _start_conversion(self):
        allowed, message = can_convert()
        if not allowed:
            self._show_upgrade_prompt(message)
            return

        input_path = self.selected_file.get().strip()
        if not input_path or input_path == "No file selected":
            messagebox.showwarning("No File", "Please select a .resolved file first.")
            return

        if not os.path.exists(input_path):
            messagebox.showerror("File Not Found", f"File does not exist:\n{input_path}")
            return

        # Build output path
        out_folder = self.out_var.get().strip()
        if out_folder:
            base = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(out_folder, base + ".pdf")
        else:
            output_path = None

        self._set_status("⏳  Converting...", YELLOW)
        self.convert_btn.config(state="disabled")
        threading.Thread(target=self._do_convert,
                         args=(input_path, output_path), daemon=True).start()

    def _do_convert(self, input_path, output_path):
        try:
            result = convert_resolved_to_pdf(input_path, output_path)
            increment_usage()
            self.after(0, self._on_success, result)
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _on_success(self, pdf_path):
        self._set_status(f"✅  Saved: {os.path.basename(pdf_path)}", GREEN)
        self.convert_btn.config(state="normal")
        self._refresh_usage_display()
        answer = messagebox.askyesno(
            "Conversion Complete",
            f"PDF saved to:\n{pdf_path}\n\nOpen the file now?"
        )
        if answer:
            os.startfile(pdf_path)

    def _on_error(self, error_msg):
        self._set_status(f"❌  Error: {error_msg}", RED)
        self.convert_btn.config(state="normal")
        messagebox.showerror("Conversion Failed", error_msg)

    def _set_status(self, msg, color=TEXT):
        self.status_text.set(msg)
        for widget in self.nametowidget(".").winfo_children():
            pass  # just trigger refresh
        self.update_idletasks()

    # ── Premium Dialog ────────────────────────────────────────────────────────
    def _show_upgrade_prompt(self, message):
        messagebox.showinfo(
            "Daily Limit Reached",
            f"{message}\n\nClick 'Upgrade to Premium' to get unlimited access."
        )

    def _open_premium_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Upgrade to Premium")
        dialog.geometry("400x280")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.grab_set()

        tk.Label(dialog, text="⭐  Go Premium", bg=BG, fg=YELLOW,
                 font=("Segoe UI", 16, "bold")).pack(pady=(20, 4))
        tk.Label(dialog, text="Unlimited conversions · All formats · Priority support",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack()

        tk.Frame(dialog, bg=SURFACE, height=1).pack(fill="x", padx=24, pady=12)

        tk.Label(dialog, text="Enter your license key:", bg=BG, fg=TEXT,
                 font=("Segoe UI", 10)).pack(anchor="w", padx=30)
        key_var = tk.StringVar()
        key_entry = tk.Entry(dialog, textvariable=key_var, bg=SURFACE, fg=TEXT,
                             insertbackground=TEXT, relief="flat",
                             font=("Courier", 11), bd=6, show="")
        key_entry.pack(fill="x", padx=30, pady=6)

        msg_var = tk.StringVar()
        msg_label = tk.Label(dialog, textvariable=msg_var, bg=BG, fg=RED,
                             font=("Segoe UI", 9))
        msg_label.pack()

        def activate():
            key = key_var.get().strip()
            if activate_premium(key):
                msg_var.set("")
                messagebox.showinfo("Success", "🎉 Premium activated! Enjoy unlimited conversions.")
                self._refresh_usage_display()
                dialog.destroy()
            else:
                msg_var.set("❌  Invalid license key. Please try again.")

        tk.Button(dialog, text="Activate License", bg=ACCENT, fg=BG,
                  font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
                  activebackground="#6C9EE8", bd=0, padx=20, pady=8,
                  command=activate).pack(pady=12)

        tk.Label(dialog, text="Don't have a key? Visit resolvedpdf.com/premium",
                 bg=BG, fg=MUTED, font=("Segoe UI", 8)).pack()


if __name__ == "__main__":
    app = ResolvedPDFPlugin()
    app.mainloop()
