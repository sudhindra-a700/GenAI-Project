/**
 * GenAI Smart Contract Pro - Production Content Script
 * Auto-detects and analyzes contract content on web pages
 * Connected to Google Cloud Run backend
 */

// Production API configuration
const API_BASE_URL = 'https://genai-project-912902007097.europe-west4.run.app';
const API_ENDPOINTS = {
    analyze: `${API_BASE_URL}/analyze`,
    health: `${API_BASE_URL}/health`
};

// Contract detection patterns
const CONTRACT_PATTERNS = [
    /\b(agreement|contract|terms of service|privacy policy|employment agreement|lease agreement)\b/i,
    /\b(party|parties|whereas|therefore|hereby|herein|hereof)\b/i,
    /\b(shall|will|must|agree|consent|acknowledge)\b/i,
    /\b(liability|damages|breach|termination|confidential)\b/i,
    /\b(salary|compensation|benefits|notice period)\b/i
];

// State management
let isAnalyzing = false;
let analysisResults = null;
let resultOverlay = null;

/**
 * Detect if current page contains contract content
 */
function detectContractContent() {
    const pageText = document.body.innerText.toLowerCase();
    const contractScore = CONTRACT_PATTERNS.reduce((score, pattern) => {
        const matches = pageText.match(pattern);
        return score + (matches ? matches.length : 0);
    }, 0);
    
    return contractScore >= 3; // Threshold for contract detection
}

/**
 * Extract contract text from the page
 */
function extractContractText() {
    // Try to find main content areas
    const contentSelectors = [
        'main',
        '[role="main"]',
        '.content',
        '.main-content',
        '#content',
        'article',
        '.contract',
        '.agreement',
        '.terms'
    ];
    
    for (const selector of contentSelectors) {
        const element = document.querySelector(selector);
        if (element && element.innerText.length > 500) {
            return element.innerText.trim();
        }
    }
    
    // Fallback to body text
    return document.body.innerText.trim();
}

/**
 * Analyze contract with Cloud Run backend
 */
async function analyzeContract(contractText) {
    if (isAnalyzing) return null;
    
    isAnalyzing = true;
    showLoadingIndicator();
    
    try {
        const response = await fetch(API_ENDPOINTS.analyze, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                text: contractText.substring(0, 5000) // Limit text size
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        analysisResults = result;
        
        hideLoadingIndicator();
        showAnalysisResults(result);
        
        return result;
        
    } catch (error) {
        console.error('Contract analysis failed:', error);
        hideLoadingIndicator();
        showError(`Analysis failed: ${error.message}`);
        return null;
    } finally {
        isAnalyzing = false;
    }
}

/**
 * Show loading indicator
 */
function showLoadingIndicator() {
    const loader = document.createElement('div');
    loader.id = 'genai-contract-loader';
    loader.innerHTML = `
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: #1a73e8;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
        ">
            <div style="
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255,255,255,0.3);
                border-top: 2px solid white;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            "></div>
            Analyzing contract...
        </div>
        <style>
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    `;
    document.body.appendChild(loader);
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator() {
    const loader = document.getElementById('genai-contract-loader');
    if (loader) {
        loader.remove();
    }
}

/**
 * Show analysis results
 */
function showAnalysisResults(results) {
    // Remove existing overlay
    if (resultOverlay) {
        resultOverlay.remove();
    }
    
    resultOverlay = document.createElement('div');
    resultOverlay.id = 'genai-contract-results';
    resultOverlay.innerHTML = `
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            width: 400px;
            max-height: 600px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            overflow: hidden;
            border: 1px solid #e1e5e9;
        ">
            <div style="
                background: linear-gradient(135deg, #1a73e8, #4285f4);
                color: white;
                padding: 16px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <h3 style="margin: 0; font-size: 16px; font-weight: 600;">Contract Analysis</h3>
                <button onclick="this.closest('#genai-contract-results').remove()" style="
                    background: none;
                    border: none;
                    color: white;
                    font-size: 18px;
                    cursor: pointer;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 4px;
                ">×</button>
            </div>
            <div style="
                padding: 20px;
                max-height: 500px;
                overflow-y: auto;
                font-size: 14px;
                line-height: 1.5;
            ">
                ${formatAnalysisResults(results)}
            </div>
        </div>
    `;
    
    document.body.appendChild(resultOverlay);
}

/**
 * Format analysis results for display
 */
function formatAnalysisResults(results) {
    if (!results) {
        return '<p style="color: #d93025;">No analysis results available.</p>';
    }
    
    let html = '';
    
    // Contract Summary
    if (results.summary) {
        html += `
            <div style="margin-bottom: 20px;">
                <h4 style="margin: 0 0 8px 0; color: #1a73e8; font-size: 14px; font-weight: 600;">Summary</h4>
                <p style="margin: 0; color: #5f6368;">${results.summary}</p>
            </div>
        `;
    }
    
    // Key Terms
    if (results.key_terms && Object.keys(results.key_terms).length > 0) {
        html += `
            <div style="margin-bottom: 20px;">
                <h4 style="margin: 0 0 8px 0; color: #1a73e8; font-size: 14px; font-weight: 600;">Key Terms</h4>
                <div style="display: grid; gap: 8px;">
        `;
        
        for (const [key, value] of Object.entries(results.key_terms)) {
            html += `
                <div style="display: flex; justify-content: space-between; padding: 8px; background: #f8f9fa; border-radius: 6px;">
                    <span style="font-weight: 500; color: #202124;">${key}:</span>
                    <span style="color: #5f6368;">${value}</span>
                </div>
            `;
        }
        
        html += '</div></div>';
    }
    
    // Constitutional Insights
    if (results.constitutional_insights) {
        html += `
            <div style="margin-bottom: 20px;">
                <h4 style="margin: 0 0 8px 0; color: #1a73e8; font-size: 14px; font-weight: 600;">Constitutional Law Insights</h4>
                <div style="background: #e8f0fe; padding: 12px; border-radius: 6px; border-left: 4px solid #1a73e8;">
                    <p style="margin: 0; color: #1a73e8; font-size: 13px;">${results.constitutional_insights}</p>
                </div>
            </div>
        `;
    }
    
    // Risk Assessment
    if (results.risk_level) {
        const riskColor = results.risk_level.toLowerCase() === 'high' ? '#d93025' : 
                         results.risk_level.toLowerCase() === 'medium' ? '#f9ab00' : '#137333';
        
        html += `
            <div style="margin-bottom: 20px;">
                <h4 style="margin: 0 0 8px 0; color: #1a73e8; font-size: 14px; font-weight: 600;">Risk Assessment</h4>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="
                        background: ${riskColor};
                        color: white;
                        padding: 4px 8px;
                        border-radius: 12px;
                        font-size: 12px;
                        font-weight: 500;
                    ">${results.risk_level || 'Unknown'}</span>
                    ${results.risk_factors ? `<span style="color: #5f6368; font-size: 13px;">${results.risk_factors}</span>` : ''}
                </div>
            </div>
        `;
    }
    
    if (!html) {
        html = '<p style="color: #5f6368;">Analysis completed but no detailed results available.</p>';
    }
    
    return html;
}

/**
 * Show error message
 */
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.innerHTML = `
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: #d93025;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            max-width: 300px;
        ">
            <strong>GenAI Contract Pro</strong><br>
            ${message}
        </div>
    `;
    
    document.body.appendChild(errorDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

/**
 * Initialize contract detection and analysis
 */
function initializeContractAnalysis() {
    // Check if page contains contract content
    if (detectContractContent()) {
        console.log('Contract content detected on page');
        
        // Show detection notification
        const notification = document.createElement('div');
        notification.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: #137333;
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
                cursor: pointer;
            " onclick="
                this.remove();
                window.genaiAnalyzeContract();
            ">
                📄 Contract detected! Click to analyze
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove notification after 10 seconds
        setTimeout(() => {
            notification.remove();
        }, 10000);
    }
}

/**
 * Manual contract analysis trigger
 */
window.genaiAnalyzeContract = function() {
    const contractText = extractContractText();
    if (contractText && contractText.length > 100) {
        analyzeContract(contractText);
    } else {
        showError('No contract content found on this page.');
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeContractAnalysis);
} else {
    initializeContractAnalysis();
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'analyzeContract') {
        const contractText = extractContractText();
        if (contractText) {
            analyzeContract(contractText).then(result => {
                sendResponse({ success: true, result });
            }).catch(error => {
                sendResponse({ success: false, error: error.message });
            });
        } else {
            sendResponse({ success: false, error: 'No contract content found' });
        }
        return true; // Keep message channel open for async response
    }
    
    if (request.action === 'getAnalysisResults') {
        sendResponse({ results: analysisResults });
    }
});

console.log('GenAI Smart Contract Pro - Production version loaded');
console.log('Connected to:', API_BASE_URL);
