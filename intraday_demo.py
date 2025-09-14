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

warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_KEY = 'bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb'
API_SECRET = 'O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS'

class IntradayDemoBot:
    """
    Demostración de bot intraday GARCH simplificado
    """
    
    def __init__(self, symbol: str = 'BTCUSDT', initial_balance: float = 10000):
        self.symbol = symbol
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        
        # Parámetros optimizados para intraday
        self.max_position_size = 0.1    # 10% del capital
        self.stop_loss_pct = 0.015      # 1.5% stop loss
        self.take_profit_pct = 0.03     # 3% take profit (2:1 R/R)
        self.max_daily_trades = 8       # Máximo 8 trades por día
        
        # Estado
        self.position = 0
        self.entry_price = 0
        self.trades_history = []
        
        # Conexión API
        try:
            self.client = Client(API_KEY, API_SECRET)
            logger.info("✓ Conexión exitosa con Binance API")
        except Exception as e:
            logger.error(f"✗ Error conectando: {e}")
            self.client = None

    def get_intraday_data(self) -> Dict[str, pd.DataFrame]:
        """Obtiene datos para análisis intraday"""
        try:
            # Datos de diferentes timeframes
            data = {}
            
            # 5 minutos - para señales principales
            klines_5m = self.client.get_historical_klines(
                self.symbol, Client.KLINE_INTERVAL_5MINUTE, "8 hours ago UTC"
            )
            
            df_5m = []
            for kline in klines_5m:
                df_5m.append({
                    'timestamp': pd.to_datetime(kline[0], unit='ms'),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            
            data['5m'] = pd.DataFrame(df_5m).set_index('timestamp')
            data['5m']['returns'] = np.log(data['5m']['close']).diff()
            
            # 15 minutos - para confirmación
            klines_15m = self.client.get_historical_klines(
                self.symbol, Client.KLINE_INTERVAL_15MINUTE, "24 hours ago UTC"
            )
            
            df_15m = []
            for kline in klines_15m:
                df_15m.append({
                    'timestamp': pd.to_datetime(kline[0], unit='ms'),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            
            data['15m'] = pd.DataFrame(df_15m).set_index('timestamp')
            data['15m']['returns'] = np.log(data['15m']['close']).diff()
            
            logger.info(f"✓ Datos obtenidos: 5m={len(data['5m'])}, 15m={len(data['15m'])}")
            return data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos: {e}")
            return {}

    def calculate_volatility_signal(self, df_15m: pd.DataFrame) -> float:
        """Calcula señal de volatilidad simplificada"""
        if len(df_15m) < 20:
            return 1.0
        
        # Volatilidad EWMA rápida
        returns = df_15m['returns'].dropna()
        ewma_vol = returns.ewm(alpha=0.2).std().iloc[-1]
        
        # Volatilidad promedio (rolling)
        avg_vol = returns.rolling(20).std().mean()
        
        # Ratio de volatilidad actual vs promedio
        vol_ratio = ewma_vol / avg_vol if avg_vol > 0 else 1
        
        return vol_ratio

    def calculate_technical_signals(self, df_5m: pd.DataFrame) -> Dict:
        """Calcula indicadores técnicos para señales intraday"""
        if len(df_5m) < 30:
            return {}
        
        df = df_5m.copy()
        
        # EMAs para tendencia
        df['ema_9'] = df['close'].ewm(span=9).mean()
        df['ema_21'] = df['close'].ewm(span=21).mean()
        
        # RSI
        df['rsi'] = pandas_ta.rsi(df['close'], length=14)
        
        # Bollinger Bands
        bb = pandas_ta.bbands(df['close'], length=20)
        df['bb_upper'] = bb.iloc[:, 2]
        df['bb_lower'] = bb.iloc[:, 0]
        df['bb_mid'] = bb.iloc[:, 1]
        
        # MACD
        macd = pandas_ta.macd(df['close'])
        df['macd'] = macd.iloc[:, 0]
        df['macd_signal'] = macd.iloc[:, 1]
        
        # Obtener valores actuales
        current = df.iloc[-1]
        
        signals = {
            'price': current['close'],
            'trend': 'bullish' if current['ema_9'] > current['ema_21'] else 'bearish',
            'rsi': current['rsi'],
            'bb_position': (current['close'] - current['bb_lower']) / (current['bb_upper'] - current['bb_lower']),
            'macd_bullish': current['macd'] > current['macd_signal'],
            'volume_strength': current['volume'] / df['volume'].rolling(20).mean().iloc[-1]
        }
        
        return signals

    def generate_intraday_signal(self, vol_ratio: float, technical: Dict) -> Dict:
        """Genera señal de trading intraday"""
        if not technical:
            return {'signal': 'HOLD', 'strength': 0}
        
        # Condiciones para LONG
        long_conditions = [
            technical['trend'] == 'bullish',           # Tendencia alcista
            technical['rsi'] < 40,                     # RSI no sobrecomprado
            technical['bb_position'] < 0.3,           # Precio en zona baja BB
            technical['macd_bullish'],                 # MACD bullish
            vol_ratio > 1.3,                          # Volatilidad elevada
            technical['volume_strength'] > 1.1        # Volumen por encima promedio
        ]
        
        # Condiciones para SHORT
        short_conditions = [
            technical['trend'] == 'bearish',          # Tendencia bajista
            technical['rsi'] > 60,                    # RSI no sobrevendido
            technical['bb_position'] > 0.7,          # Precio en zona alta BB
            not technical['macd_bullish'],           # MACD bearish
            vol_ratio > 1.3,                         # Volatilidad elevada
            technical['volume_strength'] > 1.1       # Volumen por encima promedio
        ]
        
        long_score = sum(long_conditions)
        short_score = sum(short_conditions)
        
        if long_score >= 4:  # Al menos 4 de 6 condiciones
            return {
                'signal': 'BUY',
                'strength': long_score / len(long_conditions),
                'entry_price': technical['price'],
                'stop_loss': technical['price'] * (1 - self.stop_loss_pct),
                'take_profit': technical['price'] * (1 + self.take_profit_pct),
                'reason': f'Long: {long_score}/6 condiciones'
            }
        elif short_score >= 4:
            return {
                'signal': 'SELL',
                'strength': short_score / len(short_conditions),
                'entry_price': technical['price'],
                'stop_loss': technical['price'] * (1 + self.stop_loss_pct),
                'take_profit': technical['price'] * (1 - self.take_profit_pct),
                'reason': f'Short: {short_score}/6 condiciones'
            }
        else:
            return {
                'signal': 'HOLD',
                'strength': max(long_score, short_score) / 6,
                'reason': f'Sin señal clara: L{long_score}/S{short_score}',
                'vol_ratio': vol_ratio
            }

    def simulate_intraday_session(self) -> Dict:
        """Simula una sesión de trading intraday"""
        logger.info("🚀 Iniciando simulación de sesión intraday")
        
        # Obtener datos
        data = self.get_intraday_data()
        if not data or '5m' not in data:
            return {'error': 'No data available'}
        
        df_5m = data['5m']
        df_15m = data['15m']
        
        # Simular trading en los últimos períodos
        results = []
        trades_today = 0
        
        # Analizar cada 5min de las últimas 2 horas (24 períodos)
        for i in range(max(len(df_5m) - 24, 30), len(df_5m)):
            if trades_today >= self.max_daily_trades:
                break
            
            # Datos hasta el período actual
            current_5m = df_5m.iloc[:i+1]
            
            # Calcular señales
            vol_ratio = self.calculate_volatility_signal(df_15m)
            technical = self.calculate_technical_signals(current_5m)
            
            if not technical:
                continue
            
            # Generar señal
            signal = self.generate_intraday_signal(vol_ratio, technical)
            
            # Simular entrada si hay señal y no hay posición
            if signal['signal'] != 'HOLD' and self.position == 0:
                self.position = 1 if signal['signal'] == 'BUY' else -1
                self.entry_price = signal['entry_price']
                entry_time = df_5m.index[i]
                
                # Buscar salida en los siguientes períodos (máximo 1 hora = 12 períodos)
                exit_found = False
                for j in range(i+1, min(i+13, len(df_5m))):
                    current_price = df_5m['close'].iloc[j]
                    
                    # Check stop loss / take profit
                    if self.position > 0:  # Long
                        if current_price <= signal['stop_loss'] or current_price >= signal['take_profit']:
                            exit_found = True
                        elif j == min(i+12, len(df_5m)-1):  # Salida por tiempo
                            exit_found = True
                    else:  # Short
                        if current_price >= signal['stop_loss'] or current_price <= signal['take_profit']:
                            exit_found = True
                        elif j == min(i+12, len(df_5m)-1):  # Salida por tiempo
                            exit_found = True
                    
                    if exit_found:
                        # Calcular P&L
                        if self.position > 0:
                            pnl_pct = (current_price - self.entry_price) / self.entry_price
                        else:
                            pnl_pct = (self.entry_price - current_price) / self.entry_price
                        
                        # Comisiones
                        pnl_pct -= 0.002  # 0.2% total fees
                        
                        # Actualizar balance
                        pnl_amount = self.current_balance * self.max_position_size * pnl_pct
                        self.current_balance += pnl_amount
                        
                        trade_result = {
                            'entry_time': entry_time,
                            'exit_time': df_5m.index[j],
                            'type': signal['signal'],
                            'entry_price': self.entry_price,
                            'exit_price': current_price,
                            'pnl_pct': pnl_pct,
                            'pnl_amount': pnl_amount,
                            'duration_min': (j - i) * 5,
                            'strength': signal['strength'],
                            'reason': signal['reason']
                        }
                        
                        results.append(trade_result)
                        self.trades_history.append(trade_result)
                        trades_today += 1
                        
                        # Reset posición
                        self.position = 0
                        self.entry_price = 0
                        
                        logger.info(f"Trade #{trades_today}: {signal['signal']} {pnl_pct:.2%} en {(j-i)*5}min")
                        break
        
        # Calcular métricas
        if results:
            returns = [t['pnl_pct'] for t in results]
            winning_trades = [t for t in results if t['pnl_pct'] > 0]
            
            session_results = {
                'total_trades': len(results),
                'winning_trades': len(winning_trades),
                'win_rate': len(winning_trades) / len(results),
                'avg_return': np.mean(returns),
                'total_return': (self.current_balance - self.initial_balance) / self.initial_balance,
                'avg_duration': np.mean([t['duration_min'] for t in results]),
                'start_balance': self.initial_balance,
                'end_balance': self.current_balance,
                'trades_detail': results
            }
        else:
            session_results = {
                'total_trades': 0,
                'winning_trades': 0,
                'win_rate': 0,
                'avg_return': 0,
                'total_return': 0,
                'avg_duration': 0,
                'start_balance': self.initial_balance,
                'end_balance': self.current_balance,
                'trades_detail': []
            }
        
        return session_results

    def print_session_results(self, results: Dict):
        """Imprime resultados de la sesión"""
        print("\n" + "="*80)
        print("📊 RESULTADOS SESIÓN INTRADAY - GARCH BOT")
        print("="*80)
        print(f"🎯 Símbolo: {self.symbol}")
        print(f"💰 Balance inicial: ${results['start_balance']:,.2f}")
        print(f"💰 Balance final: ${results['end_balance']:,.2f}")
        print(f"📈 Retorno total: {results['total_return']:.2%}")
        print(f"📊 Trades ejecutados: {results['total_trades']}")
        print(f"🟢 Trades ganadores: {results['winning_trades']}")
        print(f"🎯 Tasa de acierto: {results['win_rate']:.1%}")
        print(f"📊 Retorno promedio: {results['avg_return']:.2%}")
        print(f"⏱️ Duración promedio: {results['avg_duration']:.0f} minutos")
        
        if results['trades_detail']:
            print(f"\n🔍 DETALLE DE TRADES:")
            print("-" * 80)
            for i, trade in enumerate(results['trades_detail'], 1):
                print(f"  {i:2}. {trade['type']:<4} | "
                      f"P&L: {trade['pnl_pct']:>6.2%} | "
                      f"Duración: {trade['duration_min']:>3.0f}min | "
                      f"Entrada: ${trade['entry_price']:.2f}")
        
        print("="*80)

def main():
    """Función principal"""
    print("🚀 DEMO INTRADAY GARCH BOT")
    print("Demostración de trading intraday con análisis de volatilidad")
    
    # Crear bot
    bot = IntradayDemoBot(symbol='BTCUSDT', initial_balance=10000)
    
    if bot.client is None:
        print("❌ No se pudo conectar con la API")
        return
    
    # Ejecutar simulación
    results = bot.simulate_intraday_session()
    
    if 'error' not in results:
        bot.print_session_results(results)
    else:
        print(f"❌ Error: {results['error']}")
    
    print("\n🎯 ADAPTACIONES PARA INTRADAY:")
    print("-" * 50)
    print("✅ Timeframes múltiples (5m principal, 15m confirmación)")
    print("✅ Señales de alta frecuencia con filtros estrictos")
    print("✅ Stop-loss y take-profit ajustados (1.5% / 3%)")
    print("✅ Máximo 8 trades por día para evitar overtrading")
    print("✅ Salida automática después de 1 hora máximo")
    print("✅ Análisis de volatilidad en tiempo real")
    print("✅ Gestión de riesgo por operación (10% capital)")
    
    print("\n⚡ VENTAJAS DEL ENFOQUE INTRADAY:")
    print("-" * 50)
    print("• Mayor frecuencia de oportunidades")
    print("• Control estricto de riesgo por trade")
    print("• Sin exposición overnight")
    print("• Aprovecha volatilidad intraday")
    print("• Rápida adaptación a cambios de mercado")
    
    print("\n🔧 PARA IMPLEMENTACIÓN EN VIVO:")
    print("-" * 50)
    print("1. WebSocket para datos en tiempo real")
    print("2. Ejecución automática de órdenes")
    print("3. Monitoreo continuo de posiciones")
    print("4. Alertas en tiempo real")
    print("5. Dashboard de control")

if __name__ == "__main__":
    main()