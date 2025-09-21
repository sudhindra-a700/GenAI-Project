"""
Simplified FastAPI Version - GenAI Smart Contract Pro
Focus on Summarization and RAG Constitutional Analysis
"""

from fastapi import FastAPI, HTTPException
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

# Import modular components
from rag_retriever import get_rag_explanation, initialize_rag_services, extract_constitutional_themes_from_contract
from contract_summarizer import ContractSummarizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="GenAI Smart Contract Pro API - Simplified",
    description="AI-powered contract analysis with Vertex AI Summarization and Constitutional Law insights",
    version="3.1.0",
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

class ContractAnalysis(BaseModel):
    summary: str
    constitutional_insights: str
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
    rag: str
    vertexai: str

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    components: ComponentStatus

# Contract Analysis Workflow Class
class ContractAnalysisWorkflow:
    """Simplified production workflow for summarization and RAG analysis"""
    
    def __init__(self):
        self.summarizer = None
        self.rag_services = None
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
        logger.info(f"Initializing simplified workflow for project: {self.project_id}")
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
        
        # Initialize RAG services
        try:
            logger.info("Initializing RAG services...")
            self.rag_services = initialize_rag_services()
            logger.info("RAG services initialized successfully")
        except Exception as e:
            logger.error(f"RAG services initialization failed: {e}")
            self.rag_services = None

        # Log component status
        components_status = {
            "summarizer": "active" if self.summarizer else "inactive",
            "rag": "active" if self.rag_services else "inactive"
        }
        logger.info(f"Component initialization status: {components_status}")
    
    async def analyze_contract(self, contract_text: str) -> Dict[str, Any]:
        """Simplified contract analysis"""
        logger.info(f"Starting contract analysis for text length: {len(contract_text)}")
        
        results = {
            "summary": "Summarizer not available.",
            "constitutional_analysis": "Constitutional analysis not available.",
            "key_terms": {},
            "themes": [],
            "component_status": { "summarizer": "inactive", "rag": "inactive" },
            "errors": []
        }
        
        # 1. Contract Summarization and Theme Extraction
        if self.summarizer:
            try:
                logger.info("Running contract summarization...")
                results["summary"] = self.summarizer.generate_summary(contract_text)
                results["key_terms"] = self.summarizer.extract_key_terms(contract_text)
                results["themes"] = self.summarizer.get_contract_themes(contract_text)
                results["component_status"]["summarizer"] = "active"
                logger.info("Contract summarization completed.")
            except Exception as e:
                error_msg = f"Summarization failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        else:
            # Fallback theme extraction if summarizer fails
            results["themes"] = extract_constitutional_themes_from_contract(contract_text)

        # 2. Constitutional Analysis using RAG
        if self.rag_services:
            try:
                logger.info("Running constitutional analysis...")
                constitutional_insights = []
                embedding_model, generative_model, vector_search_endpoint = self.rag_services
                
                for theme in results["themes"]:
                    explanation = get_rag_explanation(theme, embedding_model, generative_model, vector_search_endpoint)
                    constitutional_insights.append(f"**Theme: {theme}**\n{explanation['explanation']}")
                
                results["constitutional_analysis"] = "\n\n".join(constitutional_insights)
                results["component_status"]["rag"] = "active"
                logger.info("Constitutional analysis completed.")
            except Exception as e:
                error_msg = f"Constitutional analysis failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # 3. Generate comprehensive analysis
        try:
            comprehensive_summary = f"""
CONTRACT ANALYSIS SUMMARY:
{results['summary']}

CONSTITUTIONAL LAW INSIGHTS:
{results['constitutional_analysis']}

KEY TERMS IDENTIFIED:
{', '.join([f"{k}: {v}" for k, v in results.get('key_terms', {}).items()]) if results.get('key_terms') else 'None extracted'}
"""
            results["comprehensive_analysis"] = comprehensive_summary.strip()
        except Exception as e:
            results["errors"].append(f"Comprehensive analysis generation failed: {e}")
        
        logger.info("Contract analysis workflow finished.")
        return results

# Initialize the workflow
workflow = ContractAnalysisWorkflow()

# FastAPI Routes
@app.get("/")
async def root():
    return { "message": "GenAI Smart Contract Pro API - Simplified Version", "status": "running" }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="GenAI Contract Pro Simplified",
        timestamp=datetime.now().isoformat(),
        components=ComponentStatus(
            summarizer="active" if workflow.summarizer else "inactive",
            rag="active" if workflow.rag_services else "inactive",
            vertexai="integrated"
        )
    )

@app.post("/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract_endpoint(request: ContractAnalysisRequest):
    try:
        contract_text = request.text.strip()
        results = await workflow.analyze_contract(contract_text)
        
        key_terms_obj = KeyTerms(**{k.lower().replace(" ", "_"): v for k, v in results.get("key_terms", {}).items() if hasattr(KeyTerms, k.lower().replace(" ", "_"))})

        analysis = ContractAnalysis(
            summary=results.get("summary", "Not available"),
            constitutional_insights=results.get("constitutional_analysis", "Not available"),
            key_terms=key_terms_obj,
            themes=results.get("themes", []),
            comprehensive_analysis=results.get("comprehensive_analysis", "Not available")
        )
        
        return ContractAnalysisResponse(
            success=True,
            timestamp=datetime.now().isoformat(),
            analysis=analysis,
            metadata={
                "text_length": len(contract_text),
                "component_status": results.get("component_status", {}),
                "processing_errors": results.get("errors", [])
            }
        )
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail={"error": "Internal server error", "details": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("main_workflow:app", host="0.0.0.0", port=port, log_level="info", workers=1)
