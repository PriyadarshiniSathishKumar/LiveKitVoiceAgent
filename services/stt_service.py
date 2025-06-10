import asyncio
import logging
import json
from typing import Optional
import websockets
import base64
from deepgram import DeepgramClient, PrerecordedOptions, LiveTranscriptionEvents, LiveOptions

from config import Config

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self):
        self.client = DeepgramClient(Config.DEEPGRAM_API_KEY)
        self.connection = None
        self.is_connected = False
        
    async def transcribe_audio(self, audio_frame) -> Optional[str]:
        """Transcribe audio frame using Deepgram STT"""
        try:
            if not self.is_connected:
                await self._connect_live_transcription()
            
            # Convert audio frame to bytes
            audio_bytes = self._convert_audio_frame(audio_frame)
            
            if audio_bytes and self.connection:
                # Send audio data to Deepgram
                self.connection.send(audio_bytes)
                
                # Wait for transcription result (with timeout)
                result = await asyncio.wait_for(
                    self._get_transcription_result(), 
                    timeout=2.0
                )
                
                return result
                
        except asyncio.TimeoutError:
            logger.debug("STT timeout - no speech detected")
            return None
        except Exception as e:
            logger.error(f"STT error: {e}")
            await self._reconnect()
            return None
    
    async def _connect_live_transcription(self):
        """Connect to Deepgram live transcription"""
        try:
            # Configure live transcription options
            options = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                interim_results=False,
                utterance_end_ms="1000",
                vad_events=True,
                encoding="linear16",
                sample_rate=16000,
                channels=1
            )
            
            # Create live transcription connection
            self.connection = self.client.listen.websocket.v("1")
            
            # Set up event handlers
            self.connection.on(LiveTranscriptionEvents.Open, self._on_open)
            self.connection.on(LiveTranscriptionEvents.Transcript, self._on_transcript)
            self.connection.on(LiveTranscriptionEvents.Error, self._on_error)
            self.connection.on(LiveTranscriptionEvents.Close, self._on_close)
            
            # Start connection
            await self.connection.start(options)
            self.is_connected = True
            
            logger.info("Connected to Deepgram live transcription")
            
        except Exception as e:
            logger.error(f"Failed to connect to Deepgram: {e}")
            self.is_connected = False
    
    async def _reconnect(self):
        """Reconnect to Deepgram"""
        logger.info("Reconnecting to Deepgram...")
        self.is_connected = False
        if self.connection:
            try:
                await self.connection.finish()
            except:
                pass
        await self._connect_live_transcription()
    
    def _convert_audio_frame(self, audio_frame):
        """Convert Livekit audio frame to bytes"""
        try:
            # Convert audio frame to the format expected by Deepgram
            # This is a simplified conversion - you may need to adjust based on actual frame format
            if hasattr(audio_frame, 'data'):
                return audio_frame.data
            elif hasattr(audio_frame, 'to_bytes'):
                return audio_frame.to_bytes()
            else:
                logger.warning("Unknown audio frame format")
                return None
        except Exception as e:
            logger.error(f"Error converting audio frame: {e}")
            return None
    
    def _on_open(self, *args, **kwargs):
        """Handle connection open"""
        logger.debug("Deepgram connection opened")
    
    def _on_transcript(self, *args, **kwargs):
        """Handle transcript result"""
        logger.debug("Received transcript from Deepgram")
        # Store the latest transcript for retrieval
        self.latest_transcript = args[0] if args else None
    
    def _on_error(self, error, **kwargs):
        """Handle connection error"""
        logger.error(f"Deepgram error: {error}")
        self.is_connected = False
    
    def _on_close(self, *args, **kwargs):
        """Handle connection close"""
        logger.debug("Deepgram connection closed")
        self.is_connected = False
    
    async def _get_transcription_result(self) -> Optional[str]:
        """Get the latest transcription result"""
        # Wait for transcript with polling
        max_wait = 2.0
        poll_interval = 0.1
        waited = 0
        
        while waited < max_wait:
            if hasattr(self, 'latest_transcript') and self.latest_transcript:
                transcript_data = self.latest_transcript
                self.latest_transcript = None  # Clear for next use
                
                # Extract text from Deepgram response
                if hasattr(transcript_data, 'channel'):
                    alternatives = transcript_data.channel.alternatives
                    if alternatives and len(alternatives) > 0:
                        transcript = alternatives[0].transcript
                        if transcript and transcript.strip():
                            return transcript.strip()
                
            await asyncio.sleep(poll_interval)
            waited += poll_interval
        
        return None
    
    async def close(self):
        """Close the STT connection"""
        if self.connection and self.is_connected:
            try:
                await self.connection.finish()
            except Exception as e:
                logger.error(f"Error closing Deepgram connection: {e}")
        self.is_connected = False
