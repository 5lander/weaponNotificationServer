import socket
import os
from dotenv import load_dotenv

load_dotenv()

def test_smtp_connection():
    print("\n🧪 TESTEANDO CONEXIÓN SMTP A GMAIL")
    print("="*60)
    
    host = 'smtp.gmail.com'
    ports = [587, 465, 25]  # Probar múltiples puertos
    
    for port in ports:
        print(f"\nProbando {host}:{port}...")
        try:
            sock = socket.create_connection((host, port), timeout=10)
            sock.close()
            print(f"✅ Puerto {port} ACCESIBLE")
        except socket.timeout:
            print(f"⏱️ Puerto {port} - TIMEOUT (firewall?)")
        except socket.error as e:
            print(f"❌ Puerto {port} - ERROR: {e}")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    test_smtp_connection()