from typing import List, Dict, Any
from dataclasses import dataclass
from openai import OpenAI
import json

@dataclass
class StagehandAction:
    """Represents an atomic Stagehand action"""
    semantic_description: str  # What the action accomplishes
    action_type: str  # GOTO, ACT, EXTRACT etc
    instruction: str  # The actual Stagehand instruction
    url: str  # URL where this action occurs

@dataclass
class ExtractedWorkflow:
    """A workflow broken down into Stagehand actions"""
    workflow_id: str
    original_transcript: str
    actions: List[StagehandAction]

class SkillExtractionService:
    def __init__(self):
        self.client = OpenAI()

    def extract_stagehand_actions(self, workflow_json: Dict[str, Any]) -> ExtractedWorkflow:
        """Convert a workflow transcript into a sequence of Stagehand actions"""
        
        # Format the transcript for the LLM
        segments = workflow_json["segments"]
        formatted_transcript = "\n".join([
            f"[Time {s['start']:.1f}-{s['end']:.1f}, URL: {s.get('url', 'unknown')}] {s['text']}"
            for s in segments
        ])

        # Prompt the LLM to extract actions
        system_prompt = """You are an expert at converting natural language workflow descriptions into 
        atomic Stagehand browser automation actions. Given a transcript of someone describing their 
        workflow, extract a sequence of Stagehand actions.

        Each action should be in the format:
        - Semantic description: What the action accomplishes
        - Action type: One of GOTO, ACT, EXTRACT
        - Instruction: The actual Stagehand instruction (should be atomic and specific)
        - URL: The URL where this action occurs

        Remember:
        - Break down complex actions into atomic steps
        - Use specific, unambiguous instructions
        - Include only actions that can be automated
        - Focus on browser interactions, not general computer actions"""

        user_prompt = f"""Convert this workflow transcript into Stagehand actions:

        {formatted_transcript}

        Format each action as:
        SEMANTIC: <description>
        TYPE: <action type>
        INSTRUCTION: <stagehand instruction>
        URL: <url>
        
        Example action:
        SEMANTIC: Navigate to Google Drive
        TYPE: GOTO
        INSTRUCTION: https://drive.google.com
        URL: https://drive.google.com"""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )

        # Parse LLM response into StagehandActions
        actions = self._parse_llm_response(response.choices[0].message.content)

        return ExtractedWorkflow(
            workflow_id=workflow_json["metadata"]["session_id"],
            original_transcript=workflow_json["transcript"],
            actions=actions
        )

    def _parse_llm_response(self, llm_response: str) -> List[StagehandAction]:
        """Parse the LLM's response into StagehandAction objects"""
        actions = []
        current_action = {}
        
        for line in llm_response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('SEMANTIC:'):
                if current_action:
                    actions.append(StagehandAction(**current_action))
                current_action = {'semantic_description': line[9:].strip()}
            elif line.startswith('TYPE:'):
                current_action['action_type'] = line[5:].strip()
            elif line.startswith('INSTRUCTION:'):
                current_action['instruction'] = line[12:].strip()
            elif line.startswith('URL:'):
                current_action['url'] = line[4:].strip()
                
        if current_action:
            actions.append(StagehandAction(**current_action))
                
        return actions

    def save_extracted_workflow(self, workflow: ExtractedWorkflow, output_path: str):
        """Save the extracted workflow to a JSON file"""
        output = {
            "workflow_id": workflow.workflow_id,
            "original_transcript": workflow.original_transcript,
            "actions": [
                {
                    "semantic_description": action.semantic_description,
                    "action_type": action.action_type,
                    "instruction": action.instruction,
                    "url": action.url
                }
                for action in workflow.actions
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

# Example usage
if __name__ == "__main__":
    # Load a workflow JSON file
    with open("workflows/example/workflow.json") as f:
        workflow_json = json.load(f)
    
    # Extract Stagehand actions
    extractor = SkillExtractionService()
    extracted_workflow = extractor.extract_stagehand_actions(workflow_json)
    
    # Save the extracted actions
    output_path = f"workflows/{workflow_json['metadata']['session_id']}/extracted_actions.json"
    extractor.save_extracted_workflow(extracted_workflow, output_path)
    
    # Print the actions
    for action in extracted_workflow.actions:
        print("\nAction:")
        print(f"Semantic: {action.semantic_description}")
        print(f"Type: {action.action_type}")
        print(f"Instruction: {action.instruction}")
        print(f"URL: {action.url}")