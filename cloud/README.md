# MuradEngine Cloud GPU Setup Guide

## Free GPU Options

### 1. Google Colab (Recommended - Free)
- **GPU**: NVIDIA T4 (12GB VRAM)
- **Runtime**: 12 hours max per session
- **RAM**: 12GB system + 12GB GPU
- **Setup**:
  ```bash
  # In Colab notebook
  !git clone https://github.com/engmuradghannam-dot/MuradEngine.git
  %cd MuradEngine
  !pip install -r requirements.txt
  !python cloud/colab_gpu_setup.py
  ```
- **Expose**: Use `ngrok` or Colab's public URL
- **Speed**: ~200,000 keys/sec

### 2. Kaggle (Free)
- **GPU**: NVIDIA P100 (16GB VRAM)
- **Runtime**: 9 hours max per session
- **RAM**: 16GB system + 16GB GPU
- **Setup**:
  ```bash
  # In Kaggle notebook
  !git clone https://github.com/engmuradghannam-dot/MuradEngine.git
  !pip install -r requirements.txt
  !python cloud/kaggle_gpu_setup.py
  ```
- **Speed**: ~300,000 keys/sec

### 3. AWS Free Tier + Spot (Almost Free)
- **Free Tier**: 750 hours/month t2.micro (CPU only)
- **Spot GPU**: g4dn.xlarge (T4) ~$0.16/hour
- **Setup**: Run `cloud/aws_gpu_setup.sh`
- **Speed**: ~250,000 keys/sec

## Multi-VM Cluster

### Architecture
```
Master Node (Railway/Local)
    |
    +---> Google Colab (T4)     ----+
    +---> Kaggle (P100)         ----+---> Unified Results
    +---> AWS Spot (T4)         ----+
    +---> AWS Free (CPU)        ----+
```

### Setup Steps

1. **Start Workers**:
   ```bash
   # Terminal 1: Colab
   python cloud/colab_gpu_setup.py

   # Terminal 2: Kaggle
   python cloud/kaggle_gpu_setup.py

   # Terminal 3: AWS
   bash cloud/aws_gpu_setup.sh
   ```

2. **Configure Orchestrator**:
   ```bash
   # Edit workers.json with your endpoints
   python cloud/multi_vm_orchestrator.py
   ```

3. **Run Distributed Analysis**:
   ```python
   from cloud.multi_vm_orchestrator import MultiVMOrchestrator

   orch = MultiVMOrchestrator()
   orch.discover_workers()

   ranges = [
       (0, 2**64),
       (2**64, 2**128),
       (2**128, 2**192),
       (2**192, 2**250),
       (2**250, N),
   ]

   results = orch.distribute_work(ranges, samples_per_range=100_000)
   ```

## Performance Comparison

| Platform | GPU | VRAM | Speed | Cost | Limit |
|----------|-----|------|-------|------|-------|
| Colab Free | T4 | 12GB | 200K/s | $0 | 12hrs/session |
| Kaggle Free | P100 | 16GB | 300K/s | $0 | 9hrs/session |
| AWS Free | CPU | - | 20K/s | $0 | 750hrs/mo |
| AWS Spot | T4 | 16GB | 250K/s | $0.16/hr | None |
| AWS p3 | V100 | 16GB | 500K/s | $0.30/hr | None |

## Total Free Capacity

With 1 Colab + 1 Kaggle + 1 AWS Free:
- **Total VRAM**: 12 + 16 + 0 = 28GB
- **Total Speed**: 200K + 300K + 20K = 520K keys/sec
- **Monthly Hours**: 12×30 + 9×30 + 750 = 1,380 hours
- **Max Keys/Month**: 520K × 3,600 × 1,380 = **2.58 TRILLION keys**

## Notes

- Colab and Kaggle sessions expire after inactivity
- Use `ngrok` or similar to expose local servers
- AWS Free Tier resets monthly
- Spot instances can be interrupted (save checkpoints)
