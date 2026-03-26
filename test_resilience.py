import requests

# Test 1: Simulate data missing
print("--- TEST 1: Missing Data Defaulting ---")
# Wait, we can't easily drop demo_state since it's global inside the uvicorn process, unless we add an endpoint to clear it or restart.
