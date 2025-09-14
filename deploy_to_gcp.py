#!/usr/bin/env python3

import subprocess
import sys
import os
import time
import json
from pathlib import Path

class GCPCriptoBotDeployer:
    """Deployer optimizado para Google Cloud VM"""
    
    def __init__(self):
        self.project_name = "cripto-bot-vm"
        self.vm_name = "cripto-bot-instance"
        self.zone = "us-central1-a"
        self.required_files = [
            'trader_24_7.py',
            'demo_trader_activo.py', 
            'dashboard_simple.py',
            'requirements.txt',
            'bot_simple.py',
            'test_bot.py'
        ]
    
    def print_banner(self):
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                🌩️ CRIPTO BOT - GOOGLE CLOUD DEPLOY               ║
║              Deployment optimizado para máxima eficiencia        ║
║                     💰 Trading 24/7 en la nube                  ║
╚══════════════════════════════════════════════════════════════════╝
        """)
    
    def check_gcloud_auth(self):
        """Verifica autenticación de Google Cloud"""
        try:
            result = subprocess.run(['gcloud', 'auth', 'list'], capture_output=True, text=True)
            return 'ACTIVE' in result.stdout
        except:
            return False
    
    def create_deployment_package(self):
        """Crea paquete optimizado para deployment"""
        print("📦 Creando paquete de deployment optimizado...")
        
        # Crear directorio temporal
        deploy_dir = Path("./gcp_deploy_package")
        deploy_dir.mkdir(exist_ok=True)
        
        # Copiar solo archivos esenciales
        essential_files = {
            'trader_24_7.py': 'Bot principal 24/7',
            'demo_trader_activo.py': 'Demo rápido',
            'dashboard_simple.py': 'Dashboard web',
            'bot_simple.py': 'Bot básico',
            'test_bot.py': 'Bot de pruebas',
            'requirements.txt': 'Dependencias'
        }
        
        for file, desc in essential_files.items():
            if os.path.exists(file):
                subprocess.run(['cp', file, str(deploy_dir)], check=True)
                print(f"   ✅ {file} - {desc}")
            else:
                print(f"   ⚠️ {file} - No encontrado")
        
        # Crear requirements optimizado para VM
        optimized_requirements = """
pandas>=1.5.0
numpy>=1.21.0
python-binance>=1.0.16
pandas-ta>=0.3.14b
streamlit>=1.28.0
plotly>=5.0.0
        """.strip()
        
        with open(deploy_dir / "requirements_vm.txt", "w") as f:
            f.write(optimized_requirements)
        
        # Crear script de inicio automático
        startup_script = """#!/bin/bash

# CriptoBot Auto-Start Script for Google Cloud VM
echo "🚀 Iniciando CriptoBot en Google Cloud VM"

# Actualizar sistema
sudo apt-get update -y

# Instalar Python y pip si no existen
sudo apt-get install -y python3 python3-pip python3-venv

# Crear directorio del bot
mkdir -p /home/cripto_bot
cd /home/cripto_bot

# Crear entorno virtual
python3 -m venv bot_env
source bot_env/bin/activate

# Instalar dependencias optimizadas
pip install --upgrade pip
pip install pandas numpy python-binance pandas-ta streamlit plotly

# Configurar firewall para dashboard
sudo ufw allow 8501
sudo ufw allow 8080

# Crear servicio systemd para bot 24/7
sudo tee /etc/systemd/system/cripto-bot.service > /dev/null <<EOF
[Unit]
Description=CriptoBot 24/7 Trading Bot
After=network.target

[Service]
Type=simple
User=\$USER
WorkingDirectory=/home/cripto_bot
Environment=PATH=/home/cripto_bot/bot_env/bin
ExecStart=/home/cripto_bot/bot_env/bin/python trader_24_7.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Crear servicio para dashboard
sudo tee /etc/systemd/system/cripto-dashboard.service > /dev/null <<EOF
[Unit]
Description=CriptoBot Dashboard
After=network.target

[Service]
Type=simple
User=\$USER
WorkingDirectory=/home/cripto_bot
Environment=PATH=/home/cripto_bot/bot_env/bin
ExecStart=/home/cripto_bot/bot_env/bin/streamlit run dashboard_simple.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilitar servicios
sudo systemctl daemon-reload
sudo systemctl enable cripto-bot.service
sudo systemctl enable cripto-dashboard.service

echo "✅ CriptoBot configurado para inicio automático"
echo "🌐 Dashboard disponible en: http://EXTERNAL_IP:8501"
        """
        
        with open(deploy_dir / "vm_startup.sh", "w") as f:
            f.write(startup_script)
        
        # Crear script de deployment
        deploy_script = f"""#!/bin/bash

# Script de deployment automático para Google Cloud

echo "🌩️ Deploying CriptoBot to Google Cloud VM"

# Variables
PROJECT_NAME="{self.project_name}"
VM_NAME="{self.vm_name}"
ZONE="{self.zone}"

# Crear VM si no existe
gcloud compute instances create $VM_NAME \\
    --project=$PROJECT_NAME \\
    --zone=$ZONE \\
    --machine-type=e2-micro \\
    --network-interface=network-tier=PREMIUM,subnet=default \\
    --maintenance-policy=MIGRATE \\
    --provisioning-model=STANDARD \\
    --service-account=default \\
    --scopes=https://www.googleapis.com/auth/cloud-platform \\
    --create-disk=auto-delete=yes,boot=yes,device-name=$VM_NAME,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20240307b,mode=rw,size=20,type=projects/$PROJECT_NAME/zones/$ZONE/diskTypes/pd-standard \\
    --no-shielded-secure-boot \\
    --shielded-vtpm \\
    --shielded-integrity-monitoring \\
    --labels=environment=production,app=cripto-bot \\
    --reservation-affinity=any \\
    --tags=http-server,https-server,cripto-bot \\
    2>/dev/null || echo "VM ya existe o error al crear"

# Configurar reglas de firewall
gcloud compute firewall-rules create allow-cripto-dashboard \\
    --allow tcp:8501 \\
    --source-ranges 0.0.0.0/0 \\
    --description "Allow CriptoBot Dashboard" \\
    2>/dev/null || echo "Regla de firewall ya existe"

# Copiar archivos a VM
echo "📤 Subiendo archivos al VM..."
gcloud compute scp --recurse ./* $VM_NAME:/tmp/cripto_bot_deploy --zone=$ZONE

# Ejecutar setup en VM
echo "⚙️ Configurando bot en VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
    # Mover archivos a directorio final
    sudo mkdir -p /home/cripto_bot
    sudo cp -r /tmp/cripto_bot_deploy/* /home/cripto_bot/
    cd /home/cripto_bot
    
    # Hacer ejecutable el script de startup
    chmod +x vm_startup.sh
    
    # Ejecutar configuración
    sudo ./vm_startup.sh
    
    # Iniciar servicios
    sudo systemctl start cripto-bot.service
    sudo systemctl start cripto-dashboard.service
    
    echo '✅ CriptoBot deployment completado'
    echo '📊 Estado de servicios:'
    sudo systemctl status cripto-bot.service --no-pager
    sudo systemctl status cripto-dashboard.service --no-pager
"

# Obtener IP externa
EXTERNAL_IP=\$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "✅ DEPLOYMENT COMPLETADO"
echo "🤖 Bot 24/7 ejecutándose en background"
echo "🌐 Dashboard disponible en: http://\$EXTERNAL_IP:8501"
echo "🔍 SSH access: gcloud compute ssh $VM_NAME --zone=$ZONE"
        """
        
        with open(deploy_dir / "deploy.sh", "w") as f:
            f.write(deploy_script)
        
        # Hacer ejecutable
        os.chmod(deploy_dir / "deploy.sh", 0o755)
        os.chmod(deploy_dir / "vm_startup.sh", 0o755)
        
        print(f"✅ Paquete creado en: {deploy_dir}")
        return deploy_dir
    
    def create_monitoring_script(self, deploy_dir):
        """Crea script de monitoreo"""
        monitoring_script = f"""#!/bin/bash

# Script de monitoreo para CriptoBot en GCP
VM_NAME="{self.vm_name}"
ZONE="{self.zone}"

echo "📊 MONITOREO CRIPTO BOT - GOOGLE CLOUD"
echo "=" * 50

# Estado de VM
echo "🖥️ Estado de VM:"
gcloud compute instances describe $VM_NAME --zone=$ZONE --format="table(status,machineType,networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)"

# Obtener IP
EXTERNAL_IP=\$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "🌐 Dashboard URL: http://\$EXTERNAL_IP:8501"

# Estado de servicios
echo "🤖 Estado de servicios:"
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
    echo 'Bot 24/7:'
    sudo systemctl status cripto-bot.service --no-pager | head -10
    echo ''
    echo 'Dashboard:'
    sudo systemctl status cripto-dashboard.service --no-pager | head -10
    echo ''
    echo 'Logs recientes del bot:'
    sudo journalctl -u cripto-bot.service --no-pager -n 5
"

echo "✅ Monitoreo completado"
        """
        
        with open(deploy_dir / "monitor.sh", "w") as f:
            f.write(monitoring_script)
        
        os.chmod(deploy_dir / "monitor.sh", 0o755)
    
    def run_deployment(self):
        """Ejecuta deployment completo"""
        self.print_banner()
        
        # Verificar autenticación
        if not self.check_gcloud_auth():
            print("❌ Google Cloud no autenticado")
            print("💡 Ejecuta: gcloud auth login")
            return False
        
        print("✅ Google Cloud autenticado")
        
        # Crear paquete
        deploy_dir = self.create_deployment_package()
        
        # Crear script de monitoreo
        self.create_monitoring_script(deploy_dir)
        
        print(f"""
🚀 DEPLOYMENT PACKAGE CREADO

📦 Archivos en: {deploy_dir}
   ✅ Bot principal (trader_24_7.py)
   ✅ Dashboard web (dashboard_simple.py)
   ✅ Scripts de deployment automático
   ✅ Configuración de servicios systemd
   ✅ Monitoreo y logs

🎯 PRÓXIMOS PASOS:

1. Navegar al directorio:
   cd {deploy_dir}

2. Ejecutar deployment:
   ./deploy.sh

3. Monitorear el bot:
   ./monitor.sh

⚡ EL BOT FUNCIONARÁ 24/7 AUTOMÁTICAMENTE
🌐 DASHBOARD ACCESIBLE DESDE CUALQUIER LUGAR
        """)
        
        # Preguntar si ejecutar deployment automático
        response = input("\n🚀 ¿Ejecutar deployment automático ahora? (s/n): ")
        
        if response.lower() == 's':
            print("🚀 Ejecutando deployment...")
            os.chdir(deploy_dir)
            subprocess.run(['./deploy.sh'])
        else:
            print(f"💡 Para deployar manualmente: cd {deploy_dir} && ./deploy.sh")
        
        return True

def main():
    """Función principal"""
    deployer = GCPCriptoBotDeployer()
    deployer.run_deployment()

if __name__ == "__main__":
    main()