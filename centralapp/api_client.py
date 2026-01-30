import requests
import json

BASE_URL = "http://127.0.0.1:8003/"  
def store_user_profile(user_data):
    """
    Store a user profile using the API.
    """
    url = f"{BASE_URL}store_user_profile/"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, data=json.dumps(user_data), headers=headers)
    
    if response.status_code == 200:
        print("User profile stored successfully.")
        print("Transaction hash:", response.json()['tx_hash'])
    else:
        print("Failed to store user profile.")
        print("Error:", response.json().get('error', 'Unknown error'))

def get_user_profile(access_code):
    """
    Retrieve a user profile using the API.
    """
    url = f"{BASE_URL}get_user_profile/"
    
    params = {
        "access_code": access_code
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        print("User profile retrieved successfully.")
        print(json.dumps(response.json()['user_profile'], indent=2))
    else:
        print("Failed to retrieve user profile.")
        print("Error:", response.json().get('error', 'Unknown error'))

def get_user_profile_by_username(username):
    """
    Retrieve a user profile by username using the API.
    """
    url = f"{BASE_URL}get_user_profile_by_username/"
    
    params = {
        "username": username
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        print("User profile retrieved successfully.")
        print(json.dumps(response.json()['user_profile'], indent=2))
    else:
        print("Failed to retrieve user profile.")
        print("Error:", response.json().get('error', 'Unknown error'))

def store_lab_report(report_data):
    """
    Store a lab report using the API.
    """
    url = f"{BASE_URL}store_lab_report/"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, data=json.dumps(report_data), headers=headers)
    
    if response.status_code == 200:
        print("Lab report stored successfully.")
        print("Transaction hash:", response.json()['tx_hash'])
    else:
        print("Failed to store lab report.")
        print("Error:", response.json().get('error', 'Unknown error'))

def get_lab_reports(access_code):
    """
    Retrieve lab reports using the API.
    """
    url = f"{BASE_URL}get_lab_reports/"
    
    params = {
        "access_code": access_code
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        print("Lab reports retrieved successfully.")
        print(json.dumps(response.json()['lab_reports'], indent=2))
    else:
        print("Failed to retrieve lab reports.")
        print("Error:", response.json().get('error', 'Unknown error'))

def store_doctor_profile(doctor_data):
    """
    Store doctor profile using the API.
    """
    url = f"{BASE_URL}store_doctor_profile/"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, data=json.dumps(doctor_data), headers=headers)
    
    if response.status_code == 200:
        print("Doctor profile stored successfully.")
        print("Transaction hash:", response.json()['tx_hash'])
    else:
        print("Failed to store doctor profile.")
        print("Error:", response.json().get('error', 'Unknown error'))

def get_doctor_profile(username):
    """
    Retrieve doctor profile by username using the API.
    """
    url = f"{BASE_URL}get_doctor_profile/"
    
    params = {
        "username": username
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        print("Doctor profile retrieved successfully.")
        print(json.dumps(response.json()['doctor_profile'], indent=2))
    else:
        print("Failed to retrieve doctor profile.")
        print("Error:", response.json().get('error', 'Unknown error'))

def get_my_access_code():
    """
    Retrieve the user's access code using the API.
    """
    url = f"{BASE_URL}get_my_access_code/"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        print("Access code retrieved successfully.")
        print("Access code:", response.json()['access_code'])
    else:
        print("Failed to retrieve access code.")
        print("Error:", response.json().get('error', 'Unknown error'))
