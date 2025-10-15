import requests
import urllib3
import json

class SpsAPI:
    def __init__(self):
        self.token = None
        self.baseUrl = "https://192.168.10.61/api/jsonrpc"
        self.login()

    def login(self):
        url = self.baseUrl
        payload = [
            {
                "id": 0,
                "jsonrpc": "2.0",
                "method": "Api.Login",
                "params": {
                    "user": "5AHIT",
                    "password": "5ahiT"
                }
            }
        ]
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
        self.token = response.json()[0]['result']['token']
        return response.json()

    def set_base_url(self, url):
        self.baseUrl = url

    def get_permissions(self):
        if(self.token):
            url = self.baseUrl
            headers = {
                'X-Auth-Token': self.token,
                'Content-Type': 'application/json'
            }
            payload = [
                {
                    "jsonrpc": "2.0",
                    "method": "Api.GetPermissions",
                    "id": 1
                }
            ]
            response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
            return response.json()
        else:
            return "Not logged in"

    def browse(self, var, id=4, mode="children"):
        if(self.token):
            url = self.baseUrl
            headers = {
                'X-Auth-Token': self.token,
                'Content-Type': 'application/json'
            }
            payload = [
                {
                    "jsonrpc": "2.0",
                    "id": id,
                    "method": "PlcProgram.Browse",
                    "params": {
                        "var": var,
                        "mode": mode
                    }
                }
            ]
            response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
            return response.json()
        else:
            return "Not logged in"

    def read(self, var):
        if(self.token):
            url = self.baseUrl
            headers = {
                'X-Auth-Token': self.token,
                'Content-Type': 'application/json'
            }
            payload = [
                {
                    "id": 1,
                    "jsonrpc": "2.0",
                    "method": "PlcProgram.Read",
                    "params": {
                        "var": var
                    }
                }
            ]
            response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
            return response.json()
        else:
            return "Not logged in"

    def read_dvisu(self, var):
        if(self.token):
            url = self.baseUrl
            headers = {
                'X-Auth-Token': self.token,
                'Content-Type': 'application/json'
            }
            payload = [
                {
                    "id": 1,
                    "jsonrpc": "2.0",
                    "method": "PlcProgram.Read",
                    "params": {
                        "var": f'"dVisu".{var}'
                    }
                }
            ]
            response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
            return response.json()
        else:
            return "Not logged in"

    def read_motor(self, var):
        if(self.token):
            url = self.baseUrl
            headers = {
                'X-Auth-Token': self.token,
                'Content-Type': 'application/json'
            }
            payload = [
                {
                    "id": 1,
                    "jsonrpc": "2.0",
                    "method": "PlcProgram.Read",
                    "params": {
                        "var": f'"Motor".{var}'
                    }
                }
            ]
            response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
            return response.json()
        else:
            return "Not logged in"

    def write(self, var, value):
        if(self.token):
            url = self.baseUrl
            headers = {
                'X-Auth-Token': self.token,
                'Content-Type': 'application/json'
            }
            payload = [
                {
                    "jsonrpc": "2.0",
                    "method": "PlcProgram.Write",
                    "id": 1,
                    "params": {
                        "var": var,
                        "value": value
                    }
                }
            ]
            response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
            return response.json()
        else:
            return "Not logged in"

    def write_on(self, value):
        if(self.token):
            url = self.baseUrl
            headers = {
                'X-Auth-Token': self.token,
                'Content-Type': 'application/json'
            }
            payload = [
                {
                    "jsonrpc": "2.0",
                    "method": "PlcProgram.Write",
                    "id": 1,
                    "params": {
                        "var": '"Motor".ein',
                        "value": value
                    }
                }
            ]
            response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
            return response.json()
        else:
            return "Not logged in"

    def write_speed(self, value):
        if(self.token):
            url = self.baseUrl
            headers = {
                'X-Auth-Token': self.token,
                'Content-Type': 'application/json'
            }
            payload = [
                {
                    "jsonrpc": "2.0",
                    "method": "PlcProgram.Write",
                    "id": 1,
                    "params": {
                        "var": '"Motor".Sollgeschwindigkeit',
                        "value": value
                    }
                }
            ]
            response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
            return response.json()
        else:
            return "Not logged in"

    def logout(self):
        if(self.token):
            url = self.baseUrl
            headers = {
                'X-Auth-Token': self.token,
                'Content-Type': 'application/json'
            }
            payload = [
                {
                    "jsonrpc": "2.0",
                    "method": "Api.Logout",
                    "id": 0
                }
            ]
            response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
            self.token = None
            return response.json()
        else:
            return "Not logged in"

if __name__ == "__main__":
    urllib3.disable_warnings()
    manager = SpsAPI()
    print(manager.get_permissions())
    manager.write_on(True)
    manager.write_speed(3000)
    print(manager.logout())
    print(manager.read_dvisu("sinus"))
    print(manager.write_on(False))
    print(manager.write_speed(3000))
    manager.login()
    print(manager.browse("\"dVisu\"", 4, "children"))
    print(manager.read("\"dVisu\".sinus"))
    print(manager.read_dvisu("sinus"))
    print(manager.write('"Motor".ein', False))
    manager.write('"Motor".Sollgeschwindigkeit', 0)
    manager.write_speed(0)