#!/usr/bin/env python3

import sys
import os

def test_basic_bot():
    """Prueba el bot básico"""
    print("🤖 CRIPTO BOT - PRUEBA BÁSICA")
    print("="*50)
    
    try:
        from binance.client import Client
        print("✅ Importando Binance API...")
        
        # Usar las API keys del archivo
        API_KEY = 'bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb'
        API_SECRET = 'O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS'
        
        client = Client(API_KEY, API_SECRET)
        print("✅ Conexión con Binance establecida")
        
        # Obtener precio de Bitcoin
        btc_price = client.get_symbol_ticker(symbol='BTCUSDT')
        print(f"💰 Precio actual de Bitcoin: ${float(btc_price['price']):,.2f} USDT")
        
        # Obtener precio de Ethereum
        eth_price = client.get_symbol_ticker(symbol='ETHUSDT')
        print(f"💰 Precio actual de Ethereum: ${float(eth_price['price']):,.2f} USDT")
        
        # Obtener top 5 criptomonedas por volumen
        print("\n📊 TOP 5 CRIPTOMONEDAS POR VOLUMEN:")
        print("-" * 50)
        
        ticker_24h = client.get_ticker()
        usdt_pairs = []
        
        for ticker in ticker_24h[:50]:  # Solo revisar las primeras 50
            if ticker['symbol'].endswith('USDT'):
                try:
                    volume_usdt = float(ticker['quoteVolume'])
                    price = float(ticker['lastPrice'])
                    change_24h = float(ticker['priceChangePercent'])
                    
                    usdt_pairs.append({
                        'symbol': ticker['symbol'],
                        'price': price,
                        'change_24h': change_24h,
                        'volume_24h': volume_usdt
                    })
                except (ValueError, KeyError):
                    continue
        
        # Ordenar por volumen
        usdt_pairs.sort(key=lambda x: x['volume_24h'], reverse=True)
        
        for i, crypto in enumerate(usdt_pairs[:5], 1):
            symbol = crypto['symbol'].replace('USDT', '')
            price = f"${crypto['price']:,.4f}"
            change_color = "🔴" if crypto['change_24h'] < 0 else "🟢"
            change = f"{crypto['change_24h']:+.2f}%"
            volume = f"${crypto['volume_24h']:,.0f}"
            
            print(f"{i}. {symbol:<8} {price:<12} {change_color} {change:<8} Vol: {volume}")
        
        print("\n✅ ¡Bot ejecutado exitosamente!")
        print("💡 Este bot usa dinero fake para simulación")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Verifica tu conexión a internet")

if __name__ == "__main__":
    test_basic_bot()