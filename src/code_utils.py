import re

class CodeCleaner:
    @staticmethod
    def extract_code(text: str) -> str:
        """
        Extracts raw Python code from an LLM response.
        Strips away conversational filler and markdown fences.
        """
        if not text:
            return ""
        
        text = text.strip()
        
        # Look for ```python ... ``` or ``` ... ``` blocks
        match = re.search(r'```(?:python)?\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
            
        # Fallback: if no markdown fences exist, return the original stripped text
        return text
