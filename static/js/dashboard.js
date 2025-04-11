// At the beginning of your dashboard.js file
// Global variables - ensure these are at the top of the file
let dashboardData = [];
let productsData = [];
let currentDataFile = null;

// Initialize the dashboard
// In the initDashboard function, let's improve the debug info hiding
function initDashboard(localDataFile, hasLogs) {
  console.log("Initializing dashboard with data file:", localDataFile);

  // Store the data file name globally
  currentDataFile = localDataFile;

  // Load data
  if (localDataFile) {
    loadData(localDataFile);
  } else {
    console.error("No data file specified");
    document.getElementById("table-body").innerHTML =
      "<tr><td colspan='100%' class='text-center'>No data available. Please process a file first.</td></tr>";
  }

  // Hide the debug info line completely
  const debugInfoElement = document.querySelector(".alert-info");
  if (debugInfoElement) {
    debugInfoElement.style.display = "none";
  }
}

// Load data from the server
function loadData(dataFile) {
  console.log("Loading data file:", dataFile);

  // Show loading indicator
  document.getElementById("table-body").innerHTML =
    "<tr><td colspan='100%' class='text-center'><div class='spinner-border text-primary' role='status'><span class='visually-hidden'>Loading...</span></div></td></tr>";

  fetch(`/api/data?file=${dataFile}`)
    .then((response) => {
      console.log("API response status:", response.status);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      console.log("Data loaded successfully, records:", data.length);
      if (data.length > 0) {
        console.log("Sample record:", data[0]);
        dashboardData = data;

        // Create products data from sales data
        createProductsData();

        // Initialize tables with data
        populateTable(data);

        // Create charts if we have data
        createCharts(data);

        // Update the mapped data count
        const mappedDataCount = document.getElementById("mapped-data-count");
        if (mappedDataCount) {
          mappedDataCount.textContent = data.length;
        }
      } else {
        document.getElementById("table-body").innerHTML =
          "<tr><td colspan='100%' class='text-center'>No data available</td></tr>";
      }
    })
    .catch((error) => {
      console.error("Error loading data:", error);
      document.getElementById(
        "table-body"
      ).innerHTML = `<tr><td colspan='100%' class='text-center text-danger'>Error loading data: ${error.message}</td></tr>`;
    });
}

// Create products data from sales data
function createProductsData() {
  const productMap = new Map();

  dashboardData.forEach((row) => {
    const msku = row.msku || "";
    if (msku && !msku.includes("[MISSING") && !msku.includes("[INVALID")) {
      if (!productMap.has(msku)) {
        // Create a new product entry
        productMap.set(msku, {
          msku: msku,
          product_name: row.product_name || row.title || row.item_name || "",
          sku: row.sku || "",
          category: row.category || "",
          total_sales: 0,
          total_returns: 0,
          total_quantity: 0,
        });
      }

      // Update product statistics
      const product = productMap.get(msku);
      const status = (
        row.status ||
        row.Status ||
        row["reason for credit entry"] ||
        row.order_state ||
        ""
      ).toLowerCase();
      const quantity = parseInt(row.quantity || row.Quantity || "1") || 1;

      product.total_quantity += quantity;

      if (status.includes("return") || status.includes("rto")) {
        product.total_returns += quantity;
      } else if (status.includes("delivered") || status.includes("shipped")) {
        product.total_sales += quantity;
      }
    }
  });

  productsData = Array.from(productMap.values());
  console.log("Created products data:", productsData.length, "products");
}

// Populate the data table
function populateTable(data) {
  if (!data || data.length === 0) {
    console.error("No data to populate table");
    return;
  }

  const tableHeader = document.getElementById("table-header");
  const tableBody = document.getElementById("table-body");

  // Clear existing content
  tableHeader.innerHTML = "";
  tableBody.innerHTML = "";

  // Get column names from the first record
  const columns = Object.keys(data[0]);
  console.log("Table columns:", columns);

  // Create header row
  const headerRow = document.createElement("tr");
  columns.forEach((column) => {
    const th = document.createElement("th");
    th.textContent = column;
    headerRow.appendChild(th);
  });
  tableHeader.appendChild(headerRow);

  // Create data rows
  data.forEach((record, index) => {
    const tr = document.createElement("tr");

    columns.forEach((column) => {
      const td = document.createElement("td");
      td.textContent = record[column] !== undefined ? record[column] : "";
      tr.appendChild(td);
    });

    tableBody.appendChild(tr);

    // Log first few rows for debugging
    if (index < 3) {
      console.log(`Row ${index + 1}:`, record);
    }
  });

  console.log("Table populated with", data.length, "rows");
}

// Load all modules
document.addEventListener("DOMContentLoaded", function() {
  // Load Part 3 module (visualization)
  const vizScript = document.createElement('script');
  vizScript.src = '/static/js/dashboard-viz.js';
  document.head.appendChild(vizScript);
  
  // Load Part 4 module (AI assistant)
  const aiScript = document.createElement('script');
  aiScript.src = '/static/js/dashboard-ai.js';
  document.head.appendChild(aiScript);
  
  // Load database module
  const dbScript = document.createElement('script');
  dbScript.src = '/static/js/dashboard-db.js';
  document.head.appendChild(dbScript);
});

// Add this at the end of your dashboard.js file
// Export global variables and functions
window.dashboardData = dashboardData;
window.productsData = productsData;
window.currentDataFile = currentDataFile;
window.createCharts = createCharts;
window.populateTable = populateTable;
window.initDashboard = initDashboard;
window.loadData = loadData;
window.createProductsData = createProductsData;