#!/usr/bin/env python3

import asyncio
import logging
import os
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli

from agent import VoiceAgent
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the Livekit agent
    """
    logger.info(f"Starting voice agent for room: {ctx.room.name}")
    
    # Create and start the voice agent
    agent = VoiceAgent()
    await agent.start(ctx)

if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs(Config.METRICS_DIR, exist_ok=True)
    os.makedirs(Config.EXCEL_OUTPUT_DIR, exist_ok=True)
    
    # Start the Livekit agent
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
