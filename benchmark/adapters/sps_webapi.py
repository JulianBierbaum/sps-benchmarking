import requests
import urllib3
import time
from typing import Dict, List, Tuple, Any
from .base import ProtocolAdapter

class SpsWebApiAdapter(ProtocolAdapter):
    """Implements the SPS communication via HTTP JSON-RPC WebAPI."""

    def __init__(self, base_url="https://192.168.10.61/api/jsonrpc", 
                 username="5AHIT", password="5ahiT"):
        self.base_url = base_url
        self.username = username
        self.password = password
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
        self.token = response.json()[0]['result']['token']
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
