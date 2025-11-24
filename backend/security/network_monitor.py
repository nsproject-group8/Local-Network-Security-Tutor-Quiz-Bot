"""
Network Traffic Monitor (Bonus Feature)
Monitors and logs network activity for security analysis.
"""
import psutil
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger

@dataclass
class NetworkConnection:
    """Represents a network connection."""
    local_addr: str
    local_port: int
    remote_addr: str
    remote_port: int
    status: str
    pid: Optional[int]
    process_name: Optional[str]
    timestamp: datetime

class NetworkMonitor:
    """
    Monitor network connections and traffic.
    Useful for detecting unauthorized data exfiltration.
    """
    
    def __init__(self):
        self.monitoring = False
        self.connections_log: List[NetworkConnection] = []
    
    def get_active_connections(self) -> List[NetworkConnection]:
        """Get all active network connections."""
        connections = []
        
        try:
            # Get all network connections
            for conn in psutil.net_connections(kind='inet'):
                # Skip connections without remote address
                if not conn.raddr:
                    continue
                
                # Get process info if available
                process_name = None
                if conn.pid:
                    try:
                        process = psutil.Process(conn.pid)
                        process_name = process.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                connection = NetworkConnection(
                    local_addr=conn.laddr.ip if conn.laddr else "unknown",
                    local_port=conn.laddr.port if conn.laddr else 0,
                    remote_addr=conn.raddr.ip,
                    remote_port=conn.raddr.port,
                    status=conn.status,
                    pid=conn.pid,
                    process_name=process_name,
                    timestamp=datetime.now()
                )
                connections.append(connection)
        
        except Exception as e:
            logger.error(f"Error getting network connections: {e}")
        
        return connections
    
    def get_network_stats(self) -> Dict:
        """Get network interface statistics."""
        try:
            stats = psutil.net_io_counters()
            return {
                'bytes_sent': stats.bytes_sent,
                'bytes_recv': stats.bytes_recv,
                'packets_sent': stats.packets_sent,
                'packets_recv': stats.packets_recv,
                'errin': stats.errin,
                'errout': stats.errout,
                'dropin': stats.dropin,
                'dropout': stats.dropout,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting network stats: {e}")
            return {}
    
    def detect_suspicious_connections(
        self,
        connections: List[NetworkConnection]
    ) -> List[NetworkConnection]:
        """
        Detect potentially suspicious connections.
        
        Flags connections to:
        - Non-standard ports
        - Unknown remote hosts
        - Processes without identification
        """
        suspicious = []
        
        # Common legitimate ports
        legitimate_ports = {80, 443, 8000, 8080, 3000, 5173, 11434}
        
        for conn in connections:
            # Flag connections to non-standard ports
            if conn.remote_port not in legitimate_ports:
                suspicious.append(conn)
            
            # Flag connections from unknown processes
            elif conn.process_name is None and conn.pid is not None:
                suspicious.append(conn)
        
        return suspicious
    
    def monitor_traffic(self, duration_seconds: int = 60, interval: int = 5):
        """
        Monitor network traffic for a specified duration.
        
        Args:
            duration_seconds: How long to monitor
            interval: Sampling interval in seconds
        """
        logger.info(f"Starting network monitoring for {duration_seconds} seconds")
        self.monitoring = True
        
        start_time = time.time()
        snapshots = []
        
        try:
            while (time.time() - start_time) < duration_seconds and self.monitoring:
                # Get current stats
                stats = self.get_network_stats()
                connections = self.get_active_connections()
                suspicious = self.detect_suspicious_connections(connections)
                
                snapshot = {
                    'timestamp': datetime.now().isoformat(),
                    'stats': stats,
                    'active_connections': len(connections),
                    'suspicious_connections': len(suspicious)
                }
                snapshots.append(snapshot)
                
                if suspicious:
                    logger.warning(f"Detected {len(suspicious)} suspicious connections")
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("Network monitoring stopped by user")
        finally:
            self.monitoring = False
        
        return snapshots
    
    def get_ollama_connections(self) -> List[NetworkConnection]:
        """Get connections specifically to Ollama service."""
        connections = self.get_active_connections()
        
        ollama_connections = [
            conn for conn in connections
            if conn.remote_port == 11434 or (
                conn.process_name and 'ollama' in conn.process_name.lower()
            )
        ]
        
        return ollama_connections
    
    def verify_local_only_operation(self) -> Dict[str, any]:
        """
        Verify that the application is operating locally only.
        Checks for external network connections.
        """
        connections = self.get_active_connections()
        
        # Local addresses
        local_addresses = {'127.0.0.1', 'localhost', '::1'}
        
        external_connections = [
            conn for conn in connections
            if conn.remote_addr not in local_addresses
        ]
        
        is_local_only = len(external_connections) == 0
        
        report = {
            'is_local_only': is_local_only,
            'total_connections': len(connections),
            'external_connections': len(external_connections),
            'external_details': [
                {
                    'remote_addr': conn.remote_addr,
                    'remote_port': conn.remote_port,
                    'process': conn.process_name
                }
                for conn in external_connections
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        if not is_local_only:
            logger.warning(f"Detected {len(external_connections)} external connections")
        else:
            logger.info("Verified: Application is operating locally only")
        
        return report

# Singleton instance
network_monitor = NetworkMonitor()
