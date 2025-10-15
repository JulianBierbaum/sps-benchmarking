from opcua import Client, ua
import time
from typing import Dict, List, Tuple, Any
from .base import ProtocolAdapter

class OpcUaAdapter(ProtocolAdapter):
    """Implements the SPS communication via OPC UA protocol."""

    def __init__(self, server_url="opc.tcp://192.168.10.61:4840"):
        self.server_url = server_url
        self.client = None

    def connect(self) -> None:
        """Establish connection to OPC UA server"""
        self.client = Client(self.server_url)
        self.client.connect()
        print(f"✓ OPC UA connected to {self.server_url}")

    def disconnect(self) -> None:
        """Close connection to OPC UA server"""
        if self.client:
            self.client.disconnect()
            self.client = None
            print("✓ OPC UA disconnected")

    def _get_node(self, var: str):
        """Helper to get OPC UA node from variable path"""
        # Convert variable path to OPC UA node ID
        # Format: "PerformaceData".ToServer.bool00 -> ns=3;s="PerformaceData".ToServer.bool00
        node_id = f'ns=3;s={var}'
        return self.client.get_node(node_id)

    def write(self, var: str, value: Any) -> Tuple[Dict, float]:
        """Write a single value, return response and latency in ms."""
        if not self.client:
            raise Exception("Not connected to OPC UA server")
        
        node = self._get_node(var)
        
        # Determine variant type based on value type
        if isinstance(value, bool):
            variant_type = ua.VariantType.Boolean
        elif isinstance(value, int):
            # Default to Int32 for integers
            variant_type = ua.VariantType.Int32
        elif isinstance(value, float):
            variant_type = ua.VariantType.Float
        else:
            variant_type = ua.VariantType.String
        
        start = time.time()
        node.set_value(ua.DataValue(ua.Variant(value, variant_type)))
        latency = (time.time() - start) * 1000
        
        # Return similar structure to WebAPI for consistency
        response = {
            "success": True,
            "node": var,
            "value": value
        }
        return response, latency

    def read(self, var: str) -> Tuple[Dict, float]:
        """Read a single value, return response and latency in ms."""
        if not self.client:
            raise Exception("Not connected to OPC UA server")
        
        node = self._get_node(var)
        
        start = time.time()
        value = node.get_value()
        latency = (time.time() - start) * 1000
        
        response = {
            "success": True,
            "node": var,
            "value": value
        }
        return response, latency

    def write_bulk_data(self, array_data: List[Any]) -> Tuple[Dict, float]:
        """Write an entire array of bulk data."""
        if not self.client:
            raise Exception("Not connected to OPC UA server")
        
        start = time.time()
        
        # Write each array element individually
        # OPC UA doesn't have the same bulk write capability as the WebAPI
        for i, value in enumerate(array_data):
            node_id = f'ns=3;s="PerformaceData".PlcData.BulkData[{i}]'
            node = self.client.get_node(node_id)
            
            # Parse LTime format: "LT#<value>ns" -> extract numeric value
            if isinstance(value, str) and value.startswith("LT#") and value.endswith("ns"):
                numeric_value = int(value[3:-2])  # Remove "LT#" and "ns"
            else:
                numeric_value = value
            
            # LTime is represented as Int64 in OPC UA
            node.set_value(ua.DataValue(ua.Variant(numeric_value, ua.VariantType.Int64)))
        
        latency = (time.time() - start) * 1000
        
        response = {
            "success": True,
            "elements_written": len(array_data)
        }
        return response, latency