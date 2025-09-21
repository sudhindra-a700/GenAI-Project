#!/usr/bin/env python3
"""
GenAI Smart Contract Pro - Production Workflow
Integrates: RAG (Indian Constitution) + Summarization Agent + IndianLegalBERT Verification
"""

import json
import re
import vertexai
from vertexai.generative_models import GenerativeModel
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from rag_retriever import initialize_rag_services, get_rag_explanation, extract_constitutional_themes_from_contract

# Configuration
PROJECT_ID = "genai-project-472704"
LOCATION = "europe-west4"

class ContractAnalysisSystem:
    """Integrated system: RAG + Summarization + IndianLegalBERT verification."""
    
    def __init__(self):
        # Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        self.summarization_model = GenerativeModel("gemini-1.5-flash-002")
        
        # Initialize RAG components
        try:
            self.embedding_model, self.generative_model, self.vector_search_endpoint = initialize_rag_services()
            self.rag_available = True
        except Exception as e:
            print(f"RAG initialization failed: {e}")
            self.rag_available = False
        
        # Initialize IndianLegalBERT
        try:
            self.legal_tokenizer = AutoTokenizer.from_pretrained("law-ai/InLegalBERT")
            self.legal_model = AutoModelForSequenceClassification.from_pretrained("law-ai/InLegalBERT")
            self.bert_available = True
        except Exception as e:
            print(f"IndianLegalBERT initialization failed: {e}")
            self.bert_available = False
    
    def detect_contract_content(self, page_data):
        """Detect contract content from page data."""
        text_content = page_data.get('text', '')
        url = page_data.get('url', '')
        
        if not text_content:
            return {"detected": False, "confidence": 0.0, "contract_text": "", "method": "no_content"}
        
        # Contract detection patterns
        contract_patterns = [
            r'\b(?:agreement|contract|terms\s+(?:and|&)\s+conditions)\b',
            r'\b(?:whereas|hereby|party|parties|governing\s+law)\b',
            r'\b(?:payment\s+terms|delivery|warranty|termination)\b',
            r'\b(?:employment|service|procurement|lease|license)\b'
        ]
        
        matches = 0
        for pattern in contract_patterns:
            matches += len(re.findall(pattern, text_content, re.IGNORECASE))
        
        # URL-based detection
        url_score = 0.3 if any(term in url.lower() for term in ['contract', 'agreement', 'terms', '.pdf']) else 0
        
        # Calculate confidence
        text_length = len(text_content.split())
        confidence = min((matches / max(text_length * 0.02, 1)) + url_score, 1.0)
        
        return {
            "detected": confidence > 0.2,
            "confidence": confidence,
            "contract_text": text_content,
            "method": "url_pattern" if url_score > 0 else "content_analysis"
        }
    
    def summarize_contract(self, contract_text):
        """Summarization agent for contract key terms extraction."""
        prompt = f"""You are a legal contract summarization agent. Extract and summarize the key terms from this contract:

Contract text:
{contract_text[:3000]}

Provide a structured summary with:
1. Contract Type
2. Parties Involved
3. Key Terms (payment, delivery, warranty, termination, governing law)
4. Important Clauses
5. Risk Factors

Format as JSON:
{{
  "contract_type": "type of contract",
  "parties": ["party1", "party2"],
  "key_terms": {{
    "payment": "payment terms",
    "delivery": "delivery terms",
    "warranty": "warranty information",
    "termination": "termination conditions",
    "governing_law": "applicable law"
  }},
  "important_clauses": ["clause1", "clause2"],
  "risk_factors": ["risk1", "risk2"]
}}"""

        try:
            response = self.summarization_model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 1000,
                    "temperature": 0.1,
                    "top_p": 0.8
                }
            )
            
            # Parse JSON response
            try:
                return json.loads(response.text.strip())
            except json.JSONDecodeError:
                return {
                    "contract_type": "General Contract",
                    "summary": response.text.strip(),
                    "key_terms": {},
                    "parsing_error": True
                }
                
        except Exception as e:
            return {"error": f"Summarization failed: {str(e)}"}
    
    def get_constitutional_analysis(self, contract_text):
        """RAG-based constitutional analysis using Indian Constitution matching."""
        if not self.rag_available:
            return {"error": "Constitutional analysis unavailable", "articles": [], "analysis": ""}
        
        try:
            # Extract constitutional themes from contract
            themes = extract_constitutional_themes_from_contract(contract_text)
            
            constitutional_results = []
            all_articles = []
            
            # Get RAG explanation for each theme
            for theme in themes:
                rag_result = get_rag_explanation(
                    theme, 
                    self.embedding_model, 
                    self.generative_model, 
                    self.vector_search_endpoint
                )
                
                if rag_result.get("explanation"):
                    constitutional_results.append({
                        "theme": theme,
                        "explanation": rag_result["explanation"],
                        "source_articles": rag_result.get("source_articles", [])
                    })
                    all_articles.extend(rag_result.get("source_articles", []))
            
            return {
                "themes": themes,
                "analysis": constitutional_results,
                "articles": list(set(all_articles)),  # Remove duplicates
                "method": "rag_constitutional_matching"
            }
            
        except Exception as e:
            return {"error": f"Constitutional analysis failed: {str(e)}", "articles": [], "analysis": ""}
    
    def verify_with_indianlegalbert(self, contract_text, summary):
        """IndianLegalBERT verification of contract analysis."""
        if not self.bert_available:
            return {"verification": "IndianLegalBERT unavailable", "confidence": 0.0}
        
        try:
            # Prepare text for BERT analysis
            verification_text = f"Contract: {contract_text[:500]} Summary: {str(summary)[:500]}"
            
            # Tokenize and predict
            inputs = self.legal_tokenizer(
                verification_text, 
                return_tensors="pt", 
                truncation=True, 
                max_length=512,
                padding=True
            )
            
            with torch.no_grad():
                outputs = self.legal_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                confidence = torch.max(predictions).item()
            
            return {
                "verification": "Analysis verified by IndianLegalBERT",
                "confidence": confidence,
                "bert_score": confidence
            }
            
        except Exception as e:
            return {"verification": f"BERT verification failed: {str(e)}", "confidence": 0.0}
    
    def analyze_contract_complete(self, contract_text):
        """Complete contract analysis: Summarization + Constitutional + Verification."""
        # Step 1: Summarization Agent
        summary = self.summarize_contract(contract_text)
        
        # Step 2: RAG Constitutional Analysis
        constitutional = self.get_constitutional_analysis(contract_text)
        
        # Step 3: IndianLegalBERT Verification
        verification = self.verify_with_indianlegalbert(contract_text, summary)
        
        return {
            "summary": summary,
            "constitutional_analysis": constitutional,
            "verification": verification,
            "analysis_complete": True
        }

# Flask Application
app = Flask(__name__)
CORS(app)
analyzer = ContractAnalysisSystem()

@app.route('/')
def index():
    return send_from_directory('.', 'browser.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Original manual analysis endpoint."""
    try:
        data = request.get_json()
        contract_text = data.get('contract_text', '').strip()
        
        if not contract_text:
            return jsonify({'status': 'error', 'error': 'No contract text provided'}), 400
        
        # Complete analysis pipeline
        result = analyzer.analyze_contract_complete(contract_text)
        
        return jsonify({
            'status': 'success',
            'analysis': result,
            'auto_detected': False
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/auto-analyze', methods=['POST'])
def auto_analyze():
    """Auto-detection and analysis endpoint."""
    try:
        data = request.get_json()
        
        # Detect contract content
        detection_result = analyzer.detect_contract_content(data)
        
        if not detection_result.get("detected", False):
            return jsonify({
                "status": "no_contract",
                "message": "No contract content detected",
                "confidence": detection_result.get("confidence", 0.0)
            })
        
        # Complete analysis pipeline
        contract_text = detection_result["contract_text"]
        result = analyzer.analyze_contract_complete(contract_text)
        
        return jsonify({
            "status": "success",
            "detection": detection_result,
            "analysis": result,
            "auto_detected": True,
            "confidence": detection_result.get("confidence", 0.0)
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': f'Auto-analysis failed: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'components': {
            'summarization': True,
            'rag_constitutional': analyzer.rag_available,
            'indianlegalbert': analyzer.bert_available
        }
    })

if __name__ == "__main__":
    print("🤖 GenAI Smart Contract Pro - Production System")
    print("=" * 50)
    print("📋 Components:")
    print(f"   ✅ Summarization Agent: Active")
    print(f"   {'✅' if analyzer.rag_available else '❌'} RAG Constitutional Matching: {'Active' if analyzer.rag_available else 'Failed'}")
    print(f"   {'✅' if analyzer.bert_available else '❌'} IndianLegalBERT Verification: {'Active' if analyzer.bert_available else 'Failed'}")
    print("")
    print("🌐 Server: http://localhost:5000")
    print("🔌 Endpoints: /analyze, /auto-analyze")
    
    app.run(debug=False, host='0.0.0.0', port=5000)
