import asyncio
import logging
import time
from typing import Optional
from livekit.agents import JobContext, llm
from livekit import rtc

from services.stt_service import STTService
from services.llm_service import LLMService
from services.tts_service import TTSService
from utils.metrics import MetricsCollector
from utils.excel_logger import ExcelLogger
from config import Config

logger = logging.getLogger(__name__)

class VoiceAgent:
    def __init__(self):
        self.stt_service = STTService()
        self.llm_service = LLMService()
        self.tts_service = TTSService()
        self.metrics = MetricsCollector()
        self.excel_logger = ExcelLogger()
        
        self.room: Optional[rtc.Room] = None
        self.participant: Optional[rtc.RemoteParticipant] = None
        self.session_id: Optional[str] = None
        self.conversation_active = False
        self.current_audio_track: Optional[rtc.AudioTrack] = None
        
        # Pipeline state
        self.is_speaking = False
        self.interrupt_requested = False
        
    async def start(self, ctx: JobContext):
        """Start the voice agent"""
        self.room = ctx.room
        self.session_id = f"session_{int(time.time())}"
        
        logger.info(f"Voice agent started for session: {self.session_id}")
        
        # Set up room event handlers
        self.room.on("participant_connected", self._on_participant_connected)
        self.room.on("participant_disconnected", self._on_participant_disconnected)
        self.room.on("track_subscribed", self._on_track_subscribed)
        self.room.on("track_unsubscribed", self._on_track_unsubscribed)
        
        # Initialize metrics for this session
        self.metrics.start_session(self.session_id)
        
        # Wait for the session to end
        await self._wait_for_session_end()
        
    async def _wait_for_session_end(self):
        """Wait for the session to end and handle cleanup"""
        try:
            # Keep the agent running until disconnected
            while self.room.connection_state == rtc.ConnectionState.CONN_CONNECTED:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error during session: {e}")
        finally:
            await self._cleanup_session()
    
    async def _cleanup_session(self):
        """Clean up resources and export metrics"""
        logger.info(f"Cleaning up session: {self.session_id}")
        
        # End metrics collection
        session_metrics = self.metrics.end_session(self.session_id)
        
        # Export to Excel
        if session_metrics:
            await self.excel_logger.export_session_metrics(self.session_id, session_metrics)
            logger.info(f"Session metrics exported for: {self.session_id}")
    
    async def _on_participant_connected(self, participant: rtc.RemoteParticipant):
        """Handle participant connection"""
        logger.info(f"Participant connected: {participant.identity}")
        self.participant = participant
        
        # Send welcome message
        await self._send_welcome_message()
    
    async def _on_participant_disconnected(self, participant: rtc.RemoteParticipant):
        """Handle participant disconnection"""
        logger.info(f"Participant disconnected: {participant.identity}")
        self.conversation_active = False
    
    async def _on_track_subscribed(self, track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        """Handle track subscription"""
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info("Audio track subscribed, starting STT")
            self.current_audio_track = track
            
            # Start continuous STT processing
            asyncio.create_task(self._process_audio_stream(track))
    
    async def _on_track_unsubscribed(self, track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        """Handle track unsubscription"""
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info("Audio track unsubscribed")
            self.current_audio_track = None
    
    async def _send_welcome_message(self):
        """Send welcome message to the participant"""
        welcome_text = "Hello! I'm your AI voice assistant. How can I help you today?"
        await self._generate_and_send_audio(welcome_text)
    
    async def _process_audio_stream(self, audio_track: rtc.AudioTrack):
        """Process incoming audio stream for STT"""
        logger.info("Starting audio stream processing")
        
        try:
            async for audio_frame in audio_track:
                if not self.conversation_active:
                    self.conversation_active = True
                
                # Check for interruption
                if self.is_speaking:
                    self.interrupt_requested = True
                    logger.info("Interruption detected, stopping current speech")
                
                # Process audio frame through STT
                await self._process_audio_frame(audio_frame)
                
        except Exception as e:
            logger.error(f"Error processing audio stream: {e}")
    
    async def _process_audio_frame(self, audio_frame):
        """Process individual audio frame"""
        try:
            # Record EOU (End of Utterance) start time
            eou_start_time = time.time()
            
            # Convert audio frame and process through STT
            transcript = await self.stt_service.transcribe_audio(audio_frame)
            
            if transcript and transcript.strip():
                logger.info(f"Transcribed: {transcript}")
                
                # Record EOU delay
                eou_delay = time.time() - eou_start_time
                self.metrics.record_eou_delay(self.session_id, eou_delay)
                
                # Process through the pipeline
                await self._process_conversation(transcript)
                
        except Exception as e:
            logger.error(f"Error processing audio frame: {e}")
    
    async def _process_conversation(self, user_input: str):
        """Process conversation through LLM and TTS pipeline"""
        try:
            # Record TTFT (Time to First Token) start
            ttft_start_time = time.time()
            
            # Generate LLM response
            llm_response = await self.llm_service.generate_response(user_input)
            
            if llm_response:
                # Record TTFT
                ttft = time.time() - ttft_start_time
                self.metrics.record_ttft(self.session_id, ttft)
                
                logger.info(f"LLM Response: {llm_response}")
                
                # Generate and send audio response
                await self._generate_and_send_audio(llm_response)
            
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
    
    async def _generate_and_send_audio(self, text: str):
        """Generate audio from text and send to room"""
        try:
            # Record TTFB (Time to First Byte) start
            ttfb_start_time = time.time()
            
            # Set speaking state
            self.is_speaking = True
            self.interrupt_requested = False
            
            # Generate audio through TTS
            audio_data = await self.tts_service.generate_audio(text)
            
            if audio_data:
                # Record TTFB
                ttfb = time.time() - ttfb_start_time
                self.metrics.record_ttfb(self.session_id, ttfb)
                
                # Record total latency start
                total_latency_start = time.time()
                
                # Create and play audio through room
                # For now, we'll log that audio would be sent
                # In a full implementation, you'd convert audio_data to proper format and stream it
                logger.info(f"Audio response ready ({len(audio_data)} bytes) - would be streamed to participant")
                
                # Record total latency
                total_latency = time.time() - total_latency_start
                self.metrics.record_total_latency(self.session_id, total_latency)
                
                # Log latency warning if above target
                if total_latency > Config.TARGET_LATENCY:
                    logger.warning(f"Total latency ({total_latency:.2f}s) exceeds target ({Config.TARGET_LATENCY}s)")
                
                logger.info(f"Audio sent - TTFB: {ttfb:.3f}s, Total: {total_latency:.3f}s")
            
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
        finally:
            self.is_speaking = False
