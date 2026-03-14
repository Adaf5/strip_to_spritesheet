import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

def generate_spritesheet():
    #Get values from UI
    path = path_entry.get()
    try:
        c_w = int(entry_w.get())
        c_h = int(entry_h.get())
        rows = int(entry_rows.get())
        cols = int(entry_cols.get())
        pad = int(entry_pad.get())
    except ValueError:
        messagebox.showerror("Error", "Please enter valid numbers.")
        return

    if not path or not os.path.exists(path):
        messagebox.showerror("Error", "Select a valid PNG.")
        return

    try:
        #Process image
        strip = Image.open(path).convert("RGBA")
        strip_w, _ = strip.size
        num_chars = strip_w // c_w
        
        #Calculate sheet size
        sheet_width = (c_w * cols) + (pad * (cols + 1))
        sheet_height = (c_h * rows) + (pad * (rows + 1))
        spritesheet = Image.new("RGBA", (sheet_width, sheet_height), (0, 0, 0, 0))

        #Slice and paste loop
        for i in range(min(num_chars, rows * cols)):
            left = i * c_w
            if left + c_w > strip_w: break 
            
            char_crop = strip.crop((left, 0, left + c_w, c_h))
            col_idx = i % cols
            row_idx = i // cols

            paste_x = pad + (col_idx * (c_w + pad))
            paste_y = pad + (row_idx * (c_h + pad))
            spritesheet.paste(char_crop, (paste_x, paste_y))

        #Save with suffix
        file_dir, file_name = os.path.split(path)
        name_no_ext = os.path.splitext(file_name)[0]
        output_path = os.path.join(file_dir, f"{name_no_ext}_spritesheet.png")
        
        spritesheet.save(output_path, "PNG")
        messagebox.showinfo("Success", f"Saved to:\n{output_path}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def browse_file():
    #Open file dialog
    filename = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
    path_entry.delete(0, tk.END)
    path_entry.insert(0, filename)

#UI Setup
root = tk.Tk()
root.title("Spritesheet Maker")
root.geometry("400x350")

#File input UI
tk.Label(root, text="Select Source PNG:", font=('Arial', 10, 'bold')).pack(pady=5)
path_entry = tk.Entry(root, width=50)
path_entry.pack(padx=10)
tk.Button(root, text="Browse", command=browse_file).pack(pady=5)

#Parameter inputs
param_frame = tk.Frame(root)
param_frame.pack(pady=10)

labels = ["Cell Width:", "Cell Height:", "Grid Rows:", "Grid Cols:", "Padding:"]
defaults = ["14", "26", "10", "11", "2"]
entries = []

for i, label_text in enumerate(labels):
    tk.Label(param_frame, text=label_text).grid(row=i, column=0, sticky="e", padx=5)
    e = tk.Entry(param_frame)
    e.insert(0, defaults[i])
    e.grid(row=i, column=1, pady=2)
    entries.append(e)

entry_w, entry_h, entry_rows, entry_cols, entry_pad = entries

#Action button
tk.Button(root, text="GENERATE", bg="#4CAF50", fg="white", 
          font=('Arial', 12, 'bold'), command=generate_spritesheet).pack(pady=20)

root.mainloop()