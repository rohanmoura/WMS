import os
import uuid
import pandas as pd
import json
import threading
import traceback
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import duckdb
from dotenv import load_dotenv
import re

# Load environment variables first
load_dotenv()

# Configure OpenRouter API for Google Gemini
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY not found in environment variables")

# Fix the import paths by adding the parent directory to sys.path
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"Adding parent directory to sys.path: {parent_dir}")
sys.path.append(parent_dir)

try:
    from part1_sku_mapping.sku_mapper import MappingLoader, SalesProcessor
    print("Successfully imported MappingLoader and SalesProcessor")
except ImportError as e:
    print(f"Error importing sku_mapper: {str(e)}")
    # Try alternative import path
    try:
        sys.path.append(os.path.join(parent_dir, 'part1_sku_mapping'))
        from sku_mapper import MappingLoader, SalesProcessor
        print("Successfully imported MappingLoader and SalesProcessor using alternative path")
    except ImportError as e2:
        print(f"Error with alternative import: {str(e2)}")
        # List files in the directory to debug
        print(f"Files in part1_sku_mapping: {os.listdir(os.path.join(parent_dir, 'part1_sku_mapping'))}")
        raise

try:
    from part3_webapp.airtable import update_airtable
    print("Successfully imported update_airtable")
except ImportError as e:
    print(f"Error importing airtable: {str(e)}")
    # Try alternative import path
    try:
        from airtable import update_airtable
        print("Successfully imported update_airtable using alternative path")
    except ImportError as e2:
        print(f"Error with alternative import: {str(e2)}")
        raise

# Create a DuckDB connection
duckdb_conn = duckdb.connect(":memory:")

# Try to import OpenAI with proper error handling
try:
    from openai import OpenAI
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
except ImportError:
    # For older versions of the openai package
    import openai
    openai.api_base = "https://openrouter.ai/api/v1"
    openai.api_key = OPENROUTER_API_KEY
    # Create a compatible client function
    class OpenAICompatClient:
        def __init__(self):
            pass
            
        def chat_completions_create(self, **kwargs):
            return openai.ChatCompletion.create(**kwargs)
            
    client = OpenAICompatClient()

# --- Flask Setup ---
app = Flask(__name__, static_folder='../static')
app.secret_key = "wms_secret_key_2024"
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
# Check this line in your app.py
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "outputs")
print(f"OUTPUT_FOLDER path: {OUTPUT_FOLDER}")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def background_airtable_update(df, output_file):
    try:
        # Just pass the DataFrame, ignore the output_file parameter
        update_airtable(df)
    except Exception as e:
        print(f"Error updating Airtable: {str(e)}")

# --- Index Route (Main Upload & Mapping) ---
@app.route("/", methods=["GET", "POST"])
def index():
    success_message = ""
    logs = ""
    result_file = None
    log_file_name = None
    
    if request.method == "POST":
        try:
            print("POST request received - starting file processing")
            # Get uploaded files
            mapping_file = request.files.get("mapping_file")
            sales_files = request.files.getlist("sales_files")
            
            print(f"Mapping file: {mapping_file.filename if mapping_file else 'None'}")
            print(f"Sales files count: {len(sales_files) if sales_files else 0}")
            
            if not mapping_file or not sales_files:
                raise Exception("Please upload both mapping file and sales files.")
            
            # Save mapping file
            mapping_filename = secure_filename(mapping_file.filename)
            mapping_path = os.path.join(UPLOAD_FOLDER, mapping_filename)
            mapping_file.save(mapping_path)
            print(f"Mapping file saved to: {mapping_path}")
            
            # Save and process sales files
            sales_df_list = []
            for file in sales_files:
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                print(f"Sales file saved to: {file_path}")
                
                # Determine file type and read accordingly
                if filename.endswith('.csv'):
                    print(f"Reading CSV file: {filename}")
                    df = pd.read_csv(file_path, encoding='utf-8')
                elif filename.endswith(('.xlsx', '.xls')):
                    print(f"Reading Excel file: {filename}")
                    df = pd.read_excel(file_path)
                else:
                    print(f"Skipping unsupported file: {filename}")
                    continue
                
                if not df.empty:
                    print(f"DataFrame loaded with {len(df)} rows and {len(df.columns)} columns")
                    sales_df_list.append(df)
                else:
                    print(f"Warning: Empty DataFrame from {filename}")
            
            if not sales_df_list:
                raise Exception("No valid sales files uploaded.")

            print("Combining DataFrames...")
            combined_df = pd.concat(sales_df_list, ignore_index=True)
            combined_path = os.path.join(UPLOAD_FOLDER, f"combined_{uuid.uuid4().hex}.xlsx")
            combined_df.to_excel(combined_path, index=False)
            print(f"Combined file saved to: {combined_path}")
            
            # Run mapping
            unique_id = uuid.uuid4().hex
            output_filename = f"output_{unique_id}.xlsx"
            log_filename = f"log_{unique_id}.txt"
            json_filename = f"output_{unique_id}.json"
            
            print(f"Starting mapping process with output: {output_filename}")
            # Use the absolute OUTPUT_FOLDER path
            try:
                mapping_loader = MappingLoader(mapping_path)
                print("MappingLoader initialized successfully")
            except Exception as e:
                print(f"Error initializing MappingLoader: {str(e)}")
                traceback.print_exc()
                raise
                
            try:
                processor = SalesProcessor(mapping_loader, combined_path, output_dir=OUTPUT_FOLDER)
                print("SalesProcessor initialized successfully")
            except Exception as e:
                print(f"Error initializing SalesProcessor: {str(e)}")
                traceback.print_exc()
                raise
            
            try:
                mapped_file, log_file = processor.process(
                    output_filename=output_filename,
                    log_filename=log_filename
                )
                print(f"Mapping completed. Output file: {mapped_file}, Log file: {log_file}")
            except Exception as e:
                print(f"Error during processing: {str(e)}")
                traceback.print_exc()
                raise
            
            # Fix NaNs before data export
            processor.sales_df.fillna('', inplace=True)
            
            # Prepare data for export - add additional columns if needed
            export_df = processor.sales_df.copy()
            
            # Add timestamp column
            export_df['processed_date'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Save JSON file for dashboard immediately
            json_path = os.path.join(OUTPUT_FOLDER, json_filename)
            print(f"Saving JSON file to: {json_path}")
            
            # Convert DataFrame to JSON with proper formatting
            # Use records orientation for better compatibility with the dashboard
            json_data = export_df.to_dict(orient='records')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print("JSON file saved successfully")
            
            # Start data export in background thread
            print("Starting Airtable update in background")
            threading.Thread(
                target=background_airtable_update,
                args=(export_df, mapped_file),
                daemon=True
            ).start()
            
            # Set success message
            flash("✅ Mapping successful! Redirecting to dashboard...", "success")
            
            # Redirect to dashboard with the specific JSON file
            print(f"Redirecting to dashboard with data_file={json_filename}")
            # Update the redirect line in the index route
            return redirect(url_for('dashboard', 
            file=json_filename, 
            result_file=output_filename, 
            log_file=log_filename))
            
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Error processing files: {error_details}")
            success_message = f"❌ Error: {str(e)}"

    return render_template("index.html",
                           success_message=success_message,
                           logs=logs,
                           result_file=result_file,
                           log_file=log_file_name)

@app.route('/dashboard')
def dashboard():
    # Get the data file from the request arguments or use a default
    data_file = request.args.get('file', None)
    result_file = request.args.get('result_file', None)
    log_file = request.args.get('log_file', None)
    
    # Check if logs exist for this file
    has_logs = False
    if log_file:
        log_path = os.path.join(OUTPUT_FOLDER, log_file)
        has_logs = os.path.exists(log_path)
    
    return render_template('dashboard.html', 
                          local_data=data_file, 
                          result_file=result_file,
                          log_file=log_file,
                          has_logs=has_logs)

@app.route('/api/data')
def api_data():
    """API endpoint to get data from a JSON file"""
    file = request.args.get('file')
    print(f"API data request for file: {file}")
    
    if not file:
        # If no specific file is requested, get the latest JSON file
        json_files = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.json')]
        if json_files:
            # Sort by creation time, newest first
            json_files.sort(key=lambda x: os.path.getctime(os.path.join(OUTPUT_FOLDER, x)), reverse=True)
            file = json_files[0]
            print(f"No file specified, using latest: {file}")
        else:
            print("No JSON files found in output directory")
            return jsonify([])
    
    # Construct the full path to the file
    file_path = os.path.join(OUTPUT_FOLDER, file)
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({"error": f"File not found: {file}"}), 404
        
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"JSON data loaded successfully: {len(data)} records")
        # Return the data
        return jsonify(data)
    except Exception as e:
        print(f"Error loading JSON file: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Remove or comment out the duplicate get_data function
# @app.route("/api/data")
# def get_data():
#    # API endpoint to get the latest data for the dashboard
#    json_file = request.args.get('file')
#    print(f"API data request for file: {json_file}")
#    
#    if json_file and os.path.exists(os.path.join(OUTPUT_FOLDER, json_file)):
#        try:
#            print(f"Loading JSON file: {os.path.join(OUTPUT_FOLDER, json_file)}")
#            with open(os.path.join(OUTPUT_FOLDER, json_file), 'r', encoding='utf-8') as f:
#                data = json.load(f)
#            print(f"JSON data loaded successfully: {len(data)} records")
#            return jsonify(data)
#        except Exception as e:
#            print(f"Error loading JSON file: {str(e)}")
#            traceback.print_exc()
#            return jsonify({"error": str(e)})
#    
#    # If no specific file is requested, get the latest JSON file
#    json_files = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.json')]
#    if json_files:
#        # Sort by creation time, newest first
#        json_files.sort(key=lambda x: os.path.getctime(os.path.join(OUTPUT_FOLDER, x)), reverse=True)
#        latest_file = json_files[0]
#        try:
#            print(f"Loading latest JSON file: {os.path.join(OUTPUT_FOLDER, latest_file)}")
#            with open(os.path.join(OUTPUT_FOLDER, latest_file), 'r', encoding='utf-8') as f:
#                data = json.load(f)
#            print(f"Latest JSON data loaded successfully: {len(data)} records")
#            return jsonify(data)
#        except Exception as e:
#            print(f"Error loading latest JSON file: {str(e)}")
#            traceback.print_exc()
#            return jsonify({"error": str(e)})
#    
#    print("No JSON files found in output directory")
#    return jsonify([])

@app.route('/download/<file_type>/<filename>')
def download_file(file_type, filename):
    """Download result or log files"""
    if not filename:
        flash("No file specified for download", "error")
        return redirect(url_for('dashboard'))
    
    try:
        return send_from_directory(
            OUTPUT_FOLDER, 
            filename, 
            as_attachment=True, 
            download_name=filename
        )
    except Exception as e:
        flash(f"Error downloading file: {str(e)}", "error")
        return redirect(url_for('dashboard'))

# Add this global variable to track the current data state
current_data_hash = None

@app.route('/api/ai-query', methods=['POST'])
def ai_query():
    """API endpoint to handle AI queries about the data"""
    global current_data_hash
    
    try:
        data = request.json
        query = data.get('query')
        data_file = data.get('dataFile')
        dashboard_data = data.get('dashboardData')  # Get the actual data from the frontend
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
            
        print(f"AI Query: {query}")
        
        # Use the dashboard data directly if provided
        if dashboard_data and len(dashboard_data) > 0:
            try:
                data_records = dashboard_data
                print(f"Using dashboard data directly: {len(data_records)} records")
                
                # Convert data to pandas DataFrame first
                df = pd.DataFrame(data_records)
                
                # Create a hash of the data to check if it's changed
                data_hash = hash(str(df.shape) + str(df.columns.tolist()))
                
                # Only recreate the table if the data has changed
                if data_hash != current_data_hash:
                    print("Data changed, recreating DuckDB table")
                    # Fix: Register the DataFrame as a view instead of passing it directly
                    duckdb_conn.execute("DROP VIEW IF EXISTS df_view")
                    duckdb_conn.register("df_view", df)
                    duckdb_conn.execute("DROP TABLE IF EXISTS data_table")
                    duckdb_conn.execute("CREATE TABLE data_table AS SELECT * FROM df_view")
                    current_data_hash = data_hash
                else:
                    print("Using existing DuckDB table (data unchanged)")
                
                # Get column names
                columns = df.columns.tolist()
                
                # Generate SQL for the query
                sql_query = generate_sql_for_query(query, columns, df)
                print(f"Generated SQL: {sql_query}")
                
                # Execute the query
                result_df = duckdb_conn.execute(sql_query).fetchdf()
                
                # Convert to HTML table
                html_table = result_df.to_html(classes='table', index=False)
                
                # Determine if we should create a chart
                chart_data = None
                if "top" in query.lower() or "trend" in query.lower() or "distribution" in query.lower():
                    chart_data = create_chart_data(result_df, query)
                
                return jsonify({
                    "title": f"Results for: {query}",
                    "html": html_table,
                    "sql": sql_query,
                    "chart_data": chart_data,
                    "raw_data": result_df.to_dict(orient='records')
                })
                
            except Exception as e:
                print(f"Error processing dashboard data: {str(e)}")
                traceback.print_exc()
        
        # If we couldn't use dashboard data, try loading from file
        try:
            json_path = os.path.join(OUTPUT_FOLDER, data_file)
            if not os.path.exists(json_path):
                # Try to find the file by name pattern
                json_files = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.json')]
                if json_files:
                    json_path = os.path.join(OUTPUT_FOLDER, json_files[0])
                    
            with open(json_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                
            print(f"Loaded {len(file_data)} records from file for AI query")
            
            # Convert to DataFrame
            df = pd.DataFrame(file_data)
            
            # Create a hash of the data to check if it's changed
            data_hash = hash(str(df.shape) + str(df.columns.tolist()))
            
            # Only recreate the table if the data has changed
            if data_hash != current_data_hash:
                print("Data changed, recreating DuckDB table")
                # Fix: Register the DataFrame as a view instead of passing it directly
                duckdb_conn.execute("DROP VIEW IF EXISTS df_view")
                duckdb_conn.register("df_view", df)
                duckdb_conn.execute("DROP TABLE IF EXISTS data_table")
                duckdb_conn.execute("CREATE TABLE data_table AS SELECT * FROM df_view")
                current_data_hash = data_hash
            else:
                print("Using existing DuckDB table (data unchanged)")
            
            # Get column names
            columns = df.columns.tolist()
            
            # Generate SQL for the query
            sql_query = generate_sql_for_query(query, columns, df)
            print(f"Generated SQL: {sql_query}")
            
            # Execute the query
            result_df = duckdb_conn.execute(sql_query).fetchdf()
            
            # Convert to HTML table
            html_table = result_df.to_html(classes='table', index=False)
            
            # Determine if we should create a chart
            chart_data = None
            if "top" in query.lower() or "trend" in query.lower() or "distribution" in query.lower():
                chart_data = create_chart_data(result_df, query)
            
            return jsonify({
                "title": f"Results for: {query}",
                "html": html_table,
                "sql": sql_query,
                "chart_data": chart_data,
                "raw_data": result_df.to_dict(orient='records')
            })
            
        except Exception as e:
            print(f"Error processing file data: {str(e)}")
            traceback.print_exc()
            
            # Try a simple fallback query
            try:
                # Create a simple example query that should work
                simple_query = "SELECT * FROM data_table LIMIT 10"
                result_df = duckdb_conn.execute(simple_query).fetchdf()
                html_table = result_df.to_html(classes='table', index=False)
                
                return jsonify({
                    "title": f"Sample data (could not process original query)",
                    "html": html_table,
                    "sql": simple_query
                })
            except Exception as e2:
                # If even that fails, return a more helpful error
                print(f"Fallback query failed: {str(e2)}")
                return jsonify({
                    "error": f"I couldn't process your query. Please try a simpler question about your data."
                })
    
    except Exception as e:
        print(f"Error processing AI query: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Error processing query: {str(e)}"}), 500

def create_chart_data(df, query):
    """Create Chart.js compatible data structure from DataFrame"""
    try:
        # Limit to 10 rows for chart
        df = df.head(10)
        
        # Determine chart type based on query and data
        chart_type = "bar"  # Default
        if "trend" in query.lower() or "over time" in query.lower() or "by date" in query.lower():
            chart_type = "line"
        elif "distribution" in query.lower() or "percentage" in query.lower():
            chart_type = "pie"
            
        # Get column names
        columns = df.columns.tolist()
        
        # For pie charts, we need exactly 2 columns
        if chart_type == "pie" and len(columns) >= 2:
            labels = df[columns[0]].tolist()
            data = df[columns[1]].tolist()
            
            return {
                "type": "pie",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": columns[1],
                        "data": data,
                        "backgroundColor": [
                            "rgba(255, 99, 132, 0.6)",
                            "rgba(54, 162, 235, 0.6)",
                            "rgba(255, 206, 86, 0.6)",
                            "rgba(75, 192, 192, 0.6)",
                            "rgba(153, 102, 255, 0.6)",
                            "rgba(255, 159, 64, 0.6)",
                            "rgba(255, 99, 132, 0.6)",
                            "rgba(54, 162, 235, 0.6)",
                            "rgba(255, 206, 86, 0.6)",
                            "rgba(75, 192, 192, 0.6)"
                        ]
                    }]
                }
            }
        
        # For bar and line charts
        if len(columns) >= 2:
            labels = df[columns[0]].tolist()
            datasets = []
            
            # Add each numeric column as a dataset
            for i in range(1, len(columns)):
                if df[columns[i]].dtype in ['int64', 'float64']:
                    datasets.append({
                        "label": columns[i],
                        "data": df[columns[i]].tolist(),
                        "backgroundColor": f"rgba({50 + i * 50}, {100 + i * 30}, 192, 0.6)",
                        "borderColor": f"rgba({50 + i * 50}, {100 + i * 30}, 192, 1)",
                        "borderWidth": 1
                    })
            
            return {
                "type": chart_type,
                "data": {
                    "labels": labels,
                    "datasets": datasets
                },
                "options": {
                    "scales": {
                        "y": {
                            "beginAtZero": True
                        }
                    }
                }
            }
            
        return None
    except Exception as e:
        print(f"Error creating chart data: {str(e)}")
        return None

def generate_sql_for_query(query, columns, df=None):
    """Generate SQL based on natural language query using Gemini AI"""
    query = query.lower()
    
    # Try to use OpenRouter API with Gemini Pro if API key is available
    if OPENROUTER_API_KEY and df is not None:
        try:
            import requests
            
            # Get column data types and sample data for context
            column_types = df.dtypes.astype(str).to_dict()
            sample_data = df.head(5).to_dict(orient="records")
            
            # Build the prompt for Gemini with EXPLICIT instructions about column names
            system_message = """
            You are an expert data assistant helping to write SQL queries for a DuckDB in-memory database. 
            The table is called data_table and it already contains the uploaded data. 
            
            The table has the following columns: {}
            
            Some column names may contain spaces or special characters, so always use the exact column names without changing the format — do not convert them to snake_case or rename them. 
            If a column contains spaces, wrap it in double quotes (e.g., "order state").
            
            Write clean and syntactically correct SQL queries that run successfully in DuckDB. 
            Do not include any explanation, markdown formatting like triple backticks, or additional commentary — just return the final SQL query as plain text.
            
            Here are some sample rows from the table to help you understand the data:
            {}
            """.format(
                ", ".join([f'"{col}"' for col in columns]),
                json.dumps(sample_data, indent=2)
            )
            
            # Prepare the API request
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "google/gemini-pro",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Now, write a SQL query that answers the following question: {query}"}
                ],
                "temperature": 0.1,  # Lower temperature for more deterministic results
                "max_tokens": 500
            }
            
            # Make the API request
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                sql_query = result["choices"][0]["message"]["content"].strip()
                
                # Clean up any potential markdown formatting that might have been included
                sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
                
                print(f"AI-generated SQL query: {sql_query}")
                return sql_query
            else:
                print(f"Error from OpenRouter API: {response.status_code}, {response.text}")
        
        except Exception as e:
            print(f"Error generating SQL with AI: {str(e)}")
            traceback.print_exc()
    
    # Fallback to rule-based SQL generation if API call fails or API key not available
    print("Using fallback rule-based SQL generation")
    
    # Normalize column names
    normalized_columns = [col.lower() for col in columns]
    
    # Handle top N products query
    if "top" in query and any(word in query for word in ["product", "msku", "sku"]):
        # Extract number
        match = re.search(r'top\s+(\d+)', query)
        limit = 5  # Default
        if match:
            limit = int(match.group(1))
        
        # Find product column
        product_col = next((col for col in columns if any(name in col.lower() for name in 
                           ["product", "title", "name", "msku", "sku"])), columns[0])
        
        # Find quantity/sales column
        quantity_col = next((col for col in columns if any(name in col.lower() for name in 
                            ["quantity", "sales", "units", "count"])), None)
        
        if quantity_col:
            return f"""
            SELECT "{product_col}" as Product, SUM("{quantity_col}") as Total
            FROM data_table
            GROUP BY "{product_col}"
            ORDER BY Total DESC
            LIMIT {limit}
            """
        else:
            return f"""
            SELECT "{product_col}" as Product, COUNT(*) as Count
            FROM data_table
            GROUP BY "{product_col}"
            ORDER BY Count DESC
            LIMIT {limit}
            """
    
    # Handle return rate query
    elif "return" in query and ("rate" in query or "percentage" in query):
        # Find status column
        status_col = next((col for col in columns if any(name in col.lower() for name in 
                          ["status", "state", "reason"])), None)
        
        if status_col:
            return f"""
            SELECT 
                'Returns' as Type,
                COUNT(*) as Count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM data_table), 2) as Percentage
            FROM data_table
            WHERE LOWER("{status_col}") LIKE '%return%' OR LOWER("{status_col}") LIKE '%rto%'
            UNION ALL
            SELECT 
                'Regular Orders' as Type,
                COUNT(*) as Count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM data_table), 2) as Percentage
            FROM data_table
            WHERE LOWER("{status_col}") NOT LIKE '%return%' AND LOWER("{status_col}") NOT LIKE '%rto%'
            """
        else:
            return """
            SELECT 'No status column found' as Message
            """
    
    # Handle sales by region/state
    elif "sales" in query and any(word in query for word in ["region", "state", "location"]):
        # Find state/region column
        region_col = next((col for col in columns if any(name in col.lower() for name in 
                          ["state", "region", "location"])), None)
        
        # Find quantity/sales column
        quantity_col = next((col for col in columns if any(name in col.lower() for name in 
                            ["quantity", "sales", "units", "count"])), None)
        
        if region_col and quantity_col:
            return f"""
            SELECT "{region_col}" as Region, SUM("{quantity_col}") as Sales
            FROM data_table
            GROUP BY "{region_col}"
            ORDER BY Sales DESC
            """
        elif region_col:
            return f"""
            SELECT "{region_col}" as Region, COUNT(*) as Orders
            FROM data_table
            GROUP BY "{region_col}"
            ORDER BY Orders DESC
            """
        else:
            return """
            SELECT 'No region/state column found' as Message
            """
    
    # Default: return basic statistics
    else:
        # Get numeric columns
        numeric_cols = [col for col in columns if "date" not in col.lower()]
        if numeric_cols:
            return f"""
            SELECT 
                COUNT(*) as "Total Records",
                (SELECT COUNT(*) FROM data_table WHERE "{numeric_cols[0]}" IS NOT NULL) as "Valid Records"
            FROM data_table
            """
        else:
            return """
            SELECT COUNT(*) as "Total Records" FROM data_table
            """

# Helper functions remain the same
def infer_column_type(series):
    if pd.api.types.is_numeric_dtype(series):
        if pd.api.types.is_integer_dtype(series):
            return "INTEGER"
        else:
            return "FLOAT"
    elif pd.api.types.is_datetime64_any_dtype(series):
        return "DATE"
    else:
        return "TEXT"

def determine_chart_type(query, df):
    query = query.lower()
    
    # Check for time series indicators
    time_indicators = ["trend", "over time", "by month", "by year", "by date"]
    if any(indicator in query for indicator in time_indicators):
        return "line"
    
    # Check for distribution indicators
    distribution_indicators = ["distribution", "breakdown", "percentage", "ratio", "share"]
    if any(indicator in query for indicator in distribution_indicators):
        return "pie"
    
    # Default to bar chart for comparisons
    comparison_indicators = ["compare", "top", "bottom", "most", "least", "highest", "lowest"]
    if any(indicator in query for indicator in comparison_indicators):
        return "bar"
    
    # If we have numeric data in second column, default to bar
    if pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
        return "bar"
    
    return "bar"  # Default

# Fallback SQL generator for testing without API key
def generate_fallback_sql(query, columns):
    query = query.lower()
    
    if "top" in query and any(col for col in columns if "msku" in col.lower()):
        msku_col = next(col for col in columns if "msku" in col.lower())
        if any(col for col in columns if "quantity" in col.lower() or "units" in col.lower()):
            qty_col = next(col for col in columns if "quantity" in col.lower() or "units" in col.lower())
            return f"SELECT {msku_col}, SUM({qty_col}) as total_quantity FROM sales GROUP BY {msku_col} ORDER BY total_quantity DESC LIMIT 5"
    
    # Simple fallback
    return f"SELECT * FROM sales LIMIT 10"

# --- Run the App ---
if __name__ == "__main__":
    app.run(debug=True)


