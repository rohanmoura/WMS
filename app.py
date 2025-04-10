import os
import uuid
import pandas as pd
import duckdb
import matplotlib.pyplot as plt
from flask import Flask, request, render_template, send_from_directory
from werkzeug.utils import secure_filename
from transformers import AutoTokenizer, AutoModelForCausalLM  # ✅ FIXED

from part1_sku_mapping.sku_mapper import MappingLoader, SalesProcessor
from part3_webapp.airtable import update_airtable

# --- Flask Setup ---
app = Flask(__name__)
UPLOAD_FOLDER = os.path.join("part3_webapp", "uploads")
OUTPUT_FOLDER = os.path.join("static", "outputs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# --- Load AI Model (only once) ---
tokenizer = AutoTokenizer.from_pretrained("defog/sqlcoder")
model = AutoModelForCausalLM.from_pretrained("defog/sqlcoder")

# --- DuckDB Setup ---
DUCKDB_PATH = os.path.join(UPLOAD_FOLDER, "sales_duck.db")
con = duckdb.connect(DUCKDB_PATH)

def update_duckdb(df: pd.DataFrame):
    con.execute("DROP TABLE IF EXISTS sales")
    con.execute("CREATE TABLE sales AS SELECT * FROM df")

# --- Index Route (Main Upload & Mapping) ---
@app.route("/", methods=["GET", "POST"])
def index():
    mapping_file = os.path.join("part1_sku_mapping", "WMS-04-02.xlsx")
    mapping_loader = MappingLoader(mapping_file)
    processor = SalesProcessor(mapping_loader)

    output_path = None
    error_path = None
    success_message = ""

    if request.method == "POST":
        files = request.files.getlist("sales_files")

        if files:
            uploaded_paths = []
            for file in files:
                filename = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(path)
                uploaded_paths.append(path)

            try:
                processor.process_sales_files(uploaded_paths)
                output_path = os.path.join(OUTPUT_FOLDER, "mapped_output.csv")
                error_path = os.path.join(OUTPUT_FOLDER, "error_log.csv")

                processor.save_output(output_path)
                processor.save_errors(error_path)

                update_airtable(processor.sales_df)
                update_duckdb(processor.sales_df)

                success_message = "✅ Sales files processed and uploaded successfully!"

            except Exception as e:
                success_message = f"❌ Error processing files: {str(e)}"

    return render_template("index.html",
                           success_message=success_message,
                           output_file=output_path,
                           error_file=error_path)

# --- Download Files ---
@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

# --- AI Dashboard ---
@app.route("/ai-dashboard", methods=["GET", "POST"])
def ai_dashboard():
    result_table = None
    user_question = ""
    sql_query = ""
    error = ""
    chart_path = None

    if request.method == "POST":
        user_question = request.form.get("question")
        if user_question:
            try:
                prompt = f"Translate this question to SQL: {user_question}. Table name is 'sales'."
                inputs = tokenizer(prompt, return_tensors="pt")
                output = model.generate(**inputs, max_length=256)
                sql_query = tokenizer.decode(output[0], skip_special_tokens=True)

                df = con.execute(sql_query).df()
                result_table = df.to_html(classes="table table-bordered table-striped", index=False)

                if "top" in user_question.lower() or "chart" in user_question.lower():
                    chart_id = str(uuid.uuid4())
                    chart_path = os.path.join("static", "outputs", f"{chart_id}.png")
                    df.plot(kind="bar", x=df.columns[0], y=df.columns[1], figsize=(10, 5))
                    plt.tight_layout()
                    plt.savefig(chart_path)
                    plt.close()

            except Exception as e:
                error = f"Error: {str(e)}"

    return render_template("ai_dashboard.html",
                           result_table=result_table,
                           question=user_question,
                           sql=sql_query,
                           chart=chart_path,
                           error=error)

# --- Run the App ---
if __name__ == "__main__":
    app.run(debug=True)
