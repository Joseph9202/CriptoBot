#!/usr/bin/env python3

import pandas as pd
import numpy as np
from datetime import datetime
from binance.client import Client
import pandas_ta
import time

# API Keys (Testnet)
API_KEY = 'bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb'
API_SECRET = 'O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS'

def quick_trading_demo():
    """Demo rápido de trading con dinero fake"""
    
    print("🚀 CRIPTO BOT - DEMO RÁPIDO")
    print("💰 Trading con Dinero 100% Fake")
    print("="*60)
    
    try:
        # Conectar a Binance
        client = Client(API_KEY, API_SECRET)
        print("✅ Conectado a Binance API")
        
        # Configuración inicial
        initial_balance = 10000  # $10,000 fake
        current_balance = initial_balance
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        
        print(f"💰 Balance inicial: ${initial_balance:,.2f} (FAKE)")
        print(f"📊 Símbolos a analizar: {', '.join(symbols)}")
        print("-" * 60)
        
        trades_executed = []
        
        for symbol in symbols:
            print(f"\n🔍 Analizando {symbol}...")
            
            # Obtener datos históricos
            klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR, "100 hours ago UTC")
            
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
            df['rsi'] = pandas_ta.rsi(df['close'], length=14)
            
            # Obtener datos actuales
            current_price = df['close'].iloc[-1]
            current_rsi = df['rsi'].iloc[-1]
            sma_20 = df['sma_20'].iloc[-1]
            
            print(f"   💰 Precio actual: ${current_price:,.2f}")
            print(f"   📈 RSI: {current_rsi:.1f}")
            print(f"   📊 SMA(20): ${sma_20:,.2f}")
            
            # Lógica de trading simple
            signal = "HOLD"
            if current_rsi < 35 and current_price < sma_20:
                signal = "BUY"
            elif current_rsi > 65 and current_price > sma_20:
                signal = "SELL"
            
            print(f"   🎯 Señal: {signal}")
            
            # Simular trade
            if signal in ["BUY", "SELL"]:
                trade_amount = current_balance * 0.1  # 10% del balance
                quantity = trade_amount / current_price
                
                # Simular comisión (0.1%)
                commission = trade_amount * 0.001
                
                # Simular resultado aleatorio (±3%)
                random_pnl_pct = np.random.uniform(-0.03, 0.03)
                pnl = trade_amount * random_pnl_pct - commission
                
                current_balance += pnl
                
                trade = {
                    'symbol': symbol,
                    'signal': signal,
                    'price': current_price,
                    'amount': trade_amount,
                    'quantity': quantity,
                    'pnl': pnl,
                    'pnl_pct': (pnl / trade_amount) * 100,
                    'commission': commission
                }
                
                trades_executed.append(trade)
                
                status = "💚 GANANCIA" if pnl > 0 else "💔 PÉRDIDA"
                print(f"   💼 Trade simulado: {signal} {quantity:.6f} {symbol}")
                print(f"   {status}: ${pnl:,.2f} ({pnl/trade_amount*100:+.2f}%)")
            
            time.sleep(0.5)  # Pequeña pausa
        
        # Resumen final
        print("\n" + "="*60)
        print("📊 RESUMEN DE TRADING SIMULADO")
        print("="*60)
        
        total_pnl = current_balance - initial_balance
        total_return = (total_pnl / initial_balance) * 100
        
        print(f"💰 Balance inicial: ${initial_balance:,.2f}")
        print(f"💰 Balance final: ${current_balance:,.2f}")
        print(f"📈 P&L Total: ${total_pnl:,.2f} ({total_return:+.2f}%)")
        print(f"🔄 Trades ejecutados: {len(trades_executed)}")
        
        if trades_executed:
            winning_trades = len([t for t in trades_executed if t['pnl'] > 0])
            win_rate = (winning_trades / len(trades_executed)) * 100
            print(f"🎯 Win Rate: {win_rate:.1f}% ({winning_trades}/{len(trades_executed)})")
            
            print(f"\n📋 DETALLE DE TRADES:")
            print("-" * 60)
            for i, trade in enumerate(trades_executed, 1):
                status = "🟢" if trade['pnl'] > 0 else "🔴"
                print(f"{i}. {status} {trade['symbol']} {trade['signal']} @ ${trade['price']:,.2f}")
                print(f"   P&L: ${trade['pnl']:,.2f} ({trade['pnl_pct']:+.2f}%)")
        
        print("\n" + "="*60)
        print("✅ DEMO COMPLETADO")
        print("💡 Este es trading 100% simulado con dinero fake")
        print("💡 Los resultados son aleatorios para demostración")
        print("💡 En el bot real se usan estrategias más sofisticadas")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Verifica tu conexión a internet")

if __name__ == "__main__":
    quick_trading_demo()