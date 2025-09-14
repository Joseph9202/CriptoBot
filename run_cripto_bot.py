#!/usr/bin/env python3

import subprocess
import sys
import os
from pathlib import Path

def print_banner():
    """Imprime banner del CriptoBot"""
    banner = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║                        🤖 CRIPTO BOT 🤖                         ║
    ║                  Bot de Trading con Paper Trading                ║
    ║                     Simulación con Dinero Fake                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_requirements():
    """Verifica e instala dependencias"""
    print("📦 Verificando dependencias...")
    
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                         check=True, capture_output=True)
            print("✅ Dependencias instaladas correctamente")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando dependencias: {e}")
            return False
    else:
        print("⚠️ Archivo requirements.txt no encontrado")
    
    return True

def show_menu():
    """Muestra menú principal"""
    print("\n" + "="*60)
    print("🎮 MENÚ PRINCIPAL - CRIPTO BOT")
    print("="*60)
    print("1. 🚀 Ejecutar Bot de Paper Trading Avanzado")
    print("2. 📊 Ejecutar Análisis de Portfolio")
    print("3. 🌐 Lanzar Dashboard Web (Streamlit)")
    print("4. ⚡ Bot de Trading Intraday GARCH")
    print("5. 📈 Bot de Consulta de Precios")
    print("6. 🔧 Configurar API Keys")
    print("7. 📋 Ver Historial de Trades")
    print("8. ❌ Salir")
    print("="*60)

def run_paper_trading_bot():
    """Ejecuta el bot de paper trading avanzado"""
    print("🚀 Iniciando Bot de Paper Trading Avanzado...")
    try:
        subprocess.run([sys.executable, "enhanced_paper_trading_bot.py"])
    except FileNotFoundError:
        print("❌ Archivo enhanced_paper_trading_bot.py no encontrado")
    except Exception as e:
        print(f"❌ Error ejecutando bot: {e}")

def run_portfolio_analyzer():
    """Ejecuta el analizador de portfolio"""
    print("📊 Iniciando Análisis de Portfolio...")
    try:
        subprocess.run([sys.executable, "portfolio_analyzer.py"])
    except FileNotFoundError:
        print("❌ Archivo portfolio_analyzer.py no encontrado")
    except Exception as e:
        print(f"❌ Error ejecutando análisis: {e}")

def run_web_dashboard():
    """Ejecuta el dashboard web"""
    print("🌐 Iniciando Dashboard Web...")
    print("📌 El dashboard se abrirá en tu navegador en unos segundos...")
    print("🔗 URL: http://localhost:8501")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "web_interface.py"])
    except FileNotFoundError:
        print("❌ Archivo web_interface.py no encontrado")
    except Exception as e:
        print(f"❌ Error ejecutando dashboard: {e}")

def run_intraday_bot():
    """Ejecuta el bot de trading intraday"""
    print("⚡ Iniciando Bot de Trading Intraday GARCH...")
    try:
        subprocess.run([sys.executable, "intraday_garch_bot.py"])
    except FileNotFoundError:
        print("❌ Archivo intraday_garch_bot.py no encontrado")
    except Exception as e:
        print(f"❌ Error ejecutando bot intraday: {e}")

def run_price_bot():
    """Ejecuta el bot de consulta de precios"""
    print("📈 Iniciando Bot de Consulta de Precios...")
    try:
        subprocess.run([sys.executable, "app.py"])
    except FileNotFoundError:
        print("❌ Archivo app.py no encontrado")
    except Exception as e:
        print(f"❌ Error ejecutando bot de precios: {e}")

def configure_api_keys():
    """Permite configurar las API keys"""
    print("🔧 CONFIGURACIÓN DE API KEYS")
    print("="*50)
    print("⚠️ IMPORTANTE: Estas son APIs de TESTNET/DEMO")
    print("⚠️ Solo para simulación con dinero fake")
    print("="*50)
    
    current_key = "bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb"
    current_secret = "O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS"
    
    print(f"API Key actual: {current_key[:20]}...")
    print(f"Secret actual: {current_secret[:20]}...")
    print("\n💡 Las keys actuales son para Binance Testnet (dinero fake)")
    print("💡 Si quieres usar keys reales, modifica los archivos Python manualmente")
    
    input("\nPresiona Enter para continuar...")

def view_trade_history():
    """Muestra el historial de trades"""
    print("📋 HISTORIAL DE TRADES")
    print("="*50)
    
    db_file = Path("trading_bot.db")
    if not db_file.exists():
        print("❌ No se encontró base de datos de trades")
        print("💡 Ejecuta primero el bot de trading para generar historial")
        input("\nPresiona Enter para continuar...")
        return
    
    try:
        import sqlite3
        import pandas as pd
        
        conn = sqlite3.connect("trading_bot.db")
        trades_df = pd.read_sql_query("SELECT * FROM trades ORDER BY entry_time DESC LIMIT 10", conn)
        
        if trades_df.empty:
            print("📝 No hay trades en el historial")
        else:
            print(f"📊 Últimos {len(trades_df)} trades:")
            print("-" * 100)
            for _, trade in trades_df.iterrows():
                status_emoji = "🟢" if trade['pnl'] > 0 else "🔴" if trade['pnl'] < 0 else "⚪"
                print(f"{status_emoji} {trade['symbol']} | {trade['side']} | P&L: ${trade['pnl']:.2f} | {trade['entry_time']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error leyendo historial: {e}")
    
    input("\nPresiona Enter para continuar...")

def main():
    """Función principal del launcher"""
    print_banner()
    
    if not check_requirements():
        print("❌ Error con las dependencias. Saliendo...")
        return
    
    while True:
        show_menu()
        
        try:
            choice = input("\n🎯 Elige una opción (1-8): ").strip()
            
            if choice == "1":
                run_paper_trading_bot()
            elif choice == "2":
                run_portfolio_analyzer()
            elif choice == "3":
                run_web_dashboard()
            elif choice == "4":
                run_intraday_bot()
            elif choice == "5":
                run_price_bot()
            elif choice == "6":
                configure_api_keys()
            elif choice == "7":
                view_trade_history()
            elif choice == "8":
                print("👋 ¡Gracias por usar CriptoBot!")
                break
            else:
                print("❌ Opción inválida. Por favor elige 1-8.")
            
            input("\nPresiona Enter para volver al menú...")
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Adiós!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()