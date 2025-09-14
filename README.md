# 🤖 CriptoBot - Bot de Trading con Paper Trading

Bot avanzado de trading de criptomonedas con simulación completa usando dinero fake para aprender y probar estrategias sin riesgo.

## 🚀 Características Principales

### ✅ Paper Trading Completo
- **Dinero virtual**: Trading con balance simulado ($10,000 inicial)
- **Comisiones reales**: Simula comisiones de Binance (0.1%)
- **Gestión de riesgo**: Stop loss, take profit, trailing stops
- **Múltiples símbolos**: BTC, ETH, BNB, ADA, SOL y más

### ✅ Análisis Técnico Avanzado
- **Indicadores técnicos**: RSI, MACD, Bollinger Bands, EMAs
- **Múltiples timeframes**: 1m, 5m, 15m, 1h
- **Volatilidad GARCH**: Modelo sofisticado para intraday
- **Señales automatizadas**: Entrada y salida automática

### ✅ Gestión de Portfolio
- **Base de datos SQLite**: Persistencia de trades e historial
- **Métricas avanzadas**: Win rate, drawdown, Sharpe ratio
- **Visualizaciones**: Gráficos de curva de capital y performance
- **Exportación**: Reportes en Excel y HTML

### ✅ Interfaz Web
- **Dashboard en tiempo real**: Monitoreo con Streamlit
- **Gráficos interactivos**: Plotly para visualizaciones dinámicas
- **Control remoto**: Ejecutar trades desde el navegador
- **Auto-refresh**: Actualización automática cada 30s

## 📁 Estructura del Proyecto

```
CriptoBot/
├── 🤖 enhanced_paper_trading_bot.py    # Bot principal con paper trading
├── 📊 portfolio_analyzer.py            # Análisis y visualización de performance
├── 🌐 web_interface.py                 # Dashboard web con Streamlit
├── ⚡ intraday_garch_bot.py           # Bot especializado en intraday
├── 📈 app.py                          # Bot básico de consulta de precios
├── 🚀 run_cripto_bot.py               # Launcher principal
├── 📋 requirements.txt                # Dependencias de Python
├── 📖 README.md                       # Este archivo
└── 💾 trading_bot.db                  # Base de datos (se crea automáticamente)
```

## 🛠️ Instalación y Configuración

### 1. Clonar o Descargar
```bash
# Si tienes git instalado
git clone <repository_url>
cd CriptoBot

# O simplemente descarga los archivos a una carpeta
```

### 2. Instalar Python
- Asegúrate de tener Python 3.8+ instalado
- Verifica con: `python --version`

### 3. Instalar Dependencias
```bash
# Automáticamente al ejecutar el launcher
python run_cripto_bot.py

# O manualmente
pip install -r requirements.txt
```

### 4. Configurar API (Opcional)
- Las API keys incluidas son de **Binance Testnet** (dinero fake)
- **No se necesita configuración adicional** para simulación
- Para trading real, cambiar keys en los archivos Python

## 🎮 Cómo Usar

### Opción 1: Launcher Automático (Recomendado)
```bash
python run_cripto_bot.py
```

### Opción 2: Ejecutar Componentes Individuales

#### Bot de Paper Trading Avanzado
```bash
python enhanced_paper_trading_bot.py
```

#### Dashboard Web
```bash
streamlit run web_interface.py
```

#### Análisis de Portfolio
```bash
python portfolio_analyzer.py
```

#### Bot Intraday GARCH
```bash
python intraday_garch_bot.py
```

## 📊 Funcionalidades Detalladas

### 1. 🤖 Bot de Paper Trading Avanzado

**Características:**
- Balance inicial: $10,000 (configurable)
- Máximo 3 posiciones simultáneas
- Stop loss: 2.5% | Take profit: 5%
- Límite de pérdida diaria: 10%
- Trailing stops automáticos

**Estrategia de Trading:**
- Análisis multi-timeframe (5m principal, 15m confirmación)
- Combinación de RSI, MACD, Bollinger Bands, EMAs
- Filtros de volumen y volatilidad
- Gestión de riesgo por posición: 2% del capital

**Ejemplo de uso:**
```python
# Crear bot
bot = EnhancedPaperTradingBot(
    symbols=['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
    initial_balance=10000
)

# Ejecutar un ciclo
bot.run_trading_cycle()

# Ver resumen
bot.print_portfolio_report()
```

### 2. 📊 Analizador de Portfolio

**Métricas calculadas:**
- Win Rate y Profit Factor
- Maximum Drawdown
- Sharpe Ratio
- Duración promedio de trades
- P&L por símbolo

**Visualizaciones:**
- Curva de capital
- Distribución de P&L
- Análisis por símbolo
- Dashboard interactivo HTML

### 3. 🌐 Dashboard Web

**Tabs disponibles:**
- **Overview**: Métricas principales del portfolio
- **Trades en Vivo**: Posiciones abiertas en tiempo real
- **Precios**: Gráficos de precios actuales
- **Performance**: Análisis histórico de rendimiento

**Controles:**
- Inicializar bot con configuración personalizada
- Ejecutar ciclos de trading manuales
- Cerrar posiciones individualmente
- Auto-refresh configurable

### 4. ⚡ Bot Intraday GARCH

**Especialización:**
- Trading de alta frecuencia (cada 5 minutos)
- Modelo de volatilidad GARCH
- Hasta 24 trades por día
- Optimizado para movimientos intraday

## 📈 Estrategias de Trading Implementadas

### Estrategia Principal (Multi-timeframe)

**Señal de COMPRA:**
- EMA rápida > EMA lenta (tendencia alcista)
- RSI < 45 (no sobrecomprado)
- Precio en zona baja de Bollinger Bands
- MACD bullish
- Volumen superior al promedio
- Confirmación en timeframe superior

**Señal de VENTA:**
- Condiciones opuestas para SHORT
- Mismos filtros de confirmación

### Gestión de Riesgo

**Por Trade:**
- Riesgo máximo: 2% del capital
- Position sizing dinámico basado en volatilidad
- Stop loss automático

**Por Día:**
- Máximo 20 trades diarios
- Límite de pérdida: 10% del capital
- Cierre automático en volatilidad extrema

## 📊 Ejemplos de Reportes

### Reporte de Performance
```
📊 REPORTE DE PERFORMANCE DETALLADO
=====================================
📈 MÉTRICAS GENERALES:
   Total de Trades: 45
   Trades Ganadores: 28
   Trades Perdedores: 17
   Win Rate: 62.22%

💰 MÉTRICAS DE P&L:
   P&L Total: $1,247.50
   Ganancia Promedio: $85.30
   Pérdida Promedio: -$42.15
   Factor de Ganancia: 3.29

⚠️ MÉTRICAS DE RIESGO:
   Max Drawdown: -8.45%
   Sharpe Ratio: 1.82
```

### Portfolio Summary
```
💼 REPORTE DE PORTFOLIO
Balance Actual: $11,247.50
P&L Total: $1,247.50 (+12.48%)
Total Trades: 45
Win Rate: 62.2%
Posiciones Abiertas: 2
```

## 🔧 Configuración Avanzada

### Modificar Parámetros de Trading

En `enhanced_paper_trading_bot.py`:
```python
self.trading_config = {
    'max_position_size': 0.15,      # 15% del capital por trade
    'stop_loss_pct': 0.025,         # 2.5% stop loss
    'take_profit_pct': 0.05,        # 5% take profit
    'max_open_positions': 3,        # Máximo 3 posiciones
    'risk_per_trade': 0.02,         # 2% riesgo por trade
    'daily_loss_limit': 0.1,        # 10% pérdida máxima diaria
}
```

### Añadir Nuevos Símbolos
```python
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT']
bot = EnhancedPaperTradingBot(symbols=symbols)
```

### Cambiar Balance Inicial
```python
bot = EnhancedPaperTradingBot(initial_balance=50000)  # $50,000
```

## 🛡️ Seguridad y Limitaciones

### ✅ Seguro para Aprender
- **Solo paper trading**: No se ejecutan trades reales
- **APIs de testnet**: Dinero completamente virtual
- **Sin riesgo financiero**: Perfecto para aprendizaje

### ⚠️ Limitaciones
- **No es asesoramiento financiero**: Solo para educación
- **Datos simulados**: Resultados pueden diferir del trading real
- **Sin garantías**: Past performance doesn't predict future results

## 📚 Casos de Uso

### 1. Aprendizaje de Trading
- Probar estrategias sin riesgo
- Entender análisis técnico
- Practicar gestión de riesgo

### 2. Desarrollo de Estrategias
- Backtesting de ideas
- Optimización de parámetros
- Análisis de performance

### 3. Educación Financiera
- Comprender mercados de criptomonedas
- Aprender sobre volatilidad
- Entender psicología del trading

## 🆘 Troubleshooting

### Error de Conexión API
```
✗ Error conectando con Binance API
```
**Solución**: Verificar conexión a internet. Las APIs de testnet a veces tienen mantenimiento.

### Error de Dependencias
```
ModuleNotFoundError: No module named 'pandas'
```
**Solución**: 
```bash
pip install -r requirements.txt
```

### Error de Base de Datos
```
Error leyendo historial: no such table: trades
```
**Solución**: Ejecutar el bot primero para crear la base de datos automáticamente.

### Dashboard no Abre
```bash
# Si streamlit no funciona
pip install streamlit --upgrade
streamlit run web_interface.py --server.port 8502
```

## 🤝 Contribución

Este proyecto es para fines educativos. Si encuentras bugs o tienes mejoras:

1. Documenta el issue claramente
2. Propón soluciones específicas
3. Testa tus cambios localmente

## 📄 Licencia

Proyecto educativo de código abierto. Usar bajo tu propia responsabilidad.

---

## 🎯 Próximos Pasos Sugeridos

1. **Ejecuta el launcher**: `python run_cripto_bot.py`
2. **Prueba el bot de paper trading**: Opción 1
3. **Revisa el dashboard web**: Opción 3
4. **Analiza los resultados**: Opción 2
5. **Experimenta con configuraciones**

---

**💡 Recuerda**: Este bot usa dinero completamente virtual. ¡Perfecto para aprender sin riesgo!

**🚀 ¡Feliz Trading!** 📈💰