import json
import urllib.request
import time

def run_benchmark(model: str):
    print(f"\n--- Benchmarking {model} ---")
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": "Explain the cardiovascular system in exactly 50 words.",
        "stream": False,
        "keep_alive": "5m"
    }

    try:
        # 1. Warm-up / Cold Start
        start = time.time()
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
        cold_latency = time.time() - start
        print(f"Cold Start Latency: {cold_latency:.2f}s")
        
        # Check GPU vs CPU
        req_ps = urllib.request.Request("http://localhost:11434/api/ps")
        with urllib.request.urlopen(req_ps) as resp:
            ps_data = json.loads(resp.read().decode("utf-8"))
            models = ps_data.get("models", [])
            hw = "CPU"
            vram = 0
            size = 1
            for m in models:
                if m.get("name") == model:
                    vram = m.get("size_vram", 0)
                    size = m.get("size", 1)
                    hw = "GPU" if vram > 0 else "CPU"
            print(f"Hardware Inference: {hw} (VRAM: {vram/(1024**2):.1f}MB / Size: {size/(1024**2):.1f}MB)")

        # 2. Warm Latency & Tokens/sec
        print("Running 3 warm iterations...")
        latencies = []
        tokens_per_sec = []
        for i in range(3):
            start = time.time()
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode("utf-8"))
            latency = time.time() - start
            
            eval_count = res.get("eval_count", 0)
            eval_duration = res.get("eval_duration", 0)
            tps = (eval_count / eval_duration) * 1e9 if eval_duration > 0 else 0
            
            latencies.append(latency)
            tokens_per_sec.append(tps)
            
        avg_latency = sum(latencies) / len(latencies)
        avg_tps = sum(tokens_per_sec) / len(tokens_per_sec)
        
        print(f"Average Warm Latency: {avg_latency:.2f}s")
        print(f"Average Tokens/sec: {avg_tps:.2f} t/s")
    except Exception as e:
        print(f"Failed to benchmark {model}: {e}")

if __name__ == "__main__":
    run_benchmark("llama3:latest")
    run_benchmark("qwen2.5:7b")
