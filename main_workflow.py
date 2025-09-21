"""
Minimal Working Version - GenAI Smart Contract Pro
Gets the service running first, then we can add features
"""

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

@app.route('/')
def root():
    """Root endpoint"""
    return jsonify({
        "message": "GenAI Smart Contract Pro API",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "endpoints": ["/", "/health", "/analyze"]
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "GenAI Contract Pro",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/analyze', methods=['POST'])
def analyze_contract():
    """Basic contract analysis endpoint"""
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        contract_text = data.get('text', '').strip()
        
        if not contract_text:
            return jsonify({"error": "No contract text provided"}), 400
        
        # Basic analysis (no ML models yet)
        words = contract_text.split()
        
        # Simple pattern-based analysis
        key_terms = {}
        if any(word.lower() in ['salary', 'payment', 'compensation'] for word in words):
            key_terms['compensation'] = 'Found'
        if any(word.lower() in ['termination', 'end', 'expire'] for word in words):
            key_terms['termination'] = 'Found'
        if any(word.lower() in ['confidentiality', 'nda', 'secret'] for word in words):
            key_terms['confidentiality'] = 'Found'
        
        response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "summary": f"Basic contract analysis completed for {len(contract_text)} characters of text. Found {len(words)} words.",
                "key_terms": key_terms,
                "word_count": len(words),
                "character_count": len(contract_text),
                "status": "Basic pattern analysis completed - AI features will be added soon"
            },
            "metadata": {
                "processing_method": "Pattern-based analysis",
                "ai_features": "Coming soon"
            }
        }
        
        logger.info(f"Analyzed contract with {len(words)} words")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({
            "success": False,
            "error": "Analysis failed",
            "timestamp": datetime.now().isoformat(),
            "details": str(e)
        }), 500

@app.route('/status')
def status():
    """Status endpoint"""
    return jsonify({
        "service": "GenAI Smart Contract Pro",
        "status": "operational",
        "version": "1.0.0 - Minimal",
        "features": {
            "basic_analysis": "active",
            "ai_analysis": "coming_soon",
            "legal_verification": "coming_soon"
        },
        "timestamp": datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/health", "/analyze", "/status"]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting GenAI Contract Pro Minimal on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
