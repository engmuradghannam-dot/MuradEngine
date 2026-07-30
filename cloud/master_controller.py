#!/usr/bin/env python3
"""
MuradEngine Master Controller v13.0
Manages 1,000,000 Cloud GPU Workers in Parallel
Connects Local Machine + VMs into Unified Cluster

Architecture:
  Master (Your Machine) -> Redis Queue -> 1M Workers (Local + VMs)

Author: Murad Ghannam
Date: 2026-07-30
"""

import asyncio
import aiohttp
import redis.asyncio as redis
import json
import time
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp

# secp256k1 order
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

@dataclass
class WorkerNode:
    id: str
    host: str
    port: int
    gpu_type: str
    status: str = "idle"
    last_heartbeat: float = 0.0
    tasks_completed: int = 0

    @property
    def endpoint(self):
        return f"http://{self.host}:{self.port}"

class MasterController:
    """Controls 1,000,000 workers in parallel"""

    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.workers: Dict[str, WorkerNode] = {}
        self.total_workers = 1_000_000
        self.active_workers = 0
        self.task_queue = "muradengine:tasks"
        self.result_queue = "muradengine:results"

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(self.redis_url)
            print("✅ Connected to Redis")
        except:
            print("⚠️ Redis not available - using in-memory queue")
            self.redis_client = None

    def register_local_workers(self, count: int = 100):
        """Register local CPU workers"""
        for i in range(count):
            worker = WorkerNode(
                id=f"local-{i}",
                host="localhost",
                port=8000 + i,
                gpu_type="CPU"
            )
            self.workers[worker.id] = worker
        print(f"✅ Registered {count} local workers")

    def register_vm_workers(self, vm_configs: List[Dict]):
        """Register VM workers from config"""
        for cfg in vm_configs:
            worker = WorkerNode(**cfg)
            self.workers[worker.id] = worker
        print(f"✅ Registered {len(vm_configs)} VM workers")

    async def health_check_all(self):
        """Check health of all workers"""
        print("\n🏥 Health Check - All Workers")
        print("=" * 60)

        async with aiohttp.ClientSession() as session:
            tasks = []
            for worker in self.workers.values():
                task = self._check_worker(session, worker)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

        online = sum(1 for r in results if r is True)
        print(f"   Online: {online}/{len(self.workers)}")
        self.active_workers = online

    async def _check_worker(self, session: aiohttp.ClientSession, worker: WorkerNode):
        """Check single worker"""
        try:
            async with session.get(f"{worker.endpoint}/health", timeout=2) as resp:
                if resp.status == 200:
                    worker.status = "online"
                    worker.last_heartbeat = time.time()
                    return True
        except:
            worker.status = "offline"
        return False

    async def distribute_task(self, task: Dict) -> Dict:
        """Distribute task to available worker"""
        # Find online worker
        available = [w for w in self.workers.values() if w.status == "online"]
        if not available:
            return {"error": "No workers available"}

        worker = available[0]  # Round-robin would be better

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{worker.endpoint}/process",
                    json=task,
                    timeout=30
                ) as resp:
                    result = await resp.json()
                    worker.tasks_completed += 1
                    return result
            except Exception as e:
                return {"error": str(e), "worker": worker.id}

    async def run_massive_job(self, total_keys: int = 1_000_000_000):
        """Run massive job across all workers"""
        print("\n" + "=" * 60)
        print("🚀 MASSIVE JOB: %s Keys" % f"{total_keys:,}")
        print("=" * 60)
        print("Workers: %s" % f"{len(self.workers):,}")
        print("Active: %s" % f"{self.active_workers:,}")
        print()

        # Split work
        keys_per_worker = total_keys // len(self.workers)
        ranges = self._generate_ranges(len(self.workers))

        start_time = time.time()
        tasks = []

        for i, (worker, (r_start, r_end)) in enumerate(zip(self.workers.values(), ranges)):
            task = {
                "worker_id": worker.id,
                "range_start": r_start,
                "range_end": r_end,
                "samples": keys_per_worker,
                "batch_size": 10000
            }
            tasks.append(self.distribute_task(task))

        # Execute all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.time() - start_time
        total_generated = sum(
            r.get("keys_generated", 0) 
            for r in results 
            if isinstance(r, dict)
        )

        print("\n📊 Results:")
        print("   Total Keys: %s" % f"{total_generated:,}")
        print("   Time: %.1fs" % elapsed)
        print("   Speed: %s keys/sec" % f"{total_generated/elapsed:,.0f}")
        print("   Efficiency: %.1f%%" % (total_generated / total_keys * 100))

        return {
            "total_keys": total_generated,
            "elapsed": elapsed,
            "speed": total_generated / elapsed,
            "workers_used": len(self.workers),
            "results": results
        }

    def _generate_ranges(self, count: int) -> List[tuple]:
        """Generate key ranges for workers"""
        ranges = []
        step = N // count
        for i in range(count):
            start = i * step
            end = (i + 1) * step if i < count - 1 else N
            ranges.append((start, end))
        return ranges

    def get_cluster_stats(self) -> Dict:
        """Get full cluster statistics"""
        return {
            "total_workers": len(self.workers),
            "active_workers": self.active_workers,
            "total_capacity": len(self.workers) * 10000,  # per worker
            "workers_by_type": self._count_by_type(),
            "total_tasks_completed": sum(w.tasks_completed for w in self.workers.values())
        }

    def _count_by_type(self) -> Dict:
        counts = {}
        for w in self.workers.values():
            counts[w.gpu_type] = counts.get(w.gpu_type, 0) + 1
        return counts


# Standalone worker for local execution
class LocalWorker:
    """Local worker that processes tasks"""

    def __init__(self, worker_id: str, port: int):
        self.id = worker_id
        self.port = port
        self.tasks_completed = 0

    def process_task(self, task: Dict) -> Dict:
        """Process a batch of keys"""
        from gpu_cluster.gpu_cluster_engine_v10 import GPUClusterEngineV10

        N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
        cluster = GPUClusterEngineV10(nodes=1000, batch_size=task.get("batch_size", 10000))

        ranges = [(task["range_start"], task["range_end"])]
        cluster.generate_keys_streaming(ranges, max_keys=task["samples"])

        self.tasks_completed += 1

        return {
            "worker_id": self.id,
            "keys_generated": cluster.keys_generated,
            "status": "success"
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "master":
        # Run master
        async def main():
            controller = MasterController()
            await controller.connect()
            controller.register_local_workers(100)
            await controller.health_check_all()

            # Run massive job
            result = await controller.run_massive_job(1_000_000)
            print("\n✅ Job Complete!")
            print(json.dumps(result, indent=2))

        asyncio.run(main())

    elif len(sys.argv) > 1 and sys.argv[1] == "worker":
        # Run worker
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        worker_id = sys.argv[3] if len(sys.argv) > 3 else "worker-0"

        from fastapi import FastAPI
        import uvicorn

        app = FastAPI()
        worker = LocalWorker(worker_id, port)

        @app.get("/health")
        def health():
            return {"status": "healthy", "worker": worker_id}

        @app.post("/process")
        def process(task: dict):
            return worker.process_task(task)

        print(f"🚀 Worker {worker_id} starting on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
