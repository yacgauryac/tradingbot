# connection_cleanup.py - Fix définitif des connexions zombies

import os
import time
import subprocess

def kill_all_python_processes():
    """Tue tous les processus Python pour nettoyer"""
    try:
        print("💀 Nettoyage des processus Python...")
        
        # Windows
        if os.name == 'nt':
            os.system('taskkill /f /im python.exe 2>nul')
            os.system('taskkill /f /im pythonw.exe 2>nul')
        else:
            # Linux/Mac
            os.system('pkill -f python')
        
        print("✅ Processus Python nettoyés")
        time.sleep(2)
        
    except Exception as e:
        print(f"⚠️ Nettoyage processus: {e}")

def disconnect_all_tws_connections():
    """Guide pour déconnecter dans TWS"""
    
    print("""
    🔧 DANS TWS - DÉCONNEXION MANUELLE:
    ===================================
    
    1. 📊 File → Global Configuration → API → Settings
    
    2. 👀 Tu vois "Active Sessions" avec des lignes comme:
       Client ID: 1    Status: Connected    IP: 127.0.0.1
       Client ID: 2    Status: Connected    IP: 127.0.0.1
       Client ID: 3    Status: Connected    IP: 127.0.0.1
    
    3. 🚫 Clique "Disconnect All" (bouton rouge)
    
    4. ✅ Attends que toutes les sessions disparaissent
    
    5. 🔄 Clique "OK" pour fermer la fenêtre
    """)

def create_clean_bot_version():
    """Crée une version du bot avec gestion propre des connexions"""
    
    clean_code = '''# trading_bot_clean.py - Version avec gestion propre des connexions
import asyncio
import signal
import sys
import atexit
from datetime import datetime
import logging

# Imports des modules
from config import ConfigManager
from ib_connector import IBConnector
from strategies import StrategyManager
from risk_manager import RiskManager

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot_clean.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class CleanTradingBot:
    """Bot avec gestion propre des connexions"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.ib_connector = IBConnector(self.config_manager)
        self.strategy_manager = StrategyManager(self.config_manager)
        self.risk_manager = RiskManager(self.config_manager)
        
        self.is_running = False
        self.cycle_count = 0
        
        # Gestion propre de l'arrêt
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        atexit.register(self._cleanup_on_exit)
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signaux pour arrêt propre"""
        logger.info(f"🛑 Signal {signum} reçu")
        self.is_running = False
    
    def _cleanup_on_exit(self):
        """Nettoyage automatique à la sortie"""
        try:
            if hasattr(self, 'ib_connector') and self.ib_connector.is_connected:
                asyncio.run(self.ib_connector.disconnect())
                logger.info("🔌 Connexion fermée automatiquement")
        except:
            pass
    
    async def start(self):
        """Démarrage du bot avec gestion d'erreurs"""
        connection_attempts = 0
        max_attempts = 3
        
        while connection_attempts < max_attempts:
            try:
                logger.info("🚀 DÉMARRAGE BOT TRADING CLEAN")
                logger.info("=" * 50)
                
                # Tentative de connexion
                logger.info(f"🔌 Connexion IB (tentative {connection_attempts + 1}/{max_attempts})")
                
                if await self.ib_connector.connect():
                    logger.info("✅ Connexion IB établie!")
                    break
                else:
                    connection_attempts += 1
                    if connection_attempts < max_attempts:
                        logger.warning(f"⚠️ Échec connexion, retry dans 10s...")
                        await asyncio.sleep(10)
                    else:
                        logger.error("❌ Impossible de se connecter après 3 tentatives")
                        return
            
            except Exception as e:
                logger.error(f"❌ Erreur connexion: {e}")
                connection_attempts += 1
                if connection_attempts < max_attempts:
                    await asyncio.sleep(10)
        
        # Boucle principale
        try:
            self.is_running = True
            await self._trading_loop()
            
        except KeyboardInterrupt:
            logger.info("🛑 Arrêt demandé par utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur critique: {e}")
        finally:
            await self._shutdown()
    
    async def _trading_loop(self):
        """Boucle de trading simplifiée"""
        logger.info("🔄 Démarrage boucle de trading")
        
        while self.is_running:
            try:
                self.cycle_count += 1
                logger.info(f"📊 === CYCLE #{self.cycle_count} ===")
                
                # Vérification santé connexion
                if not await self.ib_connector.health_check():
                    logger.warning("⚠️ Connexion IB défaillante")
                    break
                
                # Vérification marché ouvert
                if not self.ib_connector.is_market_open():
                    logger.info("⏰ Marché fermé, pause 1h")
                    await asyncio.sleep(3600)
                    continue
                
                # Analyse des tickers
                tickers = self.config_manager.system_config.tickers
                
                for symbol in tickers:
                    if not self.is_running:
                        break
                    
                    try:
                        # Récupération données
                        df = await self.ib_connector.get_historical_data(symbol, '10 D', '1 day')
                        
                        if df is not None and len(df) > 20:
                            # Analyse stratégie
                            result = self.strategy_manager.analyze(symbol, df)
                            
                            if result.buy_signal:
                                logger.info(f"🟢 Signal achat {symbol}")
                                # Ici on passerait l'ordre
                                # await self._execute_buy(symbol, result)
                            
                            elif result.sell_signal:
                                logger.info(f"🔴 Signal vente {symbol}")
                                # await self._execute_sell(symbol, result)
                        
                        # Pause entre symboles
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"❌ Erreur analyse {symbol}: {e}")
                        continue
                
                # Pause entre cycles
                if self.is_running:
                    pause_time = self.config_manager.system_config.analysis_interval
                    logger.info(f"✅ Cycle terminé, pause {pause_time}s")
                    await asyncio.sleep(pause_time)
                
            except Exception as e:
                logger.error(f"❌ Erreur boucle: {e}")
                await asyncio.sleep(60)
    
    async def _shutdown(self):
        """Arrêt propre du bot"""
        logger.info("🛑 Arrêt du bot...")
        
        try:
            # Déconnexion propre
            if self.ib_connector.is_connected:
                await self.ib_connector.disconnect()
                logger.info("🔌 Déconnexion IB OK")
            
            logger.info(f"📊 Total cycles: {self.cycle_count}")
            logger.info("✅ Bot arrêté proprement")
            
        except Exception as e:
            logger.error(f"❌ Erreur arrêt: {e}")

async def main():
    """Point d'entrée principal"""
    bot = CleanTradingBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n🛑 Arrêt utilisateur")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
'''
    
    with open("trading_bot_clean.py", "w", encoding='utf-8') as f:
        f.write(clean_code)
    
    print("✅ Bot propre créé: trading_bot_clean.py")

def show_connection_monitoring():
    """Guide pour surveiller les connexions"""
    
    print("""
    👀 SURVEILLANCE DES CONNEXIONS TWS:
    ===================================
    
    📊 En temps réel dans TWS:
    ┌─────────────────────────────────────┐
    │ Barre statut (bas droite):          │
    │ API: Connected (1 client)    🟢     │
    │ API: Connected (3 clients)   🟡     │  
    │ API: Disconnected            🔴     │
    └─────────────────────────────────────┘
    
    🔧 Détails complets:
    File → Global Configuration → API → Settings
    
    Active Sessions:
    ┌──────────┬───────────┬─────────────┐
    │Client ID │ Status    │ IP Address  │
    ├──────────┼───────────┼─────────────┤
    │    1     │Connected  │127.0.0.1    │
    │    2     │Connected  │127.0.0.1    │ ← PROBLÈME
    │    3     │Connected  │127.0.0.1    │ ← PROBLÈME  
    └──────────┴───────────┴─────────────┘
    
    💡 NORMAL: 1 seule connexion
    🚨 PROBLÈME: Plusieurs connexions = Fuites
    
    📋 Messages TWS (bas écran):
    - "API client 1 connected"     ✅
    - "API client 2 connected"     ❌ 
    - "API client 1 disconnected"  ✅
    """)

def complete_cleanup_guide():
    """Guide complet de nettoyage"""
    
    print("🧹 NETTOYAGE COMPLET - ÉTAPE PAR ÉTAPE")
    print("=" * 45)
    
    print("\n1️⃣ ARRÊT DU BOT:")
    print("   - Si le bot tourne: Ctrl+C")
    print("   - Attendre l'arrêt complet")
    
    print("\n2️⃣ KILL PROCESSUS PYTHON:")
    kill_all_python_processes()
    
    print("\n3️⃣ NETTOYAGE TWS:")
    disconnect_all_tws_connections()
    
    print("\n4️⃣ CRÉATION BOT PROPRE:")
    create_clean_bot_version()
    
    print("\n5️⃣ SURVEILLANCE:")
    show_connection_monitoring()
    
    print("\n🚀 RELANCEMENT PROPRE:")
    print("   python trading_bot_clean.py")
    print("\n✅ TU DOIS VOIR:")
    print("   - 1 seule connexion dans TWS")
    print("   - Pas d'erreur 'event loop'") 
    print("   - Arrêt propre avec Ctrl+C")

def main():
    print("🔧 FIX CONNEXIONS ZOMBIES")
    print("=" * 30)
    
    complete_cleanup_guide()

if __name__ == "__main__":
    main()