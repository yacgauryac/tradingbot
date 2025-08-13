# simple_order_test.py - Test ordres simple sans abonnement données temps réel

from ib_insync import *
import time
from datetime import datetime

class SimpleOrderTest:
    """Test ordres simple avec données historiques seulement"""
    
    def __init__(self):
        self.ib = IB()
        
    def connect(self):
        """Connexion"""
        try:
            print("🔌 Connexion pour test ordres...")
            self.ib.connect('127.0.0.1', 7497, clientId=4)
            return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def get_price_info(self, symbol):
        """Prix via données historiques (gratuit)"""
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # 5 derniers jours pour avoir le contexte
            bars = self.ib.reqHistoricalData(
                contract, '', '5 D', '1 day', 'TRADES', 1, 1, False
            )
            
            if not bars:
                return None
            
            current = bars[-1]
            prev = bars[-2] if len(bars) > 1 else current
            
            price_change = ((current.close - prev.close) / prev.close * 100)
            
            return {
                'symbol': symbol,
                'price': current.close,
                'change_pct': price_change,
                'volume': current.volume,
                'date': current.date,
                'high': current.high,
                'low': current.low,
                'contract': contract
            }
            
        except Exception as e:
            print(f"❌ Erreur prix {symbol}: {e}")
            return None
    
    def test_buy_order_ce(self):
        """Test spécifique sur CE"""
        print("🛒 TEST ORDRE D'ACHAT - CE (Celanese)")
        print("=" * 45)
        
        # Info prix
        price_info = self.get_price_info('CE')
        if not price_info:
            print("❌ Impossible de récupérer le prix CE")
            return False
        
        print(f"💰 CE: ${price_info['price']:.2f} ({price_info['change_pct']:+.1f}%)")
        print(f"📊 Volume: {price_info['volume']:,}")
        print(f"📅 Données du: {price_info['date'].strftime('%Y-%m-%d')}")
        print(f"📈 Range: ${price_info['low']:.2f} - ${price_info['high']:.2f}")
        
        # Rappel du signal
        print(f"\n🎯 RAPPEL SIGNAL CE:")
        print(f"   RSI: 20.7 (très survendu)")
        print(f"   Confiance: 31.3%")
        print(f"   Recommandation: ACHAT FORT")
        
        # Calcul position
        max_investment = 1000  # $1000 max par position
        quantity = int(max_investment / price_info['price'])
        total_cost = quantity * price_info['price']
        
        print(f"\n💼 CALCUL POSITION:")
        print(f"   Budget max: ${max_investment}")
        print(f"   Quantité: {quantity} actions")
        print(f"   Coût total: ${total_cost:.2f}")
        
        # Stratégie de sortie
        profit_target = price_info['price'] * 1.05  # +5%
        stop_loss = price_info['price'] * 0.92      # -8%
        
        print(f"\n🎯 STRATÉGIE DE SORTIE:")
        print(f"   Profit target: ${profit_target:.2f} (+5%)")
        print(f"   Stop loss: ${stop_loss:.2f} (-8%)")
        print(f"   Durée max: 10 jours")
        
        # Confirmation utilisateur
        print(f"\n❓ CONFIRMER L'ORDRE ?")
        print(f"   BUY {quantity} CE @ ~${price_info['price']:.2f}")
        print(f"   Coût: ${total_cost:.2f}")
        
        choice = input(f"   Confirmer ? (y/n) [n]: ").strip().lower()
        
        if choice == 'y':
            return self.place_buy_order(price_info['contract'], quantity, price_info['price'])
        else:
            print("❌ Ordre annulé")
            return False
    
    def place_buy_order(self, contract, quantity, estimated_price):
        """Passage ordre d'achat réel"""
        try:
            print(f"\n🚀 PASSAGE ORDRE...")
            
            # Ordre Market (exécution immédiate)
            order = MarketOrder('BUY', quantity)
            
            # Passage ordre
            trade = self.ib.placeOrder(contract, order)
            
            print(f"✅ ORDRE PASSÉ!")
            print(f"   Order ID: {trade.order.orderId}")
            print(f"   Status: {trade.orderStatus.status}")
            print(f"   Action: {trade.order.action}")
            print(f"   Quantité: {trade.order.totalQuantity}")
            
            # Suivi ordre pendant 30 secondes
            print(f"\n⏳ Suivi de l'ordre (30 sec)...")
            for i in range(6):
                self.ib.sleep(5)
                print(f"   Status: {trade.orderStatus.status}")
                
                if trade.orderStatus.status in ['Filled', 'Cancelled']:
                    break
            
            if trade.orderStatus.status == 'Filled':
                fill_price = trade.orderStatus.avgFillPrice or estimated_price
                print(f"\n🎉 ORDRE EXÉCUTÉ!")
                print(f"   Prix d'exécution: ${fill_price:.2f}")
                print(f"   Quantité: {trade.orderStatus.filled}")
                print(f"   Coût total: ${fill_price * trade.orderStatus.filled:.2f}")
                
                # Sauvegarde pour suivi
                with open('position_ce.txt', 'w') as f:
                    f.write(f"Symbol: CE\n")
                    f.write(f"Quantity: {trade.orderStatus.filled}\n")
                    f.write(f"Entry_Price: {fill_price:.2f}\n")
                    f.write(f"Entry_Date: {datetime.now()}\n")
                    f.write(f"Order_ID: {trade.order.orderId}\n")
                
                print(f"💾 Position sauvegardée dans 'position_ce.txt'")
                return True
            else:
                print(f"⚠️ Ordre non exécuté: {trade.orderStatus.status}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur passage ordre: {e}")
            return False
    
    def check_existing_positions(self):
        """Vérification positions existantes"""
        try:
            positions = self.ib.positions()
            
            if positions:
                print(f"📊 POSITIONS EXISTANTES:")
                for pos in positions:
                    pnl = pos.unrealizedPNL
                    print(f"   {pos.contract.symbol}: {pos.position} @ ${pos.avgCost:.2f}")
                    print(f"   P&L: ${pnl:.2f}")
            else:
                print(f"📊 Aucune position existante")
                
        except Exception as e:
            print(f"❌ Erreur positions: {e}")
    
    def disconnect(self):
        if self.ib.isConnected():
            self.ib.disconnect()

def main():
    """Test ordre CE"""
    print("🧪 TEST ORDRE SIMPLE - CE (CELANESE)")
    print("=" * 50)
    
    tester = SimpleOrderTest()
    
    try:
        if not tester.connect():
            print("❌ Connexion impossible")
            return
        
        # Vérification positions existantes
        tester.check_existing_positions()
        
        # Test ordre CE
        success = tester.test_buy_order_ce()
        
        if success:
            print(f"\n✅ TEST RÉUSSI!")
            print(f"🎯 Prochaine étape: surveillance position")
            print(f"💡 Utilisez 'position_monitor.py' pour suivre")
        else:
            print(f"\n❌ Test échoué ou annulé")
            
    except KeyboardInterrupt:
        print(f"\n🛑 Test interrompu")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        tester.disconnect()

if __name__ == "__main__":
    main()