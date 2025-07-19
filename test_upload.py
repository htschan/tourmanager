#!/usr/bin/env python3
import requests
import os
import sys

# Configuration
API_URL = "http://localhost:8000"
LOGIN_URL = f"{API_URL}/token"
UPLOAD_URL = f"{API_URL}/api/tours/upload"

# Default credentials - replace with actual values
USERNAME = "admin"
PASSWORD = "admin"

def login(username, password):
    """Get authentication token"""
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(LOGIN_URL, data=data)
    
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return None
    
    return response.json()["access_token"]

def upload_gpx(token, gpx_file_path):
    """Upload a GPX file"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(gpx_file_path, 'rb') as f:
        files = {
            'file': (os.path.basename(gpx_file_path), f, 'application/gpx+xml')
        }
        response = requests.post(UPLOAD_URL, headers=headers, files=files)
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response.status_code == 200

def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_test.py <gpx_file> [username] [password]")
        sys.exit(1)
    
    gpx_file = sys.argv[1]
    username = sys.argv[2] if len(sys.argv) > 2 else USERNAME
    password = sys.argv[3] if len(sys.argv) > 3 else PASSWORD
    
    if not os.path.exists(gpx_file):
        print(f"Error: File {gpx_file} not found.")
        sys.exit(1)
    
    print(f"Logging in as {username}...")
    token = login(username, password)
    
    if not token:
        print("Authentication failed.")
        sys.exit(1)
    
    print(f"Uploading file {gpx_file}...")
    success = upload_gpx(token, gpx_file)
    
    if success:
        print("Upload successful!")
    else:
        print("Upload failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
