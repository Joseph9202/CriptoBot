#!/usr/bin/env python3

# DIAGNÓSTICO COMPLETO - Para encontrar qué está fallando

def diagnostico_completo():
    print("🔍 DIAGNÓSTICO COMPLETO DEL CRIPTO BOT")
    print("="*60)
    
    # 1. Verificar Python
    import sys
    print(f"✅ Python versión: {sys.version}")
    
    # 2. Verificar ubicación
    import os
    print(f"✅ Directorio actual: {os.getcwd()}")
    
    # 3. Verificar archivos
    archivos_necesarios = [
        'bot_simple.py',
        'quick_demo.py', 
        'test_bot.py',
        'app.py',
        'intraday_garch_bot.py'
    ]
    
    print("\n📁 ARCHIVOS DISPONIBLES:")
    for archivo in archivos_necesarios:
        if os.path.exists(archivo):
            print(f"✅ {archivo} - Existe")
        else:
            print(f"❌ {archivo} - No encontrado")
    
    # 4. Verificar librerías
    print("\n📦 LIBRERÍAS:")
    librerias = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('binance', 'python-binance'),
        ('matplotlib', 'matplotlib'),
        ('pandas_ta', 'pandas-ta')
    ]
    
    for lib, nombre in librerias:
        try:
            __import__(lib)
            print(f"✅ {nombre} - Instalado")
        except ImportError:
            print(f"❌ {nombre} - NO instalado")
    
    # 5. Verificar conexión a Binance
    print("\n🌐 CONEXIÓN BINANCE:")
    try:
        from binance.client import Client
        API_KEY = 'bi2EmkU2VDtYadEfT75qihlJzBwwTKmcovIxcAViCKYsdJk0mZWywHVdFO6MAJvb'
        API_SECRET = 'O1EYxnqBwJvnfYa0TcxAq076KgeBatHSQ4w5wsUlrlCi3913gRTPw6T8OEdUGwDS'
        
        client = Client(API_KEY, API_SECRET)
        precio = client.get_symbol_ticker(symbol='BTCUSDT')
        print(f"✅ Conexión Binance - OK")
        print(f"✅ Bitcoin: ${float(precio['price']):,.2f}")
        
    except Exception as e:
        print(f"❌ Error Binance: {e}")
    
    # 6. Verificar entorno virtual
    print(f"\n🐍 ENTORNO VIRTUAL:")
    if 'VIRTUAL_ENV' in os.environ:
        print(f"✅ Entorno virtual activo: {os.environ['VIRTUAL_ENV']}")
    else:
        print("⚠️ Entorno virtual NO detectado")
        print("💡 Ejecuta: source binance_env/bin/activate")
    
    # 7. Comandos sugeridos
    print("\n🚀 COMANDOS PARA EJECUTAR:")
    print("="*60)
    print("1. Bot más simple:")
    print("   python bot_simple.py")
    print("\n2. Demo rápido:")
    print("   python quick_demo.py")
    print("\n3. Consulta precios:")
    print("   python test_bot.py")
    print("\n4. Con entorno virtual:")
    print("   source binance_env/bin/activate && python bot_simple.py")
    
    print("\n" + "="*60)
    print("📞 DIME EXACTAMENTE QUÉ ERROR VES")
    print("Copia y pega el mensaje de error completo")
    print("="*60)

if __name__ == "__main__":
    diagnostico_completo()