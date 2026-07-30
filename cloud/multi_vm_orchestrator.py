#!/usr/bin/env python3
"""
MuradEngine Multi-VM Orchestrator v12.0
Connects multiple free GPU instances (Colab + Kaggle + AWS Free Tier)
into a unified distributed cluster.

Architecture:
  Master Node (Railway/Local) -> Task Queue -> Worker Nodes (GPU VMs)

Worker Types:
  - Google Colab Free: NVIDIA T4 (12GB VRAM)
  - Kaggle Free: NVIDIA P100 (16GB VRAM)  
  - AWS Free Tier: t2.micro (CPU only, 750hrs/month)
  - AWS Spot: g4dn.xlarge (T4, ~$0.16/hr)

Author: Murad Ghannam
Date: 2026-07-30
"""

import json
import time
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import numpy as np

@dataclass
class VMWorker:
    """Represents a single VM worker node"""
    id: str
    type: str  # 'colab', 'kaggle', 'aws_free', 'aws_spot'
    endpoint: str
    gpu_type: str  # 'T4', 'P100', 'CPU'
    vram_gb: float
    status: str = 'idle'
    last_ping: float = 0.0
    tasks_completed: int = 0

    def ping(self) -> bool:
        """Check if worker is alive"""
        try:
            resp = requests.get(f"{self.endpoint}/health", timeout=5)
            self.last_ping = time.time()
            self.status = 'online' if resp.status_code == 200 else 'error'
            return resp.status_code == 200
        except:
            self.status = 'offline'
            return False

    def submit_task(self, task: Dict) -> Dict:
        """Submit a task to this worker"""
        try:
            resp = requests.post(
                f"{self.endpoint}/process_batch", 
                json=task, 
                timeout=300
            )
            self.tasks_completed += 1
            return resp.json()
        except Exception as e:
            return {"error": str(e), "worker": self.id}


class MultiVMOrchestrator:
    """Orchestrates multiple VM workers into a unified cluster"""

    def __init__(self):
        self.workers: List[VMWorker] = []
        self.task_queue = []
        self.results = []
        self.lock = threading.Lock()

    def register_worker(self, worker: VMWorker):
        """Register a new worker VM"""
        self.workers.append(worker)
        print(f"✅ Registered worker: {worker.id} ({worker.gpu_type})")

    def discover_workers(self, config_file: str = "workers.json"):
        """Load workers from config file"""
        try:
            with open(config_file, 'r') as f:
                configs = json.load(f)

            for cfg in configs.get('workers', []):
                worker = VMWorker(**cfg)
                if worker.ping():
                    self.register_worker(worker)
                else:
                    print(f"⚠️ Worker {worker.id} is offline")

            print(f"\n📊 Total online workers: {len(self.workers)}")

        except FileNotFoundError:
            print(f"⚠️ Config file {config_file} not found")
            print("Creating template...")
            self._create_template_config(config_file)

    def _create_template_config(self, filename: str):
        """Create a template worker config"""
        template = {
            "workers": [
                {
                    "id": "colab-1",
                    "type": "colab",
                    "endpoint": "https://xxxxx.ngrok.io",  # Colab ngrok URL
                    "gpu_type": "T4",
                    "vram_gb": 12.0
                },
                {
                    "id": "kaggle-1", 
                    "type": "kaggle",
                    "endpoint": "https://yyyyy.ngrok.io",  # Kaggle ngrok URL
                    "gpu_type": "P100",
                    "vram_gb": 16.0
                },
                {
                    "id": "aws-spot-1",
                    "type": "aws_spot",
                    "endpoint": "http://ec2-xx-xx-xx-xx.compute-1.amazonaws.com:8000",
                    "gpu_type": "T4",
                    "vram_gb": 16.0
                }
            ],
            "master": {
                "aggregation_strategy": "concatenate",
                "redundancy": 1
            }
        }

        with open(filename, 'w') as f:
            json.dump(template, f, indent=2)

        print(f"✅ Created template: {filename}")
        print("   Edit this file with your actual worker endpoints")

    def distribute_work(self, ranges: List[tuple], samples_per_range: int) -> Dict:
        """Distribute work across all workers"""

        if not self.workers:
            print("❌ No workers available!")
            return {}

        print("\n" + "=" * 60)
        print("🚀 DISTRIBUTING WORK ACROSS CLUSTER")
        print("=" * 60)

        # Calculate work per worker
        total_work = len(ranges) * samples_per_range
        work_per_worker = total_work // len(self.workers)

        tasks = []
        for i, (r_start, r_end) in enumerate(ranges):
            worker = self.workers[i % len(self.workers)]
            task = {
                "range_start": r_start,
                "range_end": r_end,
                "samples": samples_per_range // len(ranges),
                "worker_id": worker.id
            }
            tasks.append((worker, task))

        # Execute in parallel
        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=len(self.workers)) as executor:
            futures = {
                executor.submit(w.submit_task, t): (w.id, t) 
                for w, t in tasks
            }

            for future in as_completed(futures):
                worker_id, task = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"   ✅ {worker_id}: {result.get('keys_generated', 0):,} keys")
                except Exception as e:
                    print(f"   ❌ {worker_id}: {e}")

        elapsed = time.time() - start_time
        total_keys = sum(r.get('keys_generated', 0) for r in results)

        print(f"\n📊 Results:")
        print(f"   Workers: {len(self.workers)}")
        print(f"   Total Keys: {total_keys:,}")
        print(f"   Time: {elapsed:.1f}s")
        print(f"   Speed: {total_keys/elapsed:,.0f} keys/sec")

        return {
            "workers_used": len(self.workers),
            "total_keys": total_keys,
            "elapsed_seconds": elapsed,
            "speed": total_keys / elapsed,
            "results": results
        }

    def get_cluster_stats(self) -> Dict:
        """Get cluster-wide statistics"""
        stats = {
            "total_workers": len(self.workers),
            "online_workers": sum(1 for w in self.workers if w.status == 'online'),
            "total_vram": sum(w.vram_gb for w in self.workers),
            "total_tasks": sum(w.tasks_completed for w in self.workers),
            "workers": [asdict(w) for w in self.workers]
        }
        return stats

    def health_check(self):
        """Run health check on all workers"""
        print("\n🏥 CLUSTER HEALTH CHECK")
        print("=" * 60)

        for worker in self.workers:
            is_online = worker.ping()
            status = "🟢 ONLINE" if is_online else "🔴 OFFLINE"
            print(f"   {worker.id:15} {status} | {worker.gpu_type} | {worker.vram_gb}GB VRAM")


def create_worker_server():
    """Create a FastAPI server for worker nodes"""
    from fastapi import FastAPI
    from pydantic import BaseModel

    app = FastAPI(title="MuradEngine Worker Node")

    class BatchTask(BaseModel):
        range_start: int
        range_end: int
        samples: int
        worker_id: str

    @app.get("/health")
    def health():
        import torch
        return {
            "status": "healthy",
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
            "cuda": torch.cuda.is_available()
        }

    @app.post("/process_batch")
    def process_batch(task: BatchTask):
        import sys
        sys.path.insert(0, 'gpu_cluster')
        from gpu_cluster_engine_v10 import GPUClusterEngineV10

        N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
        cluster = GPUClusterEngineV10(nodes=1000, batch_size=10000)

        ranges = [(task.range_start, task.range_end)]
        cluster.generate_keys_streaming(ranges, max_keys=task.samples)

        return {
            "worker_id": task.worker_id,
            "keys_generated": cluster.keys_generated,
            "features_shape": list(cluster.features.shape) if cluster.features is not None else None
        }

    return app


if __name__ == "__main__":
    # Demo: Create orchestrator and show capabilities
    print("=" * 60)
    print("MURADENGINE MULTI-VM ORCHESTRATOR v12.0")
    print("=" * 60)
    print()

    orchestrator = MultiVMOrchestrator()

    # Try to discover workers
    orchestrator.discover_workers()

    # Show cluster stats
    stats = orchestrator.get_cluster_stats()
    print(f"\n📊 Cluster Stats:")
    print(f"   Workers: {stats['online_workers']}/{stats['total_workers']} online")
    print(f"   Total VRAM: {stats['total_vram']:.1f} GB")

    # If no workers, show setup instructions
    if stats['total_workers'] == 0:
        print("\n" + "=" * 60)
        print("📝 SETUP INSTRUCTIONS")
        print("=" * 60)
        print("""
1. Google Colab (Free T4 GPU):
   - Open: https://colab.research.google.com
   - Runtime -> Change runtime type -> GPU
   - Run: cloud/colab_gpu_setup.py
   - Expose: !pip install pyngrok && ngrok http 8000
   - Copy ngrok URL to workers.json

2. Kaggle (Free P100 GPU):
   - Open: https://kaggle.com/notebooks
   - Settings -> Accelerator -> GPU P100
   - Upload: cloud/kaggle_gpu_setup.py
   - Expose: Use Kaggle's public URL or ngrok
   - Copy URL to workers.json

3. AWS Spot (Cheap GPU):
   - Run: cloud/aws_gpu_setup.sh
   - Get EC2 public IP
   - Add to workers.json

4. Edit workers.json with your endpoints
   - Run this script again
   - Workers will be discovered automatically
        """)
