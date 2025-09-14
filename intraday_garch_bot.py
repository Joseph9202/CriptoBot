#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas_ta
from typing import Dict, List, Tuple, Optional
import logging
import time
from collections import deque
import threading
import json

warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_KEY = 'bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb'
API_SECRET = 'O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS'

class IntradayGARCHBot:
    """
    Bot especializado para trading intraday usando volatilidad GARCH
    Optimizado para múltiples operaciones durante el día
    """
    
    def __init__(self, symbol: str = 'BTCUSDT', initial_balance: float = 10000):
        self.symbol = symbol
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        
        # Configuración intraday optimizada
        self.volatility_lookback = 30  # Días para modelo de volatilidad
        self.fast_ema_period = 9       # EMA rápida
        self.slow_ema_period = 21      # EMA lenta
        self.rsi_period = 14
        self.bb_period = 20
        
        # Umbrales intraday
        self.rsi_overbought = 75       # Más estricto para intraday
        self.rsi_oversold = 25
        self.volatility_threshold = 1.5 # Múltiplo de volatilidad promedio
        
        # Gestión de riesgo intraday
        self.max_position_size = 0.1    # 10% del capital por operación
        self.stop_loss_pct = 0.02       # 2% stop loss
        self.take_profit_pct = 0.04     # 4% take profit (2:1 R/R)
        self.max_daily_trades = 24      # Máximo trades por día
        self.daily_loss_limit = 0.05    # 5% pérdida máxima diaria
        
        # Storage para datos
        self.data_1m = deque(maxlen=1440)   # 24h de datos 1min
        self.data_5m = deque(maxlen=288)    # 24h de datos 5min
        self.data_15m = deque(maxlen=96)    # 24h de datos 15min
        self.data_1h = deque(maxlen=168)    # 7 días de datos 1h
        
        # Estado del bot
        self.current_position = 0
        self.entry_price = 0
        self.entry_time = None
        self.daily_trades = 0
        self.daily_pnl = 0
        self.trades_history = []
        
        # Conexión API
        try:
            self.client = Client(API_KEY, API_SECRET)
            logger.info("✓ Conexión exitosa con Binance API")
        except Exception as e:
            logger.error(f"✗ Error conectando con Binance API: {e}")
            self.client = None

    def get_multi_timeframe_data(self) -> Dict[str, pd.DataFrame]:
        """Obtiene datos de múltiples timeframes"""
        timeframes = {
            '1m': Client.KLINE_INTERVAL_1MINUTE,
            '5m': Client.KLINE_INTERVAL_5MINUTE,
            '15m': Client.KLINE_INTERVAL_15MINUTE,
            '1h': Client.KLINE_INTERVAL_1HOUR
        }
        
        limits = {'1m': 240, '5m': 144, '15m': 96, '1h': 168}  # 4h, 12h, 24h, 7d
        
        data = {}
        
        for tf, interval in timeframes.items():
            try:
                klines = self.client.get_historical_klines(
                    self.symbol, interval, f"{limits[tf]} {interval}"
                )
                
                df_data = []
                for kline in klines:
                    df_data.append({
                        'timestamp': pd.to_datetime(kline[0], unit='ms'),
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
                
                df = pd.DataFrame(df_data).set_index('timestamp')
                df['returns'] = np.log(df['close']).diff()
                data[tf] = df
                
                logger.info(f"✓ {tf}: {len(df)} períodos obtenidos")
                
            except Exception as e:
                logger.error(f"Error obteniendo datos {tf}: {e}")
                data[tf] = pd.DataFrame()
        
        return data

    def calculate_intraday_volatility(self, data_1h: pd.DataFrame) -> float:
        """Calcula volatilidad intraday usando EWMA rápido"""
        if len(data_1h) < 24:  # Necesitamos al menos 24h
            return None
        
        returns = data_1h['returns'].dropna()
        
        # EWMA con decay factor para intraday (más reactivo)
        alpha = 0.15  # Más reactivo que el 0.06 tradicional
        ewma_var = returns.ewm(alpha=alpha).var().iloc[-1]
        
        # Anualizar volatilidad (252 días, 24 horas)
        annualized_vol = np.sqrt(ewma_var * 252 * 24)
        
        return annualized_vol

    def calculate_technical_signals(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """Calcula señales técnicas multi-timeframe"""
        signals = {}
        
        # Timeframe principal: 5 minutos
        df_5m = data['5m'].copy()
        if len(df_5m) < 50:
            return {}
        
        # EMAs para tendencia
        df_5m['ema_fast'] = df_5m['close'].ewm(span=self.fast_ema_period).mean()
        df_5m['ema_slow'] = df_5m['close'].ewm(span=self.slow_ema_period).mean()
        
        # RSI
        df_5m['rsi'] = pandas_ta.rsi(df_5m['close'], length=self.rsi_period)
        
        # Bollinger Bands
        bb = pandas_ta.bbands(df_5m['close'], length=self.bb_period)
        df_5m['bb_upper'] = bb.iloc[:, 2]
        df_5m['bb_lower'] = bb.iloc[:, 0]
        df_5m['bb_mid'] = bb.iloc[:, 1]
        
        # MACD
        macd = pandas_ta.macd(df_5m['close'])
        df_5m['macd'] = macd.iloc[:, 0]
        df_5m['macd_signal'] = macd.iloc[:, 1]
        df_5m['macd_hist'] = macd.iloc[:, 2]
        
        # Volumen promedio
        df_5m['vol_sma'] = df_5m['volume'].rolling(20).mean()
        
        current = df_5m.iloc[-1]
        
        signals['5m'] = {
            'trend': 'bullish' if current['ema_fast'] > current['ema_slow'] else 'bearish',
            'rsi': current['rsi'],
            'bb_position': (current['close'] - current['bb_lower']) / (current['bb_upper'] - current['bb_lower']),
            'macd_momentum': 'bullish' if current['macd'] > current['macd_signal'] else 'bearish',
            'volume_strength': current['volume'] / current['vol_sma'],
            'price': current['close']
        }
        
        # Timeframe superior: 15 minutos para confirmación
        df_15m = data['15m'].copy()
        if len(df_15m) >= 30:
            df_15m['ema_fast'] = df_15m['close'].ewm(span=9).mean()
            df_15m['ema_slow'] = df_15m['close'].ewm(span=21).mean()
            df_15m['rsi'] = pandas_ta.rsi(df_15m['close'], length=14)
            
            current_15m = df_15m.iloc[-1]
            signals['15m'] = {
                'trend': 'bullish' if current_15m['ema_fast'] > current_15m['ema_slow'] else 'bearish',
                'rsi': current_15m['rsi']
            }
        
        # Timeframe 1h para contexto general
        df_1h = data['1h'].copy()
        if len(df_1h) >= 24:
            df_1h['sma_50'] = df_1h['close'].rolling(50).mean()
            df_1h['sma_20'] = df_1h['close'].rolling(20).mean()
            
            current_1h = df_1h.iloc[-1]
            signals['1h'] = {
                'trend': 'bullish' if current_1h['sma_20'] > current_1h['sma_50'] else 'bearish',
                'context': 'strong' if abs(current_1h['close'] - current_1h['sma_20']) / current_1h['sma_20'] < 0.02 else 'weak'
            }
        
        return signals

    def generate_trading_signal(self, volatility: float, technical_signals: Dict) -> Dict:
        """Genera señal de trading combinando volatilidad y análisis técnico"""
        if not technical_signals or '5m' not in technical_signals:
            return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient data'}
        
        signal_5m = technical_signals['5m']
        signal_15m = technical_signals.get('15m', {})
        signal_1h = technical_signals.get('1h', {})
        
        # Calcular volatilidad relativa
        vol_avg = 0.3  # Volatilidad promedio estimada para BTC
        vol_ratio = volatility / vol_avg if volatility else 1
        
        # Condiciones de entrada LONG
        long_conditions = [
            signal_5m['trend'] == 'bullish',                      # Tendencia alcista 5m
            signal_5m['rsi'] < 45,                                # RSI no sobrecomprado
            signal_5m['bb_position'] < 0.3,                      # Precio en zona baja BB
            signal_5m['macd_momentum'] == 'bullish',             # MACD bullish
            signal_5m['volume_strength'] > 1.2,                  # Volumen fuerte
            signal_15m.get('trend') == 'bullish',                # Confirmación 15m
            vol_ratio > self.volatility_threshold,               # Volatilidad elevada
        ]
        
        # Condiciones de entrada SHORT
        short_conditions = [
            signal_5m['trend'] == 'bearish',                     # Tendencia bajista 5m
            signal_5m['rsi'] > 55,                               # RSI no sobrevendido
            signal_5m['bb_position'] > 0.7,                     # Precio en zona alta BB
            signal_5m['macd_momentum'] == 'bearish',            # MACD bearish
            signal_5m['volume_strength'] > 1.2,                 # Volumen fuerte
            signal_15m.get('trend') == 'bearish',               # Confirmación 15m
            vol_ratio > self.volatility_threshold,              # Volatilidad elevada
        ]
        
        # Filtros adicionales
        if signal_1h.get('context') == 'weak':
            long_conditions.append(False)
            short_conditions.append(False)
        
        # Generar señal
        long_score = sum(long_conditions)
        short_score = sum(short_conditions)
        
        if long_score >= 5:  # Al menos 5 de 7 condiciones
            return {
                'signal': 'BUY',
                'strength': long_score / len(long_conditions),
                'reason': f'Long signal: {long_score}/{len(long_conditions)} conditions met',
                'entry_price': signal_5m['price'],
                'stop_loss': signal_5m['price'] * (1 - self.stop_loss_pct),
                'take_profit': signal_5m['price'] * (1 + self.take_profit_pct)
            }
        elif short_score >= 5:
            return {
                'signal': 'SELL',
                'strength': short_score / len(short_conditions),
                'reason': f'Short signal: {short_score}/{len(short_conditions)} conditions met',
                'entry_price': signal_5m['price'],
                'stop_loss': signal_5m['price'] * (1 + self.stop_loss_pct),
                'take_profit': signal_5m['price'] * (1 - self.take_profit_pct)
            }
        else:
            return {
                'signal': 'HOLD',
                'strength': max(long_score, short_score) / 7,
                'reason': f'No clear signal: L{long_score}/S{short_score}',
                'volatility': vol_ratio
            }

    def check_exit_conditions(self, current_price: float, volatility: float) -> bool:
        """Verifica condiciones de salida"""
        if self.current_position == 0:
            return False
        
        # Tiempo máximo en posición (4 horas)
        if self.entry_time:
            time_in_position = datetime.now() - self.entry_time
            if time_in_position > timedelta(hours=4):
                return True
        
        # Stop loss y take profit
        if self.current_position > 0:  # Long position
            if current_price <= self.entry_price * (1 - self.stop_loss_pct):
                return True
            if current_price >= self.entry_price * (1 + self.take_profit_pct):
                return True
        else:  # Short position
            if current_price >= self.entry_price * (1 + self.stop_loss_pct):
                return True
            if current_price <= self.entry_price * (1 - self.take_profit_pct):
                return True
        
        # Límite de pérdida diaria
        if self.daily_pnl <= -self.daily_loss_limit * self.current_balance:
            return True
        
        # Volatilidad extrema (salida de emergencia)
        vol_avg = 0.3
        if volatility and volatility / vol_avg > 3:
            return True
        
        return False

    def execute_trade(self, signal: Dict) -> Dict:
        """Ejecuta una operación (simulada)"""
        if signal['signal'] == 'HOLD':
            return {'executed': False, 'reason': 'No signal'}
        
        # Verificar límites diarios
        if self.daily_trades >= self.max_daily_trades:
            return {'executed': False, 'reason': 'Daily trade limit reached'}
        
        if self.current_position != 0:
            return {'executed': False, 'reason': 'Already in position'}
        
        # Calcular tamaño de posición
        risk_amount = self.current_balance * self.max_position_size
        position_size = risk_amount / abs(signal['entry_price'] * self.stop_loss_pct)
        
        # Ejecutar entrada
        self.current_position = 1 if signal['signal'] == 'BUY' else -1
        self.entry_price = signal['entry_price']
        self.entry_time = datetime.now()
        self.daily_trades += 1
        
        trade = {
            'executed': True,
            'type': signal['signal'],
            'entry_price': self.entry_price,
            'position_size': position_size,
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'timestamp': self.entry_time,
            'strength': signal['strength']
        }
        
        logger.info(f"🔄 Trade ejecutado: {signal['signal']} @ ${self.entry_price:.2f}")
        return trade

    def close_position(self, exit_price: float, reason: str) -> Dict:
        """Cierra posición actual"""
        if self.current_position == 0:
            return {'closed': False, 'reason': 'No position to close'}
        
        # Calcular P&L
        if self.current_position > 0:  # Long
            pnl_pct = (exit_price - self.entry_price) / self.entry_price
        else:  # Short
            pnl_pct = (self.entry_price - exit_price) / self.entry_price
        
        # Comisiones (0.1% por lado)
        pnl_pct -= 0.002
        
        # Actualizar balance
        pnl_amount = self.current_balance * self.max_position_size * pnl_pct
        self.current_balance += pnl_amount
        self.daily_pnl += pnl_amount
        
        trade_result = {
            'closed': True,
            'exit_price': exit_price,
            'entry_price': self.entry_price,
            'pnl_pct': pnl_pct,
            'pnl_amount': pnl_amount,
            'duration': datetime.now() - self.entry_time if self.entry_time else None,
            'reason': reason,
            'balance': self.current_balance
        }
        
        self.trades_history.append(trade_result)
        
        # Reset posición
        self.current_position = 0
        self.entry_price = 0
        self.entry_time = None
        
        logger.info(f"✅ Position closed: {pnl_pct:.2%} P&L, Balance: ${self.current_balance:.2f}")
        return trade_result

    def run_intraday_simulation(self, hours: int = 8) -> Dict:
        """Ejecuta simulación de trading intraday"""
        logger.info(f"🚀 Iniciando simulación intraday por {hours} horas")
        
        # Resetear estado diario
        self.daily_trades = 0
        self.daily_pnl = 0
        start_balance = self.current_balance
        
        simulation_results = []
        
        # Simular trading cada 5 minutos
        intervals = hours * 12  # 12 intervalos de 5min por hora
        
        for i in range(intervals):
            try:
                # Obtener datos actualizados
                data = self.get_multi_timeframe_data()
                
                # Calcular volatilidad
                volatility = self.calculate_intraday_volatility(data.get('1h', pd.DataFrame()))
                
                # Calcular señales técnicas
                technical_signals = self.calculate_technical_signals(data)
                
                if not technical_signals:
                    continue
                
                current_price = technical_signals['5m']['price']
                
                # Verificar condiciones de salida
                if self.current_position != 0 and self.check_exit_conditions(current_price, volatility):
                    exit_result = self.close_position(current_price, "Exit conditions met")
                    simulation_results.append(exit_result)
                
                # Generar señal de entrada (solo si no hay posición)
                if self.current_position == 0:
                    signal = self.generate_trading_signal(volatility, technical_signals)
                    
                    if signal['signal'] != 'HOLD':
                        trade_result = self.execute_trade(signal)
                        if trade_result['executed']:
                            simulation_results.append(trade_result)
                
                # Log cada hora
                if i % 12 == 0:
                    logger.info(f"⏰ Hora {i//12+1}: Balance ${self.current_balance:.2f}, "
                              f"Trades: {self.daily_trades}, Position: {self.current_position}")
                
                # Pequeña pausa para simular tiempo real
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error en iteración {i}: {e}")
                continue
        
        # Cerrar posición si queda abierta
        if self.current_position != 0:
            data = self.get_multi_timeframe_data()
            if '5m' in data and len(data['5m']) > 0:
                final_price = data['5m']['close'].iloc[-1]
                final_exit = self.close_position(final_price, "End of session")
                simulation_results.append(final_exit)
        
        # Resultados finales
        total_return = (self.current_balance - start_balance) / start_balance
        
        results = {
            'session_duration': f"{hours} hours",
            'total_trades': self.daily_trades,
            'successful_trades': len([r for r in self.trades_history if r.get('pnl_pct', 0) > 0]),
            'start_balance': start_balance,
            'end_balance': self.current_balance,
            'total_return': total_return,
            'total_pnl': self.daily_pnl,
            'win_rate': len([r for r in self.trades_history if r.get('pnl_pct', 0) > 0]) / max(self.daily_trades, 1),
            'trades_detail': self.trades_history[-self.daily_trades:] if self.daily_trades > 0 else []
        }
        
        return results

    def print_intraday_results(self, results: Dict):
        """Imprime resultados de la simulación intraday"""
        print("\n" + "="*80)
        print("📊 RESULTADOS SIMULACIÓN INTRADAY - GARCH BOT")
        print("="*80)
        print(f"🎯 Símbolo: {self.symbol}")
        print(f"⏱️ Duración: {results['session_duration']}")
        print(f"💰 Balance inicial: ${results['start_balance']:,.2f}")
        print(f"💰 Balance final: ${results['end_balance']:,.2f}")
        print(f"📈 Retorno total: {results['total_return']:.2%}")
        print(f"💵 P&L total: ${results['total_pnl']:,.2f}")
        print(f"📊 Total trades: {results['total_trades']}")
        print(f"🟢 Trades exitosos: {results['successful_trades']}")
        print(f"🎯 Win rate: {results['win_rate']:.1%}")
        
        if results['trades_detail']:
            print(f"\n🔍 DETALLE DE TRADES:")
            print("-" * 80)
            for i, trade in enumerate(results['trades_detail'][-5:], 1):
                duration = trade.get('duration')
                duration_str = f"{duration.total_seconds()/60:.0f}min" if duration else "N/A"
                print(f"  {i:2}. P&L: {trade.get('pnl_pct', 0):.2%} | "
                      f"Duración: {duration_str} | "
                      f"Razón salida: {trade.get('reason', 'N/A')}")
        
        print("="*80)

def main():
    """Función principal para trading intraday"""
    print("🚀 INTRADAY GARCH BOT - Trading de Alta Frecuencia")
    print("Especializado en múltiples operaciones intraday usando volatilidad GARCH")
    
    # Crear bot intraday
    bot = IntradayGARCHBot(symbol='BTCUSDT', initial_balance=10000)
    
    if bot.client is None:
        print("❌ No se pudo conectar con la API")
        return
    
    # Ejecutar simulación intraday
    print(f"\n📈 Iniciando simulación de trading intraday...")
    results = bot.run_intraday_simulation(hours=8)  # Simular 8 horas de trading
    
    # Mostrar resultados
    bot.print_intraday_results(results)
    
    print("\n🎯 CARACTERÍSTICAS CLAVE PARA INTRADAY:")
    print("-" * 50)
    print("✅ Múltiples timeframes (1m, 5m, 15m, 1h)")
    print("✅ Señales de alta frecuencia")
    print("✅ Stop-loss y take-profit automáticos")
    print("✅ Límite de trades diarios")
    print("✅ Control de riesgo por operación")
    print("✅ Gestión de volatilidad en tiempo real")
    print("✅ Salida automática al final del día")
    
    print("\n⚡ OPTIMIZACIONES PARA TRADING REAL:")
    print("-" * 50)
    print("1. Conectar WebSocket para datos en tiempo real")
    print("2. Implementar ejecución de órdenes automática")
    print("3. Añadir notificaciones de trades")
    print("4. Integrar análisis de order book")
    print("5. Implementar paper trading en vivo")

if __name__ == "__main__":
    main()