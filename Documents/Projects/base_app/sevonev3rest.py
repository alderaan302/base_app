import requests
from typing import Dict, List, Optional, Any


class SevOneV3API:
    """Client for SevOne NMS REST API v3"""
    
    def __init__(self, host: str, api_key: str, verify_ssl: bool = False):
        """
        Initialize SevOne API client
        
        Args:
            host: SevOne host (e.g., '192.168.68.3')
            api_key: API key for authentication
            verify_ssl: Whether to verify SSL certificates (default: False)
        """
        self.host = host
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.base_url = f"http://{host}/api/v3"
        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'apikey {api_key}'
        }
    
    def get_alerts(self, alert_status: str = 'OPEN', timeout: int = 10) -> Dict[str, Any]:
        """
        Fetch alerts from SevOne
        
        Args:
            alert_status: Status of alerts to fetch (default: 'OPEN')
            timeout: Request timeout in seconds (default: 10)
            
        Returns:
            Dictionary containing alerts data with structure:
            {
                'alerts': List of alert objects,
                'startTime': str,
                'endTime': str,
                'partialResults': Optional
            }
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}/data/alerts"
        params = {'query.alertStatus': alert_status}
        
        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            verify=self.verify_ssl,
            timeout=timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def count_alerts_by_device(self, alert_status: str = 'OPEN') -> Dict[str, int]:
        """
        Get alert counts grouped by device name
        
        Args:
            alert_status: Status of alerts to fetch (default: 'OPEN')
            
        Returns:
            Dictionary mapping device displayName to alert count
            Example: {'sevone-nms-er-01s': 2, 'mac-mini-03': 1}
        """
        data = self.get_alerts(alert_status=alert_status)
        alerts = data.get('alerts', [])
        
        alert_counts = {}
        for alert in alerts:
            device = alert.get('device', {})
            device_name = device.get('displayName') or device.get('name')
            if device_name:
                alert_counts[device_name] = alert_counts.get(device_name, 0) + 1
        
        return alert_counts
    
    def get_devices(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Fetch all devices from SevOne
        
        Args:
            timeout: Request timeout in seconds (default: 10)
            
        Returns:
            Dictionary containing devices data with structure:
            {
                'devices': Dict mapping device ID to device object
            }
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}/metadata/devices/metadata"
        
        response = requests.get(
            url,
            headers=self.headers,
            verify=self.verify_ssl,
            timeout=timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_device_list(self) -> List[Dict[str, Any]]:
        """
        Get a simplified list of devices with id, name, and displayName
        
        Returns:
            List of device dictionaries
            Example: [{'id': 16, 'name': 'sevone-nms-er-01s', 'displayName': 'sevone-nms-er-01s'}]
        """
        data = self.get_devices()
        devices = data.get('devices', {})
        
        device_list = []
        for device_data in devices.values():
            if device_data.get('name'):
                device_list.append({
                    'id': int(device_data.get('id')),
                    'name': device_data.get('name'),
                    'displayName': device_data.get('displayName', device_data.get('name'))
                })
        
        return device_list
    
    def get_objects(self, device_id: int, timeout: int = 10) -> Dict[str, Any]:
        """
        Fetch objects for a specific device
        
        Args:
            device_id: ID of the device
            timeout: Request timeout in seconds (default: 10)
            
        Returns:
            Dictionary containing objects data with structure:
            {
                'objects': List of object dictionaries
            }
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}/metadata/objects"
        params = {'deviceIds': device_id}
        
        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            verify=self.verify_ssl,
            timeout=timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_object_list(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Get a simplified list of objects for a device
        
        Args:
            device_id: ID of the device
            
        Returns:
            List of object dictionaries with id, name, displayName, and description
            Example: [{'id': 1124, 'name': 'SNMP Availability', 'displayName': 'SNMP Availability', 'description': ''}]
        """
        data = self.get_objects(device_id)
        objects = data.get('objects', [])
        
        object_list = []
        for obj in objects:
            if obj.get('name'):
                object_list.append({
                    'id': obj.get('id'),
                    'name': obj.get('name'),
                    'displayName': obj.get('displayName', obj.get('name')),
                    'description': obj.get('description', '')
                })
        
        return object_list
    
    def get_indicators(self, device_name: str, object_name: Optional[str] = None, timeout: int = 10) -> Dict[str, Any]:
        """
        Fetch indicators for a specific device, optionally filtered by object
        
        Args:
            device_name: Name of the device
            object_name: Optional name of the object to filter by
            timeout: Request timeout in seconds (default: 10)
            
        Returns:
            Dictionary containing indicators data with structure:
            {
                'indicators': List of indicator dictionaries
            }
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}/metadata/indicators"
        
        # Build filter payload
        payload = {
            "filters": [
                {
                    "deviceNames": [
                        {
                            "value": device_name
                        }
                    ]
                }
            ]
        }
        
        headers = {
            **self.headers,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=self.verify_ssl,
            timeout=timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_indicator_list(self, device_name: str, object_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a simplified list of indicators for a device, optionally filtered by object
        
        Args:
            device_name: Name of the device
            object_name: Optional name of the object to filter by
            
        Returns:
            List of indicator dictionaries with id, name, description, indicatorType, and object
            Example: [{'id': 123, 'name': 'Availability', 'description': '', 'indicatorType': {...}, 'object': {...}}]
        """
        data = self.get_indicators(device_name, object_name)
        indicators = data.get('indicators', [])
        
        indicator_list = []
        for indicator in indicators:
            # Check if we should filter by object
            if object_name:
                indicator_object = indicator.get('object', {})
                obj_name = indicator_object.get('name', '')
                if obj_name != object_name:
                    continue
            
            # Get the indicator name - might be in indicatorType
            ind_name = indicator.get('name')
            if not ind_name:
                ind_type = indicator.get('indicatorType', {})
                ind_name = ind_type.get('name')
            
            if ind_name:
                indicator_list.append({
                    'id': indicator.get('id'),
                    'name': ind_name,
                    'description': indicator.get('description', ''),
                    'indicatorType': indicator.get('indicatorType', {}),
                    'object': indicator.get('object', {})
                })
        
        return indicator_list
    
    def get_policies(self, policy_type: str = 'POLICY_TYPE_UNKNOWN', timeout: int = 10) -> Dict[str, Any]:
        """
        Fetch policies from SevOne
        
        Args:
            policy_type: Type of policies to fetch (default: 'POLICY_TYPE_UNKNOWN')
            timeout: Request timeout in seconds (default: 10)
            
        Returns:
            Dictionary containing policies data with structure:
            {
                'policies': List of policy objects
            }
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}/policies"
        params = {
            'sorts.field': 'FIELD_ID',
            'sorts.direction': 'DIRECTION_ASCENDING',
            'policyType': policy_type
        }
        
        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            verify=self.verify_ssl,
            timeout=timeout
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_policy_list(self, policy_type: str = 'POLICY_TYPE_UNKNOWN') -> List[Dict[str, Any]]:
        """
        Get a simplified list of policies
        
        Args:
            policy_type: Type of policies to fetch (default: 'POLICY_TYPE_UNKNOWN')
            
        Returns:
            List of policy dictionaries with id, name, description, and severity
            Example: [{'id': 1, 'name': 'CPU Over 90%', 'description': 'CPU alerts', 'severity': 'WARNING'}]
        """
        data = self.get_policies(policy_type=policy_type)
        policies = data.get('policies', [])
        
        policy_list = []
        for policy in policies:
            severity_value = policy.get('severity', '')
            print(f"Policy: {policy.get('name', '')}, Severity: {severity_value} (type: {type(severity_value).__name__})")
            policy_list.append({
                'id': policy.get('id'),
                'name': policy.get('name', ''),
                'description': policy.get('description', ''),
                'severity': severity_value
            })
        
        return policy_list

    def delete_policy(self, policy_id):
        """
        Delete a policy by ID
        Args:
            policy_id: The ID of the policy to delete
        Returns:
            True if successful, raises exception otherwise
        """
        url = f"https://{self.host}/api/v3/policies/{policy_id}"
        response = requests.delete(url, headers=self.headers, verify=False)
        response.raise_for_status()
        return True
