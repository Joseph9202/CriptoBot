#!/usr/bin/env python3

import os
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import json
from datetime import datetime

API_KEY = 'bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb'
API_SECRET = 'O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS'

class CryptoBot:
    def __init__(self):
        try:
            self.client = Client(API_KEY, API_SECRET)
            print("✓ Conexión exitosa con Binance API")
        except Exception as e:
            print(f"✗ Error conectando con Binance API: {e}")
            self.client = None

    def get_account_info(self):
        """Obtiene información de la cuenta"""
        try:
            account = self.client.get_account()
            return {
                'maker_commission': account['makerCommission'],
                'taker_commission': account['takerCommission'],
                'buyer_commission': account['buyerCommission'],
                'seller_commission': account['sellerCommission'],
                'can_trade': account['canTrade'],
                'can_withdraw': account['canWithdraw'],
                'can_deposit': account['canDeposit']
            }
        except BinanceAPIException as e:
            print(f"Error API: {e}")
            return None

    def get_top_cryptocurrencies(self, limit=10):
        """Obtiene información de las principales criptomonedas"""
        try:
            # Obtener estadísticas de 24h para todos los pares
            ticker_24h = self.client.get_ticker()
            
            # Filtrar solo pares con USDT y ordenar por volumen
            usdt_pairs = []
            for ticker in ticker_24h:
                if ticker['symbol'].endswith('USDT'):
                    try:
                        volume_usdt = float(ticker['quoteVolume'])
                        price = float(ticker['lastPrice'])
                        change_24h = float(ticker['priceChangePercent'])
                        
                        usdt_pairs.append({
                            'symbol': ticker['symbol'],
                            'price': price,
                            'change_24h': change_24h,
                            'volume_24h': volume_usdt,
                            'high_24h': float(ticker['highPrice']),
                            'low_24h': float(ticker['lowPrice'])
                        })
                    except (ValueError, KeyError):
                        continue
            
            # Ordenar por volumen (mayor a menor) y tomar los primeros
            usdt_pairs.sort(key=lambda x: x['volume_24h'], reverse=True)
            return usdt_pairs[:limit]
            
        except BinanceAPIException as e:
            print(f"Error API: {e}")
            return []

    def get_crypto_price(self, symbol):
        """Obtiene el precio actual de una criptomoneda específica"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            print(f"Error obteniendo precio de {symbol}: {e}")
            return None

    def print_crypto_report(self):
        """Imprime un reporte completo de las principales criptomonedas"""
        print("\n" + "="*80)
        print("📊 REPORTE DE CRIPTOMONEDAS - BINANCE")
        print("="*80)
        print(f"🕐 Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Información de cuenta
        account_info = self.get_account_info()
        if account_info:
            print("\n📈 INFORMACIÓN DE CUENTA:")
            print(f"   Trading habilitado: {'✓' if account_info['can_trade'] else '✗'}")
            print(f"   Retiros habilitados: {'✓' if account_info['can_withdraw'] else '✗'}")
            print(f"   Depósitos habilitados: {'✓' if account_info['can_deposit'] else '✗'}")
        
        # Top criptomonedas
        top_cryptos = self.get_top_cryptocurrencies(15)
        if top_cryptos:
            print("\n💰 TOP 15 CRIPTOMONEDAS POR VOLUMEN (24H):")
            print("-" * 80)
            print(f"{'SÍMBOLO':<12} {'PRECIO (USDT)':<15} {'CAMBIO 24H':<12} {'VOLUMEN 24H':<20}")
            print("-" * 80)
            
            for crypto in top_cryptos:
                symbol = crypto['symbol'].replace('USDT', '')
                price = f"${crypto['price']:,.4f}"
                change_color = "🔴" if crypto['change_24h'] < 0 else "🟢"
                change = f"{change_color} {crypto['change_24h']:+.2f}%"
                volume = f"${crypto['volume_24h']:,.0f}"
                
                print(f"{symbol:<12} {price:<15} {change:<20} {volume:<20}")
        
        # Precios específicos de criptos principales
        main_cryptos = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']
        print("\n🔥 PRECIOS PRINCIPALES CRIPTOMONEDAS:")
        print("-" * 50)
        
        for symbol in main_cryptos:
            price = self.get_crypto_price(symbol)
            if price:
                crypto_name = symbol.replace('USDT', '')
                print(f"   {crypto_name:<6}: ${price:>12,.4f} USDT")
        
        print("\n" + "="*80)

def main():
    """Función principal"""
    print("🚀 Iniciando CriptoBot - Consulta de Binance API")
    
    bot = CryptoBot()
    
    if bot.client is None:
        print("❌ No se pudo conectar con la API. Verifica tus credenciales.")
        return
    
    try:
        bot.print_crypto_report()
    except Exception as e:
        print(f"❌ Error ejecutando el reporte: {e}")

if __name__ == "__main__":
    main()