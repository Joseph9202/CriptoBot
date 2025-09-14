#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime, timedelta
import time
import json
from enhanced_paper_trading_bot import EnhancedPaperTradingBot
from portfolio_analyzer import PortfolioAnalyzer
import threading

# Configuración de la página
st.set_page_config(
    page_title="CriptoBot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .profit {
        color: #00C851;
        font-weight: bold;
    }
    .loss {
        color: #FF4444;
        font-weight: bold;
    }
    .neutral {
        color: #FFBB33;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class TradingBotWebInterface:
    """Interfaz web para monitoreo del bot de trading"""
    
    def __init__(self):
        self.bot = None
        self.analyzer = PortfolioAnalyzer()
        self.is_bot_running = False
        
    def initialize_bot(self, symbols, initial_balance):
        """Inicializa el bot de trading"""
        try:
            self.bot = EnhancedPaperTradingBot(symbols=symbols, initial_balance=initial_balance)
            return True
        except Exception as e:
            st.error(f"Error inicializando bot: {e}")
            return False
    
    def get_real_time_data(self):
        """Obtiene datos en tiempo real del bot"""
        if not self.bot:
            return None
        
        return {
            'portfolio': self.bot.get_portfolio_summary(),
            'open_trades': list(self.bot.open_trades.values()),
            'current_prices': self.bot.current_prices,
            'daily_pnl': self.bot.daily_pnl,
            'daily_trades_count': self.bot.daily_trades_count
        }
    
    def create_portfolio_overview(self):
        """Crea vista general del portfolio"""
        st.header("📊 Portfolio Overview")
        
        if not self.bot:
            st.warning("⚠️ Bot no inicializado. Configure en la barra lateral.")
            return
        
        data = self.get_real_time_data()
        if not data:
            st.error("❌ Error obteniendo datos del bot")
            return
        
        portfolio = data['portfolio']
        
        # Métricas principales en columnas
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Balance Actual",
                f"${portfolio['current_balance']:,.2f}",
                f"${portfolio['total_pnl']:,.2f}"
            )
        
        with col2:
            return_pct = portfolio['total_return_pct']
            st.metric(
                "Retorno Total",
                f"{return_pct:.2f}%",
                f"{return_pct:.2f}%" if return_pct >= 0 else f"{return_pct:.2f}%"
            )
        
        with col3:
            st.metric(
                "Win Rate",
                f"{portfolio['win_rate']:.1f}%",
                f"{portfolio['winning_trades']}/{portfolio['total_trades']} trades"
            )
        
        with col4:
            st.metric(
                "P&L Diario",
                f"${portfolio['daily_pnl']:,.2f}",
                f"Trades: {data['daily_trades_count']}"
            )
        
        with col5:
            st.metric(
                "Posiciones Abiertas",
                portfolio['open_positions'],
                f"Max DD: {portfolio['max_drawdown']:.1f}%"
            )
    
    def create_live_trades_table(self):
        """Crea tabla de trades en vivo"""
        st.header("🔄 Posiciones Abiertas")
        
        if not self.bot:
            return
        
        data = self.get_real_time_data()
        open_trades = data['open_trades']
        current_prices = data['current_prices']
        
        if not open_trades:
            st.info("📝 No hay posiciones abiertas actualmente")
            return
        
        # Preparar datos para la tabla
        trades_data = []
        for trade in open_trades:
            current_price = current_prices.get(trade.symbol, 0)
            
            if current_price > 0:
                if trade.side == 'BUY':
                    unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
                else:
                    unrealized_pnl = (trade.entry_price - current_price) * trade.quantity
                
                unrealized_pnl_pct = (unrealized_pnl / (trade.entry_price * trade.quantity)) * 100
                
                trades_data.append({
                    'Símbolo': trade.symbol,
                    'Lado': trade.side,
                    'Cantidad': f"{trade.quantity:.6f}",
                    'Precio Entrada': f"${trade.entry_price:.2f}",
                    'Precio Actual': f"${current_price:.2f}",
                    'P&L No Realizado': f"${unrealized_pnl:.2f}",
                    'P&L %': f"{unrealized_pnl_pct:+.2f}%",
                    'Stop Loss': f"${trade.stop_loss:.2f}",
                    'Take Profit': f"${trade.take_profit:.2f}",
                    'Tiempo': trade.entry_time.strftime('%H:%M:%S') if trade.entry_time else 'N/A'
                })
        
        if trades_data:
            df = pd.DataFrame(trades_data)
            st.dataframe(df, use_container_width=True)
    
    def create_price_charts(self):
        """Crea gráficos de precios en tiempo real"""
        st.header("📈 Precios en Tiempo Real")
        
        if not self.bot:
            return
        
        data = self.get_real_time_data()
        current_prices = data['current_prices']
        
        # Crear gráfico de precios actuales
        symbols = list(current_prices.keys())
        prices = list(current_prices.values())
        
        if symbols and prices:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=symbols,
                y=prices,
                marker_color='lightblue',
                text=[f"${p:,.2f}" for p in prices],
                textposition='auto'
            ))
            
            fig.update_layout(
                title="Precios Actuales de Criptomonedas",
                xaxis_title="Símbolo",
                yaxis_title="Precio (USDT)",
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def create_performance_charts(self):
        """Crea gráficos de rendimiento"""
        st.header("📊 Análisis de Performance")
        
        self.analyzer.load_data()
        
        if self.analyzer.trades_df.empty:
            st.info("📝 No hay trades históricos para mostrar")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Curva de capital
            initial_balance = 10000
            cumulative_pnl = self.analyzer.trades_df['pnl'].cumsum()
            equity_curve = initial_balance + cumulative_pnl
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=self.analyzer.trades_df['exit_time'],
                y=equity_curve,
                mode='lines',
                name='Balance',
                line=dict(color='blue', width=2)
            ))
            fig.add_hline(y=initial_balance, line_dash="dash", line_color="red", 
                         annotation_text="Balance Inicial")
            
            fig.update_layout(
                title="Curva de Capital",
                xaxis_title="Fecha",
                yaxis_title="Balance ($)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Distribución de P&L
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=self.analyzer.trades_df['pnl'],
                nbinsx=20,
                marker_color='lightgreen',
                opacity=0.7
            ))
            fig.add_vline(x=0, line_dash="dash", line_color="red")
            
            fig.update_layout(
                title="Distribución de P&L",
                xaxis_title="P&L ($)",
                yaxis_title="Frecuencia",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def create_trading_controls(self):
        """Crea controles para el bot de trading"""
        st.sidebar.header("🎮 Control del Bot")
        
        # Configuración inicial
        st.sidebar.subheader("Configuración")
        
        symbols = st.sidebar.multiselect(
            "Símbolos a tradear",
            ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT', 'LINKUSDT'],
            default=['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        )
        
        initial_balance = st.sidebar.number_input(
            "Balance inicial ($)",
            min_value=1000.0,
            max_value=100000.0,
            value=10000.0,
            step=1000.0
        )
        
        # Botón para inicializar bot
        if st.sidebar.button("🔄 Inicializar Bot"):
            if self.initialize_bot(symbols, initial_balance):
                st.sidebar.success("✅ Bot inicializado correctamente")
                st.rerun()
            else:
                st.sidebar.error("❌ Error inicializando bot")
        
        # Control de trading
        if self.bot:
            st.sidebar.subheader("Trading")
            
            if st.sidebar.button("▶️ Ejecutar Ciclo de Trading"):
                with st.spinner("Ejecutando análisis..."):
                    self.bot.run_trading_cycle()
                st.sidebar.success("✅ Ciclo ejecutado")
                st.rerun()
            
            if st.sidebar.button("🔄 Actualizar Precios"):
                with st.spinner("Actualizando precios..."):
                    self.bot.update_prices()
                st.sidebar.success("✅ Precios actualizados")
                st.rerun()
            
            # Cerrar todas las posiciones
            if self.bot.open_trades:
                if st.sidebar.button("🛑 Cerrar Todas las Posiciones"):
                    for trade in list(self.bot.open_trades.values()):
                        current_price = self.bot.current_prices.get(trade.symbol, trade.entry_price)
                        self.bot.close_position(trade, current_price, "Manual close")
                    st.sidebar.success("✅ Todas las posiciones cerradas")
                    st.rerun()
    
    def create_statistics_panel(self):
        """Crea panel de estadísticas"""
        st.sidebar.header("📊 Estadísticas")
        
        if not self.bot:
            st.sidebar.info("Bot no inicializado")
            return
        
        data = self.get_real_time_data()
        portfolio = data['portfolio']
        
        st.sidebar.metric("Balance Disponible", f"${portfolio['available_balance']:,.2f}")
        st.sidebar.metric("Drawdown Actual", f"{portfolio['current_drawdown']:.2f}%")
        st.sidebar.metric("Total Trades", portfolio['total_trades'])
        
        # Mostrar configuración actual
        st.sidebar.subheader("⚙️ Configuración Actual")
        config = self.bot.trading_config
        st.sidebar.write(f"Max Posición: {config['max_position_size']*100:.1f}%")
        st.sidebar.write(f"Stop Loss: {config['stop_loss_pct']*100:.1f}%")
        st.sidebar.write(f"Take Profit: {config['take_profit_pct']*100:.1f}%")
        st.sidebar.write(f"Max Posiciones: {config['max_open_positions']}")
    
    def run_dashboard(self):
        """Ejecuta el dashboard principal"""
        st.title("🤖 CriptoBot - Dashboard de Trading")
        st.markdown("---")
        
        # Crear controles en sidebar
        self.create_trading_controls()
        self.create_statistics_panel()
        
        # Contenido principal
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔄 Trades en Vivo", "📈 Precios", "📊 Performance"])
        
        with tab1:
            self.create_portfolio_overview()
        
        with tab2:
            self.create_live_trades_table()
        
        with tab3:
            self.create_price_charts()
        
        with tab4:
            self.create_performance_charts()
        
        # Auto-refresh
        if st.sidebar.checkbox("🔄 Auto-refresh (30s)"):
            time.sleep(30)
            st.rerun()

def main():
    """Función principal para ejecutar la interfaz web"""
    interface = TradingBotWebInterface()
    interface.run_dashboard()

if __name__ == "__main__":
    main()