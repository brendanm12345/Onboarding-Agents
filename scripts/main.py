import argparse
import time
import sys
import os
from pathlib import Path

# project_root = Path(__file__).resolve().parent.parent
# sys.path.append(str(project_root))
from services.workflow_recorder import WorkflowRecorder

def main():
    """Script to run recording and processing of human workflow demonstration."""
    parser = argparse.ArgumentParser(description="Run workflow recording with a specified URL.")
    parser.add_argument("--url", required=True, help="URL associated with the workflow recording.")
    args = parser.parse_args()

    recorder = WorkflowRecorder()
    
    session_id = recorder.start_recording(args.url)
    print(f"Recording started with session ID: {session_id}")
    print("Perform your workflow now. Press Ctrl+C to stop recording...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping recording. Please wait for processing to finish...")
        result = recorder.stop_recording()
        print("\nRecording saved:")
        print(f"Session ID: {result['session_id']}")
        print(f"Workflow directory: {result['workflow_dir']}")
        print("\nFiles generated:")
        for file_type, file_path in result['files'].items():
            print(f"- {file_type}: {file_path}")

if __name__ == "__main__":
    main()