#!/usr/bin/env python3

import sys
import os

def print_banner():
    """Imprime banner del CriptoBot"""
    print("\n" + "="*60)
    print("🤖 CRIPTO BOT - SIMULADOR DE TRADING")
    print("💰 Trading con Dinero Fake - Sin Riesgo")
    print("="*60)

def test_imports():
    """Verifica que todas las dependencias estén instaladas"""
    missing_packages = []
    
    try:
        import pandas
        print("✅ pandas - OK")
    except ImportError:
        missing_packages.append("pandas")
        print("❌ pandas - FALTA")
    
    try:
        import numpy
        print("✅ numpy - OK")
    except ImportError:
        missing_packages.append("numpy")
        print("❌ numpy - FALTA")
    
    try:
        import matplotlib
        print("✅ matplotlib - OK")
    except ImportError:
        missing_packages.append("matplotlib")
        print("❌ matplotlib - FALTA")
    
    try:
        from binance.client import Client
        print("✅ python-binance - OK")
    except ImportError:
        missing_packages.append("python-binance")
        print("❌ python-binance - FALTA")
    
    try:
        import pandas_ta
        print("✅ pandas-ta - OK")
    except ImportError:
        missing_packages.append("pandas-ta")
        print("❌ pandas-ta - FALTA")
    
    if missing_packages:
        print(f"\n⚠️ FALTAN DEPENDENCIAS: {', '.join(missing_packages)}")
        print("📦 Para instalar ejecuta:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    else:
        print("\n✅ Todas las dependencias están instaladas")
        return True

def run_basic_bot():
    """Ejecuta el bot básico de precios"""
    print("\n🚀 Ejecutando Bot Básico de Precios...")
    try:
        exec(open('app.py').read())
    except FileNotFoundError:
        print("❌ Archivo app.py no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")

def run_intraday_bot():
    """Ejecuta el bot intraday"""
    print("\n⚡ Ejecutando Bot Intraday GARCH...")
    try:
        exec(open('intraday_garch_bot.py').read())
    except FileNotFoundError:
        print("❌ Archivo intraday_garch_bot.py no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")

def run_enhanced_bot():
    """Ejecuta el bot avanzado"""
    print("\n🤖 Ejecutando Bot Avanzado de Paper Trading...")
    try:
        exec(open('enhanced_paper_trading_bot.py').read())
    except FileNotFoundError:
        print("❌ Archivo enhanced_paper_trading_bot.py no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_menu():
    """Muestra menú principal"""
    print("\n" + "="*50)
    print("🎮 MENÚ PRINCIPAL")
    print("="*50)
    print("1. 📈 Bot Básico de Precios (Funciona siempre)")
    print("2. ⚡ Bot Intraday GARCH (Tu bot original)")
    print("3. 🤖 Bot Avanzado Paper Trading (Nuevo)")
    print("4. 🔧 Verificar Dependencias")
    print("5. ❌ Salir")
    print("="*50)

def main():
    """Función principal"""
    print_banner()
    
    while True:
        show_menu()
        
        try:
            choice = input("\n🎯 Elige una opción (1-5): ").strip()
            
            if choice == "1":
                run_basic_bot()
            elif choice == "2":
                run_intraday_bot()
            elif choice == "3":
                if test_imports():
                    run_enhanced_bot()
                else:
                    print("\n❌ Faltan dependencias para el bot avanzado")
            elif choice == "4":
                print("\n🔍 Verificando dependencias...")
                test_imports()
            elif choice == "5":
                print("\n👋 ¡Gracias por usar CriptoBot!")
                break
            else:
                print("❌ Opción inválida. Elige 1-5.")
            
            input("\nPresiona Enter para continuar...")
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Adiós!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()