from typing import List, Tuple


class SkillExtractionService:
    """Service that extracts skills, or browser action sequences, from a transcript of a user walking through a workflow that would be useful to memorize."""

    def __init__(self):
        pass

    def _parameterize_skill(self, description: str, actions: List[str]) -> Tuple[str, List[str], dict]:
        pass
    
    def _chunk_transcript(self, transcript: str) -> List[str]:
        """Break transcript of workflow into chunks
        INPUT:
            transcript: str - Raw unified transcript of a user completing a workflow. 
            Contains chronological list of speech segments and DOM actions
        OUTPUT:
            List[str] - A list of chunks of the trancript where each chunk is of the format: 
            Header: [task, summary of what happened before], Chunk: raw transcript chunk, 
            Footer: summary of what happens after this chunk
        """

        """
        TODO: Implement 
        1) programatically break down into large LLM sized chunks 
        2) for each large chunk, llm completion to build smaller chunks w/ headers and footers 
        3) return chunks
        """
        pass

    def extract_skills(self, transcript: str) -> List[Tuple[str, str, List[str]]]:
        """Given a transcript, extract skill mappings as pairs of (description, url, action_sequence)
        INPUT:
            transcript: str - Raw unified transcript of a user completing a workflow. 
            Contains chronological list of speech segments and DOM actions
        OUTPUT:
            List[Tuple[str, str, List[str]]] - List of skills in format (description, url, action_sequence)
        """

        """TODO: Implement 
        1) chunk the transcript using _chunk_transcript
        2) for each chunk, extract skills from chunk, 
        3) return skills
        """
        pass