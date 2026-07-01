import os
import tempfile
import google.generativeai as genai

def parse_pdf_to_csv_file(pdf_file_path: str, api_key: str) -> str:
    """
    Uploads a PDF to Gemini, extracts tabular transactions as CSV,
    and returns the path to a newly created temporary CSV file.
    """
    if not api_key or api_key == "mock":
        raise ValueError("A valid Gemini API key is required to parse PDF statements.")

    genai.configure(api_key=api_key)

    # Upload file to Gemini API
    uploaded_file = None
    try:
        uploaded_file = genai.upload_file(path=pdf_file_path)

        prompt = (
            "You are a strict data extraction tool. "
            "Extract the transaction table from this bank statement. "
            "Output strictly as a CSV format with the following headers: Date, Description, Amount, Type (Credit/Debit/Income/Expense).\n"
            "If the transaction is money out, set Type to 'Debit'. If money in, set Type to 'Credit'.\n"
            "DO NOT include markdown formatting, code blocks like ```csv, explanations, or any other text. "
            "Output ONLY the raw CSV text."
        )

        model = genai.GenerativeModel("gemini-1.5-pro")
        
        import time
        max_retries = 4
        response = None
        for attempt in range(max_retries):
            try:
                response = model.generate_content([uploaded_file, prompt])
                break
            except Exception as e:
                # Catch all generic exceptions which includes google.api_core.retry.RetryError and ResourceExhausted
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt + 2)
                    continue
                raise RuntimeError(f"Gemini API rate limit or processing failed permanently after {max_retries} attempts: {e}")
        
        csv_text = response.text
        
        # Clean up possible markdown code blocks if the model hallucinates them
        if csv_text.startswith("```csv"):
            csv_text = csv_text.replace("```csv", "", 1)
        if csv_text.startswith("```"):
            csv_text = csv_text.replace("```", "", 1)
        if csv_text.endswith("```"):
            csv_text = csv_text[:csv_text.rfind("```")]
        
        csv_text = csv_text.strip()
        
        return csv_text

    finally:
        # ALWAYS delete the file from the API to maintain user privacy
        if uploaded_file:
            try:
                genai.delete_file(uploaded_file.name)
            except Exception:
                pass
