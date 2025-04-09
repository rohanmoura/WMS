# sku_mapper.py
import pandas as pd
import os
from datetime import datetime

class MappingLoader:
    def __init__(self, mapping_file):
        self.mapping_file = mapping_file
        self.mapping_df = None
        self.combo_df = None
        self.load_mapping()

    def load_mapping(self):
        self.mapping_df = pd.read_excel(self.mapping_file, sheet_name="Msku With Skus")
        self.mapping_df.columns = self.mapping_df.columns.str.strip().str.lower()

        self.combo_df = pd.read_excel(self.mapping_file, sheet_name="Combos skus")
        self.combo_df.columns = self.combo_df.columns.str.strip()

    def map_single_sku(self, sku):
        result = self.mapping_df[self.mapping_df['sku'] == sku.strip()]
        if not result.empty:
            return result.iloc[0]['msku']
        return None

    def is_combo(self, sku):
        return '+' in sku

    def get_combo_parts(self, sku):
        row = self.combo_df[self.combo_df['Combo '] == sku.strip()]
        if not row.empty:
            parts = []
            for col in row.columns[1:15]:  # SKU1 to SKU14
                val = row.iloc[0][col]
                if pd.notna(val):
                    parts.append(val.strip())
            return parts
        return None

class SalesProcessor:
    def __init__(self, mapper: MappingLoader, sales_path: str):
        self.mapper = mapper
        self.sales_path = sales_path
        self.sales_df = None
        self.logs = []
        self.output_df = None

    def detect_sku_column(self, columns):
        possible_names = ['SKU', 'MSKU', 'FNSKU', 'ASIN', 'Product Code']
        for name in possible_names:
            if name in columns:
                return name
        return None

    def load_sales(self):
        if self.sales_path.endswith(".csv"):
            self.sales_df = pd.read_csv(self.sales_path)
        else:
            self.sales_df = pd.read_excel(self.sales_path)

        self.sales_df.columns = self.sales_df.columns.str.strip()
        sku_column = self.detect_sku_column(self.sales_df.columns)

        if not sku_column:
            raise ValueError("Sales sheet must contain a recognizable SKU column (e.g., 'SKU', 'FNSKU', 'ASIN').")

        self.sku_column = sku_column

    def process(self):
        self.load_sales()
        mapped_rows = []

        for _, row in self.sales_df.iterrows():
            sku = str(row[self.sku_column]).strip()
            msku = None

            if self.mapper.is_combo(sku):
                parts = self.mapper.get_combo_parts(sku)
                if parts:
                    mapped_parts = [self.mapper.map_single_sku(p) or f"[MISSING:{p}]" for p in parts]
                    msku = '+'.join(mapped_parts)
                else:
                    msku = f"[INVALID COMBO:{sku}]"
                    self.logs.append(f"Invalid combo SKU not found in combo sheet: {sku}")
            else:
                msku = self.mapper.map_single_sku(sku)
                if not msku:
                    msku = f"[MISSING:{sku}]"
                    self.logs.append(f"Unmapped SKU: {sku}")

            new_row = row.to_dict()
            new_row['MSKU'] = msku
            mapped_rows.append(new_row)

        self.output_df = pd.DataFrame(mapped_rows)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("part1_sku_mapping/output", exist_ok=True)
        out_file = f"part1_sku_mapping/output/mapped_output_{timestamp}.xlsx"
        log_file = f"part1_sku_mapping/output/mapping_log_{timestamp}.txt"

        self.output_df.to_excel(out_file, index=False)
        with open(log_file, "w") as f:
            f.write("\n".join(self.logs))

        return out_file, log_file
