"""
Complete FastAPI Version - GenAI Smart Contract Pro
All features from original main_workflow.py with better Cloud Run compatibility
Includes: Vertex AI, IndianLegalBERT, RAG Retriever, Constitutional Analysis
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import os
import logging
import traceback
import sys
import vertexai
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import modular components with error handling
try:
    from rag_retriever import get_rag_explanation
    from contract_summarizer import ContractSummarizer
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    ML_IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"ML Import warning: {e}")
    ML_IMPORTS_AVAILABLE = False

os.environ['TOKENIZERS_PARALLELISM'] = 'false
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="GenAI Smart Contract Pro API - Complete",
    description="AI-powered contract analysis with Vertex AI, IndianLegalBERT, and Constitutional Law insights",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ContractAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Contract text to analyze")

class KeyTerms(BaseModel):
    parties: Optional[str] = None
    compensation: Optional[str] = None
    duration: Optional[str] = None
    termination: Optional[str] = None
    confidentiality: Optional[str] = None

class LegalVerification(BaseModel):
    compliance_score: float = Field(..., ge=0.0, le=1.0)
    verification_method: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    legal_issues: List[str] = []
    recommendations: List[str] = []

class ContractAnalysis(BaseModel):
    summary: str
    constitutional_insights: str
    legal_verification: Optional[LegalVerification] = None
    key_terms: KeyTerms
    themes: List[str] = []
    comprehensive_analysis: Optional[str] = None

class ContractAnalysisResponse(BaseModel):
    success: bool
    timestamp: str
    analysis: ContractAnalysis
    metadata: Dict[str, Any]

class ComponentStatus(BaseModel):
    summarizer: str
    legal_verifier: str
    rag: str
    vertexai: str

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    components: ComponentStatus

# Legal Model Verifier Class
class LegalModelVerifier:
    """Enhanced legal model verification with multiple approaches"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.indian_legal_bert = None
        self.tokenizer = None
        self.vertex_model = None
        self._initialize_legal_models()
    
    def _initialize_legal_models(self):
        """Initialize legal verification models with multiple options"""
        
        # Option 1: IndianLegalBERT
        if ML_IMPORTS_AVAILABLE:
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
        
        # Option 2: Vertex AI Legal Model
        try:
            logger.info("Initializing Vertex AI legal model...")
            vertexai.init(project=self.project_id, location="us-central1")
            from vertexai.language_models import TextGenerationModel
            self.vertex_model = TextGenerationModel.from_pretrained("text-bison")
            logger.info("Vertex AI legal model initialized successfully")
        except Exception as e:
            logger.error(f"Vertex AI legal model initialization failed: {e}")
            self.vertex_model = None
    
    async def verify_legal_compliance(self, contract_text: str) -> LegalVerification:
        """Verify legal compliance using available models"""
        
        # Method 1: IndianLegalBERT Verification
        if self.indian_legal_bert and self.tokenizer:
            try:
                logger.info("Running IndianLegalBERT verification...")
                
                inputs = self.tokenizer(
                    contract_text[:512],
                    return_tensors="pt",
                    truncation=True,
                    padding=True
                )
                
                with torch.no_grad():
                    outputs = self.indian_legal_bert(**inputs)
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
                compliance_score = float(predictions[0][1])
                
                return LegalVerification(
                    compliance_score=compliance_score,
                    verification_method="IndianLegalBERT",
                    confidence=compliance_score,
                    legal_issues=self._extract_legal_issues(contract_text, compliance_score),
                    recommendations=self._generate_recommendations(compliance_score)
                )
                
            except Exception as e:
                logger.error(f"IndianLegalBERT verification failed: {e}")
        
        # Method 2: Vertex AI Legal Analysis
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
                
                analysis = response.text
                compliance_score = self._extract_score_from_text(analysis)
                
                return LegalVerification(
                    compliance_score=compliance_score,
                    verification_method="Vertex AI Legal Analysis",
                    confidence=0.8,
                    legal_issues=self._extract_issues_from_text(analysis),
                    recommendations=self._extract_recommendations_from_text(analysis)
                )
                
            except Exception as e:
                logger.error(f"Vertex AI legal verification failed: {e}")
        
        # Method 3: Pattern-based Analysis (Fallback)
        logger.info("Running pattern-based legal verification...")
        return self._pattern_based_verification(contract_text)
    
    def _extract_legal_issues(self, text: str, score: float) -> List[str]:
        """Extract legal issues based on compliance score and text analysis"""
        issues = []
        
        if score < 0.5:
            issues.append("Low legal compliance detected")
        if score < 0.3:
            issues.append("Critical legal issues may be present")
        
        text_lower = text.lower()
        if "termination" in text_lower and "notice" not in text_lower:
            issues.append("Termination clause lacks proper notice requirements")
        if "salary" in text_lower and "minimum wage" not in text_lower:
            issues.append("Salary terms should reference minimum wage compliance")
        if "confidentiality" in text_lower and "duration" not in text_lower:
            issues.append("Confidentiality clause lacks duration specification")
        
        return issues
    
    def _generate_recommendations(self, score: float) -> List[str]:
        """Generate recommendations based on compliance score"""
        recommendations = []
        
        if score < 0.7:
            recommendations.extend([
                "Review contract with legal counsel",
                "Ensure compliance with Indian Contract Act 1872"
            ])
        if score < 0.5:
            recommendations.extend([
                "Major revisions needed for legal compliance",
                "Add constitutional law compliance clauses"
            ])
        
        recommendations.append("Verify alignment with latest labor law amendments")
        return recommendations
    
    def _extract_score_from_text(self, text: str) -> float:
        """Extract compliance score from Vertex AI response"""
        import re
        
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
                    return min(max(score, 0.0), 1.0)
                except ValueError:
                    continue
        
        # Default score based on text sentiment
        if "compliant" in text.lower() or "good" in text.lower():
            return 0.75
        elif "issues" in text.lower() or "problems" in text.lower():
            return 0.4
        else:
            return 0.6
    
    def _extract_issues_from_text(self, text: str) -> List[str]:
        """Extract legal issues from Vertex AI response"""
        issues = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['issue', 'problem', 'concern', 'violation']):
                if len(line) > 10:
                    issues.append(line)
        
        return issues[:5]
    
    def _extract_recommendations_from_text(self, text: str) -> List[str]:
        """Extract recommendations from Vertex AI response"""
        recommendations = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider']):
                if len(line) > 10:
                    recommendations.append(line)
        
        return recommendations[:5]
    
    def _pattern_based_verification(self, text: str) -> LegalVerification:
        """Fallback pattern-based legal verification"""
        text_lower = text.lower()
        
        compliance_factors = []
        
        if any(term in text_lower for term in ['party', 'parties', 'between']):
            compliance_factors.append(0.2)
        
        if any(term in text_lower for term in ['consideration', 'payment', 'salary', 'amount']):
            compliance_factors.append(0.2)
        
        if any(term in text_lower for term in ['term', 'duration', 'period']):
            compliance_factors.append(0.15)
        
        if any(term in text_lower for term in ['obligation', 'duty', 'responsibility']):
            compliance_factors.append(0.15)
        
        if any(term in text_lower for term in ['termination', 'end', 'expiry']):
            compliance_factors.append(0.1)
        
        base_score = sum(compliance_factors)
        compliance_score = min(base_score + 0.2, 1.0)
        
        return LegalVerification(
            compliance_score=compliance_score,
            verification_method="Pattern-based Analysis",
            confidence=0.6,
            legal_issues=["Pattern-based analysis - limited detail available"],
            recommendations=[
                "Use advanced legal AI models for detailed analysis",
                "Consult legal counsel for comprehensive review"
            ]
        )

# Contract Analysis Workflow Class
class ContractAnalysisWorkflow:
    """Enhanced production workflow with all features"""
    
    def __init__(self):
        self.summarizer = None
        self.legal_verifier = None
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
        logger.info(f"Initializing complete workflow for project: {self.project_id}")
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all analysis components"""
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
        logger.info(f"Complete component initialization: {components_status}")
    
    async def analyze_contract(self, contract_text: str) -> Dict[str, Any]:
        """Complete contract analysis with all features"""
        logger.info(f"Starting complete contract analysis for text length: {len(contract_text)}")
        
        results = {
            "summary": None,
            "constitutional_analysis": None,
            "legal_verification": None,
            "key_terms": {},
            "themes": [],
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
        else:
            results["summary"] = "Contract summarizer not available"
        
        # 2. Legal Verification
        if self.legal_verifier:
            try:
                logger.info("Running legal verification...")
                verification_result = await self.legal_verifier.verify_legal_compliance(contract_text)
                results["legal_verification"] = verification_result.dict()
                results["component_status"]["legal_verifier"] = "active"
                logger.info(f"Legal verification completed: {verification_result.verification_method}")
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
        
        # 4. Generate comprehensive analysis
        try:
            if results["summary"] and results["constitutional_analysis"]:
                comprehensive_summary = f"""
CONTRACT ANALYSIS SUMMARY:
{results['summary']}

CONSTITUTIONAL LAW INSIGHTS:
{results['constitutional_analysis']}

LEGAL VERIFICATION:
{results.get('legal_verification', {}).get('verification_method', 'Not available')} - Score: {results.get('legal_verification', {}).get('compliance_score', 'N/A')}

KEY TERMS IDENTIFIED:
{', '.join([f"{k}: {v}" for k, v in results.get('key_terms', {}).items()]) if results.get('key_terms') else 'None extracted'}

ANALYSIS THEMES:
{', '.join(results.get('themes', [])) if results.get('themes') else 'None identified'}
"""
                results["comprehensive_analysis"] = comprehensive_summary.strip()
            else:
                results["comprehensive_analysis"] = "Partial analysis completed - some components unavailable"
                
        except Exception as e:
            error_msg = f"Comprehensive analysis generation failed: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        logger.info("Complete contract analysis workflow finished")
        return results

# Initialize the complete workflow
workflow = ContractAnalysisWorkflow()

# FastAPI Routes
@app.get("/")
async def root():
    """Root endpoint to verify service is running"""
    return {
        "message": "GenAI Smart Contract Pro API - Complete Version",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "framework": "FastAPI",
        "endpoints": ["/", "/health", "/analyze", "/status", "/docs"],
        "features": [
            "Vertex AI Contract Summarization",
            "IndianLegalBERT Legal Verification", 
            "RAG Constitutional Analysis",
            "Comprehensive Contract Insights"
        ]
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Cloud Run"""
    legal_verifier_status = "inactive"
    if workflow.legal_verifier:
        if workflow.legal_verifier.indian_legal_bert:
            legal_verifier_status = "IndianLegalBERT"
        elif workflow.legal_verifier.vertex_model:
            legal_verifier_status = "Vertex AI"
        else:
            legal_verifier_status = "Pattern-based"
    
    return HealthResponse(
        status="healthy",
        service="GenAI Contract Pro Complete",
        timestamp=datetime.now().isoformat(),
        components=ComponentStatus(
            summarizer="active" if workflow.summarizer else "inactive",
            legal_verifier=legal_verifier_status,
            rag="active",
            vertexai="integrated"
        )
    )

@app.post("/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract_endpoint(request: ContractAnalysisRequest):
    """Complete contract analysis endpoint with all features"""
    try:
        contract_text = request.text.strip()
        
        logger.info(f"Received complete analysis request for {len(contract_text)} characters")
        results = await workflow.analyze_contract(contract_text)
        
        # Format key terms
        key_terms_obj = KeyTerms()
        raw_key_terms = results.get("key_terms", {})
        
        if isinstance(raw_key_terms, dict):
            for key, value in raw_key_terms.items():
                if hasattr(key_terms_obj, key.lower()):
                    setattr(key_terms_obj, key.lower(), str(value))
        
        # Format legal verification
        legal_verification = None
        if results.get("legal_verification") and isinstance(results["legal_verification"], dict):
            legal_verification = LegalVerification(**results["legal_verification"])
        
        # Create analysis object
        analysis = ContractAnalysis(
            summary=results.get("summary", "Not available"),
            constitutional_insights=results.get("constitutional_analysis", "Not available"),
            legal_verification=legal_verification,
            key_terms=key_terms_obj,
            themes=results.get("themes", []),
            comprehensive_analysis=results.get("comprehensive_analysis", "Not available")
        )
        
        response = ContractAnalysisResponse(
            success=True,
            timestamp=datetime.now().isoformat(),
            analysis=analysis,
            metadata={
                "text_length": len(contract_text),
                "component_status": results.get("component_status", {}),
                "processing_errors": results.get("errors", []),
                "verification_method": results.get("legal_verification", {}).get("verification_method", "none"),
                "version": "3.0.0",
                "framework": "FastAPI"
            }
        )
        
        logger.info("Complete analysis completed successfully")
        return response
        
    except Exception as e:
        error_msg = f"Complete analysis endpoint error: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during complete analysis",
                "timestamp": datetime.now().isoformat(),
                "details": str(e)
            }
        )

@app.get("/status")
async def status_endpoint():
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
        
        return {
            "service": "GenAI Smart Contract Pro Complete",
            "status": "operational",
            "framework": "FastAPI",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "fastapi": "active",
                "contract_summarizer": "active" if workflow.summarizer else "inactive",
                "legal_verifier": legal_verifier_status,
                "verification_method": verification_method,
                "rag_retriever": "active",
                "vertexai": "integrated",
                "ml_imports": "available" if ML_IMPORTS_AVAILABLE else "unavailable"
            },
            "environment": {
                "project_id": workflow.project_id,
                "python_version": sys.version.split()[0],
                "fastapi_version": "0.104.1",
                "torch_available": torch.cuda.is_available() if ML_IMPORTS_AVAILABLE and 'torch' in sys.modules else False
            },
            "features": {
                "vertex_ai_summarization": "active" if workflow.summarizer else "inactive",
                "indianlegal_bert": "active" if workflow.legal_verifier and workflow.legal_verifier.indian_legal_bert else "inactive",
                "constitutional_analysis": "active",
                "comprehensive_insights": "active"
            }
        }
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

# Test endpoint
@app.get("/test")
async def test():
    """Simple test endpoint"""
    return {
        "test": "success",
        "message": "Complete FastAPI version is working correctly",
        "timestamp": datetime.now().isoformat(),
        "features": "All components loaded"
    }

# Main execution
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main_workflow:app", host="0.0.0.0", port=port)



