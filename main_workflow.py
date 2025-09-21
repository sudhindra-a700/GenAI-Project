"""
Main Workflow for GenAI Smart Contract Pro
Integrates RAG retriever, contract summarizer, and IndianLegalBERT verification
Modular architecture with separate components
"""

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, Any, Optional
import traceback

# Import modular components
from rag_retriever import get_rag_explanation
from contract_summarizer import ContractSummarizer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

class ContractAnalysisWorkflow:
    """
    Main workflow orchestrating all three components:
    1. Contract Summarizer (new modular component)
    2. RAG Retriever (existing modular component) 
    3. IndianLegalBERT Verification
    """
    
    def __init__(self):
        """Initialize all components"""
        self.summarizer = None
        self.bert_model = None
        self.bert_tokenizer = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all analysis components"""
        try:
            # Initialize contract summarizer
            logger.info("Initializing contract summarizer...")
            self.summarizer = ContractSummarizer()
            
            # Initialize IndianLegalBERT
            logger.info("Initializing IndianLegalBERT...")
            model_name = "law-ai/InLegalBERT"
            self.bert_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.bert_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            # Continue with partial functionality
    
    def analyze_contract(self, contract_text: str) -> Dict[str, Any]:
        """
        Complete contract analysis using all three components
        
        Args:
            contract_text: Full contract text
            
        Returns:
            Comprehensive analysis results
        """
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
            "errors": []
        }
        
        # Component 1: Contract Summarization
        try:
            if self.summarizer:
                logger.info("Running contract summarization...")
                results["summary"] = self.summarizer.generate_summary(contract_text)
                results["key_terms"] = self.summarizer.extract_key_terms(contract_text)
                results["themes"] = self.summarizer.get_contract_themes(contract_text)
                results["component_status"]["summarizer"] = "active"
                logger.info("Contract summarization completed")
            else:
                results["errors"].append("Contract summarizer not available")
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            results["errors"].append(f"Summarization failed: {str(e)}")
            results["summary"] = "Summarization unavailable"
        
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
                logger.info("RAG analysis completed")
            else:
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
                logger.info("BERT verification completed")
            else:
                results["errors"].append("IndianLegalBERT not available")
        except Exception as e:
            logger.error(f"BERT verification error: {e}")
            results["errors"].append(f"BERT verification failed: {str(e)}")
            results["verification_score"] = "Verification unavailable"
        
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
            # Tokenize input
            inputs = self.bert_tokenizer(
                contract_text[:512],  # Limit to BERT max length
                return_tensors="pt",
                truncation=True,
                padding=True
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
        # Simple keyword-based analysis
        constitutional_aspects = []
        
        text_lower = contract_text.lower()
        
        if any(word in text_lower for word in ["payment", "money", "rupees", "amount"]):
            constitutional_aspects.append("Economic rights under Article 19(1)(g)")
        
        if any(word in text_lower for word in ["employment", "work", "labor", "service"]):
            constitutional_aspects.append("Right against exploitation under Article 23-24")
        
        if any(word in text_lower for word in ["property", "land", "ownership"]):
            constitutional_aspects.append("Property rights under Article 300A")
        
        if any(word in text_lower for word in ["discrimination", "equality", "equal"]):
            constitutional_aspects.append("Right to equality under Article 14")
        
        if not constitutional_aspects:
            constitutional_aspects.append("General contract enforcement under Article 19(1)(g)")
        
        return "Constitutional aspects: " + "; ".join(constitutional_aspects)

# Initialize workflow
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
            return jsonify({
                "error": "No contract text provided",
                "summary": "Error: No input text",
                "constitutional_analysis": "Error: No input text",
                "verification_score": "Error: No input text"
            }), 400
        
        contract_text = data['text'].strip()
        
        if len(contract_text) < 50:
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
            "errors": results.get("errors", [])
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
            "auto_detected": True
        }
        
        logger.info(f"Auto-analysis completed with {confidence}% confidence")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Auto-analysis error: {e}")
        return jsonify({"error": f"Auto-analysis failed: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    component_status = {
        "summarizer": "active" if workflow.summarizer else "inactive",
        "bert": "active" if workflow.bert_model else "inactive",
        "rag": "unknown"  # RAG status checked dynamically
    }
    
    return jsonify({
        "status": "healthy",
        "components": component_status,
        "message": "GenAI Smart Contract Pro backend is running"
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "service": "GenAI Smart Contract Pro",
        "version": "1.0.0",
        "components": ["Contract Summarizer", "RAG Retriever", "IndianLegalBERT"],
        "endpoints": ["/analyze", "/auto-analyze", "/health"]
    })

if __name__ == '__main__':
    logger.info("Starting GenAI Smart Contract Pro backend...")
    logger.info("Components: Contract Summarizer + RAG Retriever + IndianLegalBERT")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
