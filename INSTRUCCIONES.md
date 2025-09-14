# 🤖 CRIPTO BOT - INSTRUCCIONES DE USO

## ✅ ESTADO: FUNCIONANDO CORRECTAMENTE

Tu bot de trading con dinero fake está completamente funcional y listo para usar.

## 🚀 CÓMO EJECUTAR

### Método 1: Ejecutor Principal (Recomendado)
```bash
# 1. Abrir terminal
# 2. Navegar a la carpeta del proyecto
cd /home/jose-luis-orozco/Escritorio/PacificLabs/CriptoBot

# 3. Activar entorno virtual
source binance_env/bin/activate

# 4. Ejecutar el bot
python START_BOT.py
```

### Método 2: Demos Individuales
```bash
# Demo rápido (5 minutos)
python quick_demo.py

# Consulta de precios
python test_bot.py

# Bot intraday completo
python intraday_garch_bot.py
```

## 📊 QUÉ HACE CADA OPCIÓN

### 1. 📈 Demo Rápido
- **Duración**: 2-5 minutos
- **Función**: Simula trades en BTC, ETH, BNB
- **Balance**: $10,000 fake inicial
- **Muestra**: Análisis técnico, señales, P&L simulado

### 2. 📊 Consulta de Precios
- **Duración**: 30 segundos
- **Función**: Obtiene precios reales de Binance
- **Muestra**: Bitcoin, Ethereum y top criptomonedas
- **Sin trading**: Solo consulta

### 3. ⚡ Bot Intraday GARCH
- **Duración**: 8+ horas simuladas
- **Función**: Tu bot original con estrategia GARCH
- **Balance**: $10,000 fake inicial
- **Función completa**: Trading automatizado simulado

## 🛡️ SEGURIDAD

### ✅ 100% SEGURO
- **Solo dinero fake**: No se usa dinero real
- **APIs de testnet**: Datos reales, trading simulado
- **Sin riesgo**: Perfecto para aprender

### ⚠️ IMPORTANTE
- Los resultados son simulaciones
- No es asesoramiento financiero
- Solo para fines educativos

## 🔧 SOLUCIÓN DE PROBLEMAS

### Error: "ModuleNotFoundError"
```bash
# Instalar dependencias faltantes
source binance_env/bin/activate
pip install pandas numpy matplotlib python-binance pandas-ta
```

### Error: "Conexión API"
- Verificar conexión a internet
- Las APIs de testnet a veces tienen mantenimiento
- Reintentar en unos minutos

### Bot se ejecuta muy lento
- Es normal, está obteniendo datos reales
- Usar "Demo Rápido" para pruebas rápidas

## 📈 RESULTADOS ESPERADOS

### Demo Rápido
```
💰 Balance inicial: $10,000.00
💰 Balance final: $10,XXX.XX
📈 P&L Total: $XXX.XX (+X.XX%)
🔄 Trades ejecutados: 2-3
🎯 Win Rate: XX.X%
```

### Bot Intraday
```
📊 RESULTADOS SIMULACIÓN INTRADAY
Balance inicial: $10,000.00
Balance final: $10,XXX.XX
Total trades: XX
Win rate: XX.X%
```

## 🎯 PRÓXIMOS PASOS

1. **Ejecuta**: `python START_BOT.py`
2. **Prueba**: Opción 1 (Demo Rápido)
3. **Observa**: Los resultados de trading simulado
4. **Experimenta**: Con diferentes opciones
5. **Aprende**: Sobre trading sin riesgo

## 📚 ARCHIVOS PRINCIPALES

- `START_BOT.py` - Ejecutor principal
- `quick_demo.py` - Demo rápido de trading
- `test_bot.py` - Consulta de precios
- `intraday_garch_bot.py` - Tu bot original
- `enhanced_paper_trading_bot.py` - Bot avanzado
- `portfolio_analyzer.py` - Análisis de resultados

## 💡 CONSEJOS

1. **Empieza** con el Demo Rápido
2. **Observa** cómo analiza los mercados
3. **Entiende** las señales de trading
4. **Experimenta** sin miedo (es dinero fake)
5. **Aprende** sobre gestión de riesgo

---

## 🚀 ¡LISTO PARA USAR!

Tu CriptoBot está completamente funcional. ¡Disfruta aprendiendo trading sin riesgo!

**Comando rápido:**
```bash
cd /home/jose-luis-orozco/Escritorio/PacificLabs/CriptoBot && source binance_env/bin/activate && python START_BOT.py
```