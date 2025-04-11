// Part 3: Visualization and Charts
// Create charts from data
function createCharts(data) {
  console.log("Initializing charts with data");

  if (!data || data.length === 0) {
    console.error("No data for charts");
    return;
  }

  try {
    // Status distribution chart
    const statusCanvas = document.getElementById("statusChart");
    if (statusCanvas) {
      let statusField = null;
      // Look for status-like fields
      const possibleStatusFields = [
        "status",
        "Status",
        "reason for credit entry",
        "order_status",
        "order state",
        "state",
        "condition",
      ];
      for (const field of possibleStatusFields) {
        if (data[0].hasOwnProperty(field)) {
          statusField = field;
          break;
        }
      }

      if (statusField) {
        console.log(`Using ${statusField} for status chart`);
        const statusCounts = {};
        data.forEach((record) => {
          const status = record[statusField] || "Unknown";
          statusCounts[status] = (statusCounts[status] || 0) + 1;
        });

        const statusLabels = Object.keys(statusCounts);
        const statusData = Object.values(statusCounts);

        // Check if chart exists and destroy it
        if (window.statusChart instanceof Chart) {
          window.statusChart.destroy();
        }

        window.statusChart = new Chart(statusCanvas, {
          type: "pie",
          data: {
            labels: statusLabels,
            datasets: [
              {
                data: statusData,
                backgroundColor: [
                  "#FF6384",
                  "#36A2EB",
                  "#FFCE56",
                  "#4BC0C0",
                  "#9966FF",
                  "#FF9F40",
                ],
              },
            ],
          },
          options: {
            responsive: true,
            plugins: {
              legend: {
                position: "right",
              },
              title: {
                display: true,
                text: "Status Distribution",
              },
            },
          },
        });
      } else {
        console.log("No status field found for chart");
        statusCanvas.parentNode.innerHTML =
          "<p class='text-muted'>No status data available for chart</p>";
      }
    }

    // Region distribution chart
    const regionCanvas = document.getElementById("regionChart");
    if (regionCanvas) {
      let regionField = null;
      // Look for region-like fields
      const possibleRegionFields = [
        "region",
        "Region",
        "city",
        "City",
        "location",
        "address",
        "country",
        "state",
        "State",
        "customer state",
      ];
      for (const field of possibleRegionFields) {
        if (data[0].hasOwnProperty(field)) {
          regionField = field;
          break;
        }
      }

      if (regionField) {
        console.log(`Using ${regionField} for region chart`);
        const regionCounts = {};
        data.forEach((record) => {
          const region = record[regionField] || "Unknown";
          regionCounts[region] = (regionCounts[region] || 0) + 1;
        });

        const regionLabels = Object.keys(regionCounts);
        const regionData = Object.values(regionCounts);

        // Check if chart exists and destroy it
        if (window.regionChart instanceof Chart) {
          window.regionChart.destroy();
        }

        window.regionChart = new Chart(regionCanvas, {
          type: "bar",
          data: {
            labels: regionLabels,
            datasets: [
              {
                label: `Orders by ${regionField}`,
                data: regionData,
                backgroundColor: "#36A2EB",
              },
            ],
          },
          options: {
            responsive: true,
            plugins: {
              legend: {
                display: false,
              },
              title: {
                display: true,
                text: `Orders by ${regionField}`,
              },
            },
          },
        });
      } else {
        console.log("No region field found for chart");
        regionCanvas.parentNode.innerHTML =
          "<p class='text-muted'>No region data available for chart</p>";
      }
    }

    // Product sales chart
    const productSalesCanvas = document.getElementById("productSalesChart");
    if (productSalesCanvas && productsData.length > 0) {
      // Sort products by sales
      const topProducts = [...productsData]
        .sort((a, b) => b.total_sales - a.total_sales)
        .slice(0, 10);

      const productLabels = topProducts.map(
        (p) => p.product_name.substring(0, 20) + "..."
      );
      const salesData = topProducts.map((p) => p.total_sales);

      // Check if chart exists and destroy it
      if (window.productSalesChart instanceof Chart) {
        window.productSalesChart.destroy();
      }

      window.productSalesChart = new Chart(productSalesCanvas, {
        type: "bar",
        data: {
          labels: productLabels,
          datasets: [
            {
              label: "Top Products by Sales",
              data: salesData,
              backgroundColor: "#4BC0C0",
            },
          ],
        },
        options: {
          responsive: true,
          indexAxis: "y",
          plugins: {
            legend: {
              display: false,
            },
            title: {
              display: true,
              text: "Top Products by Sales",
            },
          },
        },
      });
    }
  } catch (error) {
    console.error("Error initializing charts:", error);
  }
}

// Export functions to global scope
window.createCharts = createCharts;