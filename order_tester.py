# order_tester.py - Test ordres simulés + stratégie de sortie

from ib_insync import *
import pandas as pd
import time
from datetime import datetime, timedelta

class OrderTester:
    """Test ordres simulés avec stratégie de sortie"""
    
    def __init__(self):
        self.ib = IB()
        self.positions = {}  # Suivi positions ouvertes
        self.orders_log = []  # Historique ordres
        
        # Paramètres stratégie de sortie
        self.exit_rules = {
            'profit_target': 0.05,    # +5% profit
            'stop_loss': -0.08,       # -8% perte max
            'max_hold_days': 10,      # 10 jours max
            'rsi_exit': 70            # Sortie si RSI > 70
        }
        
    def connect(self):
        """Connexion pour tests"""
        try:
            print("🔌 Connexion pour tests ordres...")
            self.ib.connect('127.0.0.1', 7497, clientId=3)
            return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def test_buy_order(self, symbol, quantity=100, order_type='MKT'):
        """Test ordre d'achat simulé"""
        print(f"\n🛒 TEST ORDRE ACHAT - {symbol}")
        print("=" * 40)
        
        try:
            # Contrat
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Prix actuel
            ticker = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(2)  # Attendre prix
            
            if ticker.last and ticker.last > 0:
                current_price = ticker.last
            else:
                # Prix de la dernière barre si pas de temps réel
                bars = self.ib.reqHistoricalData(contract, '', '1 D', '1 day', 'TRADES', 1, 1, False)
                current_price = bars[-1].close
            
            print(f"💰 Prix actuel {symbol}: ${current_price:.2f}")
            
            # Calcul taille position (par exemple : $1000 max par position)
            max_investment = 1000
            calculated_qty = int(max_investment / current_price)
            final_qty = min(quantity, calculated_qty)
            
            print(f"📊 Quantité calculée: {final_qty} actions (${final_qty * current_price:.2f})")
            
            # Création ordre
            if order_type == 'MKT':
                order = MarketOrder('BUY', final_qty)
                print("📝 Ordre: MARKET BUY")
            else:
                # Ordre limite à -0.5% du prix actuel
                limit_price = current_price * 0.995
                order = LimitOrder('BUY', final_qty, limit_price)
                print(f"📝 Ordre: LIMIT BUY à ${limit_price:.2f}")
            
            # TEST : Simulation sans passer l'ordre réel
            print(f"\n🧪 SIMULATION ORDRE (pas d'ordre réel passé)")
            print(f"   Symbole: {symbol}")
            print(f"   Action: BUY")
            print(f"   Quantité: {final_qty}")
            print(f"   Prix estimé: ${current_price:.2f}")
            print(f"   Coût total: ${final_qty * current_price:.2f}")
            
            # Choix utilisateur
            print(f"\n🤔 Voulez-vous VRAIMENT passer cet ordre simulé ?")
            choice = input("   (y/n) [n]: ").strip().lower()
            
            if choice == 'y':
                # ORDRE RÉEL (mais en mode simulé TWS)
                trade = self.ib.placeOrder(contract, order)
                print(f"✅ ORDRE PASSÉ: {trade.order.action} {trade.order.totalQuantity} {symbol}")
                
                # Enregistrement position
                self.positions[symbol] = {
                    'quantity': final_qty,
                    'entry_price': current_price,
                    'entry_date': datetime.now(),
                    'order_id': trade.order.orderId
                }
                
                # Log
                self.orders_log.append({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'action': 'BUY',
                    'quantity': final_qty,
                    'price': current_price,
                    'status': 'PLACED'
                })
                
                return True
            else:
                print("❌ Ordre annulé par l'utilisateur")
                return False
                
        except Exception as e:
            print(f"❌ Erreur ordre {symbol}: {e}")
            return False
    
    def check_exit_conditions(self, symbol):
        """Vérification conditions de sortie"""
        if symbol not in self.positions:
            return False, "Aucune position"
        
        try:
            position = self.positions[symbol]
            
            # Prix actuel
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            bars = self.ib.reqHistoricalData(contract, '', '1 D', '1 day', 'TRADES', 1, 1, False)
            current_price = bars[-1].close
            
            # Calculs
            entry_price = position['entry_price']
            pnl_pct = (current_price - entry_price) / entry_price
            days_held = (datetime.now() - position['entry_date']).days
            
            # RSI actuel
            df = self.get_recent_data(contract, 30)
            current_rsi = self.calculate_rsi(df['close']).iloc[-1]
            
            print(f"\n📊 CHECK SORTIE - {symbol}")
            print(f"   Prix entrée: ${entry_price:.2f}")
            print(f"   Prix actuel: ${current_price:.2f}")
            print(f"   P&L: {pnl_pct:+.1%}")
            print(f"   Jours détenu: {days_held}")
            print(f"   RSI actuel: {current_rsi:.1f}")
            
            # Conditions de sortie
            reasons = []
            should_exit = False
            
            if pnl_pct >= self.exit_rules['profit_target']:
                should_exit = True
                reasons.append(f"Profit target atteint ({pnl_pct:+.1%})")
            
            if pnl_pct <= self.exit_rules['stop_loss']:
                should_exit = True
                reasons.append(f"Stop loss atteint ({pnl_pct:+.1%})")
            
            if days_held >= self.exit_rules['max_hold_days']:
                should_exit = True
                reasons.append(f"Durée max atteinte ({days_held} jours)")
            
            if current_rsi >= self.exit_rules['rsi_exit']:
                should_exit = True
                reasons.append(f"RSI surachat ({current_rsi:.1f})")
            
            return should_exit, reasons
            
        except Exception as e:
            return False, [f"Erreur: {e}"]
    
    def execute_sell_order(self, symbol):
        """Exécution ordre de vente"""
        if symbol not in self.positions:
            print(f"❌ Aucune position pour {symbol}")
            return False
        
        try:
            position = self.positions[symbol]
            quantity = position['quantity']
            
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Ordre de vente market
            order = MarketOrder('SELL', quantity)
            trade = self.ib.placeOrder(contract, order)
            
            print(f"🔴 ORDRE VENTE PASSÉ: SELL {quantity} {symbol}")
            
            # Mise à jour log
            self.orders_log.append({
                'timestamp': datetime.now(),
                'symbol': symbol,
                'action': 'SELL',
                'quantity': quantity,
                'status': 'PLACED'
            })
            
            # Suppression position
            del self.positions[symbol]
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur vente {symbol}: {e}")
            return False
    
    def monitor_positions(self):
        """Surveillance des positions ouvertes"""
        if not self.positions:
            print("📊 Aucune position à surveiller")
            return
        
        print(f"\n👁️ SURVEILLANCE POSITIONS ({len(self.positions)} actives)")
        print("=" * 50)
        
        for symbol in list(self.positions.keys()):
            should_exit, reasons = self.check_exit_conditions(symbol)
            
            if should_exit:
                print(f"🚨 SIGNAL SORTIE {symbol}:")
                for reason in reasons:
                    print(f"   - {reason}")
                
                choice = input(f"   Vendre {symbol} maintenant ? (y/n): ").strip().lower()
                if choice == 'y':
                    self.execute_sell_order(symbol)
            else:
                print(f"✅ {symbol}: Position maintenue")
    
    def get_recent_data(self, contract, days=30):
        """Données récentes pour calculs"""
        bars = self.ib.reqHistoricalData(contract, '', f'{days} D', '1 day', 'TRADES', 1, 1, False)
        
        df = pd.DataFrame([{
            'date': bar.date,
            'close': bar.close
        } for bar in bars])
        
        return df
    
    def calculate_rsi(self, prices, window=14):
        """Calcul RSI"""
        delta = prices.diff()
        gains = delta.where(delta > 0, 0).rolling(window).mean()
        losses = (-delta.where(delta < 0, 0)).rolling(window).mean()
        rs = gains / losses
        return 100 - (100 / (1 + rs))
    
    def show_portfolio_summary(self):
        """Résumé du portefeuille"""
        print(f"\n💼 RÉSUMÉ PORTEFEUILLE")
        print("=" * 30)
        print(f"Positions actives: {len(self.positions)}")
        print(f"Ordres passés: {len(self.orders_log)}")
        
        if self.positions:
            total_invested = 0
            for symbol, pos in self.positions.items():
                invested = pos['quantity'] * pos['entry_price']
                total_invested += invested
                print(f"   {symbol}: {pos['quantity']} actions @ ${pos['entry_price']:.2f}")
            
            print(f"Total investi: ${total_invested:.2f}")
    
    def disconnect(self):
        if self.ib.isConnected():
            self.ib.disconnect()

def main():
    """Test complet ordres + surveillance"""
    print("🛒 TEST ORDRES SIMULÉS + STRATÉGIE SORTIE")
    print("=" * 50)
    
    tester = OrderTester()
    
    try:
        if not tester.connect():
            return
        
        # Test sur les 3 signaux forts
        strong_signals = ['CE', 'ACVA', 'LBRT']
        
        print("🎯 ACTIONS DÉTECTÉES AVEC SIGNAUX FORTS:")
        for i, symbol in enumerate(strong_signals, 1):
            print(f"   {i}. {symbol}")
        
        choice = input(f"\nChoisissez l'action à tester (1-3) ou 'all' [1]: ").strip() or "1"
        
        if choice == 'all':
            # Test sur toutes les actions
            for symbol in strong_signals:
                success = tester.test_buy_order(symbol, 100)
                if success:
                    print(f"✅ Ordre {symbol} passé")
                time.sleep(2)
        else:
            # Test sur une action
            try:
                idx = int(choice) - 1
                symbol = strong_signals[idx]
                tester.test_buy_order(symbol, 100)
            except:
                print("❌ Choix invalide")
        
        # Surveillance si positions ouvertes
        if tester.positions:
            print(f"\n⏰ SIMULATION SURVEILLANCE CONTINUE")
            print("Surveillance toutes les 30 secondes (Ctrl+C pour arrêter)")
            
            try:
                while tester.positions:
                    time.sleep(30)
                    tester.monitor_positions()
                    tester.show_portfolio_summary()
            except KeyboardInterrupt:
                print(f"\n🛑 Surveillance arrêtée")
        
        tester.show_portfolio_summary()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        tester.disconnect()

if __name__ == "__main__":
    main()