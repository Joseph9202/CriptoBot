#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas_ta
from typing import Dict, List, Tuple, Optional
import logging
import time
import json
import sqlite3
from collections import deque
import threading
from dataclasses import dataclass, asdict
import websocket
from concurrent.futures import ThreadPoolExecutor

warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

API_KEY = 'bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb'
API_SECRET = 'O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS'

@dataclass
class Trade:
    id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    entry_price: float
    exit_price: float = None
    quantity: float = 0
    entry_time: datetime = None
    exit_time: datetime = None
    stop_loss: float = None
    take_profit: float = None
    pnl: float = 0
    pnl_pct: float = 0
    status: str = 'OPEN'  # 'OPEN', 'CLOSED', 'CANCELLED'
    strategy: str = ''
    fees: float = 0
    reason_closed: str = ''

@dataclass
class Portfolio:
    initial_balance: float
    current_balance: float
    available_balance: float
    positions: Dict[str, float]
    total_pnl: float = 0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    max_drawdown: float = 0
    current_drawdown: float = 0
    peak_balance: float = 0

class DatabaseManager:
    """Gestiona la persistencia de datos en SQLite"""
    
    def __init__(self, db_name: str = 'trading_bot.db'):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Inicializa las tablas de la base de datos"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Tabla de trades
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL,
            quantity REAL NOT NULL,
            entry_time TEXT NOT NULL,
            exit_time TEXT,
            stop_loss REAL,
            take_profit REAL,
            pnl REAL DEFAULT 0,
            pnl_pct REAL DEFAULT 0,
            status TEXT DEFAULT 'OPEN',
            strategy TEXT,
            fees REAL DEFAULT 0,
            reason_closed TEXT
        )
        ''')
        
        # Tabla de portfolio histórico
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_history (
            timestamp TEXT PRIMARY KEY,
            balance REAL NOT NULL,
            total_pnl REAL NOT NULL,
            open_positions INTEGER NOT NULL,
            daily_pnl REAL DEFAULT 0
        )
        ''')
        
        # Tabla de configuración
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_trade(self, trade: Trade):
        """Guarda un trade en la base de datos"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        trade_dict = asdict(trade)
        trade_dict['entry_time'] = trade.entry_time.isoformat() if trade.entry_time else None
        trade_dict['exit_time'] = trade.exit_time.isoformat() if trade.exit_time else None
        
        cursor.execute('''
        INSERT OR REPLACE INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', tuple(trade_dict.values()))
        
        conn.commit()
        conn.close()
    
    def save_portfolio_snapshot(self, portfolio: Portfolio):
        """Guarda un snapshot del portfolio"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO portfolio_history VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            portfolio.current_balance,
            portfolio.total_pnl,
            len([p for p in portfolio.positions.values() if p != 0]),
            0  # daily_pnl se calculará después
        ))
        
        conn.commit()
        conn.close()
    
    def get_trades_history(self, limit: int = 100) -> List[Trade]:
        """Obtiene el historial de trades"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM trades ORDER BY entry_time DESC LIMIT ?
        ''', (limit,))
        
        trades = []
        for row in cursor.fetchall():
            trade_data = dict(zip([col[0] for col in cursor.description], row))
            trade_data['entry_time'] = pd.to_datetime(trade_data['entry_time'])
            if trade_data['exit_time']:
                trade_data['exit_time'] = pd.to_datetime(trade_data['exit_time'])
            trades.append(Trade(**trade_data))
        
        conn.close()
        return trades

class EnhancedPaperTradingBot:
    """
    Bot de trading con paper trading avanzado y gestión completa de portfolio
    """
    
    def __init__(self, symbols: List[str] = None, initial_balance: float = 10000):
        self.symbols = symbols or ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT']
        self.initial_balance = initial_balance
        
        # Inicializar portfolio
        self.portfolio = Portfolio(
            initial_balance=initial_balance,
            current_balance=initial_balance,
            available_balance=initial_balance,
            positions={symbol: 0 for symbol in self.symbols},
            peak_balance=initial_balance
        )
        
        # Base de datos
        self.db = DatabaseManager()
        
        # Configuración de trading
        self.trading_config = {
            'max_position_size': 0.15,  # 15% del capital por operación
            'stop_loss_pct': 0.025,     # 2.5% stop loss
            'take_profit_pct': 0.05,    # 5% take profit
            'max_open_positions': 3,    # Máximo 3 posiciones simultáneas
            'fee_rate': 0.001,          # 0.1% comisión por lado
            'risk_per_trade': 0.02,     # 2% riesgo por trade
            'daily_loss_limit': 0.1,    # 10% pérdida máxima diaria
            'enable_trailing_stop': True,
            'trailing_stop_pct': 0.015  # 1.5% trailing stop
        }
        
        # Datos de mercado en tiempo real
        self.market_data = {symbol: deque(maxlen=1000) for symbol in self.symbols}
        self.current_prices = {symbol: 0 for symbol in self.symbols}
        self.open_trades = {}
        
        # Control de estado
        self.is_running = False
        self.daily_pnl = 0
        self.daily_trades_count = 0
        self.last_reset_date = datetime.now().date()
        
        # Conexión API
        try:
            self.client = Client(API_KEY, API_SECRET)
            logger.info("✓ Conexión exitosa con Binance API")
        except Exception as e:
            logger.error(f"✗ Error conectando con Binance API: {e}")
            self.client = None
    
    def get_historical_data(self, symbol: str, interval: str = '5m', limit: int = 200) -> pd.DataFrame:
        """Obtiene datos históricos de un símbolo"""
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
            df['returns'] = np.log(df['close']).diff()
            df['sma_20'] = df['close'].rolling(20).mean()
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
            
            # Volatilidad
            df['volatility'] = df['returns'].rolling(20).std() * np.sqrt(252)
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos para {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> float:
        """Calcula el tamaño de posición basado en gestión de riesgo"""
        # Riesgo por trade en términos monetarios
        risk_amount = self.portfolio.current_balance * self.trading_config['risk_per_trade']
        
        # Riesgo por acción
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share == 0:
            return 0
        
        # Cantidad basada en riesgo
        quantity_by_risk = risk_amount / risk_per_share
        
        # Límite por tamaño máximo de posición
        max_position_value = self.portfolio.current_balance * self.trading_config['max_position_size']
        max_quantity = max_position_value / entry_price
        
        # Usar el menor de los dos
        quantity = min(quantity_by_risk, max_quantity)
        
        # Verificar que tenemos balance suficiente
        required_balance = quantity * entry_price * (1 + self.trading_config['fee_rate'])
        if required_balance > self.portfolio.available_balance:
            quantity = self.portfolio.available_balance / (entry_price * (1 + self.trading_config['fee_rate']))
        
        return max(0, quantity)
    
    def generate_trading_signals(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Genera señales de trading basadas en análisis técnico"""
        if len(data) < 50:
            return {'signal': 'HOLD', 'strength': 0, 'reason': 'Insufficient data'}
        
        current = data.iloc[-1]
        prev = data.iloc[-2]
        
        signals = []
        signal_strength = 0
        
        # Señales de tendencia
        if current['ema_12'] > current['ema_26'] and prev['ema_12'] <= prev['ema_26']:
            signals.append("EMA Bullish Crossover")
            signal_strength += 2
        elif current['ema_12'] < current['ema_26'] and prev['ema_12'] >= prev['ema_26']:
            signals.append("EMA Bearish Crossover")
            signal_strength -= 2
        
        # RSI
        if current['rsi'] < 30:
            signals.append("RSI Oversold")
            signal_strength += 1.5
        elif current['rsi'] > 70:
            signals.append("RSI Overbought")
            signal_strength -= 1.5
        
        # Bollinger Bands
        if 'bb_lower' in current and 'bb_upper' in current:
            if current['close'] <= current['bb_lower']:
                signals.append("BB Lower Touch")
                signal_strength += 1
            elif current['close'] >= current['bb_upper']:
                signals.append("BB Upper Touch")
                signal_strength -= 1
        
        # MACD
        if 'macd' in current and 'macd_signal' in current:
            if current['macd'] > current['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                signals.append("MACD Bullish")
                signal_strength += 1.5
            elif current['macd'] < current['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                signals.append("MACD Bearish")
                signal_strength -= 1.5
        
        # Volumen confirmación
        volume_avg = data['volume'].rolling(20).mean().iloc[-1]
        if current['volume'] > volume_avg * 1.5:
            signals.append("High Volume")
            signal_strength *= 1.2
        
        # Determinar señal final
        if signal_strength >= 3:
            signal = 'BUY'
        elif signal_strength <= -3:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        return {
            'signal': signal,
            'strength': abs(signal_strength),
            'signals': signals,
            'price': current['close'],
            'rsi': current['rsi'],
            'volatility': current.get('volatility', 0)
        }
    
    def open_position(self, symbol: str, side: str, price: float, signal_data: Dict) -> Optional[Trade]:
        """Abre una nueva posición"""
        
        # Verificar límites
        if len([t for t in self.open_trades.values() if t.status == 'OPEN']) >= self.trading_config['max_open_positions']:
            logger.warning(f"Máximo de posiciones abiertas alcanzado")
            return None
        
        if self.daily_trades_count >= 20:  # Límite diario
            logger.warning(f"Límite diario de trades alcanzado")
            return None
        
        # Calcular stop loss y take profit
        if side == 'BUY':
            stop_loss = price * (1 - self.trading_config['stop_loss_pct'])
            take_profit = price * (1 + self.trading_config['take_profit_pct'])
        else:
            stop_loss = price * (1 + self.trading_config['stop_loss_pct'])
            take_profit = price * (1 - self.trading_config['take_profit_pct'])
        
        # Calcular cantidad
        quantity = self.calculate_position_size(symbol, price, stop_loss)
        
        if quantity <= 0:
            logger.warning(f"Cantidad calculada inválida: {quantity}")
            return None
        
        # Calcular comisiones
        trade_value = quantity * price
        fees = trade_value * self.trading_config['fee_rate']
        
        # Verificar balance disponible
        required_balance = trade_value + fees
        if required_balance > self.portfolio.available_balance:
            logger.warning(f"Balance insuficiente. Requerido: {required_balance}, Disponible: {self.portfolio.available_balance}")
            return None
        
        # Crear trade
        trade_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        trade = Trade(
            id=trade_id,
            symbol=symbol,
            side=side,
            entry_price=price,
            quantity=quantity,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit,
            fees=fees,
            strategy="Technical Analysis"
        )
        
        # Actualizar portfolio
        self.portfolio.available_balance -= required_balance
        if side == 'BUY':
            self.portfolio.positions[symbol] += quantity
        else:
            self.portfolio.positions[symbol] -= quantity
        
        # Guardar trade
        self.open_trades[trade_id] = trade
        self.db.save_trade(trade)
        self.daily_trades_count += 1
        
        logger.info(f"📈 Posición abierta: {side} {quantity:.6f} {symbol} @ ${price:.2f}")
        return trade
    
    def close_position(self, trade: Trade, exit_price: float, reason: str = "Manual close") -> Trade:
        """Cierra una posición existente"""
        
        # Calcular P&L
        if trade.side == 'BUY':
            pnl = (exit_price - trade.entry_price) * trade.quantity
        else:
            pnl = (trade.entry_price - exit_price) * trade.quantity
        
        # Restar comisiones
        exit_fees = exit_price * trade.quantity * self.trading_config['fee_rate']
        total_pnl = pnl - trade.fees - exit_fees
        pnl_pct = total_pnl / (trade.entry_price * trade.quantity)
        
        # Actualizar trade
        trade.exit_price = exit_price
        trade.exit_time = datetime.now()
        trade.pnl = total_pnl
        trade.pnl_pct = pnl_pct
        trade.status = 'CLOSED'
        trade.reason_closed = reason
        trade.fees += exit_fees
        
        # Actualizar portfolio
        trade_value = exit_price * trade.quantity
        self.portfolio.current_balance += trade_value + total_pnl
        self.portfolio.available_balance += trade_value
        self.portfolio.total_pnl += total_pnl
        self.daily_pnl += total_pnl
        
        # Actualizar posición
        if trade.side == 'BUY':
            self.portfolio.positions[trade.symbol] -= trade.quantity
        else:
            self.portfolio.positions[trade.symbol] += trade.quantity
        
        # Actualizar estadísticas
        self.portfolio.total_trades += 1
        if total_pnl > 0:
            self.portfolio.winning_trades += 1
        else:
            self.portfolio.losing_trades += 1
        
        # Actualizar drawdown
        if self.portfolio.current_balance > self.portfolio.peak_balance:
            self.portfolio.peak_balance = self.portfolio.current_balance
            self.portfolio.current_drawdown = 0
        else:
            self.portfolio.current_drawdown = (self.portfolio.peak_balance - self.portfolio.current_balance) / self.portfolio.peak_balance
            if self.portfolio.current_drawdown > self.portfolio.max_drawdown:
                self.portfolio.max_drawdown = self.portfolio.current_drawdown
        
        # Guardar en base de datos
        self.db.save_trade(trade)
        self.db.save_portfolio_snapshot(self.portfolio)
        
        # Remover de trades activos
        if trade.id in self.open_trades:
            del self.open_trades[trade.id]
        
        logger.info(f"📊 Posición cerrada: {trade.symbol} | P&L: ${total_pnl:.2f} ({pnl_pct:.2%}) | Razón: {reason}")
        return trade
    
    def check_exit_conditions(self):
        """Verifica condiciones de salida para todas las posiciones abiertas"""
        for trade_id, trade in list(self.open_trades.items()):
            current_price = self.current_prices.get(trade.symbol, 0)
            if current_price == 0:
                continue
            
            should_close = False
            reason = ""
            
            # Stop Loss
            if trade.side == 'BUY' and current_price <= trade.stop_loss:
                should_close = True
                reason = "Stop Loss"
            elif trade.side == 'SELL' and current_price >= trade.stop_loss:
                should_close = True
                reason = "Stop Loss"
            
            # Take Profit
            elif trade.side == 'BUY' and current_price >= trade.take_profit:
                should_close = True
                reason = "Take Profit"
            elif trade.side == 'SELL' and current_price <= trade.take_profit:
                should_close = True
                reason = "Take Profit"
            
            # Tiempo máximo en posición (24 horas)
            elif trade.entry_time and (datetime.now() - trade.entry_time) > timedelta(hours=24):
                should_close = True
                reason = "Time Limit"
            
            # Trailing Stop
            elif self.trading_config['enable_trailing_stop']:
                if trade.side == 'BUY':
                    trailing_stop = current_price * (1 - self.trading_config['trailing_stop_pct'])
                    if current_price > trade.entry_price * 1.02:  # Solo si hay ganancia > 2%
                        trade.stop_loss = max(trade.stop_loss, trailing_stop)
                
            if should_close:
                self.close_position(trade, current_price, reason)
    
    def update_prices(self):
        """Actualiza precios actuales de todos los símbolos"""
        try:
            tickers = self.client.get_all_tickers()
            for ticker in tickers:
                if ticker['symbol'] in self.symbols:
                    self.current_prices[ticker['symbol']] = float(ticker['price'])
        except Exception as e:
            logger.error(f"Error actualizando precios: {e}")
    
    def reset_daily_counters(self):
        """Resetea contadores diarios si es un nuevo día"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_pnl = 0
            self.daily_trades_count = 0
            self.last_reset_date = current_date
            logger.info("📅 Contadores diarios reseteados")
    
    def run_trading_cycle(self):
        """Ejecuta un ciclo completo de trading"""
        self.reset_daily_counters()
        
        # Verificar límite de pérdida diaria
        if self.daily_pnl <= -self.portfolio.current_balance * self.trading_config['daily_loss_limit']:
            logger.warning("🛑 Límite de pérdida diaria alcanzado. Trading pausado.")
            return
        
        # Actualizar precios
        self.update_prices()
        
        # Verificar condiciones de salida
        self.check_exit_conditions()
        
        # Buscar nuevas oportunidades
        for symbol in self.symbols:
            if len([t for t in self.open_trades.values() if t.symbol == symbol and t.status == 'OPEN']) > 0:
                continue  # Ya hay posición en este símbolo
            
            # Obtener datos y generar señal
            data = self.get_historical_data(symbol)
            if data.empty:
                continue
            
            signal_data = self.generate_trading_signals(symbol, data)
            
            if signal_data['signal'] in ['BUY', 'SELL'] and signal_data['strength'] >= 3:
                current_price = self.current_prices.get(symbol, signal_data['price'])
                self.open_position(symbol, signal_data['signal'], current_price, signal_data)
    
    def start_paper_trading(self, interval_seconds: int = 60):
        """Inicia el bot de paper trading"""
        logger.info("🚀 Iniciando Paper Trading Bot")
        self.is_running = True
        
        while self.is_running:
            try:
                self.run_trading_cycle()
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                logger.info("🛑 Deteniendo bot por solicitud del usuario")
                break
            except Exception as e:
                logger.error(f"Error en ciclo de trading: {e}")
                time.sleep(10)
    
    def stop_paper_trading(self):
        """Detiene el bot de paper trading"""
        self.is_running = False
        logger.info("⏹️ Paper Trading Bot detenido")
    
    def get_portfolio_summary(self) -> Dict:
        """Obtiene resumen del portfolio"""
        win_rate = (self.portfolio.winning_trades / max(self.portfolio.total_trades, 1)) * 100
        
        return {
            'current_balance': self.portfolio.current_balance,
            'total_pnl': self.portfolio.total_pnl,
            'total_return_pct': ((self.portfolio.current_balance - self.portfolio.initial_balance) / self.portfolio.initial_balance) * 100,
            'total_trades': self.portfolio.total_trades,
            'winning_trades': self.portfolio.winning_trades,
            'losing_trades': self.portfolio.losing_trades,
            'win_rate': win_rate,
            'max_drawdown': self.portfolio.max_drawdown * 100,
            'current_drawdown': self.portfolio.current_drawdown * 100,
            'daily_pnl': self.daily_pnl,
            'open_positions': len([t for t in self.open_trades.values() if t.status == 'OPEN']),
            'available_balance': self.portfolio.available_balance
        }
    
    def print_portfolio_report(self):
        """Imprime reporte detallado del portfolio"""
        summary = self.get_portfolio_summary()
        
        print("\n" + "="*80)
        print("💼 REPORTE DE PORTFOLIO - PAPER TRADING")
        print("="*80)
        print(f"💰 Balance Actual: ${summary['current_balance']:,.2f}")
        print(f"📈 P&L Total: ${summary['total_pnl']:,.2f} ({summary['total_return_pct']:+.2f}%)")
        print(f"💵 Balance Disponible: ${summary['available_balance']:,.2f}")
        print(f"📊 Total Trades: {summary['total_trades']}")
        print(f"🟢 Trades Ganadores: {summary['winning_trades']}")
        print(f"🔴 Trades Perdedores: {summary['losing_trades']}")
        print(f"🎯 Win Rate: {summary['win_rate']:.1f}%")
        print(f"📉 Max Drawdown: {summary['max_drawdown']:.2f}%")
        print(f"📉 Drawdown Actual: {summary['current_drawdown']:.2f}%")
        print(f"🌅 P&L Diario: ${summary['daily_pnl']:,.2f}")
        print(f"📋 Posiciones Abiertas: {summary['open_positions']}")
        
        # Mostrar posiciones abiertas
        if self.open_trades:
            print(f"\n🔄 POSICIONES ABIERTAS:")
            print("-" * 60)
            for trade in self.open_trades.values():
                current_price = self.current_prices.get(trade.symbol, 0)
                if current_price > 0:
                    if trade.side == 'BUY':
                        unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
                    else:
                        unrealized_pnl = (trade.entry_price - current_price) * trade.quantity
                    
                    unrealized_pnl_pct = unrealized_pnl / (trade.entry_price * trade.quantity) * 100
                    
                    print(f"  {trade.symbol}: {trade.side} {trade.quantity:.6f} @ ${trade.entry_price:.2f}")
                    print(f"    Precio Actual: ${current_price:.2f} | P&L: ${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.2f}%)")
        
        print("="*80)

def main():
    """Función principal para ejecutar el bot de paper trading"""
    print("🚀 ENHANCED PAPER TRADING BOT")
    print("Bot avanzado de trading con dinero virtual y gestión completa de portfolio")
    
    # Configurar símbolos a tradear
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']
    
    # Crear bot
    bot = EnhancedPaperTradingBot(symbols=symbols, initial_balance=10000)
    
    if bot.client is None:
        print("❌ No se pudo conectar con la API")
        return
    
    try:
        # Mostrar configuración inicial
        print(f"\n📋 CONFIGURACIÓN:")
        print(f"  💰 Balance inicial: ${bot.initial_balance:,.2f}")
        print(f"  📊 Símbolos: {', '.join(symbols)}")
        print(f"  🎯 Max posición: {bot.trading_config['max_position_size']*100:.1f}% del capital")
        print(f"  🛡️ Stop Loss: {bot.trading_config['stop_loss_pct']*100:.1f}%")
        print(f"  🎪 Take Profit: {bot.trading_config['take_profit_pct']*100:.1f}%")
        print(f"  📈 Max posiciones abiertas: {bot.trading_config['max_open_positions']}")
        
        # Ejecutar un ciclo de prueba
        print(f"\n🔄 Ejecutando ciclo de análisis...")
        bot.run_trading_cycle()
        
        # Mostrar reporte
        bot.print_portfolio_report()
        
        # Opción para ejecutar trading continuo
        print(f"\n⚡ OPCIONES:")
        print("1. Ejecutar trading automático (Ctrl+C para detener)")
        print("2. Solo mostrar análisis actual")
        
        choice = input("\nElige opción (1/2): ").strip()
        
        if choice == "1":
            print(f"\n🚀 Iniciando trading automático...")
            print("Presiona Ctrl+C para detener")
            bot.start_paper_trading(interval_seconds=30)  # Ejecutar cada 30 segundos
        
    except KeyboardInterrupt:
        print(f"\n🛑 Trading detenido por el usuario")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        bot.stop_paper_trading()
        print(f"\n📊 Reporte final:")
        bot.print_portfolio_report()

if __name__ == "__main__":
    main()