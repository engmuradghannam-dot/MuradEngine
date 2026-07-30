#!/bin/bash
# ============================================================
# MuradEngine GPU Cluster - AWS Free Tier + Spot GPU
# ============================================================
# AWS Free Tier: 750 hours/month t2.micro (CPU only)
# For GPU: Use spot instances (p3.2xlarge ~ $0.30/hour)

# Step 1: Launch EC2 Spot Instance with GPU
aws ec2 request-spot-instances \
    --spot-price "0.50" \
    --instance-count 1 \
    --type "one-time" \
    --launch-specification file://specs.json

# specs.json:
# {
#   "ImageId": "ami-0c55b159cbfafe1f0",
#   "InstanceType": "p3.2xlarge",
#   "KeyName": "your-key",
#   "SecurityGroupIds": ["sg-xxxx"],
#   "UserData": "base64-encoded-setup-script"
# }

# Step 2: SSH into instance
ssh -i your-key.pem ubuntu@<instance-ip>

# Step 3: Setup
sudo apt update
sudo apt install -y python3-pip git
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip3 install fastapi uvicorn scikit-learn numpy matplotlib

git clone https://github.com/engmuradghannam-dot/MuradEngine.git
cd MuradEngine

# Step 4: Run with CUDA
python3 gpu_cluster/gpu_cluster_engine_v10.py

# Cost: ~$0.30/hour for p3.2xlarge (V100 GPU)
# Free alternative: g4dn.xlarge ~$0.16/hour (T4 GPU)
