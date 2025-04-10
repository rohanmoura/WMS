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
        # Load Master SKU mappings
        self.mapping_df = pd.read_excel(self.mapping_file,
                                        sheet_name="Msku With Skus")
        self.mapping_df.columns = self.mapping_df.columns.str.strip().str.lower()

        # Load Combo SKUs
        self.combo_df = pd.read_excel(self.mapping_file,
                                      sheet_name="Combos skus")
        self.combo_df.columns = self.combo_df.columns.str.strip().str.lower()

    def map_single_sku(self, sku):
        if not re.match(r'^[A-Za-z0-9]+$', sku.strip()):
            return None

        result = self.mapping_df[self.mapping_df['sku'] == sku.strip()]
        return result.iloc[0]['msku'] if not result.empty else None

    def get_combo_parts(self, combo_sku):
        row = self.combo_df[self.combo_df['combo'] == combo_sku.strip()]
        if not row.empty:
            parts = []
            for col in row.columns[1:]:  # Skip 'combo' column
                val = row.iloc[0][col]
                if pd.notna(val):
                    parts.append(val.strip())
            return parts
        return None


class SalesProcessor:

    def __init__(self, mapper: MappingLoader, sales_path: str, output_dir=""):
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
        if self.sales_path.endswith(".csv"):
            self.sales_df = pd.read_csv(self.sales_path)
        else:
            self.sales_df = pd.read_excel(self.sales_path)

        self.sales_df.columns = self.sales_df.columns.str.strip().str.lower()
        self.sku_column = self.detect_sku_column(self.sales_df.columns)

        if not self.sku_column:
            raise ValueError(
                "Sales sheet must contain a recognizable SKU column (e.g., 'SKU', 'FNSKU', 'ASIN')."
            )

    def process(self):
        self.load_sales()
        self.sales_df['msku'] = self.sales_df[self.sku_column].apply(self._map_sku)
        self._generate_logs()
        return self._save_output()

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

    def _save_output(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

        output_path = os.path.join(self.output_dir, f"mapped_output_{timestamp}.xlsx")
        self.sales_df.to_excel(output_path, index=False)

        log_path = os.path.join(self.output_dir, f"mapping_log_{timestamp}.txt")
        with open(log_path, "w") as f:
            f.write("\n".join(self.logs))

        return output_path, log_path
