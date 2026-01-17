from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class ProtocolAdapter(ABC):
    """Abstract base class for SPS protocol adapters (e.g., WebAPI, Modbus, OPC UA)."""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection or login if required."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection or logout if required."""
        pass

    @abstractmethod
    def write(self, var: str, value: Any) -> Tuple[Dict, float]:
        """Write a single value, return response and latency in ms."""
        pass

    @abstractmethod
    def write_bulk_data(self, array_data: List[Any]) -> Tuple[Dict, float]:
        """Write an entire array of bulk data."""
        pass
