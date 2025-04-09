# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox
from sku_mapper import MappingLoader, SalesProcessor

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("WMS SKU to MSKU Mapper")

        self.mapping_file = None
        self.sales_file = None

        tk.Button(root, text="Upload Mapping Sheet", command=self.upload_mapping).pack(pady=5)
        tk.Button(root, text="Upload Sales Sheet", command=self.upload_sales).pack(pady=5)
        tk.Button(root, text="Process Mapping", command=self.process_mapping).pack(pady=5)

        self.log = tk.Text(root, height=20, width=80)
        self.log.pack()

    def upload_mapping(self):
        path = filedialog.askopenfilename()
        if path:
            self.mapping_file = path
            self.log.insert(tk.END, f"Loaded Mapping Sheet: {path}\n")

    def upload_sales(self):
        path = filedialog.askopenfilename()
        if path:
            self.sales_file = path
            self.log.insert(tk.END, f"Loaded Sales Sheet: {path}\n")

    def process_mapping(self):
        if not self.mapping_file or not self.sales_file:
            messagebox.showerror("Error", "Please upload both mapping and sales files.")
            return

        try:
            mapper = MappingLoader(self.mapping_file)
            processor = SalesProcessor(mapper, self.sales_file)
            output_path, log_path = processor.process()

            self.log.insert(tk.END, f"\nProcessing complete!\nOutput saved at: {output_path}\nLogs saved at: {log_path}\n")
        except Exception as e:
            self.log.insert(tk.END, f"\nError: {str(e)}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
