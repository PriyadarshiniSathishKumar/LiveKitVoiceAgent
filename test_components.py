#!/usr/bin/env python3

import asyncio
import logging
from services.stt_service import STTService
from services.llm_service import LLMService
from services.tts_service import TTSService
from utils.metrics import MetricsCollector
from utils.excel_logger import ExcelLogger
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_components():
    """Test all agent components"""
    logger.info("Testing AI Voice Agent Components...")
    
    # Test LLM Service
    logger.info("Testing LLM Service...")
    llm_service = LLMService()
    try:
        response = await llm_service.generate_response("Hello, how are you?")
        logger.info(f"LLM Response: {response[:100]}...")
        logger.info("✓ LLM Service working")
    except Exception as e:
        logger.error(f"✗ LLM Service failed: {e}")
    
    # Test TTS Service
    logger.info("Testing TTS Service...")
    tts_service = TTSService()
    try:
        audio_data = await tts_service.generate_audio("Hello, this is a test.")
        if audio_data:
            logger.info(f"✓ TTS Service working - Generated {len(audio_data)} bytes")
        else:
            logger.error("✗ TTS Service failed - No audio generated")
    except Exception as e:
        logger.error(f"✗ TTS Service failed: {e}")
    
    # Test Metrics and Excel Export
    logger.info("Testing Metrics and Excel Export...")
    try:
        metrics = MetricsCollector()
        excel_logger = ExcelLogger()
        
        # Start a test session
        session_id = "test_session_001"
        metrics.start_session(session_id)
        
        # Record some test metrics
        metrics.record_eou_delay(session_id, 0.5)
        metrics.record_ttft(session_id, 0.8)
        metrics.record_ttfb(session_id, 1.2)
        metrics.record_total_latency(session_id, 1.8)
        
        # End session and export
        session_metrics = metrics.end_session(session_id)
        if session_metrics:
            filepath = await excel_logger.export_session_metrics(session_id, session_metrics)
            if filepath:
                logger.info(f"✓ Metrics and Excel Export working - File: {filepath}")
            else:
                logger.error("✗ Excel Export failed")
        
    except Exception as e:
        logger.error(f"✗ Metrics/Excel Export failed: {e}")
    
    logger.info("Component testing completed!")

if __name__ == "__main__":
    asyncio.run(test_components())