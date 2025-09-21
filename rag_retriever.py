from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
from vertexai.generative_models import GenerativeModel

# --- 1. Configuration ---
# IMPORTANT: Values updated based on your screenshots.

PROJECT_ID = "genai-project-472704"
LOCATION = "europe-west4"
INDEX_ID = "indian-constitution-index"  # The name you gave your deployed index
ENDPOINT_ID = "7128582493615940608"  # UPDATED with your Endpoint ID from the screenshot


# --- 2. Initialize Models and Services ---

def initialize_rag_services():
    """Initializes and returns the necessary models and endpoints for the RAG process."""
    aiplatform.init(project=PROJECT_ID, location=LOCATION)

    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    generative_model = GenerativeModel("gemini-1.0-pro")

    vector_search_endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=ENDPOINT_ID
    )
    return embedding_model, generative_model, vector_search_endpoint


# --- 3. Core RAG Function ---

def get_rag_explanation(theme: str, embedding_model, generative_model, vector_search_endpoint, num_neighbors: int = 3):
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
    You are an expert on the Constitution of India. Your task is to provide a clear explanation for the following legal theme based *only* on the provided articles. Do not use any outside knowledge.

    **Provided Articles:**
    ---
    {context_string}
    ---

    **Legal Theme:**
    {theme}

    **Explanation:**
    """
    response = generative_model.generate_content(prompt)

    return {
        "explanation": response.text,
        "source_articles": retrieved_articles
    }

