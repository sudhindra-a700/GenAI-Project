"""
Contract Summarizer Module
Handles contract summarization using Vertex AI Gemini models
Modular design similar to rag_retriever.py
"""

import os
import logging
from typing import Dict, Any, Optional
import vertexai
from vertexai.generative_ai import GenerativeModel
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContractSummarizer:
    """
    Contract summarization using Vertex AI Gemini models
    Extracts key terms, payment conditions, and legal obligations
    """
    
    def __init__(self, project_id: str = None, location: str = "us-central1"):
        """
        Initialize the contract summarizer
        
        Args:
            project_id: Google Cloud project ID
            location: Vertex AI location
        """
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = location
        self.model_name = "gemini-1.5-flash-002"
        
        # Initialize Vertex AI
        try:
            vertexai.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel(self.model_name)
            logger.info(f"Contract summarizer initialized with project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise
    
    def extract_key_terms(self, contract_text: str) -> Dict[str, Any]:
        """
        Extract key contract terms and conditions
        
        Args:
            contract_text: Full contract text
            
        Returns:
            Dictionary containing extracted key terms
        """
        try:
            prompt = self._build_extraction_prompt(contract_text)
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            
            # Parse the structured response
            extracted_terms = self._parse_extraction_response(response.text)
            
            logger.info("Successfully extracted key contract terms")
            return extracted_terms
            
        except Exception as e:
            logger.error(f"Error extracting key terms: {e}")
            return {
                "error": str(e),
                "payment_terms": "Unable to extract",
                "delivery_terms": "Unable to extract",
                "governing_law": "Unable to extract",
                "termination_clause": "Unable to extract"
            }
    
    def generate_summary(self, contract_text: str) -> str:
        """
        Generate a comprehensive contract summary
        
        Args:
            contract_text: Full contract text
            
        Returns:
            Formatted summary string
        """
        try:
            key_terms = self.extract_key_terms(contract_text)
            
            # Generate narrative summary
            summary_prompt = self._build_summary_prompt(contract_text, key_terms)
            
            response = self.model.generate_content(
                summary_prompt,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 512,
                }
            )
            
            summary = self._format_summary(key_terms, response.text)
            
            logger.info("Successfully generated contract summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Summary generation failed: {str(e)}"
    
    def _build_extraction_prompt(self, contract_text: str) -> str:
        """Build prompt for key term extraction"""
        return f"""
        Analyze this contract and extract the key terms in a structured format:

        CONTRACT TEXT:
        {contract_text[:3000]}  # Limit text to avoid token limits

        Extract the following information:
        1. PAYMENT TERMS: When and how payment should be made
        2. DELIVERY TERMS: Delivery timeline and conditions  
        3. GOVERNING LAW: Which jurisdiction's laws apply
        4. TERMINATION CLAUSE: How the contract can be terminated
        5. WARRANTY TERMS: Any warranties or guarantees provided
        6. LIABILITY TERMS: Limitation of liability clauses

        Format your response as:
        PAYMENT TERMS: [extracted information]
        DELIVERY TERMS: [extracted information]
        GOVERNING LAW: [extracted information]
        TERMINATION CLAUSE: [extracted information]
        WARRANTY TERMS: [extracted information]
        LIABILITY TERMS: [extracted information]

        If any term is not found, write "Not specified in contract".
        """
    
    def _build_summary_prompt(self, contract_text: str, key_terms: Dict[str, Any]) -> str:
        """Build prompt for summary generation"""
        return f"""
        Create a concise summary of this contract focusing on the most important aspects:

        KEY TERMS EXTRACTED:
        - Payment: {key_terms.get('payment_terms', 'Not specified')}
        - Delivery: {key_terms.get('delivery_terms', 'Not specified')}
        - Governing Law: {key_terms.get('governing_law', 'Not specified')}
        - Termination: {key_terms.get('termination_clause', 'Not specified')}

        Write a 2-3 sentence summary that captures the essence of this contract.
        Focus on the main obligations, timeline, and key conditions.
        """
    
    def _parse_extraction_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the structured extraction response"""
        terms = {
            "payment_terms": "Not specified",
            "delivery_terms": "Not specified", 
            "governing_law": "Not specified",
            "termination_clause": "Not specified",
            "warranty_terms": "Not specified",
            "liability_terms": "Not specified"
        }
        
        # Extract each term using regex
        patterns = {
            "payment_terms": r"PAYMENT TERMS:\s*(.+?)(?=\n[A-Z]|\n\n|$)",
            "delivery_terms": r"DELIVERY TERMS:\s*(.+?)(?=\n[A-Z]|\n\n|$)",
            "governing_law": r"GOVERNING LAW:\s*(.+?)(?=\n[A-Z]|\n\n|$)",
            "termination_clause": r"TERMINATION CLAUSE:\s*(.+?)(?=\n[A-Z]|\n\n|$)",
            "warranty_terms": r"WARRANTY TERMS:\s*(.+?)(?=\n[A-Z]|\n\n|$)",
            "liability_terms": r"LIABILITY TERMS:\s*(.+?)(?=\n[A-Z]|\n\n|$)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match:
                terms[key] = match.group(1).strip()
        
        return terms
    
    def _format_summary(self, key_terms: Dict[str, Any], narrative: str) -> str:
        """Format the final summary output"""
        summary_parts = []
        
        # Add key terms
        if key_terms.get("payment_terms") != "Not specified":
            summary_parts.append(f"PAYMENT: {key_terms['payment_terms']}")
        
        if key_terms.get("delivery_terms") != "Not specified":
            summary_parts.append(f"DELIVERY: {key_terms['delivery_terms']}")
        
        if key_terms.get("governing_law") != "Not specified":
            summary_parts.append(f"GOVERNING LAW: {key_terms['governing_law']}")
        
        if key_terms.get("termination_clause") != "Not specified":
            summary_parts.append(f"TERMINATION: {key_terms['termination_clause']}")
        
        # Add narrative summary
        if narrative and narrative.strip():
            summary_parts.append(f"OVERVIEW: {narrative.strip()}")
        
        return " | ".join(summary_parts) if summary_parts else "Unable to generate summary"
    
    def get_contract_themes(self, contract_text: str) -> list:
        """
        Extract main themes for constitutional analysis
        
        Args:
            contract_text: Full contract text
            
        Returns:
            List of themes for RAG analysis
        """
        try:
            prompt = f"""
            Identify the main legal themes in this contract that might relate to Indian constitutional law:

            CONTRACT TEXT:
            {contract_text[:2000]}

            Focus on themes like:
            - Right to Equality
            - Right to Freedom
            - Right against Exploitation  
            - Right to Constitutional Remedies
            - Property Rights
            - Contract Enforcement
            - Commercial Law
            - Labor Rights

            Return only the most relevant themes as a comma-separated list.
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "max_output_tokens": 256,
                }
            )
            
            # Parse themes from response
            themes_text = response.text.strip()
            themes = [theme.strip() for theme in themes_text.split(',')]
            
            logger.info(f"Extracted themes: {themes}")
            return themes[:3]  # Limit to top 3 themes
            
        except Exception as e:
            logger.error(f"Error extracting themes: {e}")
            return ["Contract Enforcement", "Commercial Law"]  # Default themes

def test_summarizer():
    """Test function for the contract summarizer"""
    sample_contract = """
    TENDER DOCUMENT FOR PROCUREMENT OF Goods
    
    PAYMENT TERMS: Payment shall be made within 30 days of delivery and acceptance.
    
    DELIVERY TERMS: Goods must be delivered within 60 days of order confirmation.
    
    GOVERNING LAW: This contract shall be governed by the laws of India.
    
    TERMINATION: Either party may terminate with 30 days written notice.
    """
    
    try:
        summarizer = ContractSummarizer()
        
        # Test key term extraction
        print("Testing key term extraction...")
        key_terms = summarizer.extract_key_terms(sample_contract)
        print(f"Key terms: {key_terms}")
        
        # Test summary generation
        print("\nTesting summary generation...")
        summary = summarizer.generate_summary(sample_contract)
        print(f"Summary: {summary}")
        
        # Test theme extraction
        print("\nTesting theme extraction...")
        themes = summarizer.get_contract_themes(sample_contract)
        print(f"Themes: {themes}")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_summarizer()
