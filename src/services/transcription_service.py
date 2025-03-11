from typing import List, Optional, Dict, Any
import asyncio
import pyaudio
import wave
import threading
from openai import OpenAI
import uuid
from datetime import datetime
import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from playwright.async_api import async_playwright

@dataclass
class WorkflowMetadata:
    session_id: str
    timestamp: str
    duration_seconds: float
    
@dataclass
class WorkflowTranscript:
    metadata: WorkflowMetadata
    transcript: str
    segments: List[Dict[str, Any]]
    raw_response: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": asdict(self.metadata),
            "transcript": self.transcript,
            "segments": self.segments,
            "raw_response": self.raw_response
        }

class WorkflowTranscriptionService:
    def __init__(self):
        # Audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100

        self.client = OpenAI()

        # Recording state
        self.frames = []
        self.is_recording = False
        self.session_id = None
        self.start_time = None
        self.current_url = None
        self.url_history = []

        # Session storage  
        self.workflows_dir = Path("workflows")
        self.workflows_dir.mkdir(exist_ok=True)

    async def start_recording(self) -> str:
        """Start recording a workflow session"""
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now(timezone.utc)
        
        workflow_dir = self.workflows_dir / self.session_id
        workflow_dir.mkdir()

        # Start browser monitoring
        await self._start_browser_monitoring()
        
        self._start_audio_recording()
        return self.session_id

    async def _start_browser_monitoring(self):
        """Start monitoring browser URL changes"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Listen for URL changes
        async def handle_url_change(url: str):
            timestamp = datetime.now(timezone.utc).timestamp()
            self.current_url = url
            self.url_history.append({"url": url, "timestamp": timestamp})
        
        self.page.on("framenavigated", lambda frame: handle_url_change(frame.url))

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

    def _process_whisper_response(self, response) -> Dict[str, Any]:
        """Convert Whisper response to JSON-serializable format and add URL info"""
        response_dict = response.model_dump()
        
        # Process segments and add URL information
        segments = []
        for segment in response_dict.get("segments", []):
            # Find URL at this timestamp
            segment_start = segment.get("start", 0)
            segment_url = self._get_url_at_timestamp(segment_start)
            
            segments.append({
                "text": segment.get("text", ""),
                "start": segment_start,
                "end": segment.get("end", 0),
                "tokens": segment.get("tokens", []),
                "timestamp": segment.get("timestamp", []),
                "url": segment_url
            })
            
        return {
            "text": response_dict.get("text", ""),
            "segments": segments,
            "language": response_dict.get("language", ""),
            "url_history": self.url_history
        }

    def _get_url_at_timestamp(self, timestamp: float) -> str:
        """Get the URL that was active at a given timestamp"""
        recording_start = self.start_time.timestamp()
        target_time = recording_start + timestamp
        
        # Find the last URL change before this timestamp
        matching_url = None
        for url_entry in self.url_history:
            if url_entry["timestamp"] <= target_time:
                matching_url = url_entry["url"]
            else:
                break
                
        return matching_url or "unknown"

    async def stop_recording(self) -> Dict[str, Any]:
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

        # Close browser monitoring
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

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
            
        processed_response = self._process_whisper_response(whisper_response)

        workflow_transcript = WorkflowTranscript(
            metadata=WorkflowMetadata(
                session_id=self.session_id,
                timestamp=self.start_time.isoformat(),
                duration_seconds=duration
            ),
            transcript=processed_response["text"],
            segments=processed_response["segments"],
            raw_response=processed_response
        )

        workflow_path = workflow_dir / "workflow.json"
        with open(workflow_path, "w") as f:
            json.dump(workflow_transcript.to_dict(), f, indent=2)

        return {
            "session_id": self.session_id,
            "workflow_dir": str(workflow_dir),
            "files": {
                "audio": str(audio_path),
                "workflow": str(workflow_path)
            },
            "transcript": workflow_transcript.to_dict()
        }