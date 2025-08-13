# position_monitor.py - Surveillance position CE

from ib_insync import *
import time
from datetime import datetime, timedelta
import os

class PositionMonitor:
    """Surveillance position CE avec règles de sortie automatiques"""
    
    def __init__(self):
        self.ib = IB()
        self.position_data = {}
        self.monitoring = True
        
        # Règles de sortie
        self.exit_rules = {
            'profit_target': 0.05,    # +5%
            'stop_loss': -0.08,       # -8%
            'max_hold_days': 10,      # 10 jours max
            'rsi_exit': 70            # RSI > 70
        }
        
    def connect(self):
        """Connexion pour monitoring"""
        try:
            print("🔌 Connexion pour surveillance...")
            self.ib.connect('127.0.0.1', 7497, clientId=5)
            return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def load_position_file(self):
        """Chargement données position depuis fichier"""
        try:
            if not os.path.exists('position_ce.txt'):
                print("❌ Fichier position_ce.txt introuvable")
                return False
            
            with open('position_ce.txt', 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                if ':' in line:
                    key, value = line.strip().split(': ', 1)
                    self.position_data[key.lower()] = value
            
            # Conversion types (gestion des floats)
            self.position_data['quantity'] = int(float(self.position_data['quantity']))
            self.position_data['entry_price'] = float(self.position_data['entry_price'])
            self.position_data['entry_date'] = datetime.strptime(
                self.position_data['entry_date'].split('.')[0], 
                '%Y-%m-%d %H:%M:%S'
            )
            
            print(f"✅ Position chargée:")
            print(f"   Symbole: {self.position_data['symbol']}")
            print(f"   Quantité: {self.position_data['quantity']}")
            print(f"   Prix d'entrée: ${self.position_data['entry_price']:.2f}")
            print(f"   Date d'entrée: {self.position_data['entry_date'].strftime('%Y-%m-%d %H:%M')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lecture position: {e}")
            return False
    
    def get_current_price_and_rsi(self):
        """Prix actuel et RSI de CE"""
        try:
            contract = Stock('CE', 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Prix actuel
            bars = self.ib.reqHistoricalData(
                contract, '', '1 D', '1 day', 'TRADES', 1, 1, False
            )
            current_price = bars[-1].close
            
            # Données pour RSI (30 derniers jours)
            bars_rsi = self.ib.reqHistoricalData(
                contract, '', '30 D', '1 day', 'TRADES', 1, 1, False
            )
            
            if len(bars_rsi) >= 14:
                closes = [bar.close for bar in bars_rsi]
                current_rsi = self.calculate_rsi(closes)
            else:
                current_rsi = 50  # Neutre si pas assez de données
            
            return current_price, current_rsi
            
        except Exception as e:
            print(f"❌ Erreur prix/RSI: {e}")
            return None, None
    
    def calculate_rsi(self, prices, period=14):
        """Calcul RSI simple"""
        if len(prices) < period + 1:
            return 50
        
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
    
    def check_exit_conditions(self, current_price, current_rsi):
        """Vérification conditions de sortie"""
        entry_price = self.position_data['entry_price']
        entry_date = self.position_data['entry_date']
        
        # Calculs P&L
        pnl_pct = (current_price - entry_price) / entry_price
        pnl_dollar = pnl_pct * (self.position_data['quantity'] * entry_price)
        days_held = (datetime.now() - entry_date).days
        
        # Affichage status
        print(f"\n📊 STATUS POSITION CE:")
        print(f"   Prix entrée: ${entry_price:.2f}")
        print(f"   Prix actuel: ${current_price:.2f}")
        print(f"   P&L: {pnl_pct:+.1%} (${pnl_dollar:+.2f})")
        print(f"   RSI actuel: {current_rsi:.1f}")
        print(f"   Jours détenu: {days_held}")
        
        # Vérification conditions de sortie
        exit_signals = []
        should_exit = False
        
        # 1. Profit target
        if pnl_pct >= self.exit_rules['profit_target']:
            should_exit = True
            exit_signals.append(f"🎯 PROFIT TARGET atteint (+{pnl_pct:.1%})")
        
        # 2. Stop loss
        if pnl_pct <= self.exit_rules['stop_loss']:
            should_exit = True
            exit_signals.append(f"🛑 STOP LOSS atteint ({pnl_pct:.1%})")
        
        # 3. Durée max
        if days_held >= self.exit_rules['max_hold_days']:
            should_exit = True
            exit_signals.append(f"⏰ DURÉE MAX atteinte ({days_held} jours)")
        
        # 4. RSI surachat
        if current_rsi >= self.exit_rules['rsi_exit']:
            should_exit = True
            exit_signals.append(f"📈 RSI SURACHAT ({current_rsi:.1f})")
        
        # Niveaux cibles
        profit_target_price = entry_price * (1 + self.exit_rules['profit_target'])
        stop_loss_price = entry_price * (1 + self.exit_rules['stop_loss'])
        
        print(f"\n🎯 NIVEAUX CIBLES:")
        print(f"   Profit target: ${profit_target_price:.2f} ({((profit_target_price/current_price-1)*100):+.1f}%)")
        print(f"   Stop loss: ${stop_loss_price:.2f} ({((stop_loss_price/current_price-1)*100):+.1f}%)")
        
        return should_exit, exit_signals
    
    def execute_sell_order(self):
        """Exécution ordre de vente"""
        try:
            print(f"\n🔴 EXÉCUTION ORDRE DE VENTE...")
            
            contract = Stock('CE', 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            quantity = self.position_data['quantity']
            order = MarketOrder('SELL', quantity)
            
            trade = self.ib.placeOrder(contract, order)
            
            print(f"✅ ORDRE VENTE PASSÉ!")
            print(f"   SELL {quantity} CE")
            print(f"   Order ID: {trade.order.orderId}")
            
            # Suivi ordre
            for i in range(6):
                self.ib.sleep(5)
                print(f"   Status: {trade.orderStatus.status}")
                if trade.orderStatus.status in ['Filled', 'Cancelled']:
                    break
            
            if trade.orderStatus.status == 'Filled':
                fill_price = trade.orderStatus.avgFillPrice
                total_proceeds = fill_price * quantity
                
                entry_cost = self.position_data['entry_price'] * quantity
                total_pnl = total_proceeds - entry_cost
                
                print(f"\n🎉 POSITION FERMÉE!")
                print(f"   Prix de vente: ${fill_price:.2f}")
                print(f"   Produit total: ${total_proceeds:.2f}")
                print(f"   P&L total: ${total_pnl:+.2f}")
                
                # Suppression fichier position
                if os.path.exists('position_ce.txt'):
                    os.remove('position_ce.txt')
                    print(f"🗑️ Fichier position supprimé")
                
                # Sauvegarde historique
                with open('trade_history.txt', 'a') as f:
                    f.write(f"\n--- TRADE FERMÉ {datetime.now()} ---\n")
                    f.write(f"Symbol: CE\n")
                    f.write(f"Entry: ${self.position_data['entry_price']:.2f}\n")
                    f.write(f"Exit: ${fill_price:.2f}\n")
                    f.write(f"Quantity: {quantity}\n")
                    f.write(f"P&L: ${total_pnl:+.2f}\n")
                
                return True
            else:
                print(f"⚠️ Ordre vente non exécuté: {trade.orderStatus.status}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur vente: {e}")
            return False
    
    def monitor_loop(self):
        """Boucle de surveillance principale"""
        print(f"\n👁️ DÉMARRAGE SURVEILLANCE CONTINUE")
        print(f"Vérification toutes les 60 secondes")
        print(f"Ctrl+C pour arrêter\n")
        
        try:
            while self.monitoring:
                current_price, current_rsi = self.get_current_price_and_rsi()
                
                if current_price and current_rsi:
                    should_exit, exit_signals = self.check_exit_conditions(current_price, current_rsi)
                    
                    if should_exit:
                        print(f"\n🚨 SIGNAL DE SORTIE DÉTECTÉ!")
                        for signal in exit_signals:
                            print(f"   {signal}")
                        
                        choice = input(f"\n❓ VENDRE MAINTENANT ? (y/n/auto) [y]: ").strip().lower()
                        
                        if choice in ['', 'y', 'auto']:
                            success = self.execute_sell_order()
                            if success:
                                self.monitoring = False
                                break
                        else:
                            print(f"⏸️ Vente reportée, surveillance continue...")
                    else:
                        print(f"✅ Position maintenue - Prochaine vérif dans 60s")
                else:
                    print(f"❌ Erreur récupération données")
                
                if self.monitoring:
                    print(f"⏳ Attente 60s... ({datetime.now().strftime('%H:%M:%S')})")
                    time.sleep(60)
                    
        except KeyboardInterrupt:
            print(f"\n🛑 Surveillance arrêtée par l'utilisateur")
        except Exception as e:
            print(f"❌ Erreur surveillance: {e}")
    
    def disconnect(self):
        if self.ib.isConnected():
            self.ib.disconnect()

def main():
    """Surveillance position CE"""
    print("👁️ SURVEILLANCE POSITION CE")
    print("=" * 40)
    
    monitor = PositionMonitor()
    
    try:
        if not monitor.connect():
            return
        
        if not monitor.load_position_file():
            return
        
        # Démarrage surveillance
        monitor.monitor_loop()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        monitor.disconnect()

if __name__ == "__main__":
    main()