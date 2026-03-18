from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class ProtocolAdapter(ABC):
    """
    Abstract base class for SPS protocol adapters (e.g., WebAPI, Modbus, OPC UA).
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Establishes connection or login if required.

        Raises:
            Exception: Connection or login failure.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Closes connection or logout if required.

        Raises:
            Exception: Disconnection or logout failure.
        """
        pass

    @abstractmethod
    def write(self, var: str, value: Any) -> Tuple[Dict, float]:
        """
        Writes single value and returns response with latency.

        Args:
            var (str): Variable identifier or address.
            value (Any): Value to be written.

        Raises:
            Exception: Write operation failure.

        Returns:
            Tuple[Dict, float]: Response dictionary and latency in ms.
        """
        pass

    @abstractmethod
    def write_bulk_data(self, array_data: List[Any]) -> Tuple[Dict, float]:
        """
        Writes entire array of bulk data.

        Args:
            array_data (List[Any]): List of data elements to write.

        Raises:
            Exception: Bulk write operation failure.

        Returns:
            Tuple[Dict, float]: Response dictionary and latency in ms.
        """
        pass
