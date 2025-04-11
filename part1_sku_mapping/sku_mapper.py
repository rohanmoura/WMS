import pandas as pd
import os
from datetime import datetime
import re

class MappingLoader:
    def __init__(self, mapping_file):
        self.mapping_file = mapping_file
        self.mapping_df = None
        self.combo_df = None
        self.load_mapping()

    def load_mapping(self):
        # Add error handling for file loading
        try:
            self.mapping_df = pd.read_excel(self.mapping_file, sheet_name="Msku With Skus")
            self.mapping_df.columns = self.mapping_df.columns.str.strip().str.lower()
            
            # Create a dictionary for faster lookups
            self.sku_to_msku = dict(zip(self.mapping_df['sku'].str.strip(), self.mapping_df['msku']))
            
            self.combo_df = pd.read_excel(self.mapping_file, sheet_name="Combos skus")
            self.combo_df.columns = self.combo_df.columns.str.strip().str.lower()
            
            # Create a dictionary for combo lookups
            self.combo_dict = {}
            for _, row in self.combo_df.iterrows():
                # Convert to string first to handle integers
                combo_key = str(row['combo']).strip()
                parts = [str(val).strip() for val in row.iloc[1:] if pd.notna(val)]
                if parts:
                    self.combo_dict[combo_key] = parts
        except Exception as e:
            raise ValueError(f"Error loading mapping file: {str(e)}")

    def map_single_sku(self, sku):
        if not sku or not isinstance(sku, str):
            return None
            
        sku = sku.strip()
        if not re.match(r'^[A-Za-z0-9\-_&.]+$', sku):  # Updated regex to include more characters
            return None
            
        # Use dictionary lookup instead of DataFrame filtering (much faster)
        return self.sku_to_msku.get(sku)

    def get_combo_parts(self, combo_sku):
        if not combo_sku or not isinstance(combo_sku, str):
            return None
            
        combo_sku = combo_sku.strip()
        # Use dictionary lookup instead of DataFrame filtering
        return self.combo_dict.get(combo_sku)

class SalesProcessor:
    def __init__(self, mapper: MappingLoader, sales_path: str, output_dir="output"):
        self.mapper = mapper
        self.sales_path = sales_path
        self.output_dir = output_dir
        self.sales_df = None
        self.logs = []
        self.output_df = None
        self.sku_column = None

    def detect_sku_column(self, columns):
        possible_names = ['sku', 'msku', 'fnsku', 'asin', 'product code']
        for name in possible_names:
            if name in columns.str.lower().tolist():
                return columns[(columns.str.lower() == name)].values[0]
        return None

    def load_sales(self):
        try:
            if self.sales_path.endswith(".csv"):
                self.sales_df = pd.read_csv(self.sales_path)
            else:
                self.sales_df = pd.read_excel(self.sales_path)

            self.sales_df.columns = self.sales_df.columns.str.strip().str.lower()
            self.sku_column = self.detect_sku_column(self.sales_df.columns)

            if not self.sku_column:
                raise ValueError("Sales sheet must contain a recognizable SKU column (e.g., 'SKU', 'FNSKU').")
        except Exception as e:
            raise ValueError(f"Error loading sales file: {str(e)}")

    def process(self, output_filename=None, log_filename=None):
        self.load_sales()
        # Apply mapping in a more efficient way
        self.sales_df['msku'] = self.sales_df[self.sku_column].astype(str).apply(self._map_sku)
        self._generate_logs()
        return self._save_output(output_filename, log_filename)

    def _map_sku(self, sku):
        sku = str(sku).strip()
        if '+' in sku:
            return self._process_combo(sku)
        else:
            msku = self.mapper.map_single_sku(sku)
            if not msku:
                self.logs.append(f"Unmapped SKU: {sku}")
                return f"[MISSING:{sku}]"
            return msku

    def _process_combo(self, combo_sku):
        parts = self.mapper.get_combo_parts(combo_sku)
        if not parts:
            self.logs.append(f"Invalid combo SKU: {combo_sku}")
            return f"[INVALID COMBO:{combo_sku}]"

        mapped_parts = []
        for part in parts:
            mapped = self.mapper.map_single_sku(part)
            if mapped:
                mapped_parts.append(mapped)
            else:
                mapped_parts.append(f"[MISSING:{part}]")
                self.logs.append(f"Missing part in combo: {part}")
        return '+'.join(mapped_parts)

    def _generate_logs(self):
        missing_skus = [log for log in self.logs if "Unmapped" in log]
        invalid_combos = [log for log in self.logs if "Invalid combo" in log]
        missing_parts = [log for log in self.logs if "Missing part" in log]

        summary = [
            f"Total Rows Processed: {len(self.sales_df)}",
            f"Total Unmapped SKUs: {len(missing_skus)}",
            f"Invalid Combos: {len(invalid_combos)}",
            f"Missing Parts in Combos: {len(missing_parts)}",
            "---- Detailed Logs ----", *self.logs
        ]
        self.logs = summary

    def _save_output(self, output_filename=None, log_filename=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
    
        if not output_filename:
            output_filename = f"mapped_output_{timestamp}.xlsx"
        if not log_filename:
            log_filename = f"mapping_log_{timestamp}.txt"
    
        output_path = os.path.join(self.output_dir, output_filename)
        log_path = os.path.join(self.output_dir, log_filename)
    
        # Fix NaN values before saving
        self.sales_df = self.sales_df.fillna("")
        
        # Save with absolute paths
        try:
            self.sales_df.to_excel(output_path, index=False)
            with open(log_path, "w") as f:
                f.write("\n".join(self.logs))
                
                # Also save as JSON for the dashboard
                json_filename = output_filename.replace('.xlsx', '.json')
                json_path = os.path.join(self.output_dir, json_filename)
                self.sales_df.to_json(json_path, orient='records', indent=2)
                print(f"JSON file saved to: {json_path}")
        except Exception as e:
            raise ValueError(f"Error saving output files: {str(e)}")
    
        return output_path, log_path

# Optional CLI usage for testing
if __name__ == "__main__":
    wms_file = input("Enter path to WMS mapping Excel file: ").strip()
    sales_file = input("Enter path to Sales Excel/CSV file: ").strip()
    
    mapper = MappingLoader(wms_file)
    processor = SalesProcessor(mapper, sales_file)
    
    output_file, log_file = processor.process()
    print(f"✅ Mapping Complete!\nOutput File: {output_file}\nLog File: {log_file}")
