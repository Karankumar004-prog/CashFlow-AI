from engine.math.metrics import FinancialSnapshot

class FinancialCoach:
    """
    The reasoning layer operates STRICTLY on verified facts.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def generate_roadmap(self, snapshot: FinancialSnapshot) -> str:
        """
        Generates qualitative advice based on the deterministic snapshot.
        If the AI is unavailable, the system still has the snapshot.
        """
        if not self.api_key or self.api_key == "mock":
            return "### AI Coach Offline\nProvide a valid API key to unlock personalized financial planning."
            
        try:
            # We would use the prompt generation logic here, feeding it snapshot.dict()
            from skills.reasoning_layer.prompts import generate_coach_prompt
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            # Simplified mock of what the real payload would look like
            payload_str = snapshot.json()
            
            prompt = f"You are a financial coach. Analyze this deterministic snapshot and provide a 3-step roadmap:\n{payload_str}"
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"### Coach Error\n{e}"
