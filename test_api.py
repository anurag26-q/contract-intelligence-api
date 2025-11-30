
import requests
import time
import sys

BASE_URL = "http://localhost:8000/api"

def test_api():
    print("Starting API tests...")
    
    # 1. Health Check
    try:
        resp = requests.get(f"{BASE_URL}/healthz")
        if resp.status_code == 200:
            print("Health check passed")
        else:
            print(f"Health check failed: {resp.status_code}")
            return
    except Exception as e:
        print(f"Health check failed: {e}")
        return

    # 2. Ingest
    print("\nTesting Ingest...")
    files = {'files': open('test_contract.pdf', 'rb')}
    resp = requests.post(f"{BASE_URL}/ingest", files=files)
    if resp.status_code == 201:
        data = resp.json()
        print(f"Ingest response: {data}")
        if not data.get('document_ids'):
            print("No document IDs returned")
            return
        doc_id = data['document_ids'][0]
        print(f"Ingest successful. Document ID: {doc_id}")
    else:
        print(f"Ingest failed: {resp.text}")
        return

    # Wait for processing
    print("Waiting for processing...")
    time.sleep(10)

    # 3. Extract
    print("\nTesting Extract...")
    resp = requests.post(f"{BASE_URL}/extract", json={'document_id': doc_id})
    if resp.status_code == 200:
        print("Extract successful")
        print(resp.json())
    else:
        print(f"Extract failed: {resp.text}")

    # 4. Ask
    print("\nTesting Ask...")
    resp = requests.post(f"{BASE_URL}/ask", json={'question': 'What is the termination notice period?', 'document_ids': [doc_id]})
    if resp.status_code == 200:
        print("Ask successful")
        print(resp.json()['answer'])
    else:
        print(f"Ask failed: {resp.text}")

    # 5. Audit
    print("\nTesting Audit...")
    resp = requests.post(f"{BASE_URL}/audit", json={'document_id': doc_id})
    if resp.status_code == 200:
        print("Audit successful")
        print(resp.json())
    else:
        print(f"Audit failed: {resp.text}")

if __name__ == "__main__":
    test_api()
