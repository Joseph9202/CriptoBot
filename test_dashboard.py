#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import time

# Configuración de la página
st.set_page_config(
    page_title="Test CriptoBot Dashboard",
    page_icon="🚀",
    layout="wide"
)

def test_dashboard():
    """Dashboard de prueba simple"""
    
    st.title("🚀 Test CriptoBot Dashboard")
    st.subheader("Prueba básica de funcionalidad")
    
    # Test básico de componentes
    st.success("✅ Streamlit está funcionando correctamente")
    
    # Métricas de prueba
    st.header("📊 Test de Métricas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Balance", "$10,000", "+$150")
    
    with col2:
        st.metric("Trades", "5", "+2")
    
    with col3:
        st.metric("Win Rate", "80%", "+10%")
    
    with col4:
        st.metric("P&L", "+1.5%", "+0.3%")
    
    # Test de gráfico simple
    st.header("📈 Test de Gráfico")
    
    # Generar datos de ejemplo
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    prices = np.cumsum(np.random.randn(30)) + 100
    
    df = pd.DataFrame({
        'Fecha': dates,
        'Precio': prices
    })
    
    fig = px.line(df, x='Fecha', y='Precio', title='Precio Bitcoin (Simulado)')
    st.plotly_chart(fig, use_container_width=True)
    
    # Test de datos tabulares
    st.header("📋 Test de Tabla")
    
    trades_data = {
        'Timestamp': [datetime.now() - pd.Timedelta(hours=i) for i in range(5)],
        'Symbol': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT'],
        'Action': ['BUY', 'SELL', 'BUY', 'SELL', 'BUY'],
        'Price': [45000, 3200, 450, 1.20, 120],
        'P&L': [150, -80, 75, 25, -45]
    }
    
    st.dataframe(pd.DataFrame(trades_data))
    
    # Test de controles
    st.header("🎮 Test de Controles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Actualizar Datos"):
            st.success("Datos actualizados!")
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh")
    
    # Sidebar test
    st.sidebar.header("🎛️ Panel de Control")
    
    symbols = st.sidebar.multiselect(
        "Selecciona criptomonedas:",
        ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
        default=['BTCUSDT']
    )
    
    interval = st.sidebar.selectbox(
        "Intervalo de tiempo:",
        ['1m', '5m', '15m', '1h', '1d']
    )
    
    st.sidebar.info("Dashboard de prueba funcionando correctamente ✅")
    
    # Status
    st.header("🔍 Estado del Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **✅ Componentes funcionando:**
        - Streamlit ✅
        - Plotly ✅
        - Pandas ✅
        - Layout responsivo ✅
        """)
    
    with col2:
        st.success("""
        **🚀 Listo para:**
        - Conectar con Binance API
        - Mostrar datos reales
        - Ejecutar trades simulados
        - Análisis en tiempo real
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("🤖 **CriptoBot Test Dashboard** - Todos los componentes funcionando correctamente")
    
    if auto_refresh:
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    test_dashboard()