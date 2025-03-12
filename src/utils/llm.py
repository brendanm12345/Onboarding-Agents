from typing import Dict, List, Type, Union, Optional
from pydantic import BaseModel
from litellm import completion, supports_response_schema
import json

class LiteLLMClient:
    def __init__(self, model="gpt-4o"):
        """Initialize LLM Client."""
        self.model = model

    def generate(self, messages: List[Dict[str, str]], response_format: Optional[Type[BaseModel]]=None) -> Union[BaseModel, str]:
        """LLM completion function that supports all models and structured output."""
        try:
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
