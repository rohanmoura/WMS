// Add this file to check if all modules are loaded correctly
document.addEventListener('DOMContentLoaded', function() {
    console.log("Checking if all dashboard modules are loaded correctly...");
    
    // Check core dashboard
    if (typeof dashboardData !== 'undefined') {
        console.log("✅ dashboardData is defined");
    } else {
        console.error("❌ dashboardData is not defined");
    }
    
    if (typeof initDashboard === 'function') {
        console.log("✅ initDashboard function is defined");
    } else {
        console.error("❌ initDashboard function is not defined");
    }
    
    if (typeof loadData === 'function') {
        console.log("✅ loadData function is defined");
    } else {
        console.error("❌ loadData function is not defined");
    }
    
    // Check visualization module
    if (typeof createCharts === 'function') {
        console.log("✅ createCharts function is defined");
    } else {
        console.error("❌ createCharts function is not defined");
    }
    
    // Check database module
    if (typeof initEditableTable === 'function') {
        console.log("✅ initEditableTable function is defined");
    } else {
        console.error("❌ initEditableTable function is not defined");
    }
    
    if (typeof initProductsTable === 'function') {
        console.log("✅ initProductsTable function is defined");
    } else {
        console.error("❌ initProductsTable function is not defined");
    }
    
    // Check AI module
    if (typeof showAIAssistant === 'function') {
        console.log("✅ showAIAssistant function is defined");
    } else {
        console.error("❌ showAIAssistant function is not defined");
    }
    
    if (typeof askAIAssistant === 'function') {
        console.log("✅ askAIAssistant function is defined");
    } else {
        console.error("❌ askAIAssistant function is not defined");
    }
    
    // Log URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    console.log("URL parameters:", Object.fromEntries(urlParams.entries()));
});