#!/usr/bin/env python3

import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timedelta
from binance.client import Client
import pandas_ta
import json
import signal
import sys
import sqlite3

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trader_24_7.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Keys (Testnet - Dinero Fake)
API_KEY = 'bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb'
API_SECRET = 'O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS'

class Trader24_7:
    """
    🤖 TRADER AUTOMÁTICO 24/7 - FUNCIONA COMO TRADER REAL
    
    ✅ Analiza mercados cada 5 minutos
    ✅ Abre/cierra posiciones automáticamente
    ✅ Gestiona riesgo con stop loss/take profit
    ✅ Mantiene estadísticas en tiempo real
    ✅ Guarda todo en base de datos
    ✅ Opera con dinero 100% FAKE (sin riesgo)
    """
    
    def __init__(self):
        # Estado del trader
        self.balance_inicial = 10000.0
        self.balance_actual = 10000.0
        self.balance_disponible = 10000.0
        self.posiciones_abiertas = {}
        self.total_trades = 0
        self.trades_ganadores = 0
        self.corriendo = True
        self.ciclo_numero = 0
        
        # Configuración
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT']
        self.max_posiciones = 2
        self.riesgo_por_trade = 0.03  # 3%
        self.stop_loss_pct = 0.02  # 2%
        self.take_profit_pct = 0.04  # 4%
        
        # Conectar a Binance
        try:
            self.client = Client(API_KEY, API_SECRET)
            logger.info("✅ Trader 24/7 conectado a Binance")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            sys.exit(1)
        
        # Configurar signal handler para Ctrl+C
        signal.signal(signal.SIGINT, self.detener_trader)
    
    def detener_trader(self, sig, frame):
        """Handler para detener el trader con Ctrl+C"""
        logger.info("\n🛑 Deteniendo Trader 24/7...")
        self.corriendo = False
    
    def obtener_precio(self, symbol):
        """Obtiene precio actual de un símbolo"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except:
            return None
    
    def analizar_mercado(self, symbol):
        """Análisis técnico simplificado pero efectivo"""
        try:
            # Obtener datos de 1 hora
            klines = self.client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR, "50 hours ago UTC")
            
            precios = [float(kline[4]) for kline in klines]  # Precios de cierre
            df = pd.DataFrame({'close': precios})
            
            # Indicadores simples pero efectivos
            df['sma_20'] = df['close'].rolling(20).mean()
            df['rsi'] = pandas_ta.rsi(df['close'], length=14)
            
            current = df.iloc[-1]
            prev = df.iloc[-2]
            precio_actual = current['close']
            
            # Lógica de señales
            señal = "HOLD"
            fuerza = 0
            
            # Señal de COMPRA
            if (current['rsi'] < 40 and  # RSI bajo
                precio_actual > current['sma_20'] and  # Precio sobre SMA
                precio_actual > prev['close']):  # Precio subiendo
                señal = "BUY"
                fuerza = 3
            
            # Señal de VENTA  
            elif (current['rsi'] > 60 and  # RSI alto
                  precio_actual < current['sma_20'] and  # Precio bajo SMA
                  precio_actual < prev['close']):  # Precio bajando
                señal = "SELL"
                fuerza = 3
            
            return señal, fuerza, precio_actual
            
        except Exception as e:
            logger.error(f"Error analizando {symbol}: {e}")
            return "HOLD", 0, None
    
    def abrir_posicion(self, symbol, side, precio):
        """Abre nueva posición"""
        if len(self.posiciones_abiertas) >= self.max_posiciones:
            return False
        
        if symbol in self.posiciones_abiertas:
            return False
        
        # Calcular cantidad basada en riesgo
        monto = self.balance_actual * self.riesgo_por_trade
        cantidad = monto / precio
        
        # Verificar balance
        costo = cantidad * precio * 1.001  # Include comisión
        if costo > self.balance_disponible:
            return False
        
        # Calcular stop loss y take profit
        if side == 'BUY':
            stop_loss = precio * (1 - self.stop_loss_pct)
            take_profit = precio * (1 + self.take_profit_pct)
        else:
            stop_loss = precio * (1 + self.stop_loss_pct)  
            take_profit = precio * (1 - self.take_profit_pct)
        
        # Guardar posición
        self.posiciones_abiertas[symbol] = {
            'side': side,
            'cantidad': cantidad,
            'precio_entrada': precio,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'timestamp': datetime.now()
        }
        
        self.balance_disponible -= costo
        
        logger.info(f"🚀 NUEVA POSICIÓN: {side} {cantidad:.6f} {symbol} @ ${precio:.2f}")
        logger.info(f"   📍 SL: ${stop_loss:.2f} | TP: ${take_profit:.2f}")
        
        return True
    
    def cerrar_posicion(self, symbol, precio_salida, razon):
        """Cierra posición existente"""
        if symbol not in self.posiciones_abiertas:
            return
        
        pos = self.posiciones_abiertas[symbol]
        
        # Calcular P&L
        if pos['side'] == 'BUY':
            pnl = (precio_salida - pos['precio_entrada']) * pos['cantidad']
        else:
            pnl = (pos['precio_entrada'] - precio_salida) * pos['cantidad']
        
        # Comisiones (0.1% cada lado)
        comisiones = (pos['precio_entrada'] + precio_salida) * pos['cantidad'] * 0.001
        pnl_neto = pnl - comisiones
        
        # Actualizar balance
        valor_posicion = precio_salida * pos['cantidad']
        self.balance_actual += pnl_neto
        self.balance_disponible += valor_posicion
        
        # Estadísticas
        self.total_trades += 1
        if pnl_neto > 0:
            self.trades_ganadores += 1
        
        # Duración
        duracion = datetime.now() - pos['timestamp']
        duracion_horas = duracion.total_seconds() / 3600
        
        # Log resultado
        pnl_pct = (pnl_neto / (pos['precio_entrada'] * pos['cantidad'])) * 100
        estado = "💚 GANANCIA" if pnl_neto > 0 else "💔 PÉRDIDA"
        
        logger.info(f"🏁 CERRAR: {symbol} | {estado} ${pnl_neto:.2f} ({pnl_pct:+.2f}%)")
        logger.info(f"   ⏰ Duración: {duracion_horas:.1f}h | Razón: {razon}")
        
        # Guardar en base de datos (simplificado)
        self.guardar_trade(symbol, pos, precio_salida, pnl_neto, razon)
        
        # Remover posición
        del self.posiciones_abiertas[symbol]
    
    def verificar_salidas(self):
        """Verifica si hay que cerrar posiciones"""
        for symbol in list(self.posiciones_abiertas.keys()):
            pos = self.posiciones_abiertas[symbol]
            precio_actual = self.obtener_precio(symbol)
            
            if precio_actual is None:
                continue
            
            # Stop Loss
            if pos['side'] == 'BUY' and precio_actual <= pos['stop_loss']:
                self.cerrar_posicion(symbol, precio_actual, "Stop Loss")
            elif pos['side'] == 'SELL' and precio_actual >= pos['stop_loss']:
                self.cerrar_posicion(symbol, precio_actual, "Stop Loss")
            
            # Take Profit
            elif pos['side'] == 'BUY' and precio_actual >= pos['take_profit']:
                self.cerrar_posicion(symbol, precio_actual, "Take Profit")
            elif pos['side'] == 'SELL' and precio_actual <= pos['take_profit']:
                self.cerrar_posicion(symbol, precio_actual, "Take Profit")
            
            # Tiempo máximo (12 horas)
            elif (datetime.now() - pos['timestamp']).total_seconds() > 43200:
                self.cerrar_posicion(symbol, precio_actual, "Tiempo límite")
    
    def guardar_trade(self, symbol, pos, precio_salida, pnl, razon):
        """Guarda trade en archivo log"""
        try:
            trade_data = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'side': pos['side'],
                'entry': pos['precio_entrada'],
                'exit': precio_salida,
                'quantity': pos['cantidad'],
                'pnl': pnl,
                'reason': razon
            }
            
            with open('trades_24_7.json', 'a') as f:
                f.write(json.dumps(trade_data) + '\n')
                
        except Exception as e:
            logger.error(f"Error guardando trade: {e}")
    
    def mostrar_resumen(self):
        """Muestra resumen del estado actual"""
        win_rate = (self.trades_ganadores / max(self.total_trades, 1)) * 100
        retorno = ((self.balance_actual - self.balance_inicial) / self.balance_inicial) * 100
        
        logger.info("="*70)
        logger.info("📊 RESUMEN TRADER 24/7")
        logger.info("="*70)
        logger.info(f"💰 Balance: ${self.balance_actual:.2f} | Retorno: {retorno:+.2f}%")
        logger.info(f"📈 Trades: {self.total_trades} | Win Rate: {win_rate:.1f}%")
        logger.info(f"🔄 Posiciones abiertas: {len(self.posiciones_abiertas)}")
        logger.info(f"⏰ Ciclo: {self.ciclo_numero}")
        
        # Mostrar posiciones
        if self.posiciones_abiertas:
            logger.info("📋 POSICIONES ACTIVAS:")
            for symbol, pos in self.posiciones_abiertas.items():
                precio_actual = self.obtener_precio(symbol)
                if precio_actual:
                    if pos['side'] == 'BUY':
                        pnl_temp = (precio_actual - pos['precio_entrada']) * pos['cantidad']
                    else:
                        pnl_temp = (pos['precio_entrada'] - precio_actual) * pos['cantidad']
                    
                    logger.info(f"   {symbol}: {pos['side']} @ ${pos['precio_entrada']:.2f} | Actual: ${precio_actual:.2f} | P&L: ${pnl_temp:.2f}")
        
        logger.info("="*70)
    
    def ejecutar_ciclo(self):
        """Ejecuta un ciclo completo de trading"""
        self.ciclo_numero += 1
        logger.info(f"🔄 CICLO {self.ciclo_numero} - {datetime.now().strftime('%H:%M:%S')}")
        
        # 1. Verificar salidas
        self.verificar_salidas()
        
        # 2. Buscar nuevas entradas
        for symbol in self.symbols:
            if symbol in self.posiciones_abiertas:
                continue  # Ya hay posición
            
            señal, fuerza, precio = self.analizar_mercado(symbol)
            
            if precio:
                logger.info(f"📊 {symbol}: ${precio:.2f} | {señal} (Fuerza: {fuerza})")
                
                # Abrir posición si hay señal fuerte
                if señal in ['BUY', 'SELL'] and fuerza >= 3:
                    self.abrir_posicion(symbol, señal, precio)
        
        # 3. Mostrar resumen cada 12 ciclos (1 hora aprox)
        if self.ciclo_numero % 12 == 0:
            self.mostrar_resumen()
    
    def iniciar_trading_24_7(self):
        """Inicia el trading automático 24/7"""
        logger.info("🚀 INICIANDO TRADER 24/7")
        logger.info("💰 Balance inicial: $10,000 (DINERO FAKE)")
        logger.info("🎯 Símbolos: " + ", ".join(self.symbols))
        logger.info("⏰ Frecuencia: Cada 5 minutos")
        logger.info("🛑 Presiona Ctrl+C para detener")
        logger.info("="*70)
        
        try:
            while self.corriendo:
                # Ejecutar ciclo de trading
                self.ejecutar_ciclo()
                
                # Esperar 5 minutos (300 segundos)
                for i in range(300):
                    if not self.corriendo:
                        break
                    time.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Error en trading: {e}")
        
        finally:
            # Cerrar todas las posiciones al salir
            logger.info("🔐 Cerrando todas las posiciones...")
            for symbol in list(self.posiciones_abiertas.keys()):
                precio = self.obtener_precio(symbol)
                if precio:
                    self.cerrar_posicion(symbol, precio, "Cierre manual")
            
            self.mostrar_resumen()
            logger.info("✅ Trader 24/7 detenido correctamente")

def main():
    """Función principal - Se ejecuta automáticamente"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                    🤖 TRADER 24/7 AUTOMÁTICO                     ║
    ║               ✅ SE EJECUTA AUTOMÁTICAMENTE                       ║  
    ║               💰 DINERO 100% FAKE - SIN RIESGO                   ║
    ║               🔄 OPERA CADA 5 MINUTOS COMO TRADER REAL           ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Crear e iniciar el trader automáticamente
    trader = Trader24_7()
    trader.iniciar_trading_24_7()

if __name__ == "__main__":
    main()