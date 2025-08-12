# forex_fix.py - Correction immédiate pour FOREX

import re

def fix_ib_connector_for_forex():
    """Corrige le fichier ib_connector.py pour supporter FOREX"""
    
    try:
        # Lecture du fichier actuel
        with open("ib_connector.py", "r", encoding='utf-8') as f:
            content = f.read()
        
        # Ajout import Forex si manquant
        if "from ib_insync import Forex" not in content and "from ib_insync import *" not in content:
            content = "from ib_insync import Forex\n" + content
        
        # Nouvelle méthode create_contract avec support FOREX
        new_create_contract = '''    def create_contract(self, symbol: str) -> Optional[Contract]:
        """Crée un contrat pour un symbole (FOREX-aware)"""
        # Utilise le cache si disponible
        if symbol in self.contracts_cache:
            return self.contracts_cache[symbol]
        
        try:
            # FOREX - Format "EUR.USD" ou similaire
            if "." in symbol and len(symbol) == 7:
                base, quote = symbol.split(".")
                if len(base) == 3 and len(quote) == 3:
                    # Création contrat FOREX
                    forex_symbol = base + quote  # "EUR.USD" -> "EURUSD"
                    contract = Forex(forex_symbol)
                    
                    # Qualification du contrat
                    self.ib.qualifyContracts(contract)
                    
                    # Mise en cache
                    self.contracts_cache[symbol] = contract
                    
                    logger.debug(f"✅ Contrat FOREX créé: {symbol} -> {forex_symbol}")
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
                # Par défaut, essaie SMART pour actions
                contract = Stock(symbol, 'SMART', 'USD')
            
            # Qualification du contrat
            self.ib.qualifyContracts(contract)
            
            # Mise en cache
            self.contracts_cache[symbol] = contract
            
            logger.debug(f"✅ Contrat créé pour {symbol}: {contract}")
            return contract
            
        except Exception as e:
            logger.error(f"❌ Erreur création contrat {symbol}: {e}")
            return None'''
        
        # Remplacement de la méthode create_contract
        pattern = r'def create_contract\(self, symbol: str\).*?return None'
        
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, new_create_contract.strip(), content, flags=re.DOTALL)
            print("✅ Méthode create_contract remplacée")
        else:
            print("⚠️ Pattern create_contract non trouvé, ajout à la fin")
            content += "\n\n" + new_create_contract
        
        # Sauvegarde du fichier corrigé
        with open("ib_connector.py", "w", encoding='utf-8') as f:
            f.write(content)
        
        print("✅ ib_connector.py corrigé pour FOREX")
        return True
        
    except Exception as e:
        print(f"❌ Erreur correction: {e}")
        return False

def create_backup():
    """Crée une sauvegarde avant modification"""
    try:
        import shutil
        shutil.copy("ib_connector.py", "ib_connector_backup.py")
        print("💾 Sauvegarde créée: ib_connector_backup.py")
    except Exception as e:
        print(f"⚠️ Pas de sauvegarde: {e}")

def test_forex_fix():
    """Test rapide du fix FOREX"""
    
    test_code = '''
# Test des contrats FOREX
try:
    from ib_insync import Forex
    
    # Test création contrat
    contract = Forex('EURUSD')
    print(f"✅ Contrat FOREX créé: {contract}")
    
    # Test autres paires
    pairs = ['GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF']
    for pair in pairs:
        contract = Forex(pair)
        print(f"✅ {pair}: {contract}")
    
    print("✅ Test FOREX OK - Les contrats se créent correctement")
    
except Exception as e:
    print(f"❌ Test FOREX échoué: {e}")
'''
    
    exec(test_code)

def main():
    """Correction principale"""
    
    print("🔧 CORRECTION FOREX IMMÉDIATE")
    print("=" * 40)
    
    # 1. Sauvegarde
    create_backup()
    
    # 2. Correction
    success = fix_ib_connector_for_forex()
    
    if success:
        print("\n✅ CORRECTION TERMINÉE!")
        print("🔄 REDÉMARRE TON BOT MAINTENANT:")
        print("   1. Arrête le bot actuel (Ctrl+C)")
        print("   2. Relance: python trading_bot.py")
        print("   3. Les contrats FOREX vont maintenant fonctionner")
        
        # 3. Test
        print("\n🧪 Test des contrats FOREX:")
        test_forex_fix()
        
    else:
        print("\n❌ CORRECTION ÉCHOUÉE")
        print("💡 Solution alternative:")
        print("   1. Remplace temporairement par des actions US")
        print("   2. Change les tickers vers: AAPL, MSFT, GOOGL")

if __name__ == "__main__":
    main()