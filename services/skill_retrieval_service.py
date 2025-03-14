from typing import Dict, Tuple
import ollama
import numpy as np
from src.utils.data import get_base_url

class SkillRetrievalService:
    """TODO: this is not currently being used but we may want to draw from this starter RAG implementation later on"""
    def __init__(self):
        self.embedding_model = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
        # dict of in-memory vector dbs
        self.vector_dbs = {}
    
    def _cosine_similarity(self, a, b):
        dot_prod = np.dot(a, b)
        norm_a = sum([x ** 2 for x in a]) ** 0.5
        norm_b = sum([x ** 2 for x in b]) ** 0.5
        return dot_prod / (norm_a * norm_b)
    
    def add_skill_to_db(self, skill: Tuple[Dict[str, str]]):
        """
        Args:
            skill: Tuple[Dict[str, str]] - The skill to be embedding in the format ("description": <description>, ") ... let's fix this type
        """
        try:
            embedding = ollama.embed(model=self.embedding_model, input=skill)['embeddings'][0]
            # right now this means we're actually embedding the DOM actions— we might want to just embed description and url
            self.vector_dbs[get_base_url(skill["url"])].append((skill, embedding))
        except Exception as e:
            print(f"Error embedding skill: {e}")

    def retrieve(self, query: Dict[str, str], top_n=10):
        """Retrieve skills similar to query from vector DB
        Args:
            query: Dict[str, str] - Query containing a base URL of a tool (i.e. https://www.slack.com)  and a text description (i.e. "check notifications")
        """
        try:
            query_embedding = ollama.embed(model=self.embedding_model, input=query["text"])['embeddings'][0]

            similarities = []
            # iterate through the vector DB corresponding to the tool we're retrieving skills for
            for skill, embedding in self.vector_dbs[get_base_url(query["url"])]:
                similarity = self._cosine_similarity(query_embedding, embedding)
                similarities.append((skill, similarity))
            similarities.sort(lambda x: x[1], reverse=True)
            return similarities[:top_n]
        except Exception as e:
            print(f"Error retrieving skills from vector DB: {e}")

    