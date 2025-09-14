#!/bin/bash

# 🌩️ QUICK DEPLOY - CriptoBot to Google Cloud VM
# Script optimizado para deployment ultra-rápido

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║               🌩️ CRIPTO BOT - QUICK GCP DEPLOY                   ║"
echo "║              Ultra-fast deployment to Google Cloud               ║"
echo "╚══════════════════════════════════════════════════════════════════╝"

# Variables
PROJECT_ID="your-project-id"  # Replace with your project
VM_NAME="cripto-bot-vm"
ZONE="us-central1-a"
MACHINE_TYPE="e2-micro"

print_status "Verificando Google Cloud CLI..."

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    print_error "Google Cloud no está autenticado"
    echo "Ejecuta: gcloud auth login"
    exit 1
fi

print_success "Google Cloud CLI autenticado"

# Set project if provided
if [ "$1" != "" ]; then
    PROJECT_ID="$1"
    gcloud config set project $PROJECT_ID
fi

print_status "Proyecto: $PROJECT_ID"

# Check if VM already exists
if gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
    print_warning "VM $VM_NAME ya existe. ¿Eliminar y recrear? (s/n)"
    read -r response
    if [[ "$response" == "s" ]]; then
        print_status "Eliminando VM existente..."
        gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet
    else
        print_status "Usando VM existente"
    fi
fi

# Create VM if it doesn't exist
if ! gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
    print_status "Creando VM optimizada para CriptoBot..."
    
    gcloud compute instances create $VM_NAME \
        --zone=$ZONE \
        --machine-type=$MACHINE_TYPE \
        --image-family=ubuntu-2004-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=20GB \
        --boot-disk-type=pd-standard \
        --tags=http-server,https-server,cripto-bot \
        --metadata=startup-script='#!/bin/bash
        
# Update system
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git htop

# Create app directory
mkdir -p /opt/cripto-bot
cd /opt/cripto-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install optimized requirements
pip install --no-cache-dir pandas numpy python-binance pandas-ta streamlit plotly

echo "✅ VM Setup completed" > /tmp/setup_complete
        '
    
    print_success "VM creada: $VM_NAME"
else
    print_success "VM ya existe: $VM_NAME"
fi

# Configure firewall for dashboard access
print_status "Configurando firewall..."
gcloud compute firewall-rules create allow-cripto-dashboard \
    --allow tcp:8501 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow CriptoBot Dashboard access" \
    --target-tags cripto-bot 2>/dev/null || print_warning "Regla de firewall ya existe"

# Wait for VM to be ready
print_status "Esperando que VM esté lista..."
sleep 30

# Get external IP
EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
print_success "IP Externa: $EXTERNAL_IP"

# Create deployment package locally
print_status "Preparando archivos para deployment..."
TEMP_DIR=$(mktemp -d)
cp trader_24_7.py $TEMP_DIR/ 2>/dev/null || print_warning "trader_24_7.py no encontrado"
cp demo_trader_activo.py $TEMP_DIR/ 2>/dev/null || print_warning "demo_trader_activo.py no encontrado"
cp dashboard_simple.py $TEMP_DIR/ 2>/dev/null || print_warning "dashboard_simple.py no encontrado"
cp bot_simple.py $TEMP_DIR/ 2>/dev/null || print_warning "bot_simple.py no encontrado"

# Create optimized requirements for VM
cat > $TEMP_DIR/requirements.txt << EOF
pandas>=1.5.0
numpy>=1.21.0
python-binance>=1.0.16
pandas-ta>=0.3.14b
streamlit>=1.28.0
plotly>=5.0.0
EOF

# Create startup script for the bot
cat > $TEMP_DIR/start_bot.py << 'EOF'
#!/usr/bin/env python3

import subprocess
import sys
import os
import time
from pathlib import Path

def start_bot_24_7():
    """Inicia bot 24/7 en background"""
    print("🤖 Starting CriptoBot 24/7...")
    
    # Kill existing processes
    subprocess.run(['pkill', '-f', 'trader_24_7.py'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-f', 'dashboard_simple.py'], stderr=subprocess.DEVNULL)
    
    time.sleep(2)
    
    # Start bot in background
    if os.path.exists('trader_24_7.py'):
        bot_process = subprocess.Popen([
            sys.executable, 'trader_24_7.py'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ Bot 24/7 started with PID: {bot_process.pid}")
    
    # Start dashboard in background  
    if os.path.exists('dashboard_simple.py'):
        dashboard_process = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run', 'dashboard_simple.py',
            '--server.port', '8501', '--server.address', '0.0.0.0', '--server.headless', 'true'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ Dashboard started with PID: {dashboard_process.pid}")
    
    print("🌐 Dashboard URL: http://EXTERNAL_IP:8501")
    print("🤖 Bot running 24/7 in background")

def show_status():
    """Muestra estado de los procesos"""
    print("📊 CRIPTO BOT STATUS")
    print("-" * 30)
    
    # Check bot process
    bot_running = subprocess.run(['pgrep', '-f', 'trader_24_7.py'], 
                                capture_output=True, text=True)
    if bot_running.returncode == 0:
        print("🤖 Bot 24/7: ✅ Running")
    else:
        print("🤖 Bot 24/7: ❌ Stopped")
    
    # Check dashboard
    dashboard_running = subprocess.run(['pgrep', '-f', 'streamlit'], 
                                     capture_output=True, text=True)
    if dashboard_running.returncode == 0:
        print("🌐 Dashboard: ✅ Running")
    else:
        print("🌐 Dashboard: ❌ Stopped")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'status':
        show_status()
    else:
        start_bot_24_7()
EOF

chmod +x $TEMP_DIR/start_bot.py

print_status "Subiendo archivos a VM..."

# Copy files to VM
gcloud compute scp --recurse $TEMP_DIR/* $VM_NAME:/opt/cripto-bot/ --zone=$ZONE

print_status "Instalando y configurando bot en VM..."

# Setup and start bot on VM
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
cd /opt/cripto-bot

# Wait for initial setup to complete
echo 'Waiting for VM setup to complete...'
while [ ! -f /tmp/setup_complete ]; do
    sleep 5
done

# Activate virtual environment
source venv/bin/activate

# Install any missing dependencies
pip install --no-cache-dir pandas numpy python-binance pandas-ta streamlit plotly

# Start the bot
python3 start_bot.py

echo '✅ CriptoBot deployment completed successfully!'
echo '🌐 Dashboard available at: http://$EXTERNAL_IP:8501'
"

# Clean up temporary files
rm -rf $TEMP_DIR

print_success "🎉 DEPLOYMENT COMPLETADO!"
echo ""
echo "🚀 ACCESO A TU CRIPTO BOT:"
echo "   🌐 Dashboard: http://$EXTERNAL_IP:8501"
echo "   🖥️ SSH VM: gcloud compute ssh $VM_NAME --zone=$ZONE"
echo ""
echo "🤖 COMANDOS ÚTILES:"
echo "   Ver status: gcloud compute ssh $VM_NAME --zone=$ZONE --command='cd /opt/cripto-bot && python3 start_bot.py status'"
echo "   Reiniciar: gcloud compute ssh $VM_NAME --zone=$ZONE --command='cd /opt/cripto-bot && python3 start_bot.py'"
echo "   Ver logs: gcloud compute ssh $VM_NAME --zone=$ZONE --command='cd /opt/cripto-bot && tail -f trader_24_7.log'"
echo ""
print_success "✅ Bot ejecutándose 24/7 en Google Cloud!"

# Open dashboard in browser (optional)
if command -v xdg-open > /dev/null; then
    print_status "Abriendo dashboard en navegador..."
    xdg-open "http://$EXTERNAL_IP:8501"
fi