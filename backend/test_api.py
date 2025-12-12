#!/usr/bin/env python3
import requests
import json

response = requests.get('http://localhost:8000/api/v1/employees/?page_size=1')
data = response.json()

if data['data']['data']:
    employee = data['data']['data'][0]
    print(f"Employee: {employee['first_name']} {employee['last_name']}")
    print(f"Position: {employee.get('position', {}).get('name', 'N/A')}")
    print(f"Department: {employee.get('department', {}).get('name', 'N/A')}")
    print(f"Manager: {employee.get('manager', {}).get('first_name', 'N/A')} {employee.get('manager', {}).get('last_name', '')}")
    print("\nFull employee data:")
    print(json.dumps(employee, indent=2, default=str))
else:
    print("No employees found")
