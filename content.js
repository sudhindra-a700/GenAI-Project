/**
 * Enhanced Content Script for GenAI Smart Contract Pro
 * Production version with Cloud Run API integration
 * Auto-detects contract content with improved accuracy
 */

// Production API configuration
const API_BASE_URL = 'https://genai-contract-backend-xxx-uc.a.run.app'; // Replace with your actual Cloud Run URL
const API_TIMEOUT = 30000; // 30 seconds for production

class ContractDetector {
    constructor() {
        this.isDetecting = false;
        this.lastDetectionTime = 0;
        this.detectionCache = new Map();
        
        // Enhanced legal patterns for better detection
        this.legalPatterns = [
            // High confidence patterns
            /\b(agreement|contract|terms\s+and\s+conditions|memorandum\s+of\s+understanding)\b/gi,
            /\b(whereas|hereby|party|parties|governing\s+law|jurisdiction)\b/gi,
            /\b(payment|consideration|delivery|warranty|termination|liability)\b/gi,
            /\b(shall|covenant|indemnify|breach|enforce|binding)\b/gi,
            /\b(arbitration|mediation|dispute\s+resolution|force\s+majeure)\b/gi,
            
            // Medium confidence patterns
            /\b(terms|conditions|obligations|rights|duties)\b/gi,
            /\b(effective\s+date|expiration|renewal|amendment)\b/gi,
            /\b(confidential|proprietary|intellectual\s+property)\b/gi,
            /\b(compliance|regulatory|statutory|legal)\b/gi,
            
            // Legal document indicators
            /\b(article|section|clause|paragraph|subsection)\s+\d+/gi,
            /\b(exhibit|schedule|appendix|attachment)\s+[a-z0-9]/gi,
            /\b(signature|executed|witnessed|notarized)\b/gi
        ];
        
        // URL patterns that likely contain contracts
        this.contractUrlPatterns = [
            /\/contract/i,
            /\/agreement/i,
            /\/terms/i,
            /\/legal/i,
            /\.pdf$/i,
            /\/download.*\.(pdf|doc|docx)/i
        ];
        
        this.init();
    }
    
    init() {
        // Start detection when page loads
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.startDetection());
        } else {
            this.startDetection();
        }
        
        // Listen for messages from popup
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true; // Keep message channel open for async response
        });
        
        // Detect dynamic content changes
        this.observeChanges();
    }
    
    startDetection() {
        // Debounce detection to avoid excessive calls
        const now = Date.now();
        if (now - this.lastDetectionTime < 2000) return;
        
        this.lastDetectionTime = now;
        this.detectContractContent();
    }
    
    detectContractContent() {
        if (this.isDetecting) return;
        this.isDetecting = true;
        
        try {
            const result = this.analyzePageContent();
            
            // Cache result
            const cacheKey = window.location.href;
            this.detectionCache.set(cacheKey, {
                ...result,
                timestamp: Date.now()
            });
            
            // Send result to popup if it's open
            chrome.runtime.sendMessage({
                type: 'CONTRACT_DETECTED',
                data: result
            }).catch(() => {
                // Popup might not be open, ignore error
            });
            
        } catch (error) {
            console.error('Contract detection error:', error);
        } finally {
            this.isDetecting = false;
        }
    }
    
    analyzePageContent() {
        const analysis = {
            detected: false,
            confidence: 0,
            text: '',
            source: 'unknown',
            patterns_matched: [],
            word_count: 0,
            legal_terms_count: 0
        };
        
        // Strategy 1: Check URL patterns
        const urlConfidence = this.checkUrlPatterns();
        if (urlConfidence > 0) {
            analysis.confidence += urlConfidence;
            analysis.source = 'url_pattern';
        }
        
        // Strategy 2: Extract and analyze text content
        const textContent = this.extractTextContent();
        if (textContent) {
            const textAnalysis = this.analyzeTextContent(textContent);
            analysis.confidence += textAnalysis.confidence;
            analysis.text = textContent;
            analysis.patterns_matched = textAnalysis.patterns_matched;
            analysis.word_count = textAnalysis.word_count;
            analysis.legal_terms_count = textAnalysis.legal_terms_count;
            
            if (textAnalysis.confidence > analysis.confidence) {
                analysis.source = 'content_analysis';
            }
        }
        
        // Strategy 3: Check document metadata
        const metadataConfidence = this.checkDocumentMetadata();
        if (metadataConfidence > 0) {
            analysis.confidence += metadataConfidence * 0.3; // Lower weight for metadata
        }
        
        // Normalize confidence to 0-100
        analysis.confidence = Math.min(100, Math.round(analysis.confidence));
        analysis.detected = analysis.confidence >= 30; // Threshold for detection
        
        return analysis;
    }
    
    checkUrlPatterns() {
        const url = window.location.href.toLowerCase();
        let confidence = 0;
        
        for (const pattern of this.contractUrlPatterns) {
            if (pattern.test(url)) {
                confidence += 25;
            }
        }
        
        return Math.min(50, confidence); // Max 50% confidence from URL
    }
    
    extractTextContent() {
        // Priority order for text extraction
        const selectors = [
            // PDF viewers
            '.textLayer',
            '#viewer .page',
            
            // Common document containers
            '.document-content',
            '.contract-content',
            '.legal-document',
            'article',
            'main',
            
            // Generic content areas
            '.content',
            '#content',
            '.main-content',
            
            // Fallback to body
            'body'
        ];
        
        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element) {
                const text = this.cleanText(element.innerText || element.textContent);
                if (text && text.length > 200) {
                    return text.substring(0, 5000); // Limit text length
                }
            }
        }
        
        return '';
    }
    
    analyzeTextContent(text) {
        const analysis = {
            confidence: 0,
            patterns_matched: [],
            word_count: 0,
            legal_terms_count: 0
        };
        
        if (!text || text.length < 100) {
            return analysis;
        }
        
        // Count words
        analysis.word_count = text.split(/\s+/).length;
        
        // Check legal patterns
        let totalMatches = 0;
        for (let i = 0; i < this.legalPatterns.length; i++) {
            const pattern = this.legalPatterns[i];
            const matches = text.match(pattern) || [];
            
            if (matches.length > 0) {
                analysis.patterns_matched.push({
                    pattern: pattern.source,
                    matches: matches.length
                });
                
                // Weight patterns by importance (earlier patterns are more important)
                const weight = Math.max(1, 5 - i);
                totalMatches += matches.length * weight;
            }
        }
        
        analysis.legal_terms_count = totalMatches;
        
        // Calculate confidence based on pattern density
        const density = totalMatches / Math.max(1, analysis.word_count / 100);
        analysis.confidence = Math.min(70, density * 10);
        
        // Bonus for document structure
        if (/\b(article|section|clause)\s+\d+/gi.test(text)) {
            analysis.confidence += 15;
        }
        
        // Bonus for signature blocks
        if (/\b(signature|executed|witnessed)\b/gi.test(text)) {
            analysis.confidence += 10;
        }
        
        return analysis;
    }
    
    checkDocumentMetadata() {
        let confidence = 0;
        
        // Check page title
        const title = document.title.toLowerCase();
        if (/\b(contract|agreement|terms|legal)\b/.test(title)) {
            confidence += 15;
        }
        
        // Check meta tags
        const metaTags = document.querySelectorAll('meta[name*="description"], meta[name*="keywords"]');
        for (const meta of metaTags) {
            const content = (meta.getAttribute('content') || '').toLowerCase();
            if (/\b(contract|agreement|legal|terms)\b/.test(content)) {
                confidence += 10;
                break;
            }
        }
        
        return confidence;
    }
    
    cleanText(text) {
        if (!text) return '';
        
        return text
            .replace(/\s+/g, ' ') // Normalize whitespace
            .replace(/[^\w\s.,;:!?()-]/g, '') // Remove special characters
            .trim();
    }
    
    observeChanges() {
        // Observe DOM changes for dynamic content
        const observer = new MutationObserver((mutations) => {
            let shouldRedetect = false;
            
            for (const mutation of mutations) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Check if significant content was added
                    for (const node of mutation.addedNodes) {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            const text = node.textContent || '';
                            if (text.length > 100) {
                                shouldRedetect = true;
                                break;
                            }
                        }
                    }
                }
            }
            
            if (shouldRedetect) {
                setTimeout(() => this.startDetection(), 1000);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    handleMessage(request, sender, sendResponse) {
        switch (request.type) {
            case 'GET_CONTRACT_CONTENT':
                this.handleGetContractContent(sendResponse);
                break;
                
            case 'ANALYZE_PAGE':
                this.handleAnalyzePage(sendResponse);
                break;
                
            default:
                sendResponse({ error: 'Unknown message type' });
        }
    }
    
    handleGetContractContent(sendResponse) {
        try {
            const cacheKey = window.location.href;
            const cached = this.detectionCache.get(cacheKey);
            
            if (cached && (Date.now() - cached.timestamp < 30000)) {
                // Use cached result if less than 30 seconds old
                sendResponse({ success: true, data: cached });
            } else {
                // Perform fresh detection
                const result = this.analyzePageContent();
                sendResponse({ success: true, data: result });
            }
        } catch (error) {
            sendResponse({ success: false, error: error.message });
        }
    }
    
    async handleAnalyzePage(sendResponse) {
        try {
            const detection = this.analyzePageContent();
            
            if (!detection.detected || !detection.text) {
                sendResponse({
                    success: false,
                    error: 'No contract content detected on this page'
                });
                return;
            }
            
            // Send to backend for analysis
            const response = await fetch(`${API_BASE_URL}/auto-analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: detection.text,
                    confidence: detection.confidence,
                    source: detection.source
                }),
                signal: AbortSignal.timeout(API_TIMEOUT)
            });
            
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status}`);
            }
            
            const analysisResult = await response.json();
            
            sendResponse({
                success: true,
                data: {
                    detection: detection,
                    analysis: analysisResult
                }
            });
            
        } catch (error) {
            console.error('Page analysis error:', error);
            sendResponse({
                success: false,
                error: `Analysis failed: ${error.message}`
            });
        }
    }
}

// Initialize contract detector
const contractDetector = new ContractDetector();

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ContractDetector;
}
