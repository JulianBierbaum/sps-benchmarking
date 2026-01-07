import requests
import urllib3
import time
import os
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Any
from .base import ProtocolAdapter

load_dotenv()

class SpsWebApiAdapter(ProtocolAdapter):
    """Implements the SPS communication via HTTP JSON-RPC WebAPI."""

    def __init__(self, base_url=None, username=None, password=None):
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
        """Login and store authentication token"""
        payload = [{
            "id": 0,
            "jsonrpc": "2.0",
            "method": "Api.Login",
            "params": {"user": self.username, "password": self.password}
        }]
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.base_url, json=payload, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
        
        json_response = response.json()
        
        # Handle both array and object responses
        if isinstance(json_response, list) and len(json_response) > 0:
            result_obj = json_response[0]
        else:
            result_obj = json_response
        
        # Check for error in response
        if 'error' in result_obj:
            error = result_obj['error']
            raise Exception(f"Login failed: {error.get('message', error)}")
        
        if 'result' not in result_obj:
            raise Exception(f"Unexpected response format: {json_response}")
        
        self.token = result_obj['result']['token']
        print(f"✓ WebAPI connected (token: {self.token[:20]}...)")

    def disconnect(self) -> None:
        """Logout and clear token"""
        if not self.token:
            return
        payload = [{
            "jsonrpc": "2.0",
            "method": "Api.Logout",
            "id": 0
        }]
        headers = {
            'X-Auth-Token': self.token,
            'Content-Type': 'application/json'
        }
        try:
            requests.post(self.base_url, json=payload, headers=headers, verify=False, timeout=10)
        finally:
            self.token = None
            print("✓ WebAPI disconnected")

    def _headers(self) -> Dict[str, str]:
        if not self.token:
            raise Exception("Not connected (missing token)")
        return {'X-Auth-Token': self.token, 'Content-Type': 'application/json'}

    def write(self, var: str, value: Any) -> Tuple[Dict, float]:
        payload = [{
            "jsonrpc": "2.0",
            "method": "PlcProgram.Write",
            "id": 1,
            "params": {"var": var, "value": value}
        }]
        start = time.time()
        response = requests.post(self.base_url, json=payload, headers=self._headers(), verify=False, timeout=10)
        latency = (time.time() - start) * 1000
        return response.json(), latency

    def read(self, var: str) -> Tuple[Dict, float]:
        payload = [{
            "jsonrpc": "2.0",
            "method": "PlcProgram.Read",
            "id": 1,
            "params": {"var": var}
        }]
        start = time.time()
        response = requests.post(self.base_url, json=payload, headers=self._headers(), verify=False, timeout=10)
        latency = (time.time() - start) * 1000
        return response.json(), latency

    def write_bulk_data(self, array_data: List[Any]) -> Tuple[Dict, float]:
        payload = [{
            "jsonrpc": "2.0",
            "method": "PlcProgram.Write",
            "id": 1,
            "params": {"var": '"PerformaceData".PlcData.BulkData', "value": array_data}
        }]
        start = time.time()
        response = requests.post(self.base_url, json=payload, headers=self._headers(), verify=False, timeout=30)
        latency = (time.time() - start) * 1000
        return response.json(), latency
