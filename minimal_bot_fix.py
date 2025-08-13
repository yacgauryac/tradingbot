# minimal_bot_fix.py - Bot avec debug de connexion

from ib_insync import *
import time
import logging
import random

# Configuration simple
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinimalBotFix:
    """Bot minimal avec debug de connexion"""
    
    def __init__(self):
        self.ib = IB()
        
    def test_connection_modes(self):
        """Test plusieurs modes de connexion"""
        
        # Configurations à tester
        configs = [
            {'host': '127.0.0.1', 'port': 7497, 'clientId': 1, 'desc': 'Mode simulé standard'},
            {'host': '127.0.0.1', 'port': 7497, 'clientId': 999, 'desc': 'Mode simulé - clientId différent'},
            {'host': '127.0.0.1', 'port': 7496, 'clientId': 1, 'desc': 'Mode live (si connecté)'},
            {'host': 'localhost', 'port': 7497, 'clientId': 1, 'desc': 'localhost au lieu de 127.0.0.1'},
        ]
        
        for i, config in enumerate(configs, 1):
            print(f"\n🧪 Test {i}/4: {config['desc']}")
            print(f"   Connexion {config['host']}:{config['port']} (ID: {config['clientId']})")
            
            try:
                if self.ib.isConnected():
                    self.ib.disconnect()
                    time.sleep(1)
                
                self.ib.connect(
                    host=config['host'], 
                    port=config['port'], 
                    clientId=config['clientId'],
                    timeout=10
                )
                
                if self.ib.isConnected():
                    print("✅ Connexion réussie!")
                    
                    # Test simple de données
                    try:
                        account = self.ib.managedAccounts()[0]
                        print(f"💼 Compte: {account}")
                        
                        # Test contrat simple
                        contract = Stock('AAPL', 'SMART', 'USD')
                        self.ib.qualifyContracts(contract)
                        print("✅ Qualification contrat OK")
                        
                        # Test données (1 seule barre pour tester)
                        bars = self.ib.reqHistoricalData(
                            contract, '', '1 D', '1 day', 'TRADES', 1, 1, False
                        )
                        
                        if bars:
                            print(f"✅ Données historiques OK: {len(bars)} barres")
                            print(f"💰 Prix AAPL: ${bars[-1].close:.2f}")
                            print("🎉 CETTE CONFIGURATION FONCTIONNE!")
                            return config
                        else:
                            print("❌ Pas de données historiques")
                            
                    except Exception as e:
                        print(f"❌ Erreur test données: {e}")
                        
                else:
                    print("❌ Connexion échouée")
                    
            except Exception as e:
                print(f"❌ Erreur connexion: {e}")
        
        print("\n❌ Aucune configuration ne fonctionne")
        return None
    
    def get_tws_info(self):
        """Affiche les infos de connexion TWS"""
        if self.ib.isConnected():
            try:
                print(f"\n📊 INFORMATIONS TWS:")
                print(f"   Connecté: {self.ib.isConnected()}")
                print(f"   Comptes: {self.ib.managedAccounts()}")
                
                # Tentative de récupérer des infos serveur
                print(f"   Client ID utilisé: {self.ib.client.clientId}")
                
            except Exception as e:
                print(f"❌ Erreur info TWS: {e}")
    
    def disconnect(self):
        """Déconnexion"""
        if self.ib.isConnected():
            self.ib.disconnect()
            print("🔌 Déconnecté")

def main():
    print("🔧 DIAGNOSTIC DE CONNEXION TWS")
    print("=" * 40)
    
    bot = MinimalBotFix()
    
    try:
        # Test de toutes les configurations
        working_config = bot.test_connection_modes()
        
        if working_config:
            print(f"\n🎯 CONFIGURATION QUI MARCHE:")
            print(f"   Host: {working_config['host']}")
            print(f"   Port: {working_config['port']}")
            print(f"   Client ID: {working_config['clientId']}")
            print(f"\n💡 Utilisez ces paramètres dans le bot principal!")
            
            # Affichage infos TWS
            bot.get_tws_info()
            
        else:
            print(f"\n🔴 PROBLÈME DE CONFIGURATION TWS")
            print(f"\n💡 VÉRIFICATIONS À FAIRE:")
            print(f"   1. TWS est ouvert et connecté ?")
            print(f"   2. Mode simulé/papier activé ?") 
            print(f"   3. API activée dans Configuration → API ?")
            print(f"   4. 'Allow connections from localhost only' décoché ?")
            print(f"   5. Firewall/antivirus qui bloque ?")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrompu")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        bot.disconnect()

if __name__ == "__main__":
    main()