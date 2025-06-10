# AI Voice Agent with Livekit

A complete real-time AI voice agent implementation using Livekit with comprehensive metrics logging and Excel reporting.

## Features

### Core Pipeline
- **Speech-to-Text (STT)**: Deepgram real-time transcription
- **Language Model (LLM)**: Groq with Llama3-8B for fast responses
- **Text-to-Speech (TTS)**: ElevenLabs with Turbo V2 model
- **Real-time Communication**: Livekit WebRTC integration

### Advanced Capabilities
- **Interruption Handling**: Detect and handle conversation interruptions
- **Comprehensive Metrics**: Track EOU delays, TTFT, TTFB, total latency
- **Excel Reporting**: Detailed session analysis with performance metrics
- **Sub-2s Latency**: Optimized for conversational response times

### Metrics Tracked
- **EOU Delay**: End of Utterance detection time
- **TTFT**: Time to First Token from LLM
- **TTFB**: Time to First Byte from TTS
- **Total Latency**: Complete pipeline response time
- **Interruptions**: Conversation flow disruptions
- **Performance Analysis**: Percentiles, success rates, ratings

## Project Structure

```
├── agent.py                 # Main voice agent orchestration
├── main.py                  # Livekit worker entry point
├── config.py               # Configuration and environment variables
├── services/
│   ├── stt_service.py      # Deepgram speech-to-text
│   ├── llm_service.py      # Groq language model
│   └── tts_service.py      # ElevenLabs text-to-speech
├── utils/
│   ├── metrics.py          # Performance metrics collection
│   └── excel_logger.py     # Excel report generation
├── call_logs/              # Session Excel reports
└── metrics/                # Raw metrics data
```

## Quick Start

1. **API Keys Required**:
   - Livekit: URL, API key, and secret
   - Deepgram: API key for STT
   - Groq: API key for LLM
   - ElevenLabs: API key for TTS

2. **Run the Agent**:
   ```bash
   python main.py dev
   ```

3. **Connect via Livekit**:
   - Use Livekit Agent Playground
   - Connect to your Livekit room
   - Start voice conversation

## Performance Targets

- **Target Latency**: < 2.0 seconds end-to-end
- **Real-time STT**: Sub-100ms transcription
- **Fast LLM**: Groq Llama3-8B for speed
- **Low-latency TTS**: ElevenLabs Turbo V2

## Excel Reports

Each session generates detailed Excel files with:

### Session Summary
- Duration, conversation turns, interruptions
- Average, min, max for all metrics
- Performance rating and target violations

### Detailed Metrics
- Per-interaction measurements
- Latency target compliance
- Timestamped performance data

### Performance Analysis
- Percentile analysis (P50, P75, P90, P95, P99)
- Performance breakdown (Excellent/Good/Poor)
- Success rate and statistical analysis

## Development Mode Features

- **File Watching**: Auto-reload on code changes
- **Debug Interface**: Detailed tracing and logs
- **Development Logging**: Comprehensive debug output
- **Metrics Testing**: Component verification tools

## Usage Examples

### Basic Conversation Flow
1. User speaks → Deepgram STT
2. Text → Groq LLM processing
3. Response → ElevenLabs TTS
4. Audio → Livekit streaming
5. Metrics → Excel logging

### Interruption Handling
- Detects voice activity during agent speech
- Stops current audio generation
- Processes new user input immediately
- Logs interruption events for analysis

## Configuration

Environment variables in `.env`:
```
LIVEKIT_URL=wss://your-livekit-url
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
DEEPGRAM_API_KEY=your-deepgram-key
GROQ_API_KEY=your-groq-key
ELEVENLABS_API_KEY=your-elevenlabs-key
```

## Monitoring

- Real-time latency monitoring
- Automatic Excel export after each session
- Performance alerts for target violations
- Comprehensive conversation logging

Built with modern async Python for optimal performance and scalability.
