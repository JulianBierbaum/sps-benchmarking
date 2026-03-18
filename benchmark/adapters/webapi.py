import requests
import urllib3
import time
import os
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Any
from .base import ProtocolAdapter

load_dotenv()


class SpsWebApiAdapter(ProtocolAdapter):
    """
    Implements SPS communication via HTTP JSON-RPC WebAPI.
    """

    def __init__(self, base_url=None, username=None, password=None):
        """
        Initializes WebAPI adapter with connection parameters.

        Args:
            base_url (str): Base URL of WebAPI.
            username (str): Username for authentication.
            password (str): Password for authentication.
        """
        if base_url is None:
            ip = os.getenv("IP", "192.168.106.62")
            self.base_url = f"https://{ip}/api/jsonrpc"
        else:
            self.base_url = base_url
        self.username = username or os.getenv("WEBAPI_USER", "5AHIT")
        self.password = password or os.getenv("WEBAPI_PASSWORD", "5ahiT2025")
        self.token = None
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def connect(self) -> None:
        """
        Logins and stores authentication token.

        Raises:
            Exception: Login failure or unexpected response format.
        """
        payload = [
            {
                "id": 0,
                "jsonrpc": "2.0",
                "method": "Api.Login",
                "params": {"user": self.username, "password": self.password},
            }
        ]
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            self.base_url, json=payload, headers=headers, verify=False, timeout=10
        )
        response.raise_for_status()

        json_response = response.json()

        # Handle both array and object responses
        if isinstance(json_response, list) and len(json_response) > 0:
            result_obj = json_response[0]
        else:
            result_obj = json_response

        # Check for error in response
        if "error" in result_obj:
            error = result_obj["error"]
            raise Exception(f"Login failed: {error.get('message', error)}")

        if "result" not in result_obj:
            raise Exception(f"Unexpected response format: {json_response}")

        self.token = result_obj["result"]["token"]
        print(f"✓ WebAPI connected (token: {self.token[:20]}...)")

    def disconnect(self) -> None:
        """
        Logouts and clears authentication token.

        Raises:
            Exception: Logout operation failure.
        """
        if not self.token:
            return
        payload = [{"jsonrpc": "2.0", "method": "Api.Logout", "id": 0}]
        headers = {"X-Auth-Token": self.token, "Content-Type": "application/json"}
        try:
            requests.post(
                self.base_url, json=payload, headers=headers, verify=False, timeout=10
            )
        finally:
            self.token = None
            print("✓ WebAPI disconnected")

    def _headers(self) -> Dict[str, str]:
        """
        Retrieves HTTP headers for WebAPI requests.

        Raises:
            Exception: If not connected (missing token).

        Returns:
            Dict[str, str]: HTTP headers including auth token.
        """
        if not self.token:
            raise Exception("Not connected (missing token)")
        return {"X-Auth-Token": self.token, "Content-Type": "application/json"}

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
        payload = [
            {
                "jsonrpc": "2.0",
                "method": "PlcProgram.Write",
                "id": 1,
                "params": {"var": var, "value": value},
            }
        ]
        start = time.time()
        response = requests.post(
            self.base_url,
            json=payload,
            headers=self._headers(),
            verify=False,
            timeout=10,
        )
        latency = (time.time() - start) * 1000
        return response.json(), latency

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
        payload = [
            {
                "jsonrpc": "2.0",
                "method": "PlcProgram.Write",
                "id": 1,
                "params": {
                    "var": '"PerformaceData".PlcData.BulkData',
                    "value": array_data,
                },
            }
        ]
        start = time.time()
        response = requests.post(
            self.base_url,
            json=payload,
            headers=self._headers(),
            verify=False,
            timeout=30,
        )
        latency = (time.time() - start) * 1000
        return response.json(), latency
