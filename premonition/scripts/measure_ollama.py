import requests
import time
import json

URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"

def measure_prompt(prompt, label):
    print(f"\n--- Testing: {label} ---")
    start_time = time.time()
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "5m"
    }
    
    try:
        response = requests.post(URL, json=payload)
        response.raise_for_status()
        end_time = time.time()
        
        data = response.json()
        latency = end_time - start_time
        
        print(f"Latency: {latency:.2f} seconds")
        print(f"Tokens/sec: {data.get('eval_count', 0) / (data.get('eval_duration', 1) / 1e9):.2f}")
        print(f"Response: {data.get('response', '')[:100]}...")
        return latency
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("Cold Start Test...")
    cold_time = measure_prompt("hello", "Cold Start (hello)")
    
    print("\nWarm Start Test...")
    warm_time1 = measure_prompt("summarize patient with sepsis risk", "Warm Start (summarize)")
    warm_time2 = measure_prompt("what is the recommended treatment for sepsis?", "Warm Start (recommendation)")
    
    if warm_time1 and warm_time2:
        avg_warm = (warm_time1 + warm_time2) / 2
        print(f"\nAverage Warm Response Time: {avg_warm:.2f} seconds")
        if avg_warm < 5:
            print("Target (< 5s): PASS")
        else:
            print("Target (< 5s): FAIL")
