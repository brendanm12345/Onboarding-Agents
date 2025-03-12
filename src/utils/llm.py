from typing import Dict, List, Type, Union, Optional
from pydantic import BaseModel
from litellm import completion, supports_response_schema
import json

class LiteLLMClient:
    def __init__(self, model="gpt-4o"):
        """Initialize LLM Client."""
        self.model = model

    def generate(self, messages: List[Dict[str, str]], response_format: Optional[Type[BaseModel]]=None) -> Union[BaseModel, str]:
        try:
            # Only check support for structured outputs if response_format is provided
            if response_format and not supports_response_schema(model=self.model):
                print(f"Model {self.model} does not support structured outputs")
                return None
                
            response = completion(
                model=self.model,
                messages=messages,
                response_format=response_format if response_format else None
            )
            
            content = response.choices[0].message.content
            
            # If response_format is provided, try to parse into the schema
            if response_format:
                if isinstance(content, str):
                    try:
                        content_dict = json.loads(content)
                        return response_format(**content_dict)
                    except json.JSONDecodeError:
                        print("Expected JSON for schema but received plain string")
                        return None
                return response_format(**content)
            
            # If no response_format, just return the content string
            return content
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return None
    
    def __call__(self, messages: List[Dict[str, str]], response_format: Optional[Type[BaseModel]]=None) -> Union[BaseModel, str]:
        return self.generate(messages, response_format)


if __name__ == "__main__":
    class PostProcessingOutput(BaseModel):
        refactored_python_file: str
        explanation: str

    system_prompt = """You are an expert at analyzing web automation workflows..."""  # Your existing prompt

    user_prompt = f"""Please refactor this web automation workflow..."""  # Your existing prompt

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    client = LiteLLMClient()
    response: PostProcessingOutput = client.generate(messages, response_format=PostProcessingOutput)
    print(response)
    # The response is already a PostProcessingOutput object, so we can access its fields directly
    print(f"\nrefactored pythonFILE: {response.refactored_python_file}")