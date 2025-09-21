from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
from vertexai.generative_models import GenerativeModel

# --- 1. Configuration ---
PROJECT_ID = "genai-project-472704"
LOCATION = "europe-west4"
INDEX_ID = "indian-constitution-index"
ENDPOINT_ID = "1128502493615040608"

# --- 2. Initialize Models and Services ---
def initialize_rag_services():
    """Initializes and returns the necessary models and endpoints for the RAG process."""
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    generative_model = GenerativeModel("gemini-1.5-flash-002")
    
    vector_search_endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=ENDPOINT_ID
    )
    
    return embedding_model, generative_model, vector_search_endpoint

# --- 3. Core RAG Function ---
def get_rag_explanation(theme, embedding_model, generative_model, vector_search_endpoint, num_neighbors=5):
    """
    Finds relevant articles for a theme and generates a fact-based explanation.
    
    Args:
        theme: The legal theme to investigate (e.g., "Right to Equality").
        embedding_model: An initialized text embedding model.
        generative_model: An initialized generative model.
        vector_search_endpoint: An initialized Vector Search endpoint.
        num_neighbors: The number of articles to retrieve.
    
    Returns:
        A dictionary containing the generated explanation and the source articles.
    """
    print(f"Step 3: Finding relevant articles for theme: '{theme}'...")
    question_embedding = embedding_model.get_embeddings([theme])[0].values
    
    # Note: The find_neighbors method requires the ID of the specific index deployed to the endpoint.
    neighbors = vector_search_endpoint.find_neighbors(
        queries=[question_embedding],
        deployed_index_id=INDEX_ID,
        num_neighbors=num_neighbors
    )[0]
    
    if not neighbors:
        return {
            "explanation": "No relevant articles could be found in the Constitution of India for this topic.",
            "source_articles": []
        }
    
    retrieved_articles = [neighbor.instance['content'] for neighbor in neighbors]
    context_string = "\n\n---\n\n".join(retrieved_articles)
    
    print(f"Step 4: Generating explanation for '{theme}' based on retrieved articles...")
    prompt = f"""
You are an expert on the Constitution of India. Your task is to provide a clear explanation for the following legal theme based on the provided constitutional articles:

**Provided Articles:**
{context_string}

**Legal Theme:** {theme}

Please provide a comprehensive analysis that:
1. Identifies the most relevant constitutional articles
2. Explains how these articles relate to the legal theme
3. Provides practical implications for contract law
4. Highlights any fundamental rights or duties involved

**Analysis:**"""

    response = generative_model.generate_content(
        prompt,
        generation_config={
            "max_output_tokens": 800,
            "temperature": 0.1,
            "top_p": 0.8
        }
    )
    
    return {
        "explanation": response.text.strip(),
        "source_articles": retrieved_articles
    }

def extract_constitutional_themes_from_contract(contract_text):
    """Extract constitutional themes relevant to contract analysis."""
    themes = []
    contract_lower = contract_text.lower()
    
    if any(term in contract_lower for term in ['employment', 'worker', 'employee', 'labor', 'service']):
        themes.append("Right to Work and Employment")
    
    if any(term in contract_lower for term in ['payment', 'salary', 'wage', 'compensation']):
        themes.append("Right to Fair Compensation")
    
    if any(term in contract_lower for term in ['termination', 'dismissal', 'end']):
        themes.append("Due Process and Natural Justice")
    
    if any(term in contract_lower for term in ['property', 'ownership', 'asset', 'land']):
        themes.append("Right to Property")
    
    if any(term in contract_lower for term in ['trade', 'business', 'commerce', 'profession']):
        themes.append("Freedom of Trade and Commerce")
    
    if any(term in contract_lower for term in ['discrimination', 'equal', 'equality']):
        themes.append("Right to Equality")
    
    if not themes:
        themes = ["Contract Enforceability under Indian Law"]
    
    return themes[:3]
