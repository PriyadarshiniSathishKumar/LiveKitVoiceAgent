import os
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from utils.metrics import SessionMetrics
from config import Config

logger = logging.getLogger(__name__)

class ExcelLogger:
    def __init__(self):
        self.output_dir = Config.EXCEL_OUTPUT_DIR
        
    async def export_session_metrics(self, session_id: str, session_metrics: SessionMetrics):
        """Export session metrics to Excel file"""
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"call_session_{session_id}_{timestamp}.xlsx"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create Excel writer
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Session Summary Sheet
                await self._write_session_summary(writer, session_metrics)
                
                # Detailed Metrics Sheet
                await self._write_detailed_metrics(writer, session_metrics)
                
                # Performance Analysis Sheet
                await self._write_performance_analysis(writer, session_metrics)
            
            logger.info(f"Session metrics exported to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting session metrics: {e}")
            return None
    
    async def _write_session_summary(self, writer, session_metrics: SessionMetrics):
        """Write session summary sheet"""
        duration = (session_metrics.end_time or 0) - session_metrics.start_time
        averages = session_metrics.get_averages()
        max_values = session_metrics.get_max_values()
        min_values = session_metrics.get_min_values()
        
        summary_data = {
            'Metric': [
                'Session ID',
                'Start Time',
                'End Time',
                'Duration (seconds)',
                'Conversation Turns',
                'Interruptions',
                'Total EOU Measurements',
                'Total TTFT Measurements',
                'Total TTFB Measurements',
                'Total Latency Measurements',
                'Avg EOU Delay (s)',
                'Avg TTFT (s)',
                'Avg TTFB (s)',
                'Avg Total Latency (s)',
                'Max EOU Delay (s)',
                'Max TTFT (s)',
                'Max TTFB (s)',
                'Max Total Latency (s)',
                'Min EOU Delay (s)',
                'Min TTFT (s)',
                'Min TTFB (s)',
                'Min Total Latency (s)',
                'Latency Target Violations (>2s)',
                'Performance Rating'
            ],
            'Value': [
                session_metrics.session_id,
                datetime.fromtimestamp(session_metrics.start_time).strftime('%Y-%m-%d %H:%M:%S'),
                datetime.fromtimestamp(session_metrics.end_time).strftime('%Y-%m-%d %H:%M:%S') if session_metrics.end_time else 'N/A',
                f"{duration:.2f}",
                session_metrics.conversation_turns,
                session_metrics.interruptions,
                len(session_metrics.eou_delays),
                len(session_metrics.ttft_times),
                len(session_metrics.ttfb_times),
                len(session_metrics.total_latencies),
                f"{averages['avg_eou_delay']:.3f}",
                f"{averages['avg_ttft']:.3f}",
                f"{averages['avg_ttfb']:.3f}",
                f"{averages['avg_total_latency']:.3f}",
                f"{max_values['max_eou_delay']:.3f}",
                f"{max_values['max_ttft']:.3f}",
                f"{max_values['max_ttfb']:.3f}",
                f"{max_values['max_total_latency']:.3f}",
                f"{min_values['min_eou_delay']:.3f}",
                f"{min_values['min_ttft']:.3f}",
                f"{min_values['min_ttfb']:.3f}",
                f"{min_values['min_total_latency']:.3f}",
                len([l for l in session_metrics.total_latencies if l > Config.TARGET_LATENCY]),
                self._calculate_performance_rating(averages['avg_total_latency'])
            ]
        }
        
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Session Summary', index=False)
    
    async def _write_detailed_metrics(self, writer, session_metrics: SessionMetrics):
        """Write detailed metrics sheet"""
        # Prepare detailed metrics data
        max_length = max(
            len(session_metrics.eou_delays),
            len(session_metrics.ttft_times),
            len(session_metrics.ttfb_times),
            len(session_metrics.total_latencies)
        )
        
        detailed_data = {
            'Measurement #': list(range(1, max_length + 1)),
            'EOU Delay (s)': self._pad_list(session_metrics.eou_delays, max_length),
            'TTFT (s)': self._pad_list(session_metrics.ttft_times, max_length),
            'TTFB (s)': self._pad_list(session_metrics.ttfb_times, max_length),
            'Total Latency (s)': self._pad_list(session_metrics.total_latencies, max_length),
            'Latency Target Met': [
                'Yes' if lat <= Config.TARGET_LATENCY else 'No' 
                for lat in self._pad_list(session_metrics.total_latencies, max_length, 0)
            ]
        }
        
        df_detailed = pd.DataFrame(detailed_data)
        df_detailed.to_excel(writer, sheet_name='Detailed Metrics', index=False)
    
    async def _write_performance_analysis(self, writer, session_metrics: SessionMetrics):
        """Write performance analysis sheet"""
        latencies = session_metrics.total_latencies
        
        if not latencies:
            # Empty analysis if no data
            df_analysis = pd.DataFrame({'Analysis': ['No latency data available']})
            df_analysis.to_excel(writer, sheet_name='Performance Analysis', index=False)
            return
        
        # Calculate percentiles
        latencies_sorted = sorted(latencies)
        percentiles = {
            'P50': self._percentile(latencies_sorted, 50),
            'P75': self._percentile(latencies_sorted, 75),
            'P90': self._percentile(latencies_sorted, 90),
            'P95': self._percentile(latencies_sorted, 95),
            'P99': self._percentile(latencies_sorted, 99)
        }
        
        # Performance breakdown
        excellent = len([l for l in latencies if l <= 1.0])
        good = len([l for l in latencies if 1.0 < l <= 1.5])
        acceptable = len([l for l in latencies if 1.5 < l <= 2.0])
        poor = len([l for l in latencies if l > 2.0])
        
        analysis_data = {
            'Performance Metric': [
                'Total Measurements',
                '50th Percentile (P50)',
                '75th Percentile (P75)',
                '90th Percentile (P90)',
                '95th Percentile (P95)',
                '99th Percentile (P99)',
                'Excellent Performance (≤1.0s)',
                'Good Performance (1.0-1.5s)',
                'Acceptable Performance (1.5-2.0s)',
                'Poor Performance (>2.0s)',
                'Success Rate (≤2.0s)',
                'Average Latency',
                'Standard Deviation'
            ],
            'Value': [
                len(latencies),
                f"{percentiles['P50']:.3f}s",
                f"{percentiles['P75']:.3f}s",
                f"{percentiles['P90']:.3f}s",
                f"{percentiles['P95']:.3f}s",
                f"{percentiles['P99']:.3f}s",
                f"{excellent} ({excellent/len(latencies)*100:.1f}%)",
                f"{good} ({good/len(latencies)*100:.1f}%)",
                f"{acceptable} ({acceptable/len(latencies)*100:.1f}%)",
                f"{poor} ({poor/len(latencies)*100:.1f}%)",
                f"{(len(latencies)-poor)/len(latencies)*100:.1f}%",
                f"{sum(latencies)/len(latencies):.3f}s",
                f"{self._std_dev(latencies):.3f}s"
            ]
        }
        
        df_analysis = pd.DataFrame(analysis_data)
        df_analysis.to_excel(writer, sheet_name='Performance Analysis', index=False)
    
    def _pad_list(self, lst: List[float], target_length: int, fill_value=None) -> List:
        """Pad list to target length"""
        padded = lst.copy()
        while len(padded) < target_length:
            padded.append(fill_value)
        return padded
    
    def _percentile(self, sorted_list: List[float], percentile: int) -> float:
        """Calculate percentile of sorted list"""
        if not sorted_list:
            return 0.0
        
        index = (percentile / 100) * (len(sorted_list) - 1)
        lower_index = int(index)
        upper_index = min(lower_index + 1, len(sorted_list) - 1)
        
        if lower_index == upper_index:
            return sorted_list[lower_index]
        
        # Linear interpolation
        weight = index - lower_index
        return sorted_list[lower_index] * (1 - weight) + sorted_list[upper_index] * weight
    
    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _calculate_performance_rating(self, avg_latency: float) -> str:
        """Calculate performance rating based on average latency"""
        if avg_latency <= 1.0:
            return "Excellent"
        elif avg_latency <= 1.5:
            return "Good"
        elif avg_latency <= 2.0:
            return "Acceptable"
        else:
            return "Needs Improvement"
    
    async def export_aggregate_report(self, sessions_data: List[Dict]):
        """Export aggregate report for multiple sessions"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aggregate_report_{timestamp}.xlsx"
            filepath = os.path.join(self.output_dir, filename)
            
            if not sessions_data:
                logger.warning("No session data to export")
                return None
            
            # Convert sessions data to DataFrame
            df_sessions = pd.DataFrame(sessions_data)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df_sessions.to_excel(writer, sheet_name='All Sessions Summary', index=False)
                
                # Calculate aggregate statistics
                if len(sessions_data) > 1:
                    aggregate_stats = self._calculate_aggregate_stats(sessions_data)
                    df_aggregate = pd.DataFrame([aggregate_stats])
                    df_aggregate.to_excel(writer, sheet_name='Aggregate Statistics', index=False)
            
            logger.info(f"Aggregate report exported to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting aggregate report: {e}")
            return None
    
    def _calculate_aggregate_stats(self, sessions_data: List[Dict]) -> Dict:
        """Calculate aggregate statistics across all sessions"""
        total_duration = sum(session.get('duration', 0) for session in sessions_data)
        total_turns = sum(session.get('conversation_turns', 0) for session in sessions_data)
        total_interruptions = sum(session.get('interruptions', 0) for session in sessions_data)
        
        avg_latencies = [session['averages']['avg_total_latency'] for session in sessions_data if 'averages' in session]
        overall_avg_latency = sum(avg_latencies) / len(avg_latencies) if avg_latencies else 0
        
        return {
            'total_sessions': len(sessions_data),
            'total_duration_hours': total_duration / 3600,
            'total_conversation_turns': total_turns,
            'total_interruptions': total_interruptions,
            'overall_avg_latency': overall_avg_latency,
            'sessions_meeting_target': len([s for s in sessions_data if s.get('averages', {}).get('avg_total_latency', 999) <= Config.TARGET_LATENCY])
        }
