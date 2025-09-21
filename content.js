// Enhanced Content Script for Contract Detection - MVP with Lucide Icons
// Minimal changes for maximum impact

class ContractDetector {
    constructor() {
        this.isDetecting = false;
        this.lastAnalysis = null;
        this.confidenceThreshold = 0.3;
        
        // Enhanced legal patterns for better detection
        this.legalPatterns = [
            /\b(agreement|contract|terms\s+and\s+conditions)\b/gi,
            /\b(whereas|hereby|party|parties|governing\s+law)\b/gi,
            /\b(payment|delivery|warranty|termination|liability)\b/gi,
            /\b(shall|covenant|indemnify|breach|enforce)\b/gi,
            /\b(jurisdiction|dispute|arbitration|mediation)\b/gi
        ];
        
        this.init();
    }
    
    init() {
        // Listen for messages from popup
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'detectContract') {
                this.detectContractContent().then(result => {
                    sendResponse(result);
                });
                return true; // Keep message channel open
            }
        });
        
        // Auto-detect on page load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.autoDetect());
        } else {
            this.autoDetect();
        }
    }
    
    async autoDetect() {
        const result = await this.detectContractContent();
        if (result.detected && result.confidence > this.confidenceThreshold) {
            // Send detection result to popup
            chrome.runtime.sendMessage({
                action: 'contractDetected',
                data: result
            });
        }
    }
    
    async detectContractContent() {
        try {
            const pageText = this.extractPageText();
            const confidence = this.calculateConfidence(pageText);
            
            return {
                detected: confidence > this.confidenceThreshold,
                confidence: Math.round(confidence * 100),
                text: pageText.substring(0, 5000), // Limit text size
                url: window.location.href,
                title: document.title
            };
        } catch (error) {
            console.error('Contract detection error:', error);
            return {
                detected: false,
                confidence: 0,
                text: '',
                error: error.message
            };
        }
    }
    
    extractPageText() {
        // Remove script and style elements
        const clonedDoc = document.cloneNode(true);
        const scripts = clonedDoc.querySelectorAll('script, style, nav, header, footer');
        scripts.forEach(el => el.remove());
        
        // Get main content areas
        const contentSelectors = [
            'main', 'article', '.content', '.document', '.contract',
            '[class*="content"]', '[class*="document"]', '[class*="contract"]'
        ];
        
        let text = '';
        for (const selector of contentSelectors) {
            const elements = clonedDoc.querySelectorAll(selector);
            if (elements.length > 0) {
                text = Array.from(elements).map(el => el.textContent).join(' ');
                break;
            }
        }
        
        // Fallback to body text
        if (!text.trim()) {
            text = clonedDoc.body ? clonedDoc.body.textContent : '';
        }
        
        return text.trim();
    }
    
    calculateConfidence(text) {
        if (!text || text.length < 100) return 0;
        
        let score = 0;
        let totalMatches = 0;
        
        // Check legal patterns
        this.legalPatterns.forEach(pattern => {
            const matches = text.match(pattern) || [];
            totalMatches += matches.length;
        });
        
        // Base score from pattern matches
        score = Math.min(totalMatches / 10, 0.8);
        
        // Bonus for document structure
        if (text.includes('Article') || text.includes('Section')) score += 0.1;
        if (text.includes('WHEREAS') || text.includes('NOW THEREFORE')) score += 0.15;
        if (/\d+\.\s/.test(text)) score += 0.05; // Numbered sections
        
        // URL bonus
        const url = window.location.href.toLowerCase();
        if (/\b(contract|agreement|terms|legal|document)/.test(url)) score += 0.1;
        if (url.includes('.pdf')) score += 0.2;
        
        return Math.min(score, 1.0);
    }
}

// Initialize detector
new ContractDetector();
