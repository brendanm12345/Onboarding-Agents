from typing import List, Dict, Any, Optional, Tuple
import pyaudio
import time
import wave
import threading
from openai import OpenAI
import uuid
from datetime import datetime, timezone
import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
import subprocess
from pydantic import BaseModel

from utils.llm import LiteLLMClient


@dataclass
class Chunk:
    start_time: float
    end_time: float
    speech: str
    actions: List[Dict[str, Any]]
    url: str


@dataclass
class WorkflowTranscript:
    session_id: str
    timestamp: str
    duration_seconds: float
    transcript: any

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "duration_seconds": self.duration_seconds,
            "transcript": self.transcript
        }


class PostProcessingOutput(BaseModel):
    refactored_python_file: str
    explanation: str


class VerificationOutput(BaseModel):
    reasoning: str
    verified_python_file: str


class WorkflowRecorder:
    def __init__(self):
        # Audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.PAUSE_THRESHOLD = 2.0  # seconds of silence to detect pause

        self.client = OpenAI()
        self.litellmclient = LiteLLMClient()

        # Recording state
        self.frames = []
        self.is_recording = False
        self.session_id = None
        self.start_time = None

        # Find the project root directory based on the flat structure
        current_dir = Path(__file__).resolve()
        # The parent of services/ is the project root
        self.project_root = current_dir.parent.parent

        # Session storage using the flat structure
        self.workflows_dir = self.project_root / "workflows"
        self.auth_dir = self.project_root / "auth"
        self.workflows_dir.mkdir(exist_ok=True)
        self.auth_dir.mkdir(exist_ok=True)

    def start_recording(self, url: str) -> str:
        """Start recording a workflow session"""
        try:
            self.session_id = str(uuid.uuid4())
            self.start_time = datetime.now(timezone.utc)

            workflow_dir = self.workflows_dir / self.session_id
            workflow_dir.mkdir()

            # Start Playwright codegen in a separate process
            playwright_workflow_path = workflow_dir / "playwright_workflow.py"
            auth_file = self.auth_dir / "auth.json"
            print(f"Auth file: {auth_file}")
            command = [
                "playwright",
                "codegen",
                "--target", "python",
                "-o", str(playwright_workflow_path),
                "--save-storage",
                str(self.auth_dir / "auth.json"),
                url
            ]

            if auth_file.exists():
                command.extend(["--load-storage", str(auth_file)])

            self.playwright_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Give Playwright a moment to start up
            print("Starting Playwright browser...")
            time.sleep(2)  # Short delay to ensure process starts

            # Check if process started successfully
            if self.playwright_process.poll() is not None:
                # Process ended immediately - something went wrong
                stdout, stderr = self.playwright_process.communicate()
                print("Error starting Playwright:")
                print(stderr.decode())

            # Start audio recording
            self._start_audio_recording()

            return self.session_id
        except Exception as e:
            raise Exception(f"Failed start recording: {e}")

    def _start_audio_recording(self):
        """Start audio recording in a separate thread"""
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )

        self.frames = []
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.start()

    def _record_audio(self):
        """Record audio chunks"""
        while self.is_recording:
            data = self.stream.read(self.CHUNK)
            self.frames.append(data)

    def _get_file_content(self, path: str) -> str:
        """Get content of a file"""
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read()
        return ""

    def _build_post_processing_prompt(self, whisper_response, playwright_workflow_path: str) -> str:
        """"""
        response_dict = whisper_response.model_dump()
        processed_whisper_response = [{
            "speech": segment.get("text", ""),
            "start": segment.get("start", "N/A"),
            "end": segment.get("end", "N/A")
        } for segment in response_dict.get("segments", [])]

        speech_segments = ""
        for segment in processed_whisper_response:
            speech_segments += f"""
    Speech: {segment['speech']}
    Start Time: {segment['start']}
    End Time: {segment['end']}
    """
        playwright_workflow = self._get_file_content(playwright_workflow_path)

        system_prompt = """You are an expert at analyzing web automation workflows and converting them into reusable, well-structured code libraries. Your task is to:

1. Analyze the provided speech transcript from a human demonstration
2. Analyze the corresponding Playwright code generated during the demonstration
3. Refactor the code into atomic, reusable functions that map to high-level actions described in the speech
4. Add clear documentation and type hints to all functions
5. Ensure each function handles one logical operation and includes proper assertions for preconditions
6. If the is any login workflow, please leverage the cookies that we save in auth/auth.json.
So instead of adding login / auth functions to our library (i.e. use `context = browser.new_context(storage_state="auth/auth.json")`)

The output should be a complete Python file with:
- All necessary imports
- Well-documented atomic functions that each handle one logical operation
- A main workflow function that uses these atomic functions
- Type hints and docstrings for all functions
- Assertions for state preconditions where appropriate
- Note: we will add URL preconditions later on to ensure an exact match for every function so don't do this now
- However, in the final `main_workflow` function that calls the functions from our libary sequentially, add the 
following print statement BEFORE each call to the function from our library. Here is an example:
```python
# ...previous code for `main_workflow`
print(f"Current URL before executing <insert below function name>: {page.url}")
navigate_to_data_source(page)
print(f"Current URL before executing <insert below function name>: {page.url}")
set_date_range(page, "2020-01", "2024-12")
print(f"Current URL before executing <insert below function name>: {page.url}")
enter_ticker(page, "MSFT")
print(f"Current URL before executing <insert below function name>: {page.url}")
add_variables(page, ["tic", "revt", "dltt", "dt", "dlc"])
print(f"Current URL before executing <insert below function name>: {page.url}")
set_output_options(page, "mclaughlin@stanford.edu")
print(f"Current URL before executing <insert below function name>: {page.url}")
perform_query_and_download(page)
# rest of code for `main_workflow`...
```

Important guidelines:
- Each atomic function should correspond to a logical action described in the speech
- Functions should be generalized with parameters where appropriate
- Include docstrings that reference the original speech description
- Maintain error handling and assertions for robustness"""

        user_prompt = f"""Please refactor this web automation workflow into a well-structured library of atomic functions.
        
Speech Transcript:
{speech_segments}

Generated Playwright Code:
{playwright_workflow}

Please provide a complete refactored Python file that implements this workflow as a library of atomic functions and a short explanation of why you structured the file the way you did."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return messages

    def _run_refactored_workflow(self, path: Path) -> Tuple[str, int]:
        """Run refactored workflow and capture it's output/errors."""
        try:
            result = subprocess.run(
                ['python', str(path)],
                capture_output=True,
                text=True
            )

            output = result.stdout + "\n" + result.stderr
            return output, result.returncode
        except Exception as e:
            return f"Error running workflow: {str(e)}", 1
        
    def _iterative_refinement(self, messages: List[Dict[str, str]], response: VerificationOutput, verified_path: Path, max_steps: int = 2) -> str:
        """After refactoring the workflow, conducting the initial verification step, we will refine the workflow up to max_steps times until it's successful running"""

        steps = 0
        current_response = response
        while steps < max_steps:
            output, return_code = self._run_refactored_workflow(verified_path)
            if return_code == 0 and "Error" not in output:
                print(f"Workflow succeeded after {steps + 1} refinement steps")
                return current_response

            messages.append({
                "role": "assistant",
                "content": f"""# Reasoning\n{current_response.reasoning}\n\n# Revised Workflow File\n{current_response.verified_python_file}"""
            })

            messages.append({
                "role": "user",
                "content": f"""The above workflow produced the below output. Please determine whether """
            })

            refinement_prompt = f"""The latest version of the workflow produced the following output:

            Console Output:
            {output}

            Return Code: {return_code}

            The original recorded workflow (which we know works) is available in the conversation history. 
            Please:
            1. Review the original recorded workflow's approach
            2. Compare it with our current implementation
            3. Fix any issues preventing successful execution
            4. Ensure all URL assertions are correct
            5. Provide clear reasoning about what needs to change

            Focus on making the workflow work as reliably as the original recording. If you're uncertain about any part,
            defer to how it was done in the original recorded workflow since we know that version works.

            Please analyze the output and provide an updated version."""

            messages.append({"role": "user", "content": refinement_prompt})

            current_response: VerificationOutput = self.litellmclient.generate(
                messages,
                response_format=VerificationOutput
            )

            if current_response is None:
                print(f"Refinement failed at step {steps + 1}")
                return None
            
            with open(verified_path, 'w') as f:
                f.write(current_response.verified_python_file)

            steps += 1
        
        print(f"Reached max refinement steps ({max_steps})")
        return current_response

    def _build_verification_prompt(self, messages: List[Dict[str, str]], response: PostProcessingOutput, workflow_output: str, workflow_code: int) -> str:
        """Added verification prompt to current context window to add URL validation and resolve any errors"""

        messages.append({
            "role": "assistant",
            "content": f"""# Refactored Playwright Workflow\n
            {response.refactored_python_file}\n\n
            # Explanation\n
            {response.explanation}
            """
        })

        verification_prompt = f"""I've run the refactored playwright workflow and attached the console output. You need to:
        1. Add URL assertions at the start of each function using `expect(page).to_have_url(...)` based on the logged URLs in the output
        2. Fix any errors that occurred during execution, adhering to the original recorded workflow (that definitely works) when you're uncertain
        3. Create a final version that will run without errors and includes proper URL validation
        
        Refactored workflow output:
        {workflow_output}
        
        Return code: {workflow_code}
        
        Please provide a complete, working version of the script that includes URL assertions and fixes any issues."""

        messages.append({"role": "user", "content": verification_prompt})

        return messages

    def stop_recording(self) -> Dict[str, Any]:
        """Stop recording and process the workflow session"""
        workflow_dir = self.workflows_dir / self.session_id
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.start_time).total_seconds()

        # Stop recording
        self.is_recording = False
        self.recording_thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

        # Stop Playwright codegen
        self.playwright_process.terminate()

        # Save audio
        audio_path = workflow_dir / "audio.wav"
        with wave.open(str(audio_path), 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))

        # Get transcription
        with open(audio_path, "rb") as audio_file:
            whisper_response = self.client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

        playwright_workflow_path = workflow_dir / "playwright_workflow.py"

        messages = self._build_post_processing_prompt(
            whisper_response, playwright_workflow_path)
        response: PostProcessingOutput = self.litellmclient.generate(
            messages, response_format=PostProcessingOutput)

        print(f"Response from LLM: {response}")

        if response is None:
            print("Error: Failed to get valid response from LLM")
            return None

        refactored_playwright_workflow_path = workflow_dir / "refactored_workflow.py"
        with open(refactored_playwright_workflow_path, 'w') as f:
            f.write(response.refactored_python_file)

        print(
            f"Running refactored workflow: {refactored_playwright_workflow_path}")
        try:
            result = subprocess.run(
                ['python', str(refactored_playwright_workflow_path)],
                capture_output=True,
                text=True
            )
            workflow_output = result.stdout + "\n" + result.stderr
            return_code = result.returncode
        except Exception as e:
            workflow_output = f"Error running workflow: {str(e)}"
            return_code = 1

        messages = self._build_verification_prompt(
            messages, response, workflow_output, return_code)
        verified_response: VerificationOutput = self.litellmclient.generate(
            messages, response_format=VerificationOutput)
        

        if verified_response is None:
            print("Error: Verification failed")
            return None

        verified_path = workflow_dir / "verified_workflow.py"
        with open(verified_path, "w") as f:
            f.write(verified_response.verified_python_file)

        final_response: VerificationOutput = self._iterative_refinement(
            messages, 
            verified_response, 
            verified_path
        )

        explanation_path = workflow_dir / "explanation.md"
        with open(explanation_path, "w") as f:
            f.write(
                f"# Initial Explanation\n{response.explanation}\n\n"
                f"# Verification Explanation\n{final_response.reasoning if final_response else verified_response.reasoning}"
            )
            
        transcript_path = workflow_dir / "transcript.json"
        with open(transcript_path, "w") as f:
            json.dump(whisper_response.model_dump(), f, indent=2)

        auth_path = self.auth_dir / "auth.json"

        return {
            "session_id": self.session_id,
            "workflow_dir": str(workflow_dir),
            "files": {
                "audio": str(audio_path),
                "playwright": str(playwright_workflow_path),
                "refactored": str(refactored_playwright_workflow_path),
                "transcript": str(transcript_path),
                "auth": str(auth_path)
            }
        }
