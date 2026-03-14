import os
import ctypes 
import customtkinter as ctk 
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk 
import sys

#Set visual theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_font(font_path):
    if os.path.exists(font_path):
        ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0) 

try:
    myappid = 'adaf.striptospritesheet.v1' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

class Popup:
    def __init__(self, text, font, parent):
        self.parent = parent
        self.tip_window = None
        self.text = text
        self.font = font
        self.visible = False
        self.alpha = 0.0

    def show(self, x, y):
        if self.tip_window:
            return
        self.tip_window = tw = ctk.CTkToplevel(self.parent)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-alpha", 0.0)

        self.frame = ctk.CTkFrame(tw, corner_radius=8, fg_color="#333333")
        self.frame.pack()
        self.label = ctk.CTkLabel(self.frame, text=self.text, font=self.font, text_color="white")
        self.label.pack(padx=10, pady=5)

        self.alpha = 0.0
        self.visible = True
        self._fade_in()

    def hide(self):
        if self.tip_window:
            self.visible = False
            self._fade_out()

    def _fade_in(self):
        if not self.tip_window or not self.visible:
            return
        self.alpha = min(self.alpha + 0.1, 1.0)
        self.tip_window.attributes("-alpha", self.alpha)
        if self.alpha < 1.0:
            self.tip_window.after(20, self._fade_in)

    def _fade_out(self):
        if not self.tip_window:
            return
        self.alpha = max(self.alpha - 0.1, 0.0)
        self.tip_window.attributes("-alpha", self.alpha)
        if self.alpha > 0.0:
            self.tip_window.after(20, self._fade_out)
        else:
            if self.tip_window:
                self.tip_window.destroy()
                self.tip_window = None

class ToolTip:
    def __init__(self, widget, text, font):
        self.widget = widget
        self.text = text
        self.font = font
        self.popup = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.popup = Popup(self.text, self.font, parent=self.widget.winfo_toplevel())
        self.popup.show(x, y)

    def hide_tip(self, event=None):
        if self.popup:
            self.popup.hide()
            self.popup = None

class SpriteTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        load_font("SilverFont.ttf")
        
        self.ui_scale = 0.8
        base_w, base_h = 850, 900 
        w, h = int(base_w * self.ui_scale), int(base_h * self.ui_scale)
        self.title("Spritesheet Maker")
        self.geometry(f"{w}x{h}")
        
        self.apply_icon("logo.ico") 
        self.current_strip = None
        self.last_export_path = "" 
        self.preview_scale = 1.0 
        self.preview_origin = (0, 0)

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        #Left Side
        self.left_panel = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.left_panel.pack(side="left", fill="both", expand=True, padx=20)

        self.custom_font = ctk.CTkFont(family="Silver Font", size=int(24 * self.ui_scale))
        self.btn_font = ctk.CTkFont(family="Silver Font", size=int(18 * self.ui_scale))
        self.tip_font = ctk.CTkFont(family="Silver Font", size=int(14 * self.ui_scale))

        self.label = ctk.CTkLabel(self.left_panel, text="Strip to Spritesheet", font=self.custom_font)
        self.label.pack(pady=(20, 5))
        
        self.path_entry = ctk.CTkEntry(self.left_panel, width=int(400 * self.ui_scale), placeholder_text="Select a file...", font=self.btn_font)
        self.path_entry.pack(pady=int(5 * self.ui_scale))
        
        self.browse_btn = ctk.CTkButton(self.left_panel, text="Browse Files", font=self.btn_font, command=self.browse_file)
        self.browse_btn.pack(pady=int(10 * self.ui_scale), ipadx=int(10 * self.ui_scale), ipady=int(5 * self.ui_scale))

        self.inputs = {}
        params = [
            ("Cell Width", "16", "Width of one single character frame"),
            ("Cell Height", "26", "Height of one single character frame"),
            ("Rows", "10", "Total rows in the final sheet"),
            ("Cols", "11", "Total columns in the final sheet"),
            ("Padding", "2", "Empty pixels between each cell")
        ]

        for i, (label_text, default, hint) in enumerate(params):
            row_frame = ctk.CTkFrame(self.left_panel, corner_radius=10, fg_color="#1f1f1f")
            row_frame.pack(padx=10, pady=2, fill="x")
            row_frame.grid_columnconfigure(2, weight=1)

            q_mark = ctk.CTkLabel(row_frame, text="?", font=self.btn_font, text_color="#2ecc71", cursor="hand2")
            q_mark.grid(row=0, column=0, padx=(10, 8), pady=5, sticky="w")
            ToolTip(q_mark, hint, self.tip_font)

            lbl = ctk.CTkLabel(row_frame, text=label_text, font=self.btn_font)
            lbl.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="w")

            var = ctk.StringVar(value=default)
            var.trace_add("write", lambda *args: self.update_preview())
            
            entry = ctk.CTkEntry(row_frame, width=int(80 * self.ui_scale), font=self.btn_font, justify="center", textvariable=var)
            entry.grid(row=0, column=2, padx=(0, 10), pady=5, sticky="e")
            entry.bind("<MouseWheel>", lambda e, entry=entry: self._on_entry_scroll(e, entry))
            self.inputs[label_text] = entry

        self.gen_btn = ctk.CTkButton(self.left_panel, text="SAVE SPRITESHEET", 
                                     font=self.custom_font,
                                     fg_color="#0a8014", hover_color="#28bb2f",
                                     command=self.save_sheet)
        self.gen_btn.pack(pady=15, ipadx=15, ipady=8)

        self.dim_label = ctk.CTkLabel(self.left_panel, text="Strip Dimensions: 0 x 0", font=self.tip_font, text_color="gray")
        self.dim_label.pack()

        self.preview_frame = ctk.CTkFrame(self.left_panel, height=int(300 * self.ui_scale), fg_color="#111111")
        self.preview_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.preview_canvas = tk.Canvas(self.preview_frame, bg="#111111", highlightthickness=0)
        self.preview_hscroll = ctk.CTkScrollbar(self.preview_frame, orientation="horizontal", command=self.preview_canvas.xview)
        self.preview_vscroll = ctk.CTkScrollbar(self.preview_frame, orientation="vertical", command=self.preview_canvas.yview)
        self.preview_canvas.configure(xscrollcommand=self.preview_hscroll.set, yscrollcommand=self.preview_vscroll.set)
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")
        self.preview_vscroll.grid(row=0, column=1, sticky="ns")
        self.preview_hscroll.grid(row=1, column=0, sticky="ew")
        self.preview_frame.grid_rowconfigure(0, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        
        self.preview_canvas.bind("<MouseWheel>", self.on_preview_wheel)
        self.preview_canvas.bind("<ButtonPress-1>", self.start_pan)
        self.preview_canvas.bind("<B1-Motion>", self.pan)
        self.preview_canvas.bind("<ButtonRelease-1>", self.end_pan)
        self._pan_start = None

        self.right_panel = ctk.CTkFrame(self.main_container, width=0, fg_color="#181818") 
        
        controls_frame = ctk.CTkFrame(self.left_panel)
        controls_frame.pack(padx=10, pady=(5, 15), fill="x")
        self.zoom_label = ctk.CTkLabel(controls_frame, text="Zoom: 100%", font=self.tip_font)
        self.zoom_label.pack(side="left", padx=5)
        self.reset_zoom_btn = ctk.CTkButton(controls_frame, text="Reset Zoom", font=self.tip_font, command=self.reset_zoom, width=int(100 * self.ui_scale))
        self.reset_zoom_btn.pack(side="right", padx=5)

    def apply_icon(self, icon_path):
        if not os.path.isabs(icon_path):
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), icon_path)
        if os.path.exists(icon_path):
            try:
                if icon_path.lower().endswith('.ico'):
                    self.iconbitmap(icon_path)
                else:
                    img = Image.open(icon_path)
                    self.tk_icon = ImageTk.PhotoImage(img)
                    self.iconphoto(False, self.tk_icon)
            except: pass

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if filename:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, filename)
            try:
                self.current_strip = Image.open(filename).convert("RGBA")
                w, h = self.current_strip.size
                self.dim_label.configure(text=f"Strip Dimensions: {w}px x {h}px")
                self.preview_scale = 1.0 
                self.preview_origin = (0, 0)
                self.update_preview()
            except Exception as e:
                messagebox.showerror("Invalid Image", f"Unable to load image:\n{e}")

    def update_preview(self):
        try:
            c_w = int(self.inputs["Cell Width"].get() or 0)
            c_h = int(self.inputs["Cell Height"].get() or 0)
            rows = int(self.inputs["Rows"].get() or 0)
            cols = int(self.inputs["Cols"].get() or 0)
            pad = int(self.inputs["Padding"].get() or 0)
            if c_w <= 0 or c_h <= 0 or rows <= 0 or cols <= 0: return

            num_chars = self.current_strip.size[0] // c_w
            s_w, s_h = (c_w * cols) + (pad * (cols + 1)), (c_h * rows) + (pad * (rows + 1))
            if s_w > 8000 or s_h > 8000: return 

            self.generated_sheet = Image.new("RGBA", (s_w, s_h), (0, 0, 0, 0))
            for i in range(min(num_chars, rows * cols)):
                left = i * c_w
                char = self.current_strip.crop((left, 0, min(left + c_w, self.current_strip.size[0]), min(c_h, self.current_strip.size[1])))
                px, py = pad + ((i % cols) * (c_w + pad)), pad + ((i // cols) * (c_h + pad))
                self.generated_sheet.paste(char, (px, py))

            self._draw_preview()
        except (ValueError, Exception): pass

    def _draw_preview(self): 
        w = self.preview_canvas.winfo_width() or 560
        h = self.preview_canvas.winfo_height() or 280
        self.preview_canvas.delete("all")
        if not hasattr(self, "generated_sheet"): return

        img_w, img_h = int(self.generated_sheet.width * self.preview_scale), int(self.generated_sheet.height * self.preview_scale)
    
        if self.preview_scale == 1.0:
            preview_img = self.generated_sheet
        else:
            preview_img = self.generated_sheet.resize((max(1, img_w), max(1, img_h)), Image.NEAREST)
        
        self.preview_tk = ImageTk.PhotoImage(preview_img)
        
        draw_x = (w - img_w) // 2 if img_w < w else self.preview_origin[0]
        draw_y = (h - img_h) // 2 if img_h < h else self.preview_origin[1]

        self.preview_canvas.create_image(draw_x, draw_y, anchor="nw", image=self.preview_tk)
        self.preview_canvas.configure(scrollregion=(0, 0, max(w, img_w), max(h, img_h)))
        self.zoom_label.configure(text=f"Zoom: {int(self.preview_scale * 100)}%")

    def save_sheet(self):
        if not hasattr(self, 'generated_sheet'): return
        path = self.path_entry.get()
        if not path: return
        file_dir = os.path.dirname(path)
        out_name = os.path.splitext(os.path.basename(path))[0] + "_spritesheet.png"
        output_path = os.path.join(file_dir, out_name)
        try:
            self.generated_sheet.save(output_path, "PNG")
            self.last_export_path = file_dir
            self.show_export_panel(out_name)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_export_panel(self, out_name):
        for widget in self.right_panel.winfo_children(): widget.destroy()
        self.right_panel.pack(side="right", fill="both", padx=(0, 20), pady=20, expand=False)
        self.right_panel.configure(width=int(250 * self.ui_scale)) 
        header = ctk.CTkFrame(self.right_panel, fg_color="#0f4d07", corner_radius=8)
        header.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(header, text="Export Success", font=self.btn_font, text_color="white").pack(pady=10)
        ctk.CTkLabel(self.right_panel, text=f"File: {out_name}", font=self.tip_font, wraplength=180).pack(pady=10)
        ctk.CTkButton(self.right_panel, text="Open Folder", font=self.btn_font, fg_color="#0a8014", 
                      command=lambda: os.startfile(self.last_export_path)).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(self.right_panel, text="Copy Path", font=self.btn_font, fg_color="#1f6feb",
                      command=lambda: [self.clipboard_clear(), self.clipboard_append(self.last_export_path)]).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(self.right_panel, text="Dismiss", font=self.btn_font, fg_color="#444444", 
                      command=self.right_panel.pack_forget).pack(pady=(20, 5), padx=20, fill="x")

    def _on_entry_scroll(self, event, entry):
        try: value = int(entry.get())
        except: return
        delta = (1 if event.delta > 0 else -1) * (10 if event.state & 0x4 else 1)
        entry.delete(0, "end"); entry.insert(0, str(max(1, value + delta)))
        self.update_preview()

    def reset_zoom(self):
        self.preview_scale = 1.0; self.preview_origin = (0, 0); self._draw_preview()

    def on_preview_wheel(self, event):
        if not hasattr(self, "generated_sheet"): return
        if event.state & 0x4: 
            scale_step = 1.2 if event.delta > 0 else 0.8
            new_scale = max(0.1, min(10.0, self.preview_scale * scale_step))
            if new_scale != self.preview_scale:
                self.preview_scale = new_scale
                self._draw_preview()
        else:
            self.preview_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def start_pan(self, event): self._pan_start = (event.x, event.y, self.preview_origin[0], self.preview_origin[1])
    def end_pan(self, event): self._pan_start = None
    def pan(self, event):
        if not self._pan_start: return
        self.preview_origin = (self._pan_start[2] + (event.x - self._pan_start[0]), self._pan_start[3] + (event.y - self._pan_start[1]))
        self._draw_preview()

if __name__ == "__main__":
    app = SpriteTool()
    app.mainloop()