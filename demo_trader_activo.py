#!/usr/bin/env python3

import time
import logging
from datetime import datetime
from binance.client import Client
import pandas_ta
import pandas as pd
import random

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# API Keys (Testnet - Dinero Fake)
API_KEY = 'bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb'
API_SECRET = 'O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS'

class DemoTraderActivo:
    """Demo de un trader que opera automáticamente"""
    
    def __init__(self):
        self.balance = 10000.0
        self.posiciones = {}
        self.total_trades = 0
        self.trades_ganadores = 0
        self.ciclo = 0
        
        # Conectar a Binance
        self.client = Client(API_KEY, API_SECRET)
        logger.info("✅ Demo Trader conectado a Binance")
    
    def obtener_precio_y_analizar(self, symbol):
        """Obtiene precio y hace análisis básico"""
        try:
            # Precio actual
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            precio = float(ticker['price'])
            
            # Análisis técnico básico (simulado)
            # En trader real usaría RSI, MACD, etc.
            
            # Simular señal basada en movimiento de precio
            cambio_aleatorio = random.uniform(-0.02, 0.02)  # ±2%
            
            if cambio_aleatorio > 0.015:  # +1.5%
                señal = "BUY"
            elif cambio_aleatorio < -0.015:  # -1.5%
                señal = "SELL"
            else:
                señal = "HOLD"
            
            return precio, señal
            
        except Exception as e:
            logger.error(f"Error con {symbol}: {e}")
            return None, "HOLD"
    
    def ejecutar_trade(self, symbol, señal, precio):
        """Ejecuta un trade simulado"""
        if symbol in self.posiciones:
            return  # Ya hay posición
        
        if señal == "HOLD":
            return
        
        # Simular trade
        cantidad = (self.balance * 0.1) / precio  # 10% del balance
        
        # Simular resultado (±3% aleatorio)
        resultado_pct = random.uniform(-0.03, 0.03)
        pnl = (self.balance * 0.1) * resultado_pct
        
        self.balance += pnl
        self.total_trades += 1
        
        if pnl > 0:
            self.trades_ganadores += 1
            estado = "💚 GANANCIA"
        else:
            estado = "💔 PÉRDIDA"
        
        logger.info(f"🔄 TRADE: {señal} {symbol} @ ${precio:.2f}")
        logger.info(f"   {estado}: ${pnl:.2f} | Balance: ${self.balance:.2f}")
    
    def mostrar_resumen(self):
        """Muestra resumen del trader"""
        win_rate = (self.trades_ganadores / max(self.total_trades, 1)) * 100
        retorno = ((self.balance - 10000) / 10000) * 100
        
        logger.info("="*60)
        logger.info("📊 RESUMEN DEL TRADER ACTIVO")
        logger.info("="*60)
        logger.info(f"💰 Balance: ${self.balance:.2f} | Retorno: {retorno:+.2f}%")
        logger.info(f"📈 Trades: {self.total_trades} | Win Rate: {win_rate:.1f}%")
        logger.info(f"🔄 Ciclos completados: {self.ciclo}")
        logger.info("="*60)
    
    def operar_continuamente(self, ciclos=20):
        """Opera automáticamente por varios ciclos"""
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        
        logger.info("🚀 DEMO TRADER ACTIVO - INICIANDO")
        logger.info(f"💰 Balance inicial: ${self.balance:.2f} (DINERO FAKE)")
        logger.info(f"🔄 Ejecutará {ciclos} ciclos automáticamente")
        logger.info("="*60)
        
        for i in range(ciclos):
            self.ciclo += 1
            logger.info(f"🔄 CICLO {self.ciclo} - {datetime.now().strftime('%H:%M:%S')}")
            
            # Analizar cada símbolo
            for symbol in symbols:
                precio, señal = self.obtener_precio_y_analizar(symbol)
                
                if precio:
                    logger.info(f"📊 {symbol}: ${precio:.2f} | Señal: {señal}")
                    self.ejecutar_trade(symbol, señal, precio)
            
            # Mostrar progreso
            if self.ciclo % 5 == 0:
                self.mostrar_resumen()
            
            # Esperar antes del próximo ciclo
            logger.info("⏳ Esperando próximo ciclo...")
            time.sleep(3)  # 3 segundos por ciclo para demo
        
        # Resumen final
        logger.info("✅ DEMO COMPLETADO")
        self.mostrar_resumen()

def main():
    """Función principal del demo"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                🚀 DEMO TRADER ACTIVO                              ║
    ║            Bot que opera automáticamente como trader real         ║
    ║                    💰 100% Dinero FAKE - Sin riesgo              ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    trader = DemoTraderActivo()
    
    print("🎮 Este demo muestra cómo el bot:")
    print("   ✅ Analiza precios en tiempo real")
    print("   ✅ Toma decisiones automáticamente")
    print("   ✅ Ejecuta trades como trader real")
    print("   ✅ Gestiona balance automáticamente")
    print("   ✅ Mantiene estadísticas")
    print()
    
    # Ejecutar demo automático
    trader.operar_continuamente(ciclos=15)  # 15 ciclos de demo
    
    print("\n💡 PARA TRADER 24/7 REAL:")
    print("   python trader_24_7.py")
    print("   (Ese bot opera cada 5 minutos indefinidamente)")

if __name__ == "__main__":
    main()