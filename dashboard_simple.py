#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
from binance.client import Client
import sqlite3

# Configuración de la página
st.set_page_config(
    page_title="🤖 CriptoBot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Keys (Testnet - Dinero Fake)
API_KEY = 'bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb'
API_SECRET = 'O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS'

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4 0%, #17becf 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .profit {
        color: #28a745;
        font-weight: bold;
    }
    .loss {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class CriptoBotDashboard:
    """Dashboard simplificado y funcional para CriptoBot"""
    
    def __init__(self):
        self.client = None
        self.balance_inicial = 10000
        self.balance_actual = 10000
        self.trades_simulados = []
        self.init_binance_client()
    
    def init_binance_client(self):
        """Inicializa cliente de Binance"""
        try:
            self.client = Client(API_KEY, API_SECRET)
            return True
        except Exception as e:
            st.error(f"Error conectando con Binance: {e}")
            return False
    
    def get_crypto_prices(self, symbols):
        """Obtiene precios actuales de criptomonedas"""
        prices = {}
        try:
            for symbol in symbols:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                prices[symbol] = float(ticker['price'])
        except Exception as e:
            st.error(f"Error obteniendo precios: {e}")
        return prices
    
    def get_market_data(self, symbol, interval='1h', limit=24):
        """Obtiene datos históricos de mercado"""
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
            
            return pd.DataFrame(data)
            
        except Exception as e:
            st.error(f"Error obteniendo datos de mercado: {e}")
            return pd.DataFrame()
    
    def simulate_trade(self, symbol, price, action):
        """Simula un trade"""
        quantity = (self.balance_actual * 0.1) / price  # 10% del balance
        
        # Simular resultado aleatorio
        resultado_pct = np.random.uniform(-0.03, 0.03)  # ±3%
        pnl = (self.balance_actual * 0.1) * resultado_pct
        
        self.balance_actual += pnl
        
        trade = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': action,
            'price': price,
            'quantity': quantity,
            'pnl': pnl,
            'balance': self.balance_actual
        }
        
        self.trades_simulados.append(trade)
        return trade
    
    def create_price_chart(self, symbol, df):
        """Crea gráfico de precios"""
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=symbol
        ))
        
        fig.update_layout(
            title=f"📈 {symbol} - Últimas 24 horas",
            xaxis_title="Tiempo",
            yaxis_title="Precio (USDT)",
            height=400,
            xaxis_rangeslider_visible=False
        )
        
        return fig
    
    def run_dashboard(self):
        """Ejecuta el dashboard principal"""
        
        # Header principal
        st.markdown("""
        <div class="main-header">
            <h1>🤖 CriptoBot Dashboard</h1>
            <p>Trading automatizado con dinero virtual - 100% Seguro</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Verificar conexión
        if not self.client:
            st.error("❌ No se pudo conectar con Binance API")
            st.info("💡 Verifica tu conexión a internet e inténtalo de nuevo")
            return
        
        # Sidebar
        st.sidebar.header("🎮 Control del Bot")
        
        # Selección de criptomonedas
        symbols = st.sidebar.multiselect(
            "Selecciona criptomonedas:",
            ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT'],
            default=['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        )
        
        if not symbols:
            st.warning("⚠️ Selecciona al menos una criptomoneda")
            return
        
        # Botones de control
        if st.sidebar.button("🔄 Actualizar Datos"):
            st.rerun()
        
        auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)")
        
        if st.sidebar.button("🤖 Simular Trade Automático"):
            # Simular trades en todas las cryptos seleccionadas
            prices = self.get_crypto_prices(symbols)
            for symbol in symbols:
                if symbol in prices:
                    action = np.random.choice(['BUY', 'SELL'])
                    self.simulate_trade(symbol, prices[symbol], action)
            st.rerun()
        
        # Métricas principales
        st.header("📊 Resumen del Portfolio")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_pnl = self.balance_actual - self.balance_inicial
        total_return = (total_pnl / self.balance_inicial) * 100
        
        with col1:
            st.metric(
                "Balance Actual",
                f"${self.balance_actual:,.2f}",
                f"${total_pnl:,.2f}"
            )
        
        with col2:
            st.metric(
                "Retorno Total",
                f"{total_return:+.2f}%",
                f"Inicial: ${self.balance_inicial:,.2f}"
            )
        
        with col3:
            st.metric(
                "Total Trades",
                len(self.trades_simulados),
                "Simulados"
            )
        
        with col4:
            winning_trades = len([t for t in self.trades_simulados if t['pnl'] > 0])
            win_rate = (winning_trades / max(len(self.trades_simulados), 1)) * 100
            st.metric(
                "Win Rate",
                f"{win_rate:.1f}%",
                f"{winning_trades} ganadores"
            )
        
        # Precios en tiempo real
        st.header("💰 Precios en Tiempo Real")
        
        prices = self.get_crypto_prices(symbols)
        
        if prices:
            price_cols = st.columns(len(symbols))
            
            for i, (symbol, price) in enumerate(prices.items()):
                with price_cols[i]:
                    crypto_name = symbol.replace('USDT', '')
                    st.metric(
                        crypto_name,
                        f"${price:,.2f}",
                        "USDT"
                    )
        
        # Gráficos de precios
        st.header("📈 Gráficos de Mercado")
        
        if len(symbols) > 0:
            selected_chart = st.selectbox("Selecciona criptomoneda para gráfico:", symbols)
            
            df = self.get_market_data(selected_chart)
            
            if not df.empty:
                fig = self.create_price_chart(selected_chart, df)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No se pudieron obtener datos del gráfico")
        
        # Historial de trades simulados
        if self.trades_simulados:
            st.header("📋 Historial de Trades Simulados")
            
            # Crear DataFrame de trades
            trades_df = pd.DataFrame(self.trades_simulados)
            
            # Mostrar últimos 10 trades
            st.dataframe(
                trades_df[['timestamp', 'symbol', 'action', 'price', 'pnl', 'balance']].tail(10),
                use_container_width=True
            )
            
            # Gráfico de balance
            if len(trades_df) > 1:
                fig_balance = go.Figure()
                fig_balance.add_trace(go.Scatter(
                    x=trades_df['timestamp'],
                    y=trades_df['balance'],
                    mode='lines+markers',
                    name='Balance',
                    line=dict(color='#1f77b4', width=2)
                ))
                
                fig_balance.add_hline(
                    y=self.balance_inicial,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Balance Inicial"
                )
                
                fig_balance.update_layout(
                    title="💰 Evolución del Balance",
                    xaxis_title="Tiempo",
                    yaxis_title="Balance ($)",
                    height=400
                )
                
                st.plotly_chart(fig_balance, use_container_width=True)
        
        # Información del bot
        st.header("ℹ️ Información del Bot")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **🤖 CriptoBot Características:**
            - ✅ Trading con dinero 100% fake
            - ✅ Datos de mercado reales
            - ✅ Simulación de trades
            - ✅ Sin riesgo financiero
            - ✅ Perfecto para aprender
            """)
        
        with col2:
            st.success("""
            **📈 Funciones del Dashboard:**
            - 💰 Precios en tiempo real
            - 📊 Gráficos interactivos  
            - 🤖 Simulación de trades
            - 📋 Historial completo
            - 🔄 Auto-refresh opcional
            """)
        
        # Auto-refresh
        if auto_refresh:
            time.sleep(30)
            st.rerun()

def main():
    """Función principal"""
    dashboard = CriptoBotDashboard()
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()