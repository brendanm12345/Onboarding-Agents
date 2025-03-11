import asyncio
import json
from pathlib import Path
from datetime import datetime
from src.services.transcription_service import WorkflowTranscriptionService
from src.services.skill_extraction_service import SkillExtractionService

async def main():
    transcription_service = WorkflowTranscriptionService()
    extraction_service = SkillExtractionService()

    print("Starting workflow recording...")
    print("Describe your actions as you perform them in the browser.")
    print("Press Enter when finished.")

    session_id = await transcription_service.start_recording()
    input()  # Wait for user to finish

    print("\nProcessing recording...")
    result = await transcription_service.stop_recording()

    print("\nExtracting executable actions...")
    extracted_workflow = extraction_service.extract_stagehand_actions(result['transcript'])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"workflows/{timestamp}_{session_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "workflow.json", "w") as f:
        json.dump(result['transcript'], f, indent=2)
        
    # Save extracted actions
    with open(output_dir / "extracted_actions.json", "w") as f:
        json.dump({
            "workflow_id": extracted_workflow.workflow_id,
            "timestamp": timestamp,
            "original_transcript": extracted_workflow.original_transcript,
            "actions": [
                {
                    "semantic_description": action.semantic_description,
                    "action_type": action.action_type,
                    "instruction": action.instruction,
                    "url": action.url,
                }
                for action in extracted_workflow.actions
            ]
        }, f, indent=2)

    stagehand_format = {
        "workflow_id": extracted_workflow.workflow_id,
        "timestamp": timestamp,
        "actions": [
            {
                "type": action.action_type,
                "instruction": action.instruction,
                "url": action.url,
                "error_handling": {
                    "retry_count": 3,
                    "timeout_ms": 5000
                }
            }
            for action in extracted_workflow.actions
        ]
    }
    
    with open(output_dir / "stagehand_executable.json", "w") as f:
        json.dump(stagehand_format, f, indent=2)

    print(f"\nWorkflow recorded and processed!")
    print(f"Files saved to: {output_dir}")
    print("\nExtracted actions:")
    for i, action in enumerate(extracted_workflow.actions, 1):
        print(f"\n{i}. {action.semantic_description}")
        print(f"   Type: {action.action_type}")
        print(f"   Instruction: {action.instruction}")
        print(f"   URL: {action.url}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nRecording cancelled.")
    except Exception as e:
        print(f"\nError: {e}")
    

