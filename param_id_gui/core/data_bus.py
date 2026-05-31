"""Data bus for topic-based data exchange between simulation components."""

from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict, deque
import threading


class DataBus:
    """Topic-based data bus for simulation data exchange.
    
    This class provides a publish-subscribe mechanism for exchanging data
    between simulation components. It supports real-time, batch, and event
    data modes.
    """
    
    def __init__(self, max_history: int = 1000):
        """Initialize data bus.
        
        Args:
            max_history: Maximum number of historical data points to keep
        """
        self._topics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
    
    def publish(self, topic: str, data: Any):
        """Publish data to a topic.
        
        Args:
            topic: Topic name
            data: Data to publish
        """
        with self._lock:
            self._topics[topic].append(data)
            
            # Notify subscribers
            for callback in self._subscribers[topic]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Subscriber error on topic '{topic}': {e}")
    
    def subscribe(self, topic: str, callback: Optional[Callable] = None):
        """Subscribe to a topic.
        
        Args:
            topic: Topic name
            callback: Callback function to call when data is published
        """
        with self._lock:
            if callback is not None:
                self._subscribers[topic].append(callback)
            
            # Return latest data if available
            if self._topics[topic]:
                return self._topics[topic][-1]
            return None
    
    def get_latest(self, topic: str) -> Any:
        """Get the latest data from a topic.
        
        Args:
            topic: Topic name
            
        Returns:
            Latest data or None if no data available
        """
        with self._lock:
            if self._topics[topic]:
                return self._topics[topic][-1]
            return None
    
    def get_history(self, topic: str, count: Optional[int] = None) -> List[Any]:
        """Get historical data from a topic.
        
        Args:
            topic: Topic name
            count: Number of historical data points to return (None for all)
            
        Returns:
            List of historical data points
        """
        with self._lock:
            if count is None:
                return list(self._topics[topic])
            else:
                return list(self._topics[topic])[-count:]
    
    def clear(self, topic: Optional[str] = None):
        """Clear data from topics.
        
        Args:
            topic: Topic name to clear (None for all topics)
        """
        with self._lock:
            if topic is None:
                self._topics.clear()
            elif topic in self._topics:
                self._topics[topic].clear()
    
    def get_topics(self) -> List[str]:
        """Get list of all topics.
        
        Returns:
            List of topic names
        """
        with self._lock:
            return list(self._topics.keys())
