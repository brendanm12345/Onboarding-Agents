from typing import List, Dict, Any
import asyncio
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
import tempfile

from src.utils.llm import LiteLLMClient

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
        
        # Session storage
        self.workflows_dir = Path("workflows")
        self.workflows_dir.mkdir(exist_ok=True)

    def start_recording(self, url: str) -> str:
        """Start recording a workflow session"""
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now(timezone.utc)
        
        workflow_dir = self.workflows_dir / self.session_id
        workflow_dir.mkdir()

        # Start Playwright codegen in a separate process
        playwright_workflow_path = workflow_dir / "playwright_workflow.py"
        auth_path = workflow_dir / "auth.json"
        self.playwright_process = subprocess.Popen(
            [
                "playwright",
                "codegen",
                "--target", "python",
                "-o", str(playwright_workflow_path),
                "--save-storage",
                str(auth_path),
                url
            ],
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
        

        playwright_workflow = self._get_file_content(playwright_workflow_path)

        system_prompt = """You are an expert at analyzing web automation workflows and converting them into reusable, well-structured code libraries. Your task is to:

1. Analyze the provided speech transcript from a human demonstration
2. Analyze the corresponding Playwright code generated during the demonstration
3. Refactor the code into atomic, reusable functions that map to high-level actions described in the speech
4. Add clear documentation and type hints to all functions
5. Ensure each function handles one logical operation and includes proper assertions for preconditions

The output should be a complete Python file with:
- All necessary imports
- Well-documented atomic functions that each handle one logical operation
- A main workflow function that uses these atomic functions
- Type hints and docstrings for all functions
- Assertions for URL and state preconditions where appropriate

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

        messages = self._build_post_processing_prompt(whisper_response, playwright_workflow_path)
        response: PostProcessingOutput = self.litellmclient.generate(messages, response_format=PostProcessingOutput)

        print(f"Response from LLM: {response}")

        if response is None:
            print("Error: Failed to get valid response from LLM")
            return None
        
        refactored_playwright_workflow_path = workflow_dir / "refactored_workflow.py"
        with open(refactored_playwright_workflow_path, 'w') as f:
            f.write(response.refactored_python_file)

        explanation_path = workflow_dir / "explanation.md"
        with open(explanation_path, "w") as f:
            f.write(response.explanation)

        transcript_path = workflow_dir / "transcript.json"
        with open(transcript_path, "w") as f:
            json.dump(whisper_response.model_dump(), f, indent=2)

        auth_path = workflow_dir / "auth.json"

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