import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Scrollable Frame")

# Create a notebook widget
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# Create a scrollable frame
scroll_frame = ttk.Frame(notebook)
scroll_frame.pack(fill=tk.BOTH, expand=True)

# Create a vertical scrollbar
vscrollbar = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL)

# Create a horizontal scrollbar
hscrollbar = ttk.Scrollbar(scroll_frame, orient=tk.HORIZONTAL)

# Create a canvas
canvas = tk.Canvas(scroll_frame, yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Configure the scrollbars to work with the canvas
vscrollbar.configure(command=canvas.yview)
hscrollbar.configure(command=canvas.xview)

# Add the scrollbars to the scroll frame
vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)

# Create a frame inside the canvas
frame = ttk.Frame(canvas)
canvas.create_window((0, 0), window=frame, anchor='nw')

# Add widgets to the frame
for i in range(50):
    label = ttk.Label(frame, text=f"Label {i}")
    label.pack(padx=10, pady=10)

# Configure the canvas to scroll with the frame
frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))

# Add the scrollable frame to the notebook
notebook.add(scroll_frame, text="Scrollable Frame")

root.mainloop()
