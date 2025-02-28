from typing import List, Optional
import asyncio
from playwright.async_api import async_playwright, Page
import pyaudio
import wave
import threading
from openai import OpenAI
import uuid
from datetime import datetime
import os
import json
from pathlib import Path

class TranscriptionService:
    def __init__(self):
        # audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
        self.client = OpenAI()
        
        # recording state
        self.frames = []
        self.is_recording = False
        self.browser = None
        self.page = None
        self.session_id = None
        self.dom_actions = []
        
        # session storage
        self.sessions_dir = Path("sessions")
        self.sessions_dir.mkdir(exist_ok=True)
        
    async def start_recording(self) -> str:
        """Start recording both audio and browser session"""
        self.session_id = str(uuid.uuid4())
        session_dir = self.sessions_dir / self.session_id
        session_dir.mkdir()
        
        # Start browser with CDP for DOM events
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        
        await self._setup_dom_listeners()
        self._start_audio_recording()
        
        return self.session_id
    
    async def _setup_dom_listeners(self):
        """Setup listeners for DOM events"""
        # TODO: Fix this function— recording of DOM actions is not working
        async def handle_click(event):
            timestamp = datetime.now().isoformat()
            selector = await self.page.evaluate("(target) => {return target.id || target.className || target.tagName.toLowerCase()}", event)
            self.dom_actions.append({
                "timestamp": timestamp,
                "type": "click",
                "selector": selector,
                "url": self.page.url
            })
            
        async def handle_navigation(event):
            timestamp = datetime.now().isoformat()
            self.dom_actions.append({
                "timestamp": timestamp,
                "type": "navigation",
                "url": event.url
            })
        
        await self.page.evaluate("""() => {
            document.addEventListener('click', (e) => {
                window.playwrightClick(e.target);
            });
        }""")
        
        await self.page.expose_function("playwrightClick", handle_click)
        self.page.on("framenavigated", handle_navigation)
            
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

    async def stop_recording(self) -> dict:
        """Stop recording and return session data"""
        session_dir = self.sessions_dir / self.session_id
        
        # Stop audio recording
        self.is_recording = False
        self.recording_thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        
        # Save audio and get transcription
        audio_path = session_dir / "audio.wav"
        with wave.open(str(audio_path), 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))
            
        # Transcribe with segments TODO: add timestamps to each segment
        with open(audio_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
            
        # Save DOM actions
        dom_path = session_dir / "dom_actions.json"
        with open(dom_path, "w") as f:
            json.dump(self.dom_actions, f, indent=2)
            
        # Save transcript
        transcript_path = session_dir / "transcript.json"
        with open(transcript_path, "w") as f:
            json.dump(transcript.model_dump(), f, indent=2)
        
        # Close browser
        if self.browser:
            await self.browser.close()
            
        return {
            "session_id": self.session_id,
            "session_dir": str(session_dir),
            "files": {
                "audio": str(audio_path),
                "transcript": str(transcript_path),
                "dom_actions": str(dom_path)
            }
        }

# example usage
async def main():
    service = TranscriptionService()
    session_id = await service.start_recording()

    input("Press Enter to stop recording...")

    session_data = await service.stop_recording()
    print(f"Session data: {json.dumps(session_data, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())