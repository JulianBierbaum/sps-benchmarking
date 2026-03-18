from opcua import Client, ua
import time
import os
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Any
from .base import ProtocolAdapter

load_dotenv()


class OpcUaAdapter(ProtocolAdapter):
    """
    Implements SPS communication via OPC UA protocol.
    """

    def __init__(self, server_url=None):
        """
        Initializes OPC UA adapter with server URL.

        Args:
            server_url (str): OPC UA server endpoint URL.
        """
        if server_url is None:
            ip = os.getenv("IP", "192.168.106.62")
            self.server_url = f"opc.tcp://{ip}:4840"
        else:
            self.server_url = server_url
        self.client = None

    def connect(self) -> None:
        """
        Establishes connection to OPC UA server.

        Raises:
            Exception: Connection failure.
        """
        self.client = Client(self.server_url)
        self.client.connect()
        print(f"✓ OPC UA connected to {self.server_url}")

    def disconnect(self) -> None:
        """
        Closes connection to OPC UA server.

        Raises:
            Exception: Disconnection failure.
        """
        if self.client:
            self.client.disconnect()
            self.client = None
            print("✓ OPC UA disconnected")

    def _get_node(self, var: str):
        """
        Retrieves OPC UA node from variable path.

        Args:
            var (str): Variable identifier or path.

        Returns:
            Node: OPC UA node object.
        """
        # Convert variable path to OPC UA node ID
        # Format: "PerformaceData".ToServer.bool00 -> ns=3;s="PerformaceData".ToServer.bool00
        node_id = f"ns=3;s={var}"
        return self.client.get_node(node_id)

    def write(self, var: str, value: Any) -> Tuple[Dict, float]:
        """
        Writes single value and returns response with latency.

        Args:
            var (str): Variable identifier or address.
            value (Any): Value to be written.

        Raises:
            Exception: Write operation failure or if not connected.

        Returns:
            Tuple[Dict, float]: Response dictionary and latency in ms.
        """
        if not self.client:
            raise Exception("Not connected to OPC UA server")

        node = self._get_node(var)

        # Determine variant type based on value type
        if "int16" in var.lower():
            variant_type = ua.VariantType.Int16
        elif "int32" in var.lower():
            variant_type = ua.VariantType.Int32
        elif isinstance(value, bool):
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
        response = {"success": True, "node": var, "value": value}
        return response, latency

    def write_bulk_data(self, array_data: List[Any]) -> Tuple[Dict, float]:
        """
        Writes entire array of bulk data.

        Args:
            array_data (List[Any]): List of data elements to write.

        Raises:
            Exception: Bulk write operation failure or if not connected.

        Returns:
            Tuple[Dict, float]: Response dictionary and latency in ms.
        """
        if not self.client:
            raise Exception("Not connected to OPC UA server")

        # Pre-calculate nodes and values for single-request bulk write
        nodes = []
        datavalues = []

        for i, value in enumerate(array_data):
            node_id = f'ns=3;s="PerformaceData".BulkData[{i}]'
            nodes.append(self.client.get_node(node_id))

            # Parse LTime format: "LT#<value>ns" -> extract numeric value
            if (
                isinstance(value, str)
                and value.startswith("LT#")
                and value.endswith("ns")
            ):
                numeric_value = int(value[3:-2])  # Remove "LT#" and "ns"
            else:
                numeric_value = value

            # LTime is represented as Int64 in OPC UA
            datavalues.append(
                ua.DataValue(ua.Variant(numeric_value, ua.VariantType.Int64))
            )

        # Perform the actual write in a single network request
        start = time.time()
        self.client.set_values(nodes, datavalues)
        latency = (time.time() - start) * 1000

        response = {"success": True, "elements_written": len(array_data)}
        return response, latency
