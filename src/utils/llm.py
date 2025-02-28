from typing import Dict, List
from litellm import completion

class LiteLLMClient:
    def __init__(self, model="gpt-4o"):
        self.model = model

    def generate(self, messages: List[Dict[str, str]], stream=False) -> str:
        try:
            response = completion(model=self.model, messages=messages, stream=stream)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    
    def __call__(self, messages: List[Dict[str, str]], stream=False) -> str:
        return self.generate(messages, stream)