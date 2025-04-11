// Database functionality for Part 3
// Initialize the editable table for the database view
function initEditableTable() {
  if (!dashboardData || dashboardData.length === 0) {
    console.error("No data for editable table");
    return;
  }

  const data = dashboardData;
  const header = document.getElementById("editable-header");
  const body = document.getElementById("editable-body");

  if (!header || !body) {
    console.error("Editable table elements not found");
    return;
  }

  // Clear existing content
  header.innerHTML = "";
  body.innerHTML = "";

  // Get column names from the first record
  const columns = Object.keys(data[0]);

  // Create header row with editable cells
  columns.forEach((column) => {
    const th = document.createElement("th");
    th.textContent = column;
    header.appendChild(th);
  });

  // Create data rows with editable cells
  data.forEach((record, rowIndex) => {
    const tr = document.createElement("tr");

    columns.forEach((column) => {
      const td = document.createElement("td");
      td.setAttribute("contenteditable", "true");
      td.textContent = record[column] || "";
      td.dataset.originalValue = record[column] || "";
      td.dataset.row = rowIndex;
      td.dataset.column = column;
      td.classList.add("editable-cell");

      // Add MSKU click handler for related data
      if (column === "msku") {
        td.addEventListener("click", function () {
          showRelatedProduct(this.textContent);
        });
      }

      // Add change tracking
      td.addEventListener("blur", function () {
        if (this.textContent !== this.dataset.originalValue) {
          this.classList.add("bg-warning-subtle");

          // Update the data
          const rowIndex = parseInt(this.dataset.row);
          const column = this.dataset.column;
          dashboardData[rowIndex][column] = this.textContent;
        } else {
          this.classList.remove("bg-warning-subtle");
        }
      });

      tr.appendChild(td);
    });

    body.appendChild(tr);
  });

  // Set up event handlers
  setupDatabaseControls();
}

// Initialize the products table
function initProductsTable() {
  if (!productsData || productsData.length === 0) {
    console.error("No products data available");
    return;
  }

  const productsTableBody = document.getElementById("products-table-body");
  if (!productsTableBody) {
    console.error("Products table body element not found");
    return;
  }

  // Clear existing content
  productsTableBody.innerHTML = "";

  // Create data rows
  productsData.forEach((product) => {
    const tr = document.createElement("tr");

    // Add product data cells
    const cells = [
      product.msku,
      product.product_name,
      product.sku,
      product.category || "N/A",
      product.total_quantity,
      product.total_sales,
      product.total_returns,
      ((product.total_sales / product.total_quantity) * 100).toFixed(2) + "%",
    ];

    cells.forEach((cellData) => {
      const td = document.createElement("td");
      td.textContent = cellData;
      tr.appendChild(td);
    });

    productsTableBody.appendChild(tr);
  });
}

// Show related product details
function showRelatedProduct(msku) {
  if (!msku) return;
  
  const product = productsData.find(p => p.msku === msku);
  if (!product) {
    console.log("Product not found:", msku);
    return;
  }
  
  // Show product details in a modal
  const modalHtml = `
    <div class="modal fade" id="product-modal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Product Details: ${msku}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <table class="table">
              <tr><th>Product Name</th><td>${product.product_name}</td></tr>
              <tr><th>MSKU</th><td>${product.msku}</td></tr>
              <tr><th>SKU</th><td>${product.sku}</td></tr>
              <tr><th>Category</th><td>${product.category || 'N/A'}</td></tr>
              <tr><th>Total Quantity</th><td>${product.total_quantity}</td></tr>
              <tr><th>Total Sales</th><td>${product.total_sales}</td></tr>
              <tr><th>Total Returns</th><td>${product.total_returns}</td></tr>
              <tr><th>Success Rate</th><td>${((product.total_sales / product.total_quantity) * 100).toFixed(2)}%</td></tr>
            </table>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Remove existing modal if any
  const existingModal = document.getElementById('product-modal');
  if (existingModal) {
    existingModal.remove();
  }
  
  // Add modal to body
  document.body.insertAdjacentHTML('beforeend', modalHtml);
  
  // Show the modal
  const modal = new bootstrap.Modal(document.getElementById('product-modal'));
  modal.show();
}

// Setup database controls
function setupDatabaseControls() {
  // Add event listeners for database controls
  const saveChangesBtn = document.getElementById("save-changes-btn");
  if (saveChangesBtn) {
    saveChangesBtn.addEventListener("click", function() {
      alert("Changes saved to memory. In a production environment, this would save to the database.");
    });
  }
  
  const addRowBtn = document.getElementById("add-row-btn");
  if (addRowBtn) {
    addRowBtn.addEventListener("click", function() {
      // Create a new empty record
      const newRecord = {};
      Object.keys(dashboardData[0]).forEach(key => {
        newRecord[key] = "";
      });
      
      // Add to data
      dashboardData.push(newRecord);
      
      // Refresh table
      initEditableTable();
    });
  }
}

// Export functions to global scope
window.initEditableTable = initEditableTable;
window.initProductsTable = initProductsTable;
window.showRelatedProduct = showRelatedProduct;
window.setupDatabaseControls = setupDatabaseControls;