import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class SessionMetrics:
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    eou_delays: List[float] = field(default_factory=list)
    ttft_times: List[float] = field(default_factory=list)
    ttfb_times: List[float] = field(default_factory=list)
    total_latencies: List[float] = field(default_factory=list)
    conversation_turns: int = 0
    interruptions: int = 0
    
    def get_averages(self) -> Dict[str, float]:
        """Calculate average metrics"""
        return {
            "avg_eou_delay": sum(self.eou_delays) / len(self.eou_delays) if self.eou_delays else 0,
            "avg_ttft": sum(self.ttft_times) / len(self.ttft_times) if self.ttft_times else 0,
            "avg_ttfb": sum(self.ttfb_times) / len(self.ttfb_times) if self.ttfb_times else 0,
            "avg_total_latency": sum(self.total_latencies) / len(self.total_latencies) if self.total_latencies else 0,
        }
    
    def get_max_values(self) -> Dict[str, float]:
        """Get maximum values for each metric"""
        return {
            "max_eou_delay": max(self.eou_delays) if self.eou_delays else 0,
            "max_ttft": max(self.ttft_times) if self.ttft_times else 0,
            "max_ttfb": max(self.ttfb_times) if self.ttfb_times else 0,
            "max_total_latency": max(self.total_latencies) if self.total_latencies else 0,
        }
    
    def get_min_values(self) -> Dict[str, float]:
        """Get minimum values for each metric"""
        return {
            "min_eou_delay": min(self.eou_delays) if self.eou_delays else 0,
            "min_ttft": min(self.ttft_times) if self.ttft_times else 0,
            "min_ttfb": min(self.ttfb_times) if self.ttfb_times else 0,
            "min_total_latency": min(self.total_latencies) if self.total_latencies else 0,
        }

class MetricsCollector:
    def __init__(self):
        self.sessions: Dict[str, SessionMetrics] = {}
        
    def start_session(self, session_id: str):
        """Start collecting metrics for a new session"""
        self.sessions[session_id] = SessionMetrics(
            session_id=session_id,
            start_time=time.time()
        )
        logger.info(f"Started metrics collection for session: {session_id}")
    
    def end_session(self, session_id: str) -> Optional[SessionMetrics]:
        """End metrics collection for a session"""
        if session_id in self.sessions:
            self.sessions[session_id].end_time = time.time()
            session_duration = self.sessions[session_id].end_time - self.sessions[session_id].start_time
            
            logger.info(f"Ended metrics collection for session: {session_id} (Duration: {session_duration:.2f}s)")
            return self.sessions[session_id]
        
        logger.warning(f"No session found for ID: {session_id}")
        return None
    
    def record_eou_delay(self, session_id: str, delay: float):
        """Record End of Utterance delay"""
        if session_id in self.sessions:
            self.sessions[session_id].eou_delays.append(delay)
            logger.debug(f"EOU delay recorded: {delay:.3f}s for session {session_id}")
    
    def record_ttft(self, session_id: str, ttft: float):
        """Record Time to First Token"""
        if session_id in self.sessions:
            self.sessions[session_id].ttft_times.append(ttft)
            self.sessions[session_id].conversation_turns += 1
            logger.debug(f"TTFT recorded: {ttft:.3f}s for session {session_id}")
    
    def record_ttfb(self, session_id: str, ttfb: float):
        """Record Time to First Byte"""
        if session_id in self.sessions:
            self.sessions[session_id].ttfb_times.append(ttfb)
            logger.debug(f"TTFB recorded: {ttfb:.3f}s for session {session_id}")
    
    def record_total_latency(self, session_id: str, latency: float):
        """Record total pipeline latency"""
        if session_id in self.sessions:
            self.sessions[session_id].total_latencies.append(latency)
            logger.debug(f"Total latency recorded: {latency:.3f}s for session {session_id}")
    
    def record_interruption(self, session_id: str):
        """Record conversation interruption"""
        if session_id in self.sessions:
            self.sessions[session_id].interruptions += 1
            logger.debug(f"Interruption recorded for session {session_id}")
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get comprehensive session summary"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        averages = session.get_averages()
        max_values = session.get_max_values()
        min_values = session.get_min_values()
        
        duration = (session.end_time or time.time()) - session.start_time
        
        return {
            "session_id": session_id,
            "duration": duration,
            "conversation_turns": session.conversation_turns,
            "interruptions": session.interruptions,
            "total_measurements": {
                "eou_delays": len(session.eou_delays),
                "ttft_times": len(session.ttft_times),
                "ttfb_times": len(session.ttfb_times),
                "total_latencies": len(session.total_latencies),
            },
            "averages": averages,
            "max_values": max_values,
            "min_values": min_values,
            "latency_target_violations": len([l for l in session.total_latencies if l > 2.0])
        }
    
    def get_all_sessions_summary(self) -> List[Dict]:
        """Get summary for all sessions"""
        summaries = []
        for session_id in self.sessions.keys():
            summary = self.get_session_summary(session_id)
            if summary:
                summaries.append(summary)
        return summaries
