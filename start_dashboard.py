#!/usr/bin/env python3

import subprocess
import sys
import os
import time

def print_banner():
    """Imprime banner del dashboard"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                    🌐 CRIPTO BOT DASHBOARD                        ║
    ║                 Interfaz Web para Trading Bot                    ║
    ║                     💰 Con dinero 100% FAKE                      ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

def check_streamlit():
    """Verifica si Streamlit está instalado"""
    try:
        import streamlit
        return True
    except ImportError:
        return False

def main():
    """Función principal para lanzar el dashboard"""
    print_banner()
    
    if not check_streamlit():
        print("❌ Streamlit no está instalado")
        print("📦 Instalando Streamlit...")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit"])
    
    print("🚀 OPCIONES DE DASHBOARD:")
    print("1. 🧪 Test Dashboard (Prueba básica)")
    print("2. 💹 Dashboard Simple (Con precios reales)")
    print("3. 🌐 Dashboard Original (Completo)")
    print("4. ❌ Cancelar")
    
    while True:
        try:
            opcion = input("\n🎯 Elige opción (1-4): ").strip()
            
            if opcion == "1":
                print("\n🧪 Lanzando Test Dashboard...")
                print("🌐 Se abrirá en: http://localhost:8501")
                print("🛑 Presiona Ctrl+C para detener")
                
                subprocess.run([
                    sys.executable, "-m", "streamlit", "run", 
                    "test_dashboard.py", "--server.port", "8501"
                ])
                
            elif opcion == "2":
                print("\n💹 Lanzando Dashboard Simple...")
                print("🌐 Se abrirá en: http://localhost:8501")
                print("🛑 Presiona Ctrl+C para detener")
                
                subprocess.run([
                    sys.executable, "-m", "streamlit", "run", 
                    "dashboard_simple.py", "--server.port", "8501"
                ])
                
            elif opcion == "3":
                print("\n🌐 Lanzando Dashboard Original...")
                print("🌐 Se abrirá en: http://localhost:8501")
                print("🛑 Presiona Ctrl+C para detener")
                
                subprocess.run([
                    sys.executable, "-m", "streamlit", "run", 
                    "web_interface.py", "--server.port", "8501"
                ])
                
            elif opcion == "4":
                print("👋 ¡Hasta luego!")
                break
                
            else:
                print("❌ Opción inválida. Usa 1-4.")
                
        except KeyboardInterrupt:
            print("\n\n🛑 Dashboard detenido")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()