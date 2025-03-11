from typing import Optional, Dict, List
import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
import time
from datetime import datetime
import uuid

class BrowserRecorder:
    def __init__(self):
        self.events = []
        self.is_recording = False
        self.session_id = None
        self.sessions_dir = Path("sessions")
        self.sessions_dir.mkdir(exist_ok=True)

    async def start_recording(self, session_id: Optional[str] = None) -> str:
        """Start browser recording session."""
        self.session_id = session_id or str(uuid.uuid4())
        session_dir = self.sessions_dir / self.session_id
        session_dir.mkdir(exist_ok=True)

        self.events = []
        self.is_recording = True

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            record_har_path=str(session_dir / "session.har"),  # This helps with debugging
        )
        
        self.page = await self.context.new_page()
        await self._setup_listeners()
        
        # Enable better debugging
        self.page.set_default_timeout(5000)
        await self.context.tracing.start(screenshots=True, snapshots=True)

        return self.session_id

    async def stop_recording(self) -> dict:
        """Stop recording and return session data"""
        self.is_recording = False
        
        # Save tracing data
        session_dir = self.sessions_dir / self.session_id
        await self.context.tracing.stop(path=str(session_dir / "trace.zip"))
        
        events_path = session_dir / "events.json"
        with open(events_path, "w") as f:
            json.dump(self.events, f, indent=2)
        
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

        return {
            "session_id": self.session_id,
            "session_dir": str(session_dir),
            "files": {
                "events": str(events_path),
                "trace": str(session_dir / "trace.zip"),
                "har": str(session_dir / "session.har")
            }
        }

    async def _setup_listeners(self):
        """Setup Playwright event listeners"""
        print("Setting up event listeners...")

        # Inject our event listeners directly into the page
        await self.page.evaluate("""() => {
            window._recordEvent = (eventData) => {
                console.log('RECORDER_EVENT:', JSON.stringify(eventData));
            };

            document.addEventListener('click', (event) => {
                const element = event.target;
                const data = {
                    type: 'click',
                    timestamp: Date.now(),
                    details: {
                        tag: element.tagName.toLowerCase(),
                        id: element.id || '',
                        className: element.className || '',
                        text: element.textContent?.trim() || '',
                        href: element.href || '',
                        value: element.value || '',
                        x: event.clientX,
                        y: event.clientY
                    }
                };
                window._recordEvent(data);
            }, true);

            document.addEventListener('input', (event) => {
                const element = event.target;
                const data = {
                    type: 'input',
                    timestamp: Date.now(),
                    details: {
                        tag: element.tagName.toLowerCase(),
                        id: element.id || '',
                        className: element.className || '',
                        value: element.value || '',
                        type: element.type || ''
                    }
                };
                window._recordEvent(data);
            }, true);
        }""")

        async def handle_console(msg):
            if msg.text.startswith('RECORDER_EVENT:'):
                try:
                    # Extract the JSON string after the prefix
                    json_str = msg.text.replace('RECORDER_EVENT:', '').strip()
                    event_data = json.loads(json_str)
                    
                    # Add server-side timestamp
                    event_data['server_timestamp'] = time.time_ns()
                    
                    self.events.append(event_data)
                    print(f"Event recorded: {json.dumps(event_data, indent=2)}")
                except Exception as e:
                    print(f"Error processing event: {str(e)}")
            else:
                print(f"Console {msg.type}: {msg.text}")

        # Listen for console messages which will contain our events
        self.page.on("console", handle_console)

        print("Event listeners setup complete!")

async def main():
    recorder = BrowserRecorder()
    session_id = await recorder.start_recording()
    
    # Navigate to test page
    await recorder.page.goto("https://www.google.com")
    print("Navigated to Google. Recording started...")
    
    # Wait for user input
    try:
        while True:
            if await asyncio.get_event_loop().run_in_executor(None, input, "Press 'q' to stop recording: ") == 'q':
                break
    except KeyboardInterrupt:
        pass

    session_data = await recorder.stop_recording()
    print(f"Recording stopped. Session data: {json.dumps(session_data, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())