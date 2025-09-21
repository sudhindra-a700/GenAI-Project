// Enhanced Content Script for GenAI Smart Contract Pro - MVP Version
// Only essential improvements from Grammarly's approach

class ContractDetector {
    constructor() {
        // Original contract patterns (unchanged)
        this.contractPatterns = [
            /\b(?:agreement|contract|terms\s+(?:and|&)\s+conditions)\b/gi,
            /\b(?:whereas|hereby|party|parties|governing\s+law)\b/gi,
            /\b(?:payment\s+terms|delivery|warranty|termination)\b/gi,
            /\b(?:employment|service|procurement|lease|license)\b/gi,
            /\b(?:confidentiality|non-disclosure|intellectual\s+property)\b/gi
        ];
        
        // ENHANCEMENT #1: Add legal keyword patterns (inspired by Grammarly's layered detection)
        this.legalPatterns = [
            /\b(agreement|contract|terms\s+and\s+conditions)\b/gi,
            /\b(whereas|hereby|party|parties|governing\s+law)\b/gi,
            /\b(payment|delivery|warranty|termination|liability)\b/gi,
            /\b(shall|covenant|indemnify|breach|enforce)\b/gi,
            /\b(jurisdiction|dispute|arbitration|mediation)\b/gi
        ];
        
        this.legalKeywords = [
            'shall', 'hereby', 'whereas', 'therefore', 'notwithstanding',
            'pursuant', 'covenant', 'indemnify', 'liability', 'breach'
        ];
    }

    extractPageContent() {
        // Get main text content (unchanged)
        const textContent = this.getCleanTextContent();
        
        // Get page metadata (unchanged)
        const url = window.location.href;
        const title = document.title;
        
        return {
            text: textContent,
            url: url,
            title: title,
            timestamp: Date.now()
        };
    }

    getCleanTextContent() {
        // Remove script and style elements (unchanged)
        const elementsToRemove = document.querySelectorAll('script, style, nav, header, footer, aside');
        const tempDoc = document.cloneNode(true);
        
        elementsToRemove.forEach(el => {
            const tempEl = tempDoc.querySelector(el.tagName.toLowerCase());
            if (tempEl) tempEl.remove();
        });

        // Priority selectors for contract content (unchanged)
        const contentSelectors = [
            'main',
            '.contract-content',
            '.document-content',
            '.legal-document',
            'article',
            '.content',
            'body'
        ];

        let textContent = '';
        
        for (const selector of contentSelectors) {
            const element = document.querySelector(selector);
            if (element) {
                textContent = element.innerText || element.textContent || '';
                if (textContent.length > 500) break;
            }
        }

        // Fallback to body text (unchanged)
        if (textContent.length < 100) {
            textContent = document.body.innerText || document.body.textContent || '';
        }

        // Clean and normalize text (unchanged)
        return textContent
            .replace(/\s+/g, ' ')
            .replace(/[\r\n]+/g, '\n')
            .trim()
            .substring(0, 10000); // Limit to 10k chars
    }

    detectContractContent(pageData) {
        const text = pageData.text.toLowerCase();
        const url = pageData.url.toLowerCase();
        
        if (!text || text.length < 50) {
            return {
                detected: false,
                confidence: 0.0,
                method: 'insufficient_content',
                contract_text: pageData.text
            };
        }

        let score = 0;
        let matches = 0;

        // Original pattern matching (unchanged)
        this.contractPatterns.forEach(pattern => {
            const patternMatches = (text.match(pattern) || []).length;
            matches += patternMatches;
            score += patternMatches * 0.1;
        });

        // ENHANCEMENT #1: Enhanced legal pattern detection (Grammarly-inspired)
        this.legalPatterns.forEach(pattern => {
            const legalMatches = (text.match(pattern) || []).length;
            matches += legalMatches;
            score += legalMatches * 0.15; // Slightly higher weight for legal patterns
        });

        // Legal keyword density (unchanged)
        const words = text.split(/\s+/);
        const legalWordCount = words.filter(word => 
            this.legalKeywords.includes(word.toLowerCase())
        ).length;
        
        const legalDensity = legalWordCount / Math.max(words.length, 1);
        score += legalDensity * 2;

        // URL indicators (unchanged)
        const urlIndicators = ['contract', 'agreement', 'terms', 'legal', '.pdf'];
        const urlScore = urlIndicators.some(indicator => url.includes(indicator)) ? 0.3 : 0;
        score += urlScore;

        // Document structure indicators (unchanged)
        const structureScore = this.analyzeDocumentStructure(text);
        score += structureScore;

        // Normalize confidence score
        const confidence = Math.min(score, 1.0);
        const detected = confidence > 0.25; // Slightly lower threshold due to enhanced detection

        return {
            detected: detected,
            confidence: confidence,
            method: detected ? 'enhanced_pattern_analysis' : 'no_patterns',
            contract_text: pageData.text,
            matches: matches,
            legal_density: legalDensity,
            url_score: urlScore
        };
    }

    analyzeDocumentStructure(text) {
        let score = 0;
        
        // Check for numbered sections (unchanged)
        if (/\b\d+\.\s/.test(text)) score += 0.1;
        
        // Check for article/section references (unchanged)
        if (/\b(?:article|section|clause)\s+\d+/i.test(text)) score += 0.2;
        
        // Check for signature blocks (unchanged)
        if (/\b(?:signature|signed|date|witness)\b/i.test(text)) score += 0.1;
        
        // Check for party definitions (unchanged)
        if (/\b(?:party|parties|company|individual|entity)\b/i.test(text)) score += 0.1;
        
        return score;
    }

    async performAutoAnalysis(pageData) {
        try {
            const response = await fetch('http://localhost:5000/auto-analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(pageData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            return {
                status: 'error',
                error: `Auto-analysis failed: ${error.message}`
            };
        }
    }
}

// Initialize detector (unchanged)
const detector = new ContractDetector();

// Message listener for browser extension communication (unchanged)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getPageData') {
        const pageData = detector.extractPageContent();
        const detectionResult = detector.detectContractContent(pageData);
        
        sendResponse({
            ...pageData,
            ...detectionResult
        });
        
    } else if (request.action === 'autoAnalyze') {
        const pageData = detector.extractPageContent();
        
        detector.performAutoAnalysis(pageData)
            .then(result => sendResponse(result))
            .catch(error => sendResponse({
                status: 'error',
                error: error.message
            }));
        
        return true; // Indicates async response
    }
});

// Auto-detect on page load (unchanged)
document.addEventListener('DOMContentLoaded', () => {
    // Passive detection - no automatic analysis
    const pageData = detector.extractPageContent();
    const detection = detector.detectContractContent(pageData);
    
    if (detection.detected && detection.confidence > 0.7) {
        // High confidence detection - could notify extension
        console.log('High-confidence contract detected:', detection.confidence);
    }
});
