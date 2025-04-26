import requests
import json

# API endpoint URL
url = "http://localhost:8000/career/guidance"

# Test data
payload = {
    "education": "Bachelor's in Computer Science",
    "skills": ["Python", "SQL", "Machine Learning"],
    "experience": "2 years as Data Analyst",
    "certificates": "AWS Certified Developer",
    "target_job": "Data Scientist"
}

# Make the POST request
response = requests.post(url, json=payload)

# Print the response status and content
print(f"Status code: {response.status_code}")
print("Response:")
print(json.dumps(response.json(), indent=2)) 