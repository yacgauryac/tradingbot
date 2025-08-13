# minimal_bot.py - Bot ultra-simple sans problèmes asyncio

from ib_insync import *
import time
import logging

# Configuration simple
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinimalBot:
    """Bot minimal qui marche à coup sûr"""
    
    def __init__(self):
        self.ib = IB()
        
    def connect(self):
        """Connexion simple"""
        try:
            print("🔌 Connexion à IB...")
            self.ib.connect('127.0.0.1', 7497, clientId=1)
            print("✅ Connecté!")
            return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def get_data_simple(self, symbol):
        """Récupération données SANS asyncio"""
        try:
            print(f"📊 Récupération {symbol}...")
            
            # Création contrat simple
            if symbol == 'AAPL':
                contract = Stock('AAPL', 'SMART', 'USD')
            elif symbol == 'MSFT':
                contract = Stock('MSFT', 'SMART', 'USD')
            elif symbol == 'GOOGL':
                contract = Stock('GOOGL', 'SMART', 'USD')
            elif symbol == 'TSLA':
                contract = Stock('TSLA', 'SMART', 'USD')
            else:
                contract = Stock(symbol, 'SMART', 'USD')
            
            # Qualification
            self.ib.qualifyContracts(contract)
            
            # Données historiques (SYNCHRONE)
            bars = self.ib.reqHistoricalData(
                contract, '', '10 D', '1 day', 'TRADES', 1, 1, False
            )
            
            if bars:
                print(f"✅ {symbol}: {len(bars)} barres récupérées")
                # Dernier prix
                last_price = bars[-1].close
                print(f"💰 Prix {symbol}: ${last_price:.2f}")
                
                # Calcul RSI simple (derniers 14 jours)
                closes = [bar.close for bar in bars[-14:]]
                rsi = self.calculate_simple_rsi(closes)
                print(f"📈 RSI {symbol}: {rsi:.1f}")
                
                # Signal simple
                if rsi < 30:
                    print(f"🟢 SIGNAL ACHAT {symbol} (RSI: {rsi:.1f})")
                elif rsi > 70:
                    print(f"🔴 SIGNAL VENTE {symbol} (RSI: {rsi:.1f})")
                else:
                    print(f"⏸️ PAS DE SIGNAL {symbol} (RSI: {rsi:.1f})")
                
                return True
            else:
                print(f"❌ Pas de données pour {symbol}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur {symbol}: {e}")
            return False
    
    def calculate_simple_rsi(self, prices, period=14):
        """Calcul RSI simple"""
        if len(prices) < period:
            return 50  # Neutre si pas assez de données
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def run_once(self):
        """Un seul cycle d'analyse"""
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        
        for symbol in symbols:
            self.get_data_simple(symbol)
            time.sleep(1)  # Pause entre symboles
            print("-" * 40)
    
    def disconnect(self):
        """Déconnexion"""
        if self.ib.isConnected():
            self.ib.disconnect()
            print("🔌 Déconnecté")

def main():
    print("🤖 BOT MINIMAL - TEST SIMPLE")
    print("=" * 40)
    
    bot = MinimalBot()
    
    try:
        if bot.connect():
            print("🚀 Lancement analyse...")
            bot.run_once()
            print("\n✅ ANALYSE TERMINÉE!")
            print("Si ça marche = le problème vient de l'asyncio complexe")
            print("Si ça marche pas = problème plus profond avec IB")
        else:
            print("❌ Connexion impossible")
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        bot.disconnect()

if __name__ == "__main__":
    main()