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
from threading import Thread
import sqlite3

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trader_automatico.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Keys (Testnet - Dinero Fake)
API_KEY = 'bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb'
API_SECRET = 'O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS'

class TraderAutomatico:
    """
    Bot de Trading Automático que opera 24/7 como un trader real
    🤖 Trading continuo con dinero fake
    """
    
    def __init__(self):
        # Configuración del trader
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']
        self.balance_inicial = 10000.0  # $10,000 dinero fake
        self.balance_actual = 10000.0
        self.balance_disponible = 10000.0
        
        # Configuración de trading
        self.max_posiciones = 3  # Máximo 3 posiciones simultáneas
        self.riesgo_por_trade = 0.02  # 2% del capital por trade
        self.stop_loss_pct = 0.025  # 2.5% stop loss
        self.take_profit_pct = 0.05  # 5% take profit
        self.comision = 0.001  # 0.1% comisión
        
        # Estado del trader
        self.posiciones_abiertas = {}  # {symbol: {side, quantity, entry_price, timestamp}}
        self.historial_trades = []
        self.corriendo = False
        self.ciclos_completados = 0
        
        # Estadísticas
        self.total_trades = 0
        self.trades_ganadores = 0
        self.trades_perdedores = 0
        
        # Cliente Binance
        try:
            self.client = Client(API_KEY, API_SECRET)
            logger.info("✅ Conexión establecida con Binance API")
        except Exception as e:
            logger.error(f"❌ Error conectando con Binance: {e}")
            self.client = None
        
        # Base de datos
        self.init_database()
    
    def init_database(self):
        """Inicializa base de datos para persistir datos"""
        conn = sqlite3.connect('trader_automatico.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades_automaticos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            side TEXT,
            entry_price REAL,
            exit_price REAL,
            quantity REAL,
            pnl REAL,
            pnl_pct REAL,
            duration_minutes REAL,
            reason TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS balance_history (
            timestamp TEXT PRIMARY KEY,
            balance REAL,
            pnl_total REAL,
            posiciones_abiertas INTEGER
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def obtener_datos_mercado(self, symbol, interval='5m', limit=100):
        """Obtiene datos de mercado para análisis"""
        try:
            klines = self.client.get_historical_klines(symbol, interval, f"{limit} {interval}")
            
            data = []
            for kline in klines:
                data.append({
                    'timestamp': pd.to_datetime(kline[0], unit='ms'),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            
            # Calcular indicadores técnicos
            df['sma_20'] = df['close'].rolling(20).mean()
            df['sma_50'] = df['close'].rolling(50).mean()
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            df['rsi'] = pandas_ta.rsi(df['close'], length=14)
            
            # Bollinger Bands
            bb = pandas_ta.bbands(df['close'], length=20)
            if bb is not None and len(bb.columns) >= 3:
                df['bb_upper'] = bb.iloc[:, 2]
                df['bb_lower'] = bb.iloc[:, 0]
                df['bb_mid'] = bb.iloc[:, 1]
            
            # MACD
            macd = pandas_ta.macd(df['close'])
            if macd is not None and len(macd.columns) >= 3:
                df['macd'] = macd.iloc[:, 0]
                df['macd_signal'] = macd.iloc[:, 1]
                df['macd_hist'] = macd.iloc[:, 2]
            
            # Volumen promedio
            df['vol_avg'] = df['volume'].rolling(20).mean()
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {e}")
            return pd.DataFrame()
    
    def analizar_señal(self, symbol, df):
        """Analiza señales de trading automático"""
        if len(df) < 50:
            return 'HOLD', 0
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Señales de compra
        señales_compra = 0
        
        # 1. RSI oversold
        if current['rsi'] < 35:
            señales_compra += 1
        
        # 2. Precio por debajo de Bollinger Band inferior
        if 'bb_lower' in current and current['close'] < current['bb_lower']:
            señales_compra += 1
        
        # 3. EMA crossover bullish
        if current['ema_12'] > current['ema_26'] and prev['ema_12'] <= prev['ema_26']:
            señales_compra += 2
        
        # 4. MACD bullish
        if 'macd' in current and 'macd_signal' in current:
            if current['macd'] > current['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                señales_compra += 2
        
        # 5. Volumen alto
        if current['volume'] > current['vol_avg'] * 1.5:
            señales_compra += 1
        
        # 6. Precio por encima de SMA 20
        if current['close'] > current['sma_20']:
            señales_compra += 1
        
        # Señales de venta
        señales_venta = 0
        
        # 1. RSI overbought
        if current['rsi'] > 65:
            señales_venta += 1
        
        # 2. Precio por encima de Bollinger Band superior
        if 'bb_upper' in current and current['close'] > current['bb_upper']:
            señales_venta += 1
        
        # 3. EMA crossover bearish
        if current['ema_12'] < current['ema_26'] and prev['ema_12'] >= prev['ema_26']:
            señales_venta += 2
        
        # 4. MACD bearish
        if 'macd' in current and 'macd_signal' in current:
            if current['macd'] < current['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                señales_venta += 2
        
        # 5. Volumen alto
        if current['volume'] > current['vol_avg'] * 1.5:
            señales_venta += 1
        
        # 6. Precio por debajo de SMA 20
        if current['close'] < current['sma_20']:
            señales_venta += 1
        
        # Decidir señal
        if señales_compra >= 4:
            return 'BUY', señales_compra
        elif señales_venta >= 4:
            return 'SELL', señales_venta
        else:
            return 'HOLD', max(señales_compra, señales_venta)
    
    def ejecutar_entrada(self, symbol, side, precio_actual, fuerza_señal):
        """Ejecuta entrada de posición"""
        if len(self.posiciones_abiertas) >= self.max_posiciones:
            logger.info(f"⚠️ Máximo de posiciones alcanzado ({self.max_posiciones})")
            return False
        
        if symbol in self.posiciones_abiertas:
            logger.info(f"⚠️ Ya hay posición abierta en {symbol}")
            return False
        
        # Calcular cantidad basada en riesgo
        monto_riesgo = self.balance_actual * self.riesgo_por_trade
        cantidad = monto_riesgo / (precio_actual * self.stop_loss_pct)
        
        # Verificar balance disponible
        costo_trade = cantidad * precio_actual * (1 + self.comision)
        if costo_trade > self.balance_disponible:
            logger.info(f"⚠️ Balance insuficiente para {symbol}")
            return False
        
        # Calcular stop loss y take profit
        if side == 'BUY':
            stop_loss = precio_actual * (1 - self.stop_loss_pct)
            take_profit = precio_actual * (1 + self.take_profit_pct)
        else:
            stop_loss = precio_actual * (1 + self.stop_loss_pct)
            take_profit = precio_actual * (1 - self.take_profit_pct)
        
        # Guardar posición
        self.posiciones_abiertas[symbol] = {
            'side': side,
            'quantity': cantidad,
            'entry_price': precio_actual,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'timestamp': datetime.now(),
            'fuerza_señal': fuerza_señal
        }
        
        # Actualizar balance
        self.balance_disponible -= costo_trade
        
        logger.info(f"🚀 ENTRADA: {side} {cantidad:.6f} {symbol} @ ${precio_actual:.2f} (Señal: {fuerza_señal})")
        logger.info(f"   SL: ${stop_loss:.2f} | TP: ${take_profit:.2f}")
        
        return True
    
    def verificar_salidas(self):
        """Verifica condiciones de salida para posiciones abiertas"""
        for symbol in list(self.posiciones_abiertas.keys()):
            posicion = self.posiciones_abiertas[symbol]
            
            # Obtener precio actual
            try:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                precio_actual = float(ticker['price'])
            except:
                continue
            
            should_close = False
            razon = ""
            
            # Stop Loss
            if posicion['side'] == 'BUY' and precio_actual <= posicion['stop_loss']:
                should_close = True
                razon = "Stop Loss"
            elif posicion['side'] == 'SELL' and precio_actual >= posicion['stop_loss']:
                should_close = True
                razon = "Stop Loss"
            
            # Take Profit
            elif posicion['side'] == 'BUY' and precio_actual >= posicion['take_profit']:
                should_close = True
                razon = "Take Profit"
            elif posicion['side'] == 'SELL' and precio_actual <= posicion['take_profit']:
                should_close = True
                razon = "Take Profit"
            
            # Tiempo máximo (24 horas)
            elif (datetime.now() - posicion['timestamp']).total_seconds() > 86400:
                should_close = True
                razon = "Tiempo límite"
            
            if should_close:
                self.ejecutar_salida(symbol, precio_actual, razon)
    
    def ejecutar_salida(self, symbol, precio_salida, razon):
        """Ejecuta salida de posición"""
        if symbol not in self.posiciones_abiertas:
            return
        
        posicion = self.posiciones_abiertas[symbol]
        
        # Calcular P&L
        if posicion['side'] == 'BUY':
            pnl = (precio_salida - posicion['entry_price']) * posicion['quantity']
        else:
            pnl = (posicion['entry_price'] - precio_salida) * posicion['quantity']
        
        # Restar comisiones
        pnl -= (posicion['entry_price'] * posicion['quantity'] * self.comision)  # Entrada
        pnl -= (precio_salida * posicion['quantity'] * self.comision)  # Salida
        
        pnl_pct = (pnl / (posicion['entry_price'] * posicion['quantity'])) * 100
        
        # Actualizar balance
        valor_posicion = precio_salida * posicion['quantity']
        self.balance_actual += pnl
        self.balance_disponible += valor_posicion
        
        # Duración
        duracion = (datetime.now() - posicion['timestamp']).total_seconds() / 60
        
        # Estadísticas
        self.total_trades += 1
        if pnl > 0:
            self.trades_ganadores += 1
        else:
            self.trades_perdedores += 1
        
        # Guardar en historial
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': posicion['side'],
            'entry_price': posicion['entry_price'],
            'exit_price': precio_salida,
            'quantity': posicion['quantity'],
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'duration_minutes': duracion,
            'reason': razon
        }
        
        self.historial_trades.append(trade_record)
        self.guardar_trade_db(trade_record)
        
        # Log
        status = "💚 GANANCIA" if pnl > 0 else "💔 PÉRDIDA"
        logger.info(f"🏁 SALIDA: {symbol} | {status} ${pnl:.2f} ({pnl_pct:+.2f}%) | {razon}")
        logger.info(f"   Balance: ${self.balance_actual:.2f} | Duración: {duracion:.1f}min")
        
        # Remover posición
        del self.posiciones_abiertas[symbol]
    
    def guardar_trade_db(self, trade):
        """Guarda trade en base de datos"""
        try:
            conn = sqlite3.connect('trader_automatico.db')
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO trades_automaticos 
            (timestamp, symbol, side, entry_price, exit_price, quantity, pnl, pnl_pct, duration_minutes, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade['timestamp'], trade['symbol'], trade['side'],
                trade['entry_price'], trade['exit_price'], trade['quantity'],
                trade['pnl'], trade['pnl_pct'], trade['duration_minutes'], trade['reason']
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error guardando en DB: {e}")
    
    def mostrar_estado(self):
        """Muestra estado actual del trader"""
        win_rate = (self.trades_ganadores / max(self.total_trades, 1)) * 100
        retorno_total = ((self.balance_actual - self.balance_inicial) / self.balance_inicial) * 100
        
        logger.info("="*80)
        logger.info("📊 ESTADO DEL TRADER AUTOMÁTICO")
        logger.info("="*80)
        logger.info(f"💰 Balance: ${self.balance_actual:.2f} | Disponible: ${self.balance_disponible:.2f}")
        logger.info(f"📈 Retorno: {retorno_total:+.2f}% | Trades: {self.total_trades}")
        logger.info(f"🎯 Win Rate: {win_rate:.1f}% ({self.trades_ganadores}W/{self.trades_perdedores}L)")
        logger.info(f"🔄 Posiciones: {len(self.posiciones_abiertas)} | Ciclos: {self.ciclos_completados}")
        
        if self.posiciones_abiertas:
            logger.info("📋 POSICIONES ABIERTAS:")
            for symbol, pos in self.posiciones_abiertas.items():
                tiempo = (datetime.now() - pos['timestamp']).total_seconds() / 3600
                logger.info(f"   {symbol}: {pos['side']} @ ${pos['entry_price']:.2f} ({tiempo:.1f}h)")
        
        logger.info("="*80)
    
    def ciclo_trading(self):
        """Ejecuta un ciclo completo de trading"""
        logger.info(f"🔄 Ciclo {self.ciclos_completados + 1} - Analizando mercados...")
        
        # 1. Verificar salidas de posiciones existentes
        self.verificar_salidas()
        
        # 2. Buscar nuevas oportunidades
        for symbol in self.symbols:
            if symbol in self.posiciones_abiertas:
                continue  # Ya hay posición en este símbolo
            
            # Obtener datos y analizar
            df = self.obtener_datos_mercado(symbol)
            if df.empty:
                continue
            
            señal, fuerza = self.analizar_señal(symbol, df)
            precio_actual = df['close'].iloc[-1]
            
            logger.info(f"📊 {symbol}: ${precio_actual:.2f} | Señal: {señal} (Fuerza: {fuerza})")
            
            # Ejecutar entrada si hay señal fuerte
            if señal in ['BUY', 'SELL'] and fuerza >= 4:
                self.ejecutar_entrada(symbol, señal, precio_actual, fuerza)
        
        self.ciclos_completados += 1
        
        # Mostrar estado cada 10 ciclos
        if self.ciclos_completados % 10 == 0:
            self.mostrar_estado()
    
    def iniciar_trading_automatico(self, intervalo_segundos=300):
        """Inicia el trading automático continuo"""
        logger.info("🚀 INICIANDO TRADER AUTOMÁTICO")
        logger.info(f"⏰ Intervalo: {intervalo_segundos} segundos")
        logger.info(f"💰 Balance inicial: ${self.balance_inicial:,.2f} (DINERO FAKE)")
        logger.info(f"📊 Símbolos: {', '.join(self.symbols)}")
        logger.info("🛑 Presiona Ctrl+C para detener")
        logger.info("="*80)
        
        self.corriendo = True
        
        # Handler para detener con Ctrl+C
        def signal_handler(sig, frame):
            logger.info("\n🛑 Deteniendo trader automático...")
            self.corriendo = False
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            while self.corriendo:
                self.ciclo_trading()
                
                # Esperar hasta el próximo ciclo
                for i in range(intervalo_segundos):
                    if not self.corriendo:
                        break
                    time.sleep(1)
                    
                    # Mostrar cuenta regresiva cada 60 segundos
                    if i % 60 == 0 and i > 0:
                        tiempo_restante = intervalo_segundos - i
                        logger.info(f"⏳ Próximo ciclo en {tiempo_restante} segundos...")
        
        except Exception as e:
            logger.error(f"❌ Error en trading automático: {e}")
        
        finally:
            # Cerrar todas las posiciones
            logger.info("🔐 Cerrando todas las posiciones...")
            for symbol in list(self.posiciones_abiertas.keys()):
                try:
                    ticker = self.client.get_symbol_ticker(symbol=symbol)
                    precio_actual = float(ticker['price'])
                    self.ejecutar_salida(symbol, precio_actual, "Cierre manual")
                except:
                    pass
            
            self.mostrar_estado()
            logger.info("✅ Trader automático detenido")

def main():
    """Función principal"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                    🤖 TRADER AUTOMÁTICO 🤖                       ║
    ║                  Bot que opera 24/7 como trader real             ║
    ║                        💰 Con dinero 100% FAKE                   ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    trader = TraderAutomatico()
    
    if trader.client is None:
        print("❌ No se pudo conectar con Binance API")
        return
    
    print("⚙️ CONFIGURACIÓN:")
    print(f"   Balance inicial: ${trader.balance_inicial:,.2f}")
    print(f"   Símbolos: {', '.join(trader.symbols)}")
    print(f"   Max posiciones: {trader.max_posiciones}")
    print(f"   Riesgo por trade: {trader.riesgo_por_trade*100:.1f}%")
    print(f"   Stop Loss: {trader.stop_loss_pct*100:.1f}%")
    print(f"   Take Profit: {trader.take_profit_pct*100:.1f}%")
    
    print("\n🎮 MODOS DE OPERACIÓN:")
    print("1. 🚀 Trading automático continuo (recomendado)")
    print("2. 🔄 Un solo ciclo de prueba")
    print("3. ❌ Salir")
    
    opcion = input("\nElige opción (1-3): ").strip()
    
    if opcion == "1":
        intervalo = input("⏰ Intervalo entre ciclos en segundos (300 = 5min): ").strip()
        try:
            intervalo = int(intervalo) if intervalo else 300
        except:
            intervalo = 300
        
        trader.iniciar_trading_automatico(intervalo)
        
    elif opcion == "2":
        trader.ciclo_trading()
        trader.mostrar_estado()
        
    else:
        print("👋 ¡Hasta luego!")

if __name__ == "__main__":
    main()