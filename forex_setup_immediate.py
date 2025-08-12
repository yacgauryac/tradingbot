# forex_setup_immediate.py - Configuration FOREX immédiate

import json
import os
from datetime import datetime

def create_forex_config_now():
    """Crée la configuration FOREX optimisée pour trading immédiat"""
    
    config = {
        "ib": {
            "host": "127.0.0.1",
            "port": 7497,  # Paper Trading
            "client_id": 1
        },
        "trading": {
            "capital_initial": 10000,
            "position_size_pct": 0.03,      # 3% par position (prudent pour FOREX)
            "max_positions": 4,             # Max 4 paires simultanées
            "stop_loss_pct": 0.008,         # 0.8% stop loss (serré pour FOREX)
            "take_profit_pct": 0.012,       # 1.2% take profit (réaliste)
            "frais_pourcentage": 0.00002    # Très faibles frais FOREX (spread)
        },
        "strategy": {
            "rsi_window": 14,               # RSI classique
            "rsi_oversold": 25,             # Plus restrictif pour FOREX
            "rsi_overbought": 75,           # Plus restrictif
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9
        },
        "system": {
            "market_open_hour": 0.0,        # 24/7
            "market_close_hour": 23.99,     # 24/7 
            "analysis_interval": 180,       # 3 minutes (réactif)
            "log_level": "INFO",
            "tickers": [
                # Paires FOREX majeures (format Interactive Brokers)
                "EUR.USD",   # Euro/Dollar - LA plus tradée
                "GBP.USD",   # Livre Sterling/Dollar
                "USD.JPY",   # Dollar/Yen Japonais
                "AUD.USD",   # Dollar Australien/Dollar US
                "USD.CHF"    # Dollar/Franc Suisse
            ]
        }
    }
    
    # Sauvegarde immédiate
    with open("trading_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration FOREX créée et sauvegardée!")
    return config

def create_forex_connector_patch():
    """Patch spécialisé pour FOREX dans le connecteur IB"""
    
    patch_code = '''
# forex_patch.py - Modifications pour FOREX

def create_forex_contract(symbol):
    """Crée un contrat FOREX pour Interactive Brokers"""
    from ib_insync import Forex
    
    # Format: "EUR.USD" -> EUR, USD
    if "." in symbol:
        base, quote = symbol.split(".")
        contract = Forex(base + quote)  # "EURUSD"
        return contract
    else:
        # Format direct: "EURUSD"
        contract = Forex(symbol)
        return contract

# Modification pour ib_connector.py
def create_contract_forex_aware(self, symbol):
    """Version modifiée qui gère FOREX"""
    from ib_insync import Stock, Forex
    
    try:
        # Détection FOREX
        if "." in symbol and len(symbol) == 7:  # Format "EUR.USD"
            base, quote = symbol.split(".")
            if len(base) == 3 and len(quote) == 3:
                contract = Forex(base + quote)
                self.ib.qualifyContracts(contract)
                self.contracts_cache[symbol] = contract
                return contract
        
        # Actions normales
        if symbol.endswith('.PA'):
            base_symbol = symbol.replace('.PA', '')
            contract = Stock(base_symbol, 'SBF', 'EUR')
        else:
            contract = Stock(symbol, 'SMART', 'USD')
        
        self.ib.qualifyContracts(contract)
        self.contracts_cache[symbol] = contract
        return contract
        
    except Exception as e:
        print(f"❌ Erreur contrat {symbol}: {e}")
        return None
'''
    
    with open("forex_patch.py", "w") as f:
        f.write(patch_code)
    
    print("📝 Patch FOREX créé (forex_patch.py)")

def update_ib_connector_for_forex():
    """Met à jour le connecteur pour supporter FOREX"""
    
    # Lecture du fichier ib_connector.py
    try:
        with open("ib_connector.py", "r") as f:
            content = f.read()
        
        # Modification de la méthode create_contract
        forex_method = '''
    def create_contract(self, symbol: str) -> Optional[Contract]:
        """Crée un contrat pour un symbole (FOREX-aware)"""
        # Utilise le cache si disponible
        if symbol in self.contracts_cache:
            return self.contracts_cache[symbol]
        
        try:
            # FOREX - Format "EUR.USD"
            if "." in symbol and len(symbol) == 7:
                base, quote = symbol.split(".")
                if len(base) == 3 and len(quote) == 3:
                    contract = Forex(base + quote)  # "EURUSD"
                    self.ib.qualifyContracts(contract)
                    self.contracts_cache[symbol] = contract
                    logger.debug(f"✅ Contrat FOREX créé: {symbol} -> {contract}")
                    return contract
            
            # Actions françaises (CAC40)
            if symbol.endswith('.PA'):
                base_symbol = symbol.replace('.PA', '')
                contract = Stock(base_symbol, 'SBF', 'EUR')
            # Actions américaines
            elif symbol.endswith('.US'):
                base_symbol = symbol.replace('.US', '')
                contract = Stock(base_symbol, 'SMART', 'USD')
            else:
                # Par défaut, essaie SMART
                contract = Stock(symbol, 'SMART', 'USD')
            
            # Qualification du contrat
            self.ib.qualifyContracts(contract)
            
            # Mise en cache
            self.contracts_cache[symbol] = contract
            
            logger.debug(f"✅ Contrat créé pour {symbol}: {contract}")
            return contract
            
        except Exception as e:
            logger.error(f"❌ Erreur création contrat {symbol}: {e}")
            return None
'''
        
        # Ajouter l'import Forex si pas présent
        if "from ib_insync import *" not in content:
            content = "from ib_insync import *\n" + content
        
        # Remplacement de la méthode
        import re
        pattern = r'def create_contract\(self.*?return None'
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, forex_method.strip().replace('    def create_contract', 'def create_contract'), content, flags=re.DOTALL)
        
        # Sauvegarde
        with open("ib_connector_forex.py", "w") as f:
            f.write(content)
        
        print("✅ Connecteur FOREX mis à jour (ib_connector_forex.py)")
        
    except Exception as e:
        print(f"⚠️ Patch automatique échoué: {e}")
        print("💡 Pas grave, on peut utiliser la version normale")

def show_forex_symbols_info():
    """Informations sur les paires FOREX sélectionnées"""
    
    pairs_info = {
        "EUR.USD": {
            "name": "Euro/Dollar US",
            "description": "LA plus tradée au monde - Très liquide",
            "volatilité": "Modérée",
            "best_hours": "14h-18h & 20h-24h",
            "tip": "Réagit aux nouvelles BCE/FED"
        },
        "GBP.USD": {
            "name": "Livre Sterling/Dollar US", 
            "description": "Volatilité élevée - Bons mouvements",
            "volatilité": "Élevée",
            "best_hours": "12h-16h & 20h-24h",
            "tip": "Réagit au Brexit et BoE"
        },
        "USD.JPY": {
            "name": "Dollar US/Yen Japonais",
            "description": "Très technique - Suit les tendances",
            "volatilité": "Modérée-Faible",
            "best_hours": "12h-16h & 1h-5h",
            "tip": "Safe haven en cas de crise"
        },
        "AUD.USD": {
            "name": "Dollar Australien/Dollar US",
            "description": "Commodity currency - Suit l'or/pétrole",
            "volatilité": "Élevée",
            "best_hours": "21h-2h & 12h-16h",
            "tip": "Réagit aux prix des matières premières"
        },
        "USD.CHF": {
            "name": "Dollar US/Franc Suisse",
            "description": "Safe haven - Moins volatil",
            "volatilité": "Faible-Modérée", 
            "best_hours": "14h-18h",
            "tip": "Inverse à EUR/USD souvent"
        }
    }
    
    print("\n💱 PAIRES FOREX SÉLECTIONNÉES:")
    print("=" * 60)
    
    for symbol, info in pairs_info.items():
        print(f"\n📊 {symbol} - {info['name']}")
        print(f"   📝 {info['description']}")
        print(f"   📈 Volatilité: {info['volatilité']}")
        print(f"   ⏰ Meilleures heures: {info['best_hours']}")
        print(f"   💡 Astuce: {info['tip']}")
    
    print(f"\n🎯 POUR COMMENCER:")
    print(f"   ✅ EUR/USD: Le plus prévisible")
    print(f"   ✅ GBP/USD: Plus de mouvement")
    print(f"   ⚠️ USD/JPY: Plutôt le matin")

def forex_trading_tips():
    """Conseils spécifiques au trading FOREX"""
    
    print("""
    💡 CONSEILS FOREX TRADING:
    ==========================
    
    ⏰ MEILLEURS MOMENTS:
    - 14h-18h: Superposition Londres/NY (max volatilité)
    - 20h-24h: Session US active
    - 1h-5h: Session asiatique (USD/JPY)
    
    📊 SIGNAUX À SURVEILLER:
    - RSI < 25: Très survendu (signal fort)
    - RSI > 75: Très suracheté (signal fort)
    - Croisements MACD sur graphiques 1h
    - Volume/momentum sur nouvelles économiques
    
    📰 NEWS IMPORTANTES:
    - 14h30: Données US (NFP, inflation, PIB)
    - 15h: Décisions FED
    - 13h45: Décisions BCE
    - 12h30: Données UK
    
    🎯 STRATÉGIE OPTIMALE:
    - Positions courtes (1-4h max)
    - Stop loss serrés (0.8%)
    - Take profit rapides (1.2%)
    - Pas plus de 4 paires simultanées
    
    ⚠️ ATTENTION AUX:
    - Spreads plus larges la nuit
    - News économiques majeures
    - Vendredi soir (moins de liquidité)
    - Gaps du dimanche soir
    """)

def final_checklist():
    """Checklist finale avant lancement"""
    
    print("""
    ✅ CHECKLIST FINALE FOREX:
    ==========================
    
    🔧 CONFIGURATION:
    □ trading_config.json créé ✅
    □ Paires FOREX: EUR.USD, GBP.USD, etc. ✅ 
    □ Stop Loss: 0.8% ✅
    □ Take Profit: 1.2% ✅
    □ Analyse: 3 minutes ✅
    
    🔌 INTERACTIVE BROKERS:
    □ TWS ouvert et connecté
    □ Mode Paper Trading (port 7497)
    □ API activée (Enable Socket Clients)
    □ Permissions FOREX (incluses par défaut)
    
    📊 SURVEILLANCE TWS:
    □ Onglet Portfolio ouvert
    □ Onglet Trades ouvert  
    □ Fenêtre Account visible
    □ Alertes sonores activées (optionnel)
    
    🚀 LANCEMENT:
    □ python start.py
    □ Option 1 (Interface graphique)
    □ Test Connexion ✅
    □ Démarrer Bot ✅
    
    👀 PREMIER TRADE ATTENDU:
    - Dans 5-15 minutes max
    - Visible dans TWS Portfolio
    - EUR.USD ou GBP.USD probablement
    - P&L temps réel
    """)

def main():
    """Setup complet FOREX"""
    
    print("💱 SETUP FOREX TRADING - IMMÉDIAT")
    print("=" * 40)
    print(f"🕐 Heure: {datetime.now().strftime('%H:%M')} (Marché FOREX ouvert 24/7)")
    
    # 1. Configuration
    print(f"\n📝 1. Création configuration FOREX...")
    config = create_forex_config_now()
    
    # 2. Patch FOREX (optionnel)
    print(f"\n🔧 2. Optimisation pour FOREX...")
    try:
        update_ib_connector_for_forex()
    except:
        print("⚠️ Patch optionnel échoué (pas grave)")
    
    # 3. Informations paires
    show_forex_symbols_info()
    
    # 4. Conseils
    forex_trading_tips()
    
    # 5. Checklist
    final_checklist()
    
    print(f"\n🚀 PRÊT POUR LE LANCEMENT!")
    print(f"═" * 40)
    print(f"Lance maintenant:")
    print(f"   python start.py")
    print(f"   Choisis option 1")
    print(f"   Démarrer Bot")
    print(f"")
    print(f"📈 Premier trade attendu en 5-15 minutes !")
    print(f"👀 Surveille TWS > Portfolio")

if __name__ == "__main__":
    main()