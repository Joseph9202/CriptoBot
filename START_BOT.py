#!/usr/bin/env python3

def main():
    """Script principal para ejecutar el CriptoBot"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                        🤖 CRIPTO BOT 🤖                         ║
    ║                  Bot de Trading con Paper Trading                ║
    ║                     ✅ FUNCIONANDO CORRECTAMENTE                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    print("🚀 OPCIONES DISPONIBLES:")
    print("="*60)
    print("1. 📈 Demo Rápido - Simulación de trading (5 minutos)")
    print("2. 📊 Consulta de Precios - Ver precios actuales")
    print("3. ⚡ Bot Intraday GARCH - Tu bot original completo")
    print("4. ❌ Salir")
    print("="*60)
    
    while True:
        try:
            opcion = input("\n🎯 Elige una opción (1-4): ").strip()
            
            if opcion == "1":
                print("\n🚀 Ejecutando Demo Rápido...")
                import quick_demo
                quick_demo.quick_trading_demo()
                
            elif opcion == "2":
                print("\n📊 Consultando precios...")
                import test_bot
                test_bot.test_basic_bot()
                
            elif opcion == "3":
                print("\n⚡ Iniciando Bot Intraday GARCH...")
                print("⚠️ Este bot puede tardar varios minutos")
                respuesta = input("¿Continuar? (s/n): ").lower()
                if respuesta == 's':
                    import intraday_garch_bot
                    # El bot se ejecutará automáticamente
                else:
                    print("❌ Cancelado")
                    
            elif opcion == "4":
                print("👋 ¡Gracias por usar CriptoBot!")
                break
                
            else:
                print("❌ Opción inválida. Usa 1-4.")
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Adiós!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            
        print("\n" + "-"*40)
        input("Presiona Enter para continuar...")

if __name__ == "__main__":
    main()