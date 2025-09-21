"""
Production Main Workflow for GenAI Smart Contract Pro
With IndianLegalBERT verification and law model alternatives
Optimized for Google Cloud Run deployment
"""

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, Any, Optional
import traceback
import sys
import vertexai
from datetime import datetime

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

class LegalModelVerifier:
    """
    Legal model verification using multiple approaches:
    1. IndianLegalBERT (primary)
    2. Vertex AI Legal Analysis (alternative)
    3. Custom legal pattern matching (fallback)
    """
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.indian_legal_bert = None
        self.tokenizer = None
        self.vertex_model = None
        
        # Initialize models with fallback options
        self._initialize_legal_models()
    
    def _initialize_legal_models(self):
        """Initialize legal verification models with multiple options"""
        
        # Option 1: IndianLegalBERT (Primary)
        try:
            logger.info("Initializing IndianLegalBERT...")
            model_name = "law-ai/InLegalBERT"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.indian_legal_bert = AutoModelForSequenceClassification.from_pretrained(model_name)
            logger.info("IndianLegalBERT initialized successfully")
        except Exception as e:
            logger.error(f"IndianLegalBERT initialization failed: {e}")
            self.indian_legal_bert = None
            self.tokenizer = None
        
        # Option 2: Vertex AI Legal Model (Alternative)
        try:
            logger.info("Initializing Vertex AI legal model...")
            vertexai.init(project=self.project_id, location="us-central1")
            from vertexai.language_models import TextGenerationModel
            self.vertex_model = TextGenerationModel.from_pretrained("text-bison")
            logger.info("Vertex AI legal model initialized successfully")
        except Exception as e:
            logger.error(f"Vertex AI legal model initialization failed: {e}")
            self.vertex_model = None
    
    def verify_legal_compliance(self, contract_text: str) -> Dict[str, Any]:
        """
        Verify legal compliance using available models
        """
        results = {
            "compliance_score": 0.0,
            "legal_issues": [],
            "verification_method": "none",
            "confidence": 0.0,
            "recommendations": []
        }
        
        # Method 1: IndianLegalBERT Verification
        if self.indian_legal_bert and self.tokenizer:
            try:
                logger.info("Running IndianLegalBERT verification...")
                
                # Tokenize and analyze
                inputs = self.tokenizer(
                    contract_text[:512],  # Limit to 512 tokens
                    return_tensors="pt",
                    truncation=True,
                    padding=True
                )
                
                with torch.no_grad():
                    outputs = self.indian_legal_bert(**inputs)
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                    
                # Extract compliance score
                compliance_score = float(predictions[0][1])  # Assuming binary classification
                
                results.update({
                    "compliance_score": compliance_score,
                    "verification_method": "IndianLegalBERT",
                    "confidence": compliance_score,
                    "legal_issues": self._extract_legal_issues(contract_text, compliance_score),
                    "recommendations": self._generate_recommendations(compliance_score)
                })
                
                logger.info(f"IndianLegalBERT verification completed: {compliance_score:.3f}")
                return results
                
            except Exception as e:
                logger.error(f"IndianLegalBERT verification failed: {e}")
        
        # Method 2: Vertex AI Legal Analysis (Alternative)
        if self.vertex_model:
            try:
                logger.info("Running Vertex AI legal verification...")
                
                legal_prompt = f"""
                Analyze this contract for legal compliance and potential issues:
                
                Contract: {contract_text[:2000]}
                
                Provide:
                1. Compliance score (0.0 to 1.0)
                2. Specific legal issues found
                3. Recommendations for improvement
                4. Constitutional law considerations for Indian contracts
                
                Format as structured analysis.
                """
                
                response = self.vertex_model.predict(
                    legal_prompt,
                    max_output_tokens=1024,
                    temperature=0.2
                )
                
                # Parse Vertex AI response
                analysis = response.text
                compliance_score = self._extract_score_from_text(analysis)
                
                results.update({
                    "compliance_score": compliance_score,
                    "verification_method": "Vertex AI Legal Analysis",
                    "confidence": 0.8,  # High confidence in Vertex AI
                    "legal_issues": self._extract_issues_from_text(analysis),
                    "recommendations": self._extract_recommendations_from_text(analysis),
                    "detailed_analysis": analysis
                })
                
                logger.info(f"Vertex AI legal verification completed: {compliance_score:.3f}")
                return results
                
            except Exception as e:
                logger.error(f"Vertex AI legal verification failed: {e}")
        
        # Method 3: Pattern-based Legal Analysis (Fallback)
        logger.info("Running pattern-based legal verification...")
        results = self._pattern_based_verification(contract_text)
        results["verification_method"] = "Pattern-based Analysis"
        
        return results
    
    def _extract_legal_issues(self, text: str, score: float) -> list:
        """Extract legal issues based on compliance score and text analysis"""
        issues = []
        
        if score < 0.5:
            issues.append("Low legal compliance detected")
        if score < 0.3:
            issues.append("Critical legal issues may be present")
        
        # Pattern-based issue detection
        text_lower = text.lower()
        if "termination" in text_lower and "notice" not in text_lower:
            issues.append("Termination clause lacks proper notice requirements")
        if "salary" in text_lower and "minimum wage" not in text_lower:
            issues.append("Salary terms should reference minimum wage compliance")
        if "confidentiality" in text_lower and "duration" not in text_lower:
            issues.append("Confidentiality clause lacks duration specification")
        
        return issues
    
    def _generate_recommendations(self, score: float) -> list:
        """Generate recommendations based on compliance score"""
        recommendations = []
        
        if score < 0.7:
            recommendations.append("Review contract with legal counsel")
            recommendations.append("Ensure compliance with Indian Contract Act 1872")
        if score < 0.5:
            recommendations.append("Major revisions needed for legal compliance")
            recommendations.append("Add constitutional law compliance clauses")
        
        recommendations.append("Verify alignment with latest labor law amendments")
        return recommendations
    
    def _extract_score_from_text(self, text: str) -> float:
        """Extract compliance score from Vertex AI response"""
        import re
        
        # Look for score patterns
        score_patterns = [
            r'compliance score[:\s]*([0-9]*\.?[0-9]+)',
            r'score[:\s]*([0-9]*\.?[0-9]+)',
            r'([0-9]*\.?[0-9]+)/1\.0',
            r'([0-9]*\.?[0-9]+)\s*out of\s*1'
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    score = float(match.group(1))
                    return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
                except ValueError:
                    continue
        
        # Default score based on text sentiment
        if "compliant" in text.lower() or "good" in text.lower():
            return 0.75
        elif "issues" in text.lower() or "problems" in text.lower():
            return 0.4
        else:
            return 0.6
    
    def _extract_issues_from_text(self, text: str) -> list:
        """Extract legal issues from Vertex AI response"""
        issues = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['issue', 'problem', 'concern', 'violation']):
                if len(line) > 10:  # Avoid very short lines
                    issues.append(line)
        
        return issues[:5]  # Limit to top 5 issues
    
    def _extract_recommendations_from_text(self, text: str) -> list:
        """Extract recommendations from Vertex AI response"""
        recommendations = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider']):
                if len(line) > 10:
                    recommendations.append(line)
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _pattern_based_verification(self, text: str) -> Dict[str, Any]:
        """Fallback pattern-based legal verification"""
        text_lower = text.lower()
        
        # Basic legal compliance checks
        compliance_factors = []
        
        # Check for essential contract elements
        if any(term in text_lower for term in ['party', 'parties', 'between']):
            compliance_factors.append(0.2)  # Parties identified
        
        if any(term in text_lower for term in ['consideration', 'payment', 'salary', 'amount']):
            compliance_factors.append(0.2)  # Consideration present
        
        if any(term in text_lower for term in ['term', 'duration', 'period']):
            compliance_factors.append(0.15)  # Duration specified
        
        if any(term in text_lower for term in ['obligation', 'duty', 'responsibility']):
            compliance_factors.append(0.15)  # Obligations defined
        
        if any(term in text_lower for term in ['termination', 'end', 'expiry']):
            compliance_factors.append(0.1)  # Termination clause
        
        # Calculate compliance score
        base_score = sum(compliance_factors)
        compliance_score = min(base_score + 0.2, 1.0)  # Add base compliance
        
        return {
            "compliance_score": compliance_score,
            "confidence": 0.6,  # Medium confidence for pattern-based
            "legal_issues": ["Pattern-based analysis - limited detail available"],
            "recommendations": [
                "Use advanced legal AI models for detailed analysis",
                "Consult legal counsel for comprehensive review"
            ]
        }

class ContractAnalysisWorkflow:
    """
    Enhanced production workflow with legal model verification
    """
    
    def __init__(self):
        """Initialize all components with production settings"""
        self.summarizer = None
        self.legal_verifier = None
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
        logger.info(f"Initializing enhanced workflow for project: {self.project_id}")
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
        
        # Initialize legal verifier
        try:
            logger.info("Initializing legal verifier...")
            self.legal_verifier = LegalModelVerifier(project_id=self.project_id)
            logger.info("Legal verifier initialized successfully")
        except Exception as e:
            logger.error(f"Legal verifier initialization failed: {e}")
            self.legal_verifier = None
        
        # Log component status
        components_status = {
            "summarizer": "active" if self.summarizer else "inactive",
            "legal_verifier": "active" if self.legal_verifier else "inactive",
            "rag": "active"
        }
        logger.info(f"Enhanced component initialization complete: {components_status}")
    
    def analyze_contract(self, contract_text: str) -> Dict[str, Any]:
        """
        Complete contract analysis with legal verification
        """
        logger.info(f"Starting enhanced contract analysis for text length: {len(contract_text)}")
        
        results = {
            "summary": None,
            "constitutional_analysis": None,
            "legal_verification": None,
            "key_terms": None,
            "themes": None,
            "component_status": {
                "summarizer": "inactive",
                "legal_verifier": "inactive",
                "rag": "inactive"
            },
            "errors": []
        }
        
        # 1. Contract Summarization using Vertex AI
        if self.summarizer:
            try:
                logger.info("Running contract summarization...")
                summary_result = self.summarizer.summarize_contract(contract_text)
                results["summary"] = summary_result.get("summary", "Summary not available")
                results["key_terms"] = summary_result.get("key_terms", {})
                results["themes"] = summary_result.get("themes", [])
                results["component_status"]["summarizer"] = "active"
                logger.info("Contract summarization completed successfully")
            except Exception as e:
                error_msg = f"Summarization failed: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["summary"] = "Contract summarization temporarily unavailable"
        
        # 2. Legal Verification using IndianLegalBERT or alternatives
        if self.legal_verifier:
            try:
                logger.info("Running legal verification...")
                verification_result = self.legal_verifier.verify_legal_compliance(contract_text)
                results["legal_verification"] = verification_result
                results["component_status"]["legal_verifier"] = "active"
                logger.info(f"Legal verification completed: {verification_result['verification_method']}")
            except Exception as e:
                error_msg = f"Legal verification failed: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["legal_verification"] = {"error": "Legal verification temporarily unavailable"}
        
        # 3. Constitutional Analysis using RAG
        try:
            logger.info("Running constitutional analysis...")
            constitutional_result = get_rag_explanation(contract_text)
            results["constitutional_analysis"] = constitutional_result
            results["component_status"]["rag"] = "active"
            logger.info("Constitutional analysis completed successfully")
        except Exception as e:
            error_msg = f"Constitutional analysis failed: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["constitutional_analysis"] = "Constitutional analysis temporarily unavailable"
        
        logger.info("Enhanced contract analysis workflow completed")
        return results

# Initialize the enhanced workflow
workflow = ContractAnalysisWorkflow()

# Flask Routes
@app.route('/')
def root():
    """Root endpoint to verify service is running"""
    return jsonify({
        "message": "GenAI Smart Contract Pro API - Enhanced with Legal Verification",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": ["/", "/health", "/analyze", "/status"],
        "features": ["Contract Summarization", "Legal Verification", "Constitutional Analysis"],
        "version": "2.1.0"
    })

@app.route('/health')
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({
        "status": "healthy",
        "service": "GenAI Contract Pro Enhanced",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "summarizer": "active" if workflow.summarizer else "inactive",
            "legal_verifier": "active" if workflow.legal_verifier else "inactive",
            "rag": "active",
            "vertexai": "integrated"
        }
    })

@app.route('/analyze', methods=['POST'])
def analyze_contract_endpoint():
    """
    Enhanced contract analysis endpoint with legal verification
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        contract_text = data.get('text', '').strip()
        
        if not contract_text:
            return jsonify({"error": "No contract text provided"}), 400
        
        if len(contract_text) < 10:
            return jsonify({"error": "Contract text too short for analysis"}), 400
        
        # Perform enhanced analysis
        logger.info(f"Received enhanced analysis request for {len(contract_text)} characters")
        results = workflow.analyze_contract(contract_text)
        
        # Format enhanced response
        response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "summary": results.get("summary", "Not available"),
                "constitutional_insights": results.get("constitutional_analysis", "Not available"),
                "legal_verification": results.get("legal_verification", {}),
                "key_terms": results.get("key_terms", {}),
                "themes": results.get("themes", [])
            },
            "metadata": {
                "text_length": len(contract_text),
                "component_status": results.get("component_status", {}),
                "processing_errors": results.get("errors", []),
                "verification_method": results.get("legal_verification", {}).get("verification_method", "none")
            }
        }
        
        logger.info("Enhanced analysis completed successfully")
        return jsonify(response)
        
    except Exception as e:
        error_msg = f"Enhanced analysis endpoint error: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        return jsonify({
            "success": False,
            "error": "Internal server error during enhanced analysis",
            "timestamp": datetime.now().isoformat(),
            "details": str(e) if app.debug else "Contact support for assistance"
        }), 500

@app.route('/status', methods=['GET'])
def status_endpoint():
    """Detailed status endpoint for monitoring"""
    try:
        legal_verifier_status = "inactive"
        verification_method = "none"
        
        if workflow.legal_verifier:
            legal_verifier_status = "active"
            if workflow.legal_verifier.indian_legal_bert:
                verification_method = "IndianLegalBERT"
            elif workflow.legal_verifier.vertex_model:
                verification_method = "Vertex AI Legal"
            else:
                verification_method = "Pattern-based"
        
        return jsonify({
            "service": "GenAI Smart Contract Pro Enhanced",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "flask": "active",
                "contract_summarizer": "active" if workflow.summarizer else "inactive",
                "legal_verifier": legal_verifier_status,
                "verification_method": verification_method,
                "rag_retriever": "active",
                "vertexai": "integrated"
            },
            "environment": {
                "project_id": workflow.project_id,
                "python_version": sys.version.split()[0],
                "flask_version": Flask.__version__,
                "torch_available": torch.cuda.is_available() if 'torch' in sys.modules else False
            }
        })
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({
            "service": "GenAI Smart Contract Pro Enhanced",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

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

# Main execution
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting GenAI Contract Pro Enhanced on port {port}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info(f"Project ID: {workflow.project_id}")
    
    app.run(
        host="0.0.0.0", 
        port=port, 
        debug=debug_mode,
        threaded=True
    )
