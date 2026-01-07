import snap7
from snap7.util import set_bool, get_bool
import time
import os
import struct
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Any
from .base import ProtocolAdapter

load_dotenv()


class S7Adapter(ProtocolAdapter):
    """Implements the SPS communication via S7 proprietary protocol using python-snap7."""

    def __init__(self, ip=None, rack=None, slot=None):
        self.ip = ip or os.getenv("IP", "192.168.106.62")
        self.rack = rack if rack is not None else int(os.getenv("S7_RACK", "0"))
        self.slot = slot if slot is not None else int(os.getenv("S7_SLOT", "1"))
        self.client = None

        # DB number for PerformaceData (configure in .env or via constructor)
        self.db_number = int(os.getenv("S7_DB_NUMBER", "7"))

        # Offsets within the DB (configure in .env based on your PLC data block layout)
        self.bool_offset = int(os.getenv("S7_BOOL_OFFSET", "0"))
        self.bulk_offset = int(os.getenv("S7_BULK_OFFSET", "136"))
        self.bulk_element_size = int(os.getenv("S7_BULK_ELEMENT_SIZE", "8"))

    def connect(self) -> None:
        """Establish connection to S7 PLC"""
        self.client = snap7.client.Client()
        self.client.connect(self.ip, self.rack, self.slot)
        print(f"✓ S7 connected to {self.ip} (rack={self.rack}, slot={self.slot})")

    def disconnect(self) -> None:
        """Close connection to S7 PLC"""
        if self.client:
            self.client.disconnect()
            self.client = None
            print("✓ S7 disconnected")

    def write(self, var: str, value: Any) -> Tuple[Dict, float]:
        """Write a single value, return response and latency in ms."""
        if not self.client:
            raise Exception("Not connected to S7 PLC")

        start = time.time()

        # Parse the variable path and determine offset/type
        if "bool00" in var.lower():
            # Write boolean to DB
            # Read the byte first, modify the bit, then write back
            data = self.client.db_read(self.db_number, self.bool_offset, 1)
            set_bool(data, 0, 0, value)
            self.client.db_write(self.db_number, self.bool_offset, data)
        elif isinstance(value, bool):
            # Generic boolean write
            data = bytearray(1)
            set_bool(data, 0, 0, value)
            self.client.db_write(self.db_number, self.bool_offset, data)
        elif isinstance(value, int):
            # Write as 64-bit integer (big-endian for S7)
            data = bytearray(8)
            struct.pack_into(">q", data, 0, value)
            self.client.db_write(self.db_number, self.bool_offset, data)
        elif isinstance(value, float):
            # Write as LREAL (64-bit float, big-endian for S7)
            data = bytearray(8)
            struct.pack_into(">d", data, 0, value)
            self.client.db_write(self.db_number, self.bool_offset, data)
        else:
            raise Exception(f"Unsupported value type: {type(value)}")

        latency = (time.time() - start) * 1000

        response = {"success": True, "var": var, "value": value}
        return response, latency

    def read(self, var: str) -> Tuple[Dict, float]:
        """Read a single value, return response and latency in ms."""
        if not self.client:
            raise Exception("Not connected to S7 PLC")

        start = time.time()

        # Parse the variable path and determine offset/type
        if "bool00" in var.lower():
            data = self.client.db_read(self.db_number, self.bool_offset, 1)
            value = get_bool(data, 0, 0)
        else:
            # Default to reading a boolean
            data = self.client.db_read(self.db_number, self.bool_offset, 1)
            value = get_bool(data, 0, 0)

        latency = (time.time() - start) * 1000

        response = {"success": True, "var": var, "value": value}
        return response, latency

    def write_bulk_data(self, array_data: List[Any]) -> Tuple[Dict, float]:
        """Write an entire array of bulk data."""
        if not self.client:
            raise Exception("Not connected to S7 PLC")

        start = time.time()

        # Each LTime value is 8 bytes (64-bit)
        # Prepare a buffer for all 100 elements
        buffer_size = len(array_data) * self.bulk_element_size
        data = bytearray(buffer_size)

        for i, value in enumerate(array_data):
            # Parse LTime format: "LT#<value>ns" -> extract numeric value
            if (
                isinstance(value, str)
                and value.startswith("LT#")
                and value.endswith("ns")
            ):
                numeric_value = int(value[3:-2])  # Remove "LT#" and "ns"
            else:
                numeric_value = int(value) if not isinstance(value, int) else value

            # Write as 64-bit integer (big-endian for S7)
            offset = i * self.bulk_element_size
            struct.pack_into(">q", data, offset, numeric_value)

        # Write the entire buffer in one operation
        self.client.db_write(self.db_number, self.bulk_offset, data)

        latency = (time.time() - start) * 1000

        response = {"success": True, "elements_written": len(array_data)}
        return response, latency
