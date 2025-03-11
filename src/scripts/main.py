import time
from src.services.workflow_recorder import WorkflowRecorder

def main():
    # Initialize recorder
    recorder = WorkflowRecorder()
    
    # Start recording with initial URL
    url = input("Enter the starting URL: ")
    session_id = recorder.start_recording(url)
    print(f"Recording started with session ID: {session_id}")
    print("Perform your workflow now. Press Ctrl+C to stop recording...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping recording...")
        result = recorder.stop_recording()
        print("\nRecording saved:")
        print(f"Session ID: {result['session_id']}")
        print(f"Workflow directory: {result['workflow_dir']}")
        print("\nFiles generated:")
        for file_type, file_path in result['files'].items():
            print(f"- {file_type}: {file_path}")

if __name__ == "__main__":
    main()