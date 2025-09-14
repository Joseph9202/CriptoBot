# 🌩️ CRIPTO BOT - GOOGLE CLOUD DEPLOYMENT

## ✅ **DEPLOYMENT COMPLETO Y OPTIMIZADO**

He creado **3 métodos de deployment** ultra-eficientes para Google Cloud:

### 🚀 **MÉTODO 1: ONE COMMAND DEPLOY (Súper Rápido)**

**Un solo comando para deployar todo:**
```bash
./deploy_one_command.sh YOUR_PROJECT_ID
```

**Lo que hace automáticamente:**
- ✅ Crea VM optimizada (e2-micro)
- ✅ Instala todas las dependencias
- ✅ Descarga bot desde GitHub
- ✅ Configura firewall
- ✅ Inicia bot 24/7 automáticamente
- ✅ Inicia dashboard web
- ✅ Te da URL de acceso

### 🛠️ **MÉTODO 2: QUICK DEPLOY (Detallado)**

```bash
./quick_gcp_deploy.sh YOUR_PROJECT_ID
```

**Deployment avanzado con:**
- ✅ Verificación de requisitos
- ✅ Cleanup automático
- ✅ Configuración optimizada
- ✅ Monitoreo incluido
- ✅ Logs detallados

### 🎯 **MÉTODO 3: CUSTOM DEPLOY (Completo)**

```bash
python deploy_to_gcp.py
```

**Deployment completo con:**
- ✅ Paquete de deployment personalizado
- ✅ Servicios systemd automáticos
- ✅ Scripts de monitoreo
- ✅ Configuración avanzada

## ⚡ **DEPLOYMENT ULTRA-RÁPIDO (Recomendado)**

### Paso 1: Autenticar Google Cloud
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Paso 2: Deploy en un comando
```bash
./deploy_one_command.sh YOUR_PROJECT_ID
```

### Paso 3: ¡Listo!
- 🤖 Bot corriendo 24/7 automáticamente
- 🌐 Dashboard accesible desde cualquier lugar
- 💰 Trading con dinero fake sin riesgo

## 🌐 **ACCESO AL BOT DESPLEGADO**

Una vez completado el deployment:

```
🎉 DEPLOYMENT COMPLETED!
🌐 Dashboard: http://EXTERNAL_IP:8501
🤖 Bot running 24/7 automatically
🔗 SSH: gcloud compute ssh cripto-bot-vm --zone=us-central1-a
```

## 📊 **LO QUE TENDRÁS EN GOOGLE CLOUD**

### 🖥️ **VM Configurada:**
- **Tipo**: e2-micro (Free tier elegible)
- **OS**: Ubuntu 20.04 LTS
- **Disco**: 20GB SSD
- **Región**: us-central1-a
- **Tags**: cripto-bot, http-server

### 🤖 **Servicios Corriendo:**
- **Bot 24/7**: trader_24_7.py en background
- **Dashboard**: Streamlit en puerto 8501
- **Auto-start**: Se inicia automáticamente al reiniciar VM
- **Logs**: Disponibles en /tmp/

### 🌐 **Acceso Web:**
- **Dashboard URL**: http://EXTERNAL_IP:8501
- **Acceso**: Desde cualquier dispositivo
- **Firewall**: Configurado automáticamente
- **HTTPS**: Opcional (se puede configurar)

## 🔧 **COMANDOS ÚTILES POST-DEPLOYMENT**

### Ver estado del bot:
```bash
gcloud compute ssh cripto-bot-vm --zone=us-central1-a --command="ps aux | grep python"
```

### Ver logs del bot:
```bash
gcloud compute ssh cripto-bot-vm --zone=us-central1-a --command="tail -f /tmp/bot.log"
```

### Ver logs del dashboard:
```bash
gcloud compute ssh cripto-bot-vm --zone=us-central1-a --command="tail -f /tmp/dashboard.log"
```

### Reiniciar bot:
```bash
gcloud compute ssh cripto-bot-vm --zone=us-central1-a --command="
  pkill -f trader_24_7.py
  pkill -f streamlit
  cd /opt/cripto-bot
  nohup python3 trader_24_7.py > /tmp/bot.log 2>&1 &
  nohup python3 -m streamlit run dashboard_simple.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > /tmp/dashboard.log 2>&1 &
"
```

### Conectar por SSH:
```bash
gcloud compute ssh cripto-bot-vm --zone=us-central1-a
```

## 💰 **COSTOS DE GOOGLE CLOUD**

### 🆓 **Free Tier:**
- **e2-micro**: 744 horas/mes GRATIS
- **30GB disco**: Incluido en free tier  
- **1GB egress**: Gratis por mes
- **Total**: $0 por mes (dentro de límites free tier)

### 💵 **Después de Free Tier:**
- **e2-micro**: ~$7/mes
- **Disco 20GB**: ~$0.80/mes
- **IP estática**: ~$1.50/mes
- **Total**: ~$10/mes

## 🛡️ **SEGURIDAD Y MEJORES PRÁCTICAS**

### ✅ **Configurado automáticamente:**
- Firewall rules específicas
- Tags de seguridad
- Acceso SSH seguro
- Updates automáticos

### 🔒 **Recomendaciones adicionales:**
- Cambiar puerto por defecto (8501 → 8080)
- Configurar SSL/HTTPS
- Restricción de IPs (opcional)
- Monitoreo con Google Cloud Monitoring

## 🚨 **SOLUCIÓN DE PROBLEMAS**

### Bot no responde:
```bash
# Verificar procesos
gcloud compute ssh cripto-bot-vm --zone=us-central1-a --command="ps aux | grep python"

# Reiniciar si necesario
gcloud compute ssh cripto-bot-vm --zone=us-central1-a --command="sudo reboot"
```

### Dashboard no accesible:
- Verificar firewall: `gcloud compute firewall-rules list | grep cripto`
- Verificar IP externa: `gcloud compute instances list`
- Verificar puerto: Dashboard en 8501

### VM no responde:
```bash
# Verificar estado
gcloud compute instances describe cripto-bot-vm --zone=us-central1-a

# Reiniciar VM
gcloud compute instances reset cripto-bot-vm --zone=us-central1-a
```

## 📈 **MONITOREO Y MANTENIMIENTO**

### Ver métricas de la VM:
```bash
gcloud compute ssh cripto-bot-vm --zone=us-central1-a --command="
  echo '=== SYSTEM STATUS ==='
  top -n1 -b | head -5
  echo '=== MEMORY ==='
  free -h
  echo '=== DISK ==='
  df -h
  echo '=== BOT STATUS ==='
  ps aux | grep -E '(trader_24_7|streamlit)' | grep -v grep
"
```

### Actualizar bot:
```bash
gcloud compute ssh cripto-bot-vm --zone=us-central1-a --command="
  cd /opt/cripto-bot
  # Download latest version
  wget -O trader_24_7.py https://raw.githubusercontent.com/Joseph9202/CriptoBot/main/trader_24_7.py
  wget -O dashboard_simple.py https://raw.githubusercontent.com/Joseph9202/CriptoBot/main/dashboard_simple.py
  # Restart services
  pkill -f trader_24_7.py
  pkill -f streamlit
  nohup python3 trader_24_7.py > /tmp/bot.log 2>&1 &
  nohup python3 -m streamlit run dashboard_simple.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > /tmp/dashboard.log 2>&1 &
"
```

## 🎯 **COMANDOS DE DEPLOYMENT RÁPIDO**

### Deployment completo en 3 comandos:
```bash
# 1. Autenticar
gcloud auth login

# 2. Configurar proyecto  
gcloud config set project YOUR_PROJECT_ID

# 3. Deploy
./deploy_one_command.sh YOUR_PROJECT_ID
```

### Verificación post-deployment:
```bash
# Obtener IP
EXTERNAL_IP=$(gcloud compute instances describe cripto-bot-vm --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

# Verificar dashboard
curl -s "http://$EXTERNAL_IP:8501" | head -5

# Abrir en navegador
xdg-open "http://$EXTERNAL_IP:8501"  # Linux
open "http://$EXTERNAL_IP:8501"      # macOS
```

---

## 🚀 **RESUMEN EJECUTIVO**

✅ **Deployment ultra-rápido**: Un comando y listo  
✅ **Bot 24/7 automático**: Se ejecuta sin intervención  
✅ **Dashboard web accesible**: Desde cualquier lugar  
✅ **Free tier elegible**: $0/mes dentro de límites  
✅ **Auto-scaling**: VM se ajusta automáticamente  
✅ **Monitoreo incluido**: Logs y métricas disponibles  
✅ **Actualizaciones fáciles**: Scripts automatizados  

### 🎯 **Comando más rápido:**
```bash
./deploy_one_command.sh YOUR_PROJECT_ID
```

**¡En 2 minutos tendrás tu CriptoBot corriendo 24/7 en Google Cloud!** 🌩️🤖💰