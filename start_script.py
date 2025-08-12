# start.py - Script de démarrage rapide pour le bot de trading
import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import asyncio
import threading

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    required_packages = [
        'ib_insync',
        'pandas',
        'ta', 
        'numpy',
        'matplotlib'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies(packages):
    """Installe les dépendances manquantes"""
    for package in packages:
        print(f"📦 Installation de {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_files():
    """Vérifie que tous les fichiers nécessaires sont présents"""
    required_files = [
        'config.py',
        'ib_connector.py', 
        'strategies.py',
        'risk_manager.py',
        'trading_bot.py',
        'trading_interface.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    return missing_files

def test_ib_connection():
    """Test rapide de connexion IB"""
    try:
        from config import ConfigManager
        from ib_connector import IBConnector
        
        async def test():
            config = ConfigManager()
            connector = IBConnector(config)
            
            print("🔌 Test de connexion à Interactive Brokers...")
            result = await connector.connect()
            
            if result:
                print("✅ Connexion réussie!")
                await connector.disconnect()
                return True
            else:
                print("❌ Connexion échouée")
                return False
        
        return asyncio.run(test())
        
    except Exception as e:
        print(f"❌ Erreur test connexion: {e}")
        return False

def create_initial_config():
    """Crée une configuration initiale si elle n'existe pas"""
    config_file = "trading_config.json"
    
    if not os.path.exists(config_file):
        print("📝 Création de la configuration initiale...")
        
        from config import ConfigManager
        config = ConfigManager()
        config.save_config()
        
        print(f"✅ Configuration créée: {config_file}")
        print("   Vous pouvez la modifier via l'interface ou directement")

def show_startup_menu():
    """Affiche le menu de démarrage"""
    print("=" * 60)
    print("🤖 BOT DE TRADING AUTOMATIQUE")
    print("   Basé sur tes stratégies RSI + MACD")
    print("=" * 60)
    print()
    print("Options de démarrage:")
    print("1. 🖥️  Lancer l'interface graphique (RECOMMANDÉ)")
    print("2. 🤖 Lancer le bot directement")
    print("3. 🧪 Test de connexion IB")
    print("4. ⚙️  Vérifier la configuration")
    print("5. 📋 Aide et documentation")
    print("0. ❌ Quitter")
    print()
    
    while True:
        choice = input("Votre choix (0-5): ").strip()
        
        if choice == "1":
            launch_interface()
            break
        elif choice == "2":
            launch_bot()
            break
        elif choice == "3":
            test_connection()
        elif choice == "4":
            check_configuration()
        elif choice == "5":
            show_help()
        elif choice == "0":
            print("👋 À bientôt!")
            sys.exit(0)
        else:
            print("❌ Choix invalide, recommencez")

def launch_interface():
    """Lance l'interface graphique"""
    try:
        print("🖥️  Lancement de l'interface graphique...")
        
        from trading_interface import TradingInterface
        interface = TradingInterface()
        interface.run()
        
    except Exception as e:
        print(f"❌ Erreur lancement interface: {e}")
        print("💡 Essayez: python trading_interface.py")

def launch_bot():
    """Lance le bot directement"""
    try:
        print("🤖 Lancement du bot de trading...")
        print("⚠️  Pour arrêter: Ctrl+C")
        print()
        
        from config import ConfigManager
        config = ConfigManager()
        
        # Vérification mode live
        if not config.is_paper_trading():
            response = input("⚠️  ATTENTION: Mode LIVE TRADING détecté!\n"
                           "Tapez 'CONFIRME' pour continuer: ")
            if response != 'CONFIRME':
                print("❌ Annulé")
                return
        
        # Import et lancement
        import asyncio
        from trading_bot import TradingBot
        
        bot = TradingBot()
        asyncio.run(bot.start())
        
    except KeyboardInterrupt:
        print("\n🛑 Bot arrêté par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lancement bot: {e}")

def test_connection():
    """Test de connexion"""
    print("\n🧪 Test de connexion Interactive Brokers...")
    
    def test_async():
        return test_ib_connection()
    
    # Lancement du test en arrière-plan
    thread = threading.Thread(target=test_async)
    thread.start()
    thread.join()

def check_configuration():
    """Vérifie la configuration"""
    print("\n⚙️  Vérification de la configuration...")
    
    try:
        from config import ConfigManager
        config = ConfigManager()
        config.display_summary()
        
        print("\n✅ Configuration valide")
        
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")

def show_help():
    """Affiche l'aide"""
    help_text = """
📚 AIDE ET DOCUMENTATION

🎯 QU'EST-CE QUE CE BOT?
   Un système de trading automatique qui reproduit exactement tes 
   stratégies de backtest (RSI + MACD) avec Interactive Brokers.

🔧 PRÉREQUIS:
   1. Compte Interactive Brokers (Paper Trading recommandé)
   2. TWS (Trader Workstation) installé et configuré
   3. API activée dans TWS (File > Global Config > API)
   4. Python 3.7+ avec les packages requis

⚙️  CONFIGURATION:
   - Le fichier trading_config.json contient tous les paramètres
   - Tu peux le modifier via l'interface ou directement
   - Par défaut: Paper Trading port 7497

🚀 UTILISATION:
   1. RECOMMANDÉ: Lance l'interface graphique (option 1)
   2. Configure tes paramètres dans l'onglet Configuration
   3. Teste la connexion IB
   4. Démarre le bot depuis l'interface

📊 STRATÉGIE:
   - RSI + MACD (exactement comme ton backtest)
   - Stop Loss: 5% / Take Profit: 8%
   - Frais: 0.1% par transaction
   - Gestion automatique des positions

🛡️  SÉCURITÉ:
   - Mode Paper Trading par défaut (argent virtuel)
   - Confirmation obligatoire pour mode Live
   - Stop Loss automatiques
   - Logs détaillés de toutes les opérations

📋 FICHIERS IMPORTANTS:
   - trading_config.json : Configuration
   - trading_bot.log : Logs du bot
   - start.py : Ce script (point d'entrée)

💡 CONSEILS:
   - Commence TOUJOURS par Paper Trading
   - Teste tes stratégies pendant plusieurs jours
   - Surveille les logs en temps réel
   - Commence avec un petit capital en Live

🆘 PROBLÈMES COURANTS:
   - "Connexion IB échouée" : Vérifier que TWS est ouvert
   - "API en lecture seule" : Accepter les droits d'écriture
   - "Port 7497 fermé" : Vérifier config API dans TWS

📞 SUPPORT:
   - Vérifier les logs dans trading_bot.log
   - Tester la connexion depuis l'interface
   - Vérifier la configuration Interactive Brokers
"""
    
    print(help_text)
    input("\nAppuyez sur Entrée pour continuer...")

def main():
    """Point d'entrée principal"""
    print("🔍 Vérification de l'environnement...")
    
    # Vérification des dépendances
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"📦 Dépendances manquantes: {', '.join(missing_deps)}")
        
        response = input("Installer automatiquement? (o/N): ")
        if response.lower() in ['o', 'oui', 'y', 'yes']:
            try:
                install_dependencies(missing_deps)
                print("✅ Dépendances installées")
            except Exception as e:
                print(f"❌ Erreur installation: {e}")
                print("💡 Essayez manuellement: pip install ib_insync pandas ta numpy matplotlib")
                sys.exit(1)
        else:
            print("❌ Installation annulée")
            sys.exit(1)
    
    # Vérification des fichiers
    missing_files = check_files()
    if missing_files:
        print(f"❌ Fichiers manquants: {', '.join(missing_files)}")
        print("💡 Assurez-vous d'avoir tous les fichiers du bot")
        sys.exit(1)
    
    # Création config initiale
    create_initial_config()
    
    print("✅ Environnement OK")
    print()
    
    # Menu principal
    show_startup_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Arrêt demandé")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)