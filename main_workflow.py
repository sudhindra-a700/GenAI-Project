"""
Production Main Workflow for GenAI Smart Contract Pro
Optimized for Google Cloud Run deployment
Integrates RAG retriever, contract summarizer, and IndianLegalBERT verification
"""

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, Any, Optional
import traceback
import sys

# Import modular components
try:
    from rag_retriever import get_rag_explanation
    from contract_summarizer import ContractSummarizer
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure CORS for production
CORS(app, origins=[
    "chrome-extension://*",  # Allow all Chrome extensions
    "https://*",  # Allow HTTPS websites
    "http://localhost:*"  # Allow localhost for development
])

class ContractAnalysisWorkflow:
    """
    Production workflow orchestrating all three components:
    1. Contract Summarizer (modular component)
    2. RAG Retriever (existing modular component) 
    3. IndianLegalBERT Verification
    """
    
    def __init__(self):
        """Initialize all components with production settings"""
        self.summarizer = None
        self.bert_model = None
        self.bert_tokenizer = None
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
        logger.info(f"Initializing workflow for project: {self.project_id}")
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all analysis components with error handling"""
        # Initialize contract summarizer
        try:
            logger.info("Initializing contract summarizer...")
            self.summarizer = ContractSummarizer(project_id=self.project_id)
            logger.info("Contract summarizer initialized successfully")
        except Exception as e:
            logger.error(f"Contract summarizer initialization failed: {e}")
            self.summarizer = None
        
        # Initialize IndianLegalBERT
        try:
            logger.info("Initializing IndianLegalBERT...")
            model_name = "law-ai/InLegalBERT"
            self.bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.bert_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            logger.info("IndianLegalBERT initialized successfully")
        except Exception as e:
            logger.error(f"IndianLegalBERT initialization failed: {e}")
            self.bert_model = None
            self.bert_tokenizer = None
        
        # Log component status
        components_status = {
            "summarizer": "active" if self.summarizer else "inactive",
            "bert": "active" if self.bert_model else "inactive",
            "rag": "unknown"  # RAG status checked dynamically
        }
        logger.info(f"Component initialization complete: {components_status}")
    
    def analyze_contract(self, contract_text: str) -> Dict[str, Any]:
        """
        Complete contract analysis using all three components
        
        Args:
            contract_text: Full contract text
            
        Returns:
            Comprehensive analysis results
        """
        logger.info(f"Starting contract analysis for text length: {len(contract_text)}")
        
        results = {
            "summary": None,
            "constitutional_analysis": None,
            "verification_score": None,
            "key_terms": None,
            "themes": None,
            "component_status": {
                "summarizer": "inactive",
                "rag": "inactive", 
                "bert": "inactive"
            },
            "errors": [],
            "processing_time": None
        }
        
        import time
        start_time = time.time()
        
        # Component 1: Contract Summarization
        try:
            if self.summarizer:
                logger.info("Running contract summarization...")
                results["summary"] = self.summarizer.generate_summary(contract_text)
                results["key_terms"] = self.summarizer.extract_key_terms(contract_text)
                results["themes"] = self.summarizer.get_contract_themes(contract_text)
                results["component_status"]["summarizer"] = "active"
                logger.info("Contract summarization completed successfully")
            else:
                logger.warning("Contract summarizer not available")
                results["errors"].append("Contract summarizer not available")
                results["summary"] = "Summarization service unavailable"
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            results["errors"].append(f"Summarization failed: {str(e)}")
            results["summary"] = "Summarization failed"
        
        # Component 2: RAG Constitutional Analysis
        try:
            logger.info("Running RAG constitutional analysis...")
            themes = results.get("themes", ["Contract Enforcement"])
            
            # Use first theme for RAG analysis
            primary_theme = themes[0] if themes else "Contract Enforcement"
            rag_result = get_rag_explanation(primary_theme)
            
            if rag_result and "error" not in rag_result.lower():
                results["constitutional_analysis"] = rag_result
                results["component_status"]["rag"] = "active"
                logger.info("RAG analysis completed successfully")
            else:
                logger.warning("RAG service returned error, using fallback")
                results["constitutional_analysis"] = self._fallback_constitutional_analysis(contract_text)
                results["errors"].append("RAG service unavailable, using fallback")
                
        except Exception as e:
            logger.error(f"RAG analysis error: {e}")
            results["errors"].append(f"RAG analysis failed: {str(e)}")
            results["constitutional_analysis"] = self._fallback_constitutional_analysis(contract_text)
        
        # Component 3: IndianLegalBERT Verification
        try:
            if self.bert_model and self.bert_tokenizer:
                logger.info("Running IndianLegalBERT verification...")
                verification_score = self._verify_with_bert(contract_text)
                results["verification_score"] = verification_score
                results["component_status"]["bert"] = "active"
                logger.info("BERT verification completed successfully")
            else:
                logger.warning("IndianLegalBERT not available")
                results["errors"].append("IndianLegalBERT not available")
                results["verification_score"] = "Verification service unavailable"
        except Exception as e:
            logger.error(f"BERT verification error: {e}")
            results["errors"].append(f"BERT verification failed: {str(e)}")
            results["verification_score"] = "Verification failed"
        
        # Calculate processing time
        results["processing_time"] = round(time.time() - start_time, 2)
        logger.info(f"Contract analysis completed in {results['processing_time']} seconds")
        
        return results
    
    def _verify_with_bert(self, contract_text: str) -> str:
        """
        Verify contract using IndianLegalBERT
        
        Args:
            contract_text: Contract text to verify
            
        Returns:
            Verification confidence score
        """
        try:
            # Tokenize input (limit to BERT max length)
            inputs = self.bert_tokenizer(
                contract_text[:512],
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            )
            
            # Get model prediction
            with torch.no_grad():
                outputs = self.bert_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                confidence = torch.max(predictions).item()
            
            # Convert to percentage
            confidence_percentage = round(confidence * 100, 1)
            
            return f"{confidence_percentage}% confidence"
            
        except Exception as e:
            logger.error(f"BERT verification error: {e}")
            return "Verification failed"
    
    def _fallback_constitutional_analysis(self, contract_text: str) -> str:
        """
        Fallback constitutional analysis when RAG is unavailable
        
        Args:
            contract_text: Contract text to analyze
            
        Returns:
            Basic constitutional analysis
        """
        constitutional_aspects = []
        text_lower = contract_text.lower()
        
        # Analyze constitutional relevance
        if any(word in text_lower for word in ["payment", "money", "rupees", "amount", "consideration"]):
            constitutional_aspects.append("Economic rights under Article 19(1)(g) - Right to practice profession")
        
        if any(word in text_lower for word in ["employment", "work", "labor", "service", "employee"]):
            constitutional_aspects.append("Right against exploitation under Articles 23-24")
        
        if any(word in text_lower for word in ["property", "land", "ownership", "title", "possession"]):
            constitutional_aspects.append("Property rights under Article 300A")
        
        if any(word in text_lower for word in ["discrimination", "equality", "equal", "bias"]):
            constitutional_aspects.append("Right to equality under Article 14")
        
        if any(word in text_lower for word in ["freedom", "liberty", "expression", "speech"]):
            constitutional_aspects.append("Fundamental rights under Article 19")
        
        if not constitutional_aspects:
            constitutional_aspects.append("General contract enforcement under Article 19(1)(g)")
        
        return "Constitutional relevance: " + "; ".join(constitutional_aspects)

# Initialize workflow
logger.info("Initializing contract analysis workflow...")
workflow = ContractAnalysisWorkflow()

@app.route('/analyze', methods=['POST'])
def analyze_contract():
    """
    Main analysis endpoint
    Processes contract text through all three components
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            logger.warning("Analysis request missing text data")
            return jsonify({
                "error": "No contract text provided",
                "summary": "Error: No input text",
                "constitutional_analysis": "Error: No input text",
                "verification_score": "Error: No input text"
            }), 400
        
        contract_text = data['text'].strip()
        
        if len(contract_text) < 50:
            logger.warning(f"Contract text too short: {len(contract_text)} characters")
            return jsonify({
                "error": "Contract text too short",
                "summary": "Error: Text too short for analysis",
                "constitutional_analysis": "Error: Text too short for analysis", 
                "verification_score": "Error: Text too short for analysis"
            }), 400
        
        # Run complete analysis
        results = workflow.analyze_contract(contract_text)
        
        # Format response for frontend compatibility
        response = {
            "summary": results.get("summary", "Summary unavailable"),
            "constitutional_analysis": results.get("constitutional_analysis", "Analysis unavailable"),
            "verification_score": results.get("verification_score", "Verification unavailable"),
            "component_status": results.get("component_status", {}),
            "key_terms": results.get("key_terms", {}),
            "themes": results.get("themes", []),
            "errors": results.get("errors", []),
            "processing_time": results.get("processing_time", 0)
        }
        
        logger.info("Analysis completed successfully")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Analysis endpoint error: {e}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            "error": f"Analysis failed: {str(e)}",
            "summary": "Analysis failed due to server error",
            "constitutional_analysis": "Analysis failed due to server error",
            "verification_score": "Analysis failed due to server error"
        }), 500

@app.route('/auto-analyze', methods=['POST'])
def auto_analyze_contract():
    """
    Auto-analysis endpoint for detected contract content
    Same functionality as /analyze but optimized for auto-detection
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "No contract text provided"}), 400
        
        contract_text = data['text'].strip()
        confidence = data.get('confidence', 0)
        
        logger.info(f"Auto-analysis request with {confidence}% confidence")
        
        # Add confidence info to analysis
        results = workflow.analyze_contract(contract_text)
        results['detection_confidence'] = confidence
        results['auto_detected'] = True
        
        # Format response
        response = {
            "summary": results.get("summary", "Summary unavailable"),
            "constitutional_analysis": results.get("constitutional_analysis", "Analysis unavailable"),
            "verification_score": results.get("verification_score", "Verification unavailable"),
            "component_status": results.get("component_status", {}),
            "detection_confidence": confidence,
            "auto_detected": True,
            "processing_time": results.get("processing_time", 0)
        }
        
        logger.info(f"Auto-analysis completed with {confidence}% confidence")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Auto-analysis error: {e}")
        return jsonify({"error": f"Auto-analysis failed: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run"""
    component_status = {
        "summarizer": "active" if workflow.summarizer else "inactive",
        "bert": "active" if workflow.bert_model else "inactive",
        "rag": "unknown"  # RAG status checked dynamically
    }
    
    return jsonify({
        "status": "healthy",
        "components": component_status,
        "project_id": workflow.project_id,
        "message": "GenAI Smart Contract Pro backend is running"
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "service": "GenAI Smart Contract Pro",
        "version": "1.0.0",
        "environment": "production",
        "components": ["Contract Summarizer", "RAG Retriever", "IndianLegalBERT"],
        "endpoints": ["/analyze", "/auto-analyze", "/health"]
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500
    
@app.route('/health', methods=['GET'] )
def health_check():
    return {"status": "healthy", "service": "GenAI Contract Pro"}, 200

@app.route('/', methods=['GET']) 
def root():
    return {"message": "GenAI Smart Contract Pro API", "status": "running"}, 200

# Main execution for Cloud Run
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

    logger.info(f"Starting GenAI Smart Contract Pro backend on port {port}")
    logger.info("Components: Contract Summarizer + RAG Retriever + IndianLegalBERT")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )


