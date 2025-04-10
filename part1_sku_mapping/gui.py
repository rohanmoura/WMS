import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from sku_mapper import MappingLoader, SalesProcessor
import pandas as pd

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("WMS SKU Mapper")
        self.root.geometry("800x600")

        self.mapping_file = None
        self.sales_file = None
        self.output_df = None

        # Widgets
        self.create_widgets()

    def create_widgets(self):
        # Mapping File Section
        tk.Label(self.root, text="Mapping File (Excel):").pack(pady=5)
        self.mapping_entry = tk.Entry(self.root, width=50)
        self.mapping_entry.pack()
        tk.Button(self.root, text="Browse", command=self.upload_mapping).pack(pady=5)

        # Sales File Section
        tk.Label(self.root, text="Sales Data File:").pack(pady=5)
        self.sales_entry = tk.Entry(self.root, width=50)
        self.sales_entry.pack()
        tk.Button(self.root, text="Browse", command=self.upload_sales).pack(pady=5)

        # Progress Bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=20)

        # Process Button
        tk.Button(self.root, text="Process Mapping", command=self.process_mapping).pack(pady=10)

        # Logs and Preview
        self.log = tk.Text(self.root, height=10, width=80)
        self.log.pack(pady=10)
        self.preview = ttk.Treeview(self.root, columns=("SKU", "MSKU"), show="headings")
        self.preview.heading("SKU", text="SKU")
        self.preview.heading("MSKU", text="MSKU")
        self.preview.pack(pady=10)

    def upload_mapping(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            self.mapping_entry.delete(0, tk.END)
            self.mapping_entry.insert(0, path)
            self.mapping_file = path

    def upload_sales(self):
        path = filedialog.askopenfilename(filetypes=[("Excel/CSV files", "*.xlsx *.xls *.csv")])
        if path:
            self.sales_entry.delete(0, tk.END)
            self.sales_entry.insert(0, path)
            self.sales_file = path

    def process_mapping(self):
        if not self.mapping_file or not self.sales_file:
            messagebox.showerror("Error", "Both files must be selected.")
            return

        try:
            # Initialize processor
            loader = MappingLoader(self.mapping_file)
            processor = SalesProcessor(loader, self.sales_file)
            processor.process()
            self.output_df = processor.sales_df

            # Update UI
            self.log.delete(1.0, tk.END)
            self.log.insert(tk.END, "\n".join(processor.logs))
            self.preview.delete(*self.preview.get_children())

            # Show first 5 rows
            for _, row in processor.sales_df.head(5).iterrows():
                self.preview.insert("", "end", values=(row[processor.sku_column], row['msku']))

            messagebox.showinfo("Success", "Mapping complete! Output saved.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log.insert(tk.END, f"Error: {str(e)}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()