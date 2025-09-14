#!/bin/bash

# 🚀 ONE COMMAND DEPLOY - CriptoBot to Google Cloud
# Usage: ./deploy_one_command.sh YOUR_PROJECT_ID

PROJECT_ID=${1:-"cripto-bot-project"}
VM_NAME="cripto-bot-vm" 
ZONE="us-central1-a"

echo "🚀 DEPLOYING CRIPTO BOT TO GOOGLE CLOUD..."
echo "Project: $PROJECT_ID | VM: $VM_NAME | Zone: $ZONE"

# Set project
gcloud config set project $PROJECT_ID 2>/dev/null || echo "Using default project"

# Create VM and deploy in one command
gcloud compute instances create $VM_NAME \
  --zone=$ZONE \
  --machine-type=e2-micro \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --tags=http-server,https-server,cripto-bot \
  --metadata=startup-script='#!/bin/bash
  
  # Install dependencies
  apt-get update -y
  apt-get install -y python3 python3-pip git
  
  # Create bot directory
  mkdir -p /opt/cripto-bot
  cd /opt/cripto-bot
  
  # Install Python packages
  pip3 install pandas numpy python-binance pandas-ta streamlit plotly
  
  # Download bot from GitHub
  wget https://raw.githubusercontent.com/Joseph9202/CriptoBot/main/trader_24_7.py
  wget https://raw.githubusercontent.com/Joseph9202/CriptoBot/main/dashboard_simple.py
  wget https://raw.githubusercontent.com/Joseph9202/CriptoBot/main/bot_simple.py
  
  # Start bot in background
  nohup python3 trader_24_7.py > /tmp/bot.log 2>&1 &
  
  # Start dashboard
  nohup python3 -m streamlit run dashboard_simple.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > /tmp/dashboard.log 2>&1 &
  
  echo "✅ CriptoBot deployed and running!" > /tmp/deployment_complete
  ' 2>/dev/null || echo "VM may already exist"

# Configure firewall
gcloud compute firewall-rules create allow-cripto-bot \
  --allow tcp:8501 \
  --source-ranges 0.0.0.0/0 \
  --target-tags cripto-bot 2>/dev/null || echo "Firewall rule exists"

# Wait a moment
echo "⏳ Waiting for deployment (60 seconds)..."
sleep 60

# Get external IP
EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null)

echo ""
echo "🎉 DEPLOYMENT COMPLETED!"
echo "🌐 Dashboard: http://$EXTERNAL_IP:8501"
echo "🤖 Bot running 24/7 automatically"
echo "🔗 SSH: gcloud compute ssh $VM_NAME --zone=$ZONE"
echo ""
echo "✅ Your CriptoBot is now live in Google Cloud!"