import gemma_analyzer
import rag_retriever
import answer_verifier
import json


def run_full_pipeline(contract_text: str):
    """
    Executes the complete analysis, retrieval, and verification pipeline.

    Args:
        contract_text: The full text of the legal contract.

    Returns:
        A dictionary containing the complete analysis.
    """
    # --- Part 1: Analyze with Gemma ---
    # This step summarizes the contract and finds the key legal topics.
    summary, themes = gemma_analyzer.run_analysis(contract_text)

    # --- Part 2: Retrieve and Explain with RAG ---
    # Initialize the RAG services once
    embedding_model, generative_model, vector_search_endpoint = rag_retriever.initialize_rag_services()

    constitutional_analysis = {}
    for theme in themes:
        # For each theme, get a fact-based explanation from the RAG retriever
        rag_result = rag_retriever.get_rag_explanation(
            theme, embedding_model, generative_model, vector_search_endpoint
        )

        # --- Part 3: Verify the RAG Explanation ---
        # Check if the explanation is faithful to the source articles
        verification = answer_verifier.verify_answer_faithfulness(
            rag_result["explanation"], rag_result["source_articles"]
        )

        # Store the complete analysis for this theme
        rag_result['verification'] = verification
        constitutional_analysis[theme] = rag_result

    # --- Compile the final result ---
    final_output = {
        "summary": summary,
        "constitutional_analysis": constitutional_analysis
    }

    return final_output


# --- Example Usage ---
if __name__ == "__main__":
    # A sample contract to test the entire pipeline
    sample_contract_text = """
    EMPLOYMENT AGREEMENT
    This Agreement is made between 'Innovate Corp' ("Company") and 'John Doe' ("Employee").
    1. TERM: This agreement will last for a period of two years, starting from January 1, 2025.
    2. GOVERNING LAW: This agreement shall be governed by the laws of India.
    3. EQUALITY: The Company shall not discriminate against the Employee on the grounds of religion, race, caste, sex or place of birth.
    4. FREEDOM OF SPEECH: The employee agrees not to make any public statements that could harm the company's reputation.
    """

    # Run the full pipeline
    final_analysis = run_full_pipeline(sample_contract_text)

    # Print the final, structured result
    print("\n" + "=" * 50)
    print("      FINAL AUTOMATED CONTRACT ANALYSIS")
    print("=" * 50 + "\n")
    print(json.dumps(final_analysis, indent=2))

