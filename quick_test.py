# quick_test.py - Test rapide avec gestion popup

from ib_insync import *
import time

class QuickTest:
    def __init__(self):
        self.ib = IB()
    
    def test_with_popup_warning(self):
        print("🚨 ATTENTION - POPUP TWS ATTENDUE !")
        print("=" * 40)
        print("⚠️  Quand TWS affiche la popup :")
        print("   'Do you want to accept this connection?'")
        print("   👆 CLIQUEZ RAPIDEMENT SUR 'ACCEPTER' !")
        print("=" * 40)
        
        input("Appuyez sur Entrée quand vous êtes prêt...")
        
        try:
            print("\n🔌 Connexion...")
            self.ib.connect('127.0.0.1', 7497, clientId=1)
            
            print("✅ Connecté!")
            
            # Test données RAPIDE
            print("📊 Test données AAPL...")
            contract = Stock('AAPL', 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Requête simple avec timeout court
            bars = self.ib.reqHistoricalData(
                contract, '', '2 D', '1 day', 'TRADES', 1, 1, False
            )
            
            if bars:
                price = bars[-1].close
                print(f"🎉 SUCCÈS! Prix AAPL: ${price:.2f}")
                print("✅ Les données marchent maintenant!")
                return True
            else:
                print("❌ Toujours pas de données")
                return False
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
        finally:
            if self.ib.isConnected():
                self.ib.disconnect()

def main():
    tester = QuickTest()
    
    success = tester.test_with_popup_warning()
    
    if success:
        print("\n🎯 PARFAIT! Le problème était la popup!")
        print("📋 Maintenant configurons TWS pour éviter ça...")
        print("\n💡 CONFIGURATION TWS :")
        print("   1. Configuration → API → Settings")
        print("   2. Cochez 'Create API message log file'")
        print("   3. Dans 'Trusted IPs' ajoutez: 127.0.0.1")
        print("   4. Ou cochez 'Bypass Order Precautions for API orders'")
        print("\n🚀 Après ça, plus de popup!")
    else:
        print("❌ Toujours un problème...")

if __name__ == "__main__":
    main()