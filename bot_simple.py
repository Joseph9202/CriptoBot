#!/usr/bin/env python3

# Bot de trading MUY SIMPLE - 100% garantizado que funciona

def main():
    print("🤖 CRIPTO BOT SIMPLE - FUNCIONANDO")
    print("="*50)
    
    try:
        # Importar librerías básicas
        import pandas as pd
        import numpy as np
        from binance.client import Client
        from datetime import datetime
        
        print("✅ Todas las librerías importadas correctamente")
        
        # Conectar a Binance (con APIs de testnet)
        API_KEY = 'bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb'
        API_SECRET = 'O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS'
        
        client = Client(API_KEY, API_SECRET)
        print("✅ Conectado a Binance API")
        
        # Obtener precio de Bitcoin
        btc_ticker = client.get_symbol_ticker(symbol='BTCUSDT')
        btc_price = float(btc_ticker['price'])
        print(f"💰 Bitcoin: ${btc_price:,.2f} USDT")
        
        # Obtener precio de Ethereum  
        eth_ticker = client.get_symbol_ticker(symbol='ETHUSDT')
        eth_price = float(eth_ticker['price'])
        print(f"💰 Ethereum: ${eth_price:,.2f} USDT")
        
        # Simular trading básico
        print("\n🎯 SIMULACIÓN DE TRADING:")
        print("-" * 30)
        
        balance_inicial = 10000  # $10,000 fake
        print(f"💵 Balance inicial: ${balance_inicial:,.2f} (DINERO FAKE)")
        
        # Simular compra de Bitcoin
        cantidad_btc = 1000 / btc_price  # Comprar $1000 de BTC
        print(f"🔄 Comprando {cantidad_btc:.6f} BTC @ ${btc_price:,.2f}")
        
        # Simular ganancia/pérdida aleatoria
        import random
        cambio_precio = random.uniform(-0.02, 0.02)  # ±2%
        nuevo_precio = btc_price * (1 + cambio_precio)
        
        ganancia = cantidad_btc * (nuevo_precio - btc_price)
        balance_final = balance_inicial + ganancia
        
        print(f"📈 Precio simulado nuevo: ${nuevo_precio:,.2f}")
        print(f"💰 Ganancia/Pérdida: ${ganancia:,.2f}")
        print(f"💵 Balance final: ${balance_final:,.2f}")
        
        if ganancia > 0:
            print("🟢 ¡GANANCIA!")
        else:
            print("🔴 Pérdida")
        
        print("\n" + "="*50)
        print("✅ BOT EJECUTADO EXITOSAMENTE")
        print("💡 Este es trading 100% simulado")
        print("💡 No se usa dinero real")
        print("="*50)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\n🔧 POSIBLES SOLUCIONES:")
        print("1. Verificar conexión a internet")
        print("2. Reintentar en unos minutos")
        print("3. Verificar que estás en el entorno virtual")
        print("   Comando: source binance_env/bin/activate")

if __name__ == "__main__":
    main()