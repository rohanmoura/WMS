// Dashboard initialization script
document.addEventListener('DOMContentLoaded', function() {
    console.log("Dashboard initialization started");
    
    // Get data file from hidden input
    const dataFile = document.getElementById('data-file').value;
    const hasLogs = document.getElementById('has-logs').value === 'true';
    
    console.log("Data file from template:", dataFile);
    
    // Initialize dashboard with the data file
    if (typeof initDashboard === 'function') {
        console.log("Initializing dashboard with:", dataFile, "Has logs:", hasLogs);
        initDashboard(dataFile, hasLogs);
    } else {
        console.error("initDashboard function not found! Check if dashboard.js is loaded correctly.");
    }
});