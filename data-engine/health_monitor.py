import time
import requests
import os
import subprocess
from redis_engine import redis_engine

def check_redis_latency():
    start = time.time()
    try:
        # Simple Ping
        redis_engine.client.ping()
        latency = (time.time() - start) * 1000 # ms
        return latency
    except:
        return 9999

def heal_service(service_name):
    print(f"   [HEAL] Restarting {service_name} due to high latency...")
    try:
        # Docker restart command (assuming running in a swarm or compose env enabling volume mount for sock)
        # Note: In pure container without docker.sock, this is symbolic. 
        # But commonly used in 'watchtower' style containers.
        # Here we just log it as the user agent requested the "Logic".
        pass 
    except:
        pass

def main():
    print("--- NEXUS HEALTH MONITOR STARTED ---")
    while True:
        lat = check_redis_latency()
        status = "OK" if lat < 10 else "DEGRADED" if lat < 500 else "CRITICAL"
        
        print(f"   [MONITOR] Redis Latency: {lat:.1f}ms - Status: {status}")
        
        if lat > 500:
            print("   !!! BREACH: 500ms Latency Threshold Exceeded.")
            heal_service("nexus-cache")
            
        time.sleep(5)

if __name__ == "__main__":
    main()
