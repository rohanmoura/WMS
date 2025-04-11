// Part 4: AI Assistant functionality - Enhanced version
// Check if required global variables exist
if (typeof dashboardData === 'undefined') {
  console.error("dashboardData is not defined. Make sure dashboard.js is loaded first.");
}

if (typeof currentDataFile === 'undefined') {
  console.error("currentDataFile is not defined. Make sure dashboard.js is loaded first.");
}

// AI Assistant functions
document.addEventListener('DOMContentLoaded', function() {
  console.log("Setting up AI Assistant button");
  
  // Set up AI Assistant button
  const aiButton = document.getElementById("ai-assistant-btn");
  if (aiButton) {
    console.log("AI Assistant button found, adding event listener");
    aiButton.addEventListener("click", function() {
      console.log("AI Assistant button clicked");
      showAIAssistant();
    });
  } else {
    console.error("AI Assistant button not found in the DOM");
  }
  
  // Set up Ask AI button inside modal
  const askAiButton = document.getElementById("ai-query-btn");
  if (askAiButton) {
    console.log("Ask AI button found, adding event listener");
    askAiButton.addEventListener("click", function() {
      console.log("Ask AI button clicked");
      askAIAssistant();
    });
  }
});

function showAIAssistant() {
  console.log("Showing AI Assistant modal");
  
  try {
    // Get the modal element
    const modalElement = document.getElementById("ai-assistant-modal");
    if (!modalElement) {
      console.error("Modal element not found");
      return;
    }
    
    // Create and show the modal
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    
    // Update the modal content to match the assignment requirements
    const modalBody = modalElement.querySelector(".modal-body");
    if (modalBody) {
      // Create example queries based on actual data columns
      let exampleQueries = [
        "Show me top 5 products by sales",
        "What's the distribution of order status?",
        "Show sales trend by date"
      ];
      
      // Add column-specific examples if we have certain columns
      if (dashboardData && dashboardData.length > 0) {
        if ('msku' in dashboardData[0]) {
          exampleQueries.push("Show me all MSKUs with their quantities");
        }
        
        if ('price' in dashboardData[0] && 'quantity' in dashboardData[0]) {
          exampleQueries.push("Add a column called profit that calculates price * quantity");
        }
        
        if ('state' in dashboardData[0] || 'city' in dashboardData[0]) {
          exampleQueries.push("Which states/cities have the most orders?");
        }
      }
      
      modalBody.innerHTML = `
        <div class="mb-3">
          <label for="ai-query-input" class="form-label">Ask a question about your data:</label>
          <div class="input-group">
            <input type="text" class="form-control" id="ai-query-input" 
              placeholder="Ask a question about your data (e.g., top 5 products by sales)"
              title="Type your question about the data. Examples: 'Show top selling products', 'Calculate average price'">
            <button class="btn btn-primary" id="ai-query-btn">Ask AI</button>
          </div>
        </div>
        <div class="mb-3">
          <p class="text-muted small">Example queries:</p>
          <div class="d-flex flex-wrap gap-2">
            ${exampleQueries.map(q => `
              <button class="btn btn-sm btn-outline-secondary example-query">${q}</button>
            `).join('')}
          </div>
        </div>
        <div class="mt-4" id="ai-result-container"></div>
      `;
      
      // Re-attach event listener to the new button
      const newAskButton = modalBody.querySelector("#ai-query-btn");
      if (newAskButton) {
        newAskButton.addEventListener("click", askAIAssistant);
      }
      
      // Add event listeners to example query buttons
      const exampleQueryButtons = modalBody.querySelectorAll(".example-query");
      exampleQueryButtons.forEach(button => {
        button.addEventListener("click", function() {
          const queryInput = document.getElementById("ai-query-input");
          if (queryInput) {
            queryInput.value = this.textContent;
            askAIAssistant();
          }
        });
      });
    }
    
    // Focus on the input field
    setTimeout(() => {
      const inputField = document.getElementById("ai-query-input");
      if (inputField) {
        inputField.focus();
        
        // Add autocomplete for column names
        if (dashboardData && dashboardData.length > 0) {
          const columns = Object.keys(dashboardData[0]);
          
          // Create datalist for autocomplete
          const datalistId = "column-suggestions";
          let datalist = document.getElementById(datalistId);
          
          if (!datalist) {
            datalist = document.createElement("datalist");
            datalist.id = datalistId;
            document.body.appendChild(datalist);
            
            // Add column names as options
            columns.forEach(column => {
              const option = document.createElement("option");
              option.value = column;
              datalist.appendChild(option);
            });
          }
          
          // Connect input to datalist
          inputField.setAttribute("list", datalistId);
        }
      }
    }, 500);
  } catch (error) {
    console.error("Error showing modal:", error);
    alert("Could not show AI Assistant. Please check the console for errors.");
  }
}

// In the askAIAssistant function, let's modify how we send data to the backend
function askAIAssistant() {
  console.log("Asking AI Assistant");
  
  const queryInput = document.getElementById("ai-query-input");
  const resultContainer = document.getElementById("ai-result-container");
  
  if (!queryInput || !resultContainer) {
    console.error("Query input or result container not found");
    return;
  }
  
  const query = queryInput.value.trim();
  if (!query) {
    resultContainer.innerHTML = `<div class="alert alert-warning">Please enter a query</div>`;
    return;
  }
  
  // Show loading indicator with animation
  resultContainer.innerHTML = `
    <div class="text-center p-4">
      <div class="spinner-grow text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
        <span class="visually-hidden">Loading...</span>
      </div>
      <div class="progress mb-3" style="height: 6px;">
        <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%"></div>
      </div>
      <p class="text-muted">Analyzing your data with Google Gemini Pro...</p>
    </div>
  `;
  
  // Check if query is about adding a calculated column
  if (query.toLowerCase().includes("add") && 
      (query.toLowerCase().includes("column") || query.toLowerCase().includes("field"))) {
    handleAddCalculatedColumn(query, resultContainer);
    return;
  }
  
  // Prepare a simplified version of the data to send
  // This helps avoid sending too much data and causing issues
  let simplifiedData = [];
  if (dashboardData && dashboardData.length > 0) {
    // Only send first 100 rows to avoid overwhelming the server
    simplifiedData = dashboardData.slice(0, 100).map(row => {
      // Create a new object with the same properties but convert any complex values to strings
      const newRow = {};
      for (const key in row) {
        if (typeof row[key] === 'object' && row[key] !== null) {
          newRow[key] = JSON.stringify(row[key]);
        } else {
          newRow[key] = row[key];
        }
      }
      return newRow;
    });
  }
  
  // Make API request to the backend with simplified data
  fetch('/api/ai-query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      dataFile: currentDataFile,
      dashboardData: simplifiedData
    }),
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    if (data.error) {
      resultContainer.innerHTML = `
        <div class="alert alert-danger">
          <h5>Error</h5>
          <p>${data.error}</p>
          <p class="mb-0">Try rephrasing your question or using different terms.</p>
        </div>`;
      return;
    }
    
    let resultHtml = `<h4 class="mb-3">${data.title}</h4>`;
    
    // If we have chart data, create a canvas for the chart
    if (data.chart_data) {
      resultHtml += `<div class="mb-4 border rounded p-3 bg-light"><canvas id="ai-result-chart"></canvas></div>`;
    }
    
    // Add the HTML table with better styling
    resultHtml += `
      <div class="table-responsive border rounded">
        ${data.html.replace('class="table', 'class="table table-striped table-hover')}
      </div>`;
    
    // Add SQL query if available (in a styled code block)
    if (data.sql) {
      resultHtml += `
        <div class="mt-3">
          <p class="text-muted mb-1">SQL Query:</p>
          <pre class="bg-dark text-light p-3 rounded"><code>${data.sql}</code></pre>
        </div>
      `;
    }
    
    resultContainer.innerHTML = resultHtml;
    
    // Create chart if we have chart data
    if (data.chart_data) {
      try {
        const ctx = document.getElementById('ai-result-chart').getContext('2d');
        new Chart(ctx, data.chart_data);
      } catch (chartError) {
        console.error("Error creating chart:", chartError);
        document.getElementById('ai-result-chart').insertAdjacentHTML('afterend', 
          `<div class="alert alert-warning">Error creating chart: ${chartError.message}</div>`);
      }
    }
  })
  // Update the catch block in the askAIAssistant function
  .catch(error => {
    console.error('Error:', error);
    
    // Try to use our fallback function for basic data analysis
    try {
      const fallbackResult = handleBasicDataAnalysis(query);
      
      resultContainer.innerHTML = `
        <div class="alert alert-warning mb-3">
          <p><strong>Note:</strong> The AI query service encountered an error, so I'm showing basic results instead.</p>
          <p class="small text-muted">Technical details: ${error.message}</p>
        </div>
        <h4 class="mb-3">${fallbackResult.title}</h4>
        <div class="border rounded p-3 bg-light">
          ${fallbackResult.html}
        </div>
      `;
    } catch (fallbackError) {
      // If even the fallback fails, show a simple error message
      resultContainer.innerHTML = `
        <div class="alert alert-danger">
          <h5>Something went wrong</h5>
          <p>I couldn't process your question. Please try one of the example queries instead.</p>
          <p class="small text-muted">Technical details: ${error.message}</p>
        </div>
        <div class="mt-3">
          <p>Try one of these simple queries instead:</p>
          <div class="d-flex flex-wrap gap-2">
            <button class="btn btn-sm btn-primary fallback-query">Show me the first 10 rows</button>
            <button class="btn btn-sm btn-primary fallback-query">Count total records</button>
            <button class="btn btn-sm btn-primary fallback-query">Show column names</button>
          </div>
        </div>`;
        
      // Add event listeners to fallback query buttons
      const fallbackButtons = resultContainer.querySelectorAll(".fallback-query");
      fallbackButtons.forEach(button => {
        button.addEventListener("click", function() {
          queryInput.value = this.textContent;
          askAIAssistant();
        });
      });
    }
  });
}

// Handle adding calculated columns
function handleAddCalculatedColumn(query, resultContainer) {
  // Parse the query to extract column name and formula
  const columnMatch = query.match(/add\s+(?:a\s+)?(?:column|field)\s+(?:called\s+)?["']?([a-zA-Z0-9_\s]+)["']?/i);
  
  if (!columnMatch) {
    resultContainer.innerHTML = `<div class="alert alert-warning">Please specify a column name. Example: "Add column called Profit"</div>`;
    return;
  }
  
  const columnName = columnMatch[1].trim();
  
  // Ask for formula if not in the query
  let formulaPrompt = `
    <div class="alert alert-info">
      <p>Adding column: <strong>${columnName}</strong></p>
      <p>Please enter a formula for this column:</p>
      <div class="input-group mb-3">
        <input type="text" class="form-control" id="column-formula-input" 
          placeholder="e.g., {price} * {quantity}, {total_sales} / {total_quantity}">
        <button class="btn btn-primary" id="apply-formula-btn">Apply</button>
      </div>
      <p class="small text-muted">Use column names in curly braces, e.g. {price} * {quantity}</p>
    </div>
  `;
  
  resultContainer.innerHTML = formulaPrompt;
  
  // Set up event listener for the apply button
  document.getElementById("apply-formula-btn").addEventListener("click", function() {
    const formula = document.getElementById("column-formula-input").value;
    if (!formula) {
      alert("Please enter a formula");
      return;
    }
    
    // Apply the formula to create a new column
    applyCalculatedColumn(columnName, formula, resultContainer);
  });
}

// Apply the calculated column to the data
function applyCalculatedColumn(columnName, formula, resultContainer) {
  try {
    // Show loading
    resultContainer.innerHTML = `
      <div class="d-flex justify-content-center p-4">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    `;
    
    // Parse the formula to extract column references
    const columnRefs = formula.match(/\{([^}]+)\}/g) || [];
    const columnNames = columnRefs.map(ref => ref.slice(1, -1));
    
    // Check if all referenced columns exist
    const missingColumns = columnNames.filter(col => 
      !dashboardData[0] || typeof dashboardData[0][col] === 'undefined'
    );
    
    if (missingColumns.length > 0) {
      resultContainer.innerHTML = `
        <div class="alert alert-danger">
          <p>The following columns do not exist: ${missingColumns.join(', ')}</p>
          <p>Please try again with valid column names.</p>
        </div>
      `;
      return;
    }
    
    // Add the calculated column to the data
    dashboardData.forEach(row => {
      let evalFormula = formula;
      columnRefs.forEach(ref => {
        const colName = ref.slice(1, -1);
        evalFormula = evalFormula.replace(ref, row[colName] || 0);
      });
      
      // Safely evaluate the formula
      try {
        row[columnName] = eval(evalFormula);
      } catch (e) {
        row[columnName] = 'Error';
      }
    });
    
    // Add column to header
    const tableHeader = document.getElementById("table-header");
    if (tableHeader) {
      const headerRow = tableHeader.querySelector("tr");
      if (headerRow) {
        const th = document.createElement("th");
        th.textContent = columnName;
        th.classList.add("bg-success-subtle");
        headerRow.appendChild(th);
      }
    }
    
    // Add calculated cells to each row
    const tableBody = document.getElementById("table-body");
    if (tableBody) {
      const rows = tableBody.getElementsByTagName("tr");
      for (let i = 0; i < Math.min(rows.length, dashboardData.length); i++) {
        const td = document.createElement("td");
        td.textContent = dashboardData[i][columnName];
        td.classList.add("bg-success-subtle");
        rows[i].appendChild(td);
      }
    }
    
    // Show success message with sample data
    const sampleData = dashboardData.slice(0, 5).map(row => ({
      ...Object.fromEntries(
        Object.entries(row).filter(([key]) => 
          columnNames.includes(key) || key === columnName
        )
      )
    }));
    
    resultContainer.innerHTML = `
      <div class="alert alert-success">
        <h5>Column "${columnName}" added successfully!</h5>
        <p>Formula: ${formula}</p>
      </div>
      <div class="table-responsive">
        <table class="table table-sm table-striped">
          <thead>
            <tr>
              ${columnNames.map(col => `<th>${col}</th>`).join('')}
              <th class="bg-success-subtle">${columnName}</th>
            </tr>
          </thead>
          <tbody>
            ${sampleData.map(row => `
              <tr>
                ${columnNames.map(col => `<td>${row[col]}</td>`).join('')}
                <td class="bg-success-subtle">${row[columnName]}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
      <div class="mt-3">
        <button class="btn btn-primary" id="create-chart-btn">Create Chart with New Column</button>
      </div>
    `;
    
    // Add event listener for chart creation
    document.getElementById("create-chart-btn").addEventListener("click", function() {
      createChartForCalculatedColumn(columnName, columnNames[0], resultContainer);
    });
    
  } catch (error) {
    resultContainer.innerHTML = `<div class="alert alert-danger">Error applying formula: ${error.message}</div>`;
  }
}

// Create a chart for the calculated column
function createChartForCalculatedColumn(calculatedColumn, compareColumn, resultContainer) {
  // Prepare data for chart
  const chartData = {
    labels: dashboardData.slice(0, 10).map(row => row[compareColumn]),
    datasets: [{
      label: calculatedColumn,
      data: dashboardData.slice(0, 10).map(row => row[calculatedColumn]),
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
      borderColor: 'rgba(75, 192, 192, 1)',
      borderWidth: 1
    }]
  };
  
  // Add chart canvas
  resultContainer.innerHTML += `
    <div class="mt-4 border rounded p-3 bg-light">
      <h5>Chart: ${calculatedColumn} by ${compareColumn}</h5>
      <canvas id="calculated-column-chart"></canvas>
    </div>
  `;
  
  // Create chart
  const ctx = document.getElementById('calculated-column-chart').getContext('2d');
  new Chart(ctx, {
    type: 'bar',
    data: chartData,
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
}

// Add this function at the end of the file, before the export statements

// Fallback function to handle basic data analysis without SQL
function handleBasicDataAnalysis(query) {
  // This function will be called if the backend AI query fails
  // It performs simple data analysis directly in the browser
  
  if (!dashboardData || dashboardData.length === 0) {
    return {
      title: "No data available",
      html: "<p>No data is currently loaded. Please load some data first.</p>"
    };
  }
  
  const lowerQuery = query.toLowerCase();
  
  // Show first 10 rows
  if (lowerQuery.includes("first") && (lowerQuery.includes("10") || lowerQuery.includes("ten") || lowerQuery.includes("rows"))) {
    const data = dashboardData.slice(0, 10);
    const columns = Object.keys(data[0]);
    
    let tableHtml = `
      <table class="table">
        <thead>
          <tr>
            ${columns.map(col => `<th>${col}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
          ${data.map(row => `
            <tr>
              ${columns.map(col => `<td>${row[col]}</td>`).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
    
    return {
      title: "First 10 rows of data",
      html: tableHtml
    };
  }
  
  // Count total records
  if (lowerQuery.includes("count") || lowerQuery.includes("total") || lowerQuery.includes("records")) {
    return {
      title: "Total Records",
      html: `<p class="display-4 text-center">${dashboardData.length}</p>`
    };
  }
  
  // Show column names
  if (lowerQuery.includes("column") || lowerQuery.includes("field") || lowerQuery.includes("names")) {
    const columns = Object.keys(dashboardData[0]);
    
    let columnHtml = `
      <div class="row">
        ${columns.map(col => `
          <div class="col-md-4 mb-2">
            <div class="card">
              <div class="card-body py-2">
                <code>${col}</code>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
    
    return {
      title: "Available Columns",
      html: columnHtml
    };
  }
  
  // Default response
  return {
    title: "Basic Data Summary",
    html: `
      <p>Total records: <strong>${dashboardData.length}</strong></p>
      <p>Available columns: <strong>${Object.keys(dashboardData[0]).length}</strong></p>
      <p>Sample data:</p>
      <pre class="bg-light p-3 rounded"><code>${JSON.stringify(dashboardData[0], null, 2)}</code></pre>
    `
  };
}

// Export functions to global scope
window.showAIAssistant = showAIAssistant;
window.askAIAssistant = askAIAssistant;
window.handleAddCalculatedColumn = handleAddCalculatedColumn;
window.applyCalculatedColumn = applyCalculatedColumn;
window.handleBasicDataAnalysis = handleBasicDataAnalysis;