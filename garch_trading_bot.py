#!/usr/bin/env python3

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
from arch import arch_model
import pandas_ta
from typing import Dict, List, Tuple, Optional
import logging

warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_KEY = 'bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb'
API_SECRET = 'O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS'

class GARCHVolatilityBot:
    """
    Bot de trading basado en modelo GARCH para predicción de volatilidad
    Implementa la estrategia del notebook con mejoras y simulación en tiempo real
    """
    
    def __init__(self, symbol: str = 'BTCUSDT', initial_balance: float = 10000):
        self.symbol = symbol
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.position_size = 0
        self.entry_price = 0
        self.trades_history = []
        
        # Configuración del modelo
        self.lookback_window = 180  # 6 meses
        self.garch_p = 1
        self.garch_q = 3
        
        # Configuración de indicadores técnicos
        self.rsi_period = 20
        self.bb_period = 20
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        
        # DataFrames para almacenar datos
        self.daily_data = pd.DataFrame()
        self.intraday_data = pd.DataFrame()
        
        # Conexión a Binance
        try:
            self.client = Client(API_KEY, API_SECRET)
            logger.info("✓ Conexión exitosa con Binance API")
        except Exception as e:
            logger.error(f"✗ Error conectando con Binance API: {e}")
            self.client = None

    def fetch_historical_data(self, days: int = 365) -> bool:
        """Obtiene datos históricos diarios para el entrenamiento del modelo"""
        try:
            # Datos diarios
            klines = self.client.get_historical_klines(
                self.symbol, 
                Client.KLINE_INTERVAL_1DAY, 
                f"{days} days ago UTC"
            )
            
            daily_data = []
            for kline in klines:
                daily_data.append({
                    'timestamp': pd.to_datetime(kline[0], unit='ms'),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            
            self.daily_data = pd.DataFrame(daily_data).set_index('timestamp')
            self.daily_data['log_ret'] = np.log(self.daily_data['close']).diff()
            self.daily_data['variance'] = self.daily_data['log_ret'].rolling(self.lookback_window).var()
            
            logger.info(f"✓ Obtenidos {len(self.daily_data)} días de datos históricos")
            return True
            
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos: {e}")
            return False

    def fetch_intraday_data(self, hours: int = 24) -> bool:
        """Obtiene datos intradiarios de 5 minutos"""
        try:
            klines = self.client.get_historical_klines(
                self.symbol, 
                Client.KLINE_INTERVAL_5MINUTE, 
                f"{hours} hours ago UTC"
            )
            
            intraday_data = []
            for kline in klines:
                intraday_data.append({
                    'timestamp': pd.to_datetime(kline[0], unit='ms'),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            
            self.intraday_data = pd.DataFrame(intraday_data).set_index('timestamp')
            self.intraday_data['date'] = pd.to_datetime(self.intraday_data.index.date)
            self.intraday_data['return'] = np.log(self.intraday_data['close']).diff()
            
            logger.info(f"✓ Obtenidos {len(self.intraday_data)} períodos de 5min")
            return True
            
        except Exception as e:
            logger.error(f"Error obteniendo datos intradiarios: {e}")
            return False

    def fit_garch_model(self, returns: pd.Series) -> Optional[float]:
        """Ajusta modelo GARCH y predice volatilidad"""
        try:
            if len(returns.dropna()) < 50:
                return None
                
            model = arch_model(
                returns.dropna(), 
                p=self.garch_p, 
                q=self.garch_q,
                rescale=False
            )
            
            fitted_model = model.fit(disp='off', show_warning=False)
            forecast = fitted_model.forecast(horizon=1)
            
            return forecast.variance.iloc[-1, 0]
            
        except Exception as e:
            logger.warning(f"Error ajustando modelo GARCH: {e}")
            return None

    def calculate_garch_signals(self) -> pd.DataFrame:
        """Calcula señales basadas en predicciones GARCH"""
        if len(self.daily_data) < self.lookback_window:
            logger.warning("No hay suficientes datos para el modelo GARCH")
            return pd.DataFrame()
        
        # Calcular predicciones GARCH en ventana móvil
        predictions = []
        
        for i in range(self.lookback_window, len(self.daily_data)):
            window_returns = self.daily_data['log_ret'].iloc[i-self.lookback_window:i]
            prediction = self.fit_garch_model(window_returns)
            
            predictions.append({
                'timestamp': self.daily_data.index[i],
                'prediction': prediction,
                'actual_variance': self.daily_data['variance'].iloc[i]
            })
        
        predictions_df = pd.DataFrame(predictions).set_index('timestamp')
        predictions_df = predictions_df.dropna()
        
        # Calcular premium de predicción
        predictions_df['prediction_premium'] = (
            (predictions_df['prediction'] - predictions_df['actual_variance']) / 
            predictions_df['actual_variance']
        )
        
        # Calcular señal diaria
        predictions_df['premium_std'] = predictions_df['prediction_premium'].rolling(self.lookback_window).std()
        
        predictions_df['signal_daily'] = predictions_df.apply(
            lambda x: 1 if x['prediction_premium'] > x['premium_std']
            else (-1 if x['prediction_premium'] < -x['premium_std'] else 0),
            axis=1
        )
        
        # Desplazar señal un día
        predictions_df['signal_daily'] = predictions_df['signal_daily'].shift(1)
        
        return predictions_df

    def calculate_technical_indicators(self) -> pd.DataFrame:
        """Calcula indicadores técnicos intradiarios"""
        if len(self.intraday_data) == 0:
            return pd.DataFrame()
        
        df = self.intraday_data.copy()
        
        # RSI
        df['rsi'] = pandas_ta.rsi(df['close'], length=self.rsi_period)
        
        # Bollinger Bands
        bb = pandas_ta.bbands(df['close'], length=self.bb_period)
        df['bb_lower'] = bb.iloc[:, 0]
        df['bb_upper'] = bb.iloc[:, 2]
        
        # Señal intradiaria
        df['signal_intraday'] = df.apply(
            lambda x: 1 if (x['rsi'] > self.rsi_overbought) and (x['close'] > x['bb_upper'])
            else (-1 if (x['rsi'] < self.rsi_oversold) and (x['close'] < x['bb_lower']) else 0),
            axis=1
        )
        
        return df

    def combine_signals(self, garch_signals: pd.DataFrame, technical_df: pd.DataFrame) -> pd.DataFrame:
        """Combina señales GARCH con señales técnicas intradiarias"""
        if len(garch_signals) == 0 or len(technical_df) == 0:
            return pd.DataFrame()
        
        # Fusionar datos
        combined_df = technical_df.reset_index().merge(
            garch_signals[['signal_daily']].reset_index(),
            left_on='date',
            right_on='timestamp',
            how='left'
        ).set_index('timestamp_x')
        
        # Señal de trading combinada
        combined_df['trading_signal'] = combined_df.apply(
            lambda x: -1 if (x['signal_daily'] == 1) and (x['signal_intraday'] == 1)  # Venta en alta volatilidad + sobrecompra
            else (1 if (x['signal_daily'] == -1) and (x['signal_intraday'] == -1) else 0),  # Compra en baja volatilidad + sobreventa
            axis=1
        )
        
        # Forward fill señales durante el día
        combined_df['trading_signal'] = combined_df.groupby('date')['trading_signal'].transform(lambda x: x.replace(0, method='ffill'))
        
        return combined_df

    def simulate_trading_strategy(self, combined_df: pd.DataFrame) -> Dict:
        """Simula estrategia de trading y calcula métricas"""
        if len(combined_df) == 0:
            return {}
        
        trades = []
        portfolio_value = [self.initial_balance]
        current_balance = self.initial_balance
        position = 0
        entry_price = 0
        
        for i in range(1, len(combined_df)):
            row = combined_df.iloc[i]
            prev_row = combined_df.iloc[i-1]
            
            signal = row['trading_signal']
            price = row['close']
            
            # Entrada en posición
            if signal != 0 and position == 0:
                position = signal
                entry_price = price
                
                trade = {
                    'entry_time': row.name,
                    'entry_price': entry_price,
                    'signal': signal,
                    'type': 'LONG' if signal == 1 else 'SHORT'
                }
                
            # Salida al final del día o cambio de señal
            elif position != 0 and (row['date'] != prev_row['date'] or signal != position):
                exit_price = price
                
                if position == 1:  # Long position
                    return_pct = (exit_price - entry_price) / entry_price
                else:  # Short position
                    return_pct = (entry_price - exit_price) / entry_price
                
                current_balance *= (1 + return_pct)
                
                trade.update({
                    'exit_time': row.name,
                    'exit_price': exit_price,
                    'return_pct': return_pct,
                    'profit_loss': current_balance - portfolio_value[-1]
                })
                
                trades.append(trade)
                position = 0
                entry_price = 0
            
            portfolio_value.append(current_balance)
        
        # Calcular métricas
        returns = pd.Series([t['return_pct'] for t in trades])
        
        metrics = {
            'total_trades': len(trades),
            'winning_trades': len([t for t in trades if t['return_pct'] > 0]),
            'losing_trades': len([t for t in trades if t['return_pct'] < 0]),
            'win_rate': len([t for t in trades if t['return_pct'] > 0]) / max(len(trades), 1),
            'total_return': (current_balance - self.initial_balance) / self.initial_balance,
            'sharpe_ratio': returns.mean() / returns.std() if len(returns) > 1 and returns.std() > 0 else 0,
            'max_drawdown': self.calculate_max_drawdown(portfolio_value),
            'final_balance': current_balance,
            'trades': trades,
            'portfolio_value': portfolio_value
        }
        
        return metrics

    def calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calcula el máximo drawdown"""
        if len(portfolio_values) < 2:
            return 0
        
        portfolio_series = pd.Series(portfolio_values)
        rolling_max = portfolio_series.expanding().max()
        drawdown = (portfolio_series - rolling_max) / rolling_max
        
        return drawdown.min()

    def run_backtest(self) -> Dict:
        """Ejecuta el backtest completo"""
        logger.info("🚀 Iniciando backtest de estrategia GARCH")
        
        # 1. Obtener datos
        if not self.fetch_historical_data():
            return {}
        
        if not self.fetch_intraday_data(hours=48):  # 2 días de datos intraday
            return {}
        
        # 2. Calcular señales GARCH
        logger.info("📊 Calculando señales GARCH...")
        garch_signals = self.calculate_garch_signals()
        
        if len(garch_signals) == 0:
            logger.error("No se pudieron calcular señales GARCH")
            return {}
        
        # 3. Calcular indicadores técnicos
        logger.info("📈 Calculando indicadores técnicos...")
        technical_df = self.calculate_technical_indicators()
        
        # 4. Combinar señales
        logger.info("🔄 Combinando señales...")
        combined_df = self.combine_signals(garch_signals, technical_df)
        
        if len(combined_df) == 0:
            logger.error("No se pudieron combinar las señales")
            return {}
        
        # 5. Simular trading
        logger.info("💹 Simulando estrategia de trading...")
        results = self.simulate_trading_strategy(combined_df)
        
        return results

    def print_results(self, results: Dict):
        """Imprime resultados del backtest"""
        if not results:
            print("❌ No hay resultados para mostrar")
            return
        
        print("\n" + "="*80)
        print("📊 RESULTADOS DEL BACKTEST - ESTRATEGIA GARCH")
        print("="*80)
        print(f"🎯 Símbolo: {self.symbol}")
        print(f"💰 Balance inicial: ${self.initial_balance:,.2f}")
        print(f"💰 Balance final: ${results['final_balance']:,.2f}")
        print(f"📈 Retorno total: {results['total_return']:.2%}")
        print(f"📊 Total de trades: {results['total_trades']}")
        print(f"🟢 Trades ganadores: {results['winning_trades']}")
        print(f"🔴 Trades perdedores: {results['losing_trades']}")
        print(f"🎯 Tasa de acierto: {results['win_rate']:.2%}")
        print(f"📉 Máximo drawdown: {results['max_drawdown']:.2%}")
        print(f"📊 Sharpe ratio: {results['sharpe_ratio']:.3f}")
        
        if results['trades']:
            print(f"\n🔍 ÚLTIMOS 5 TRADES:")
            print("-" * 80)
            for trade in results['trades'][-5:]:
                print(f"  {trade['type']:<5} | Entrada: ${trade['entry_price']:.2f} | "
                      f"Salida: ${trade['exit_price']:.2f} | "
                      f"Retorno: {trade['return_pct']:.2%}")
        
        print("="*80)

    def plot_results(self, results: Dict):
        """Grafica los resultados"""
        if not results or not results['portfolio_value']:
            return
        
        plt.figure(figsize=(15, 10))
        
        # Subplot 1: Evolución del portfolio
        plt.subplot(2, 1, 1)
        portfolio_values = results['portfolio_value']
        times = range(len(portfolio_values))
        
        plt.plot(times, portfolio_values, linewidth=2, color='blue', label='Portfolio Value')
        plt.axhline(y=self.initial_balance, color='red', linestyle='--', alpha=0.7, label='Initial Balance')
        plt.title(f'Evolución del Portfolio - Estrategia GARCH ({self.symbol})', fontsize=14)
        plt.ylabel('Valor del Portfolio ($)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Subplot 2: Drawdown
        plt.subplot(2, 1, 2)
        portfolio_series = pd.Series(portfolio_values)
        rolling_max = portfolio_series.expanding().max()
        drawdown = (portfolio_series - rolling_max) / rolling_max * 100
        
        plt.fill_between(times, drawdown, 0, alpha=0.3, color='red')
        plt.plot(times, drawdown, color='red', linewidth=1)
        plt.title('Drawdown (%)', fontsize=14)
        plt.ylabel('Drawdown (%)')
        plt.xlabel('Tiempo')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()

def main():
    """Función principal"""
    print("🚀 Iniciando Bot de Trading con Modelo GARCH")
    
    # Configuración
    symbol = 'BTCUSDT'
    initial_balance = 10000
    
    # Crear e inicializar bot
    bot = GARCHVolatilityBot(symbol=symbol, initial_balance=initial_balance)
    
    if bot.client is None:
        print("❌ No se pudo conectar con la API. Verifica tus credenciales.")
        return
    
    # Ejecutar backtest
    results = bot.run_backtest()
    
    if results:
        # Mostrar resultados
        bot.print_results(results)
        
        # Graficar resultados
        try:
            bot.plot_results(results)
        except Exception as e:
            logger.warning(f"No se pudieron mostrar gráficos: {e}")
    
    print("\n🔧 ANÁLISIS DE MEJORAS POTENCIALES:")
    print("-" * 50)
    print("1. 📊 OPTIMIZACIÓN DE PARÁMETROS:")
    print("   - Ventana de lookback (actual: 180 días)")
    print("   - Parámetros GARCH (p, q)")
    print("   - Períodos RSI y Bollinger Bands")
    
    print("\n2. 🎯 MEJORAS EN SEÑALES:")
    print("   - Filtros adicionales de volatilidad")
    print("   - Indicadores de momentum (MACD, Stochastic)")
    print("   - Análisis de volumen")
    
    print("\n3. 🛡️ GESTIÓN DE RIESGO:")
    print("   - Stop-loss dinámico")
    print("   - Position sizing basado en volatilidad")
    print("   - Límites de drawdown")
    
    print("\n4. 🔄 OPTIMIZACIONES TÉCNICAS:")
    print("   - Implementación de backtesting vectorizado")
    print("   - Walk-forward analysis")
    print("   - Validación cruzada temporal")
    
    print("\n5. 📈 CARACTERÍSTICAS AVANZADAS:")
    print("   - Múltiples timeframes")
    print("   - Correlación entre assets")
    print("   - Análisis de regímenes de mercado")

if __name__ == "__main__":
    main()