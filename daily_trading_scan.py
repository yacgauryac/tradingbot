# daily_trading_scan.py - Scan quotidien automatique

from ib_insync import *
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time

class DailyTradingScanner:
    """Scanner quotidien avec rapport complet"""
    
    def __init__(self):
        self.ib = IB()
        self.load_config()
        self.load_state()
        
        # Résultats du scan
        self.scan_results = {
            'timestamp': datetime.now().isoformat(),
            'positions_current': {},
            'signals_detected': [],
            'portfolio_summary': {},
            'actions_taken': []
        }
    
    def load_config(self):
        """Charger configuration"""
        try:
            if os.path.exists('bot_config.json'):
                with open('bot_config.json', 'r') as f:
                    interface_config = json.load(f)
                self.max_positions = interface_config.get('max_positions', 4)
                self.max_investment = interface_config.get('max_investment', 1000)
            else:
                self.max_positions = 4
                self.max_investment = 1000
        except:
            self.max_positions = 4
            self.max_investment = 1000
    
    def load_state(self):
        """Charger état des positions"""
        try:
            if os.path.exists('bot_state.json'):
                with open('bot_state.json', 'r') as f:
                    state = json.load(f)
                self.positions = state.get('positions', {})
            else:
                self.positions = {}
        except:
            self.positions = {}
    
    def connect(self):
        """Connexion IB"""
        try:
            self.ib.connect('127.0.0.1', 7497, clientId=16)
            return True
        except Exception as e:
            print(f"❌ Connexion impossible: {e}")
            return False
    
    def analyze_symbol(self, symbol):
        """Analyse technique d'un symbole"""
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Données historiques
            bars = self.ib.reqHistoricalData(
                contract, '', '60 D', '1 day', 'TRADES', 1, 1, False
            )
            
            if len(bars) < 30:
                return None
            
            # DataFrame
            df = pd.DataFrame([{
                'close': bar.close,
                'volume': bar.volume
            } for bar in bars])
            
            # RSI
            delta = df['close'].diff()
            gains = delta.where(delta > 0, 0).rolling(14).mean()
            losses = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gains / losses
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
            
            current = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else current
            
            # Signaux
            achat_rsi = current['RSI'] < 30
            achat_macd = (current['MACD'] > current['MACD_signal']) and \
                        (prev['MACD'] <= prev['MACD_signal'])
            
            buy_signal = achat_rsi or achat_macd
            
            # Calcul confiance
            confidence = 0.0
            if achat_rsi:
                confidence += (30 - current['RSI']) / 30
            if achat_macd:
                macd_div = abs(current['MACD'] - current['MACD_signal'])
                confidence += min(macd_div / 0.5, 1.0)
            
            confidence = min(confidence, 1.0)
            
            return {
                'symbol': symbol,
                'price': bars[-1].close,
                'rsi': current['RSI'],
                'macd': current['MACD'],
                'macd_signal': current['MACD_signal'],
                'buy_signal': buy_signal and confidence > 0.1,
                'confidence': confidence,
                'reasons': {
                    'rsi_oversold': achat_rsi,
                    'macd_bullish': achat_macd
                }
            }
            
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
    
    def scan_market(self):
        """Scan quotidien du marché"""
        print(f"\n📊 SCAN QUOTIDIEN - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 60)
        
        # Watchlist étendue
        watchlist = [
            'AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMZN', 'TSLA',
            'JPM', 'BAC', 'WFC', 'JNJ', 'PFE', 'XOM', 'CVX',
            'CE', 'ACVA', 'CSCO', 'BSX', 'APP'
        ]
        
        signals_found = []
        market_overview = []
        
        print(f"🔍 Analyse de {len(watchlist)} symboles...")
        
        for symbol in watchlist:
            # Skip si déjà en position
            if symbol in self.positions:
                print(f"   ⏭️ {symbol}: Déjà détenu")
                continue
            
            analysis = self.analyze_symbol(symbol)
            
            if analysis and 'error' not in analysis:
                market_overview.append(analysis)
                
                if analysis['buy_signal']:
                    signals_found.append(analysis)
                    print(f"   🟢 {symbol}: ${analysis['price']:.2f} | RSI {analysis['rsi']:.1f} | Conf: {analysis['confidence']:.1%}")
                else:
                    print(f"   ⚪ {symbol}: ${analysis['price']:.2f} | RSI {analysis['rsi']:.1f} | Neutre")
            else:
                error = analysis.get('error', 'Données indisponibles') if analysis else 'Analyse échouée'
                print(f"   ❌ {symbol}: {error}")
        
        # Tri des signaux par confiance
        signals_found.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"\n📊 RÉSULTATS SCAN:")
        print(f"   Symboles analysés: {len(market_overview)}")
        print(f"   Signaux détectés: {len(signals_found)}")
        
        self.scan_results['signals_detected'] = signals_found
        
        return signals_found
    
    def check_current_positions(self):
        """Vérifier positions actuelles"""
        print(f"\n📈 POSITIONS ACTUELLES:")
        
        if not self.positions:
            print("   Aucune position")
            return
        
        total_pnl = 0
        
        for symbol, position in self.positions.items():
            try:
                # Prix actuel
                contract = Stock(symbol, 'SMART', 'USD')
                self.ib.qualifyContracts(contract)
                
                bars = self.ib.reqHistoricalData(contract, '', '1 D', '1 day', 'TRADES', 1, 1, False)
                current_price = bars[-1].close
                
                # Calculs P&L
                entry_price = position['entry_price']
                quantity = position['quantity']
                pnl_dollar = (current_price - entry_price) * quantity
                pnl_pct = (current_price - entry_price) / entry_price * 100
                
                total_pnl += pnl_dollar
                
                # Jours détenu
                entry_date = datetime.fromisoformat(position['entry_date'])
                days_held = (datetime.now() - entry_date).days
                
                status_icon = "🟢" if pnl_dollar > 0 else "🔴" if pnl_dollar < 0 else "⚪"
                
                print(f"   {status_icon} {symbol}: {quantity} @ ${entry_price:.2f} → ${current_price:.2f}")
                print(f"       P&L: {pnl_pct:+.1f}% (${pnl_dollar:+.2f}) | {days_held} jours")
                
                self.scan_results['positions_current'][symbol] = {
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'pnl_pct': pnl_pct,
                    'pnl_dollar': pnl_dollar,
                    'days_held': days_held
                }
                
            except Exception as e:
                print(f"   ❌ {symbol}: Erreur prix - {e}")
        
        print(f"\n💰 P&L TOTAL: ${total_pnl:+.2f}")
        self.scan_results['portfolio_summary']['total_pnl'] = total_pnl
    
    def execute_daily_actions(self, signals):
        """Exécuter actions quotidiennes"""
        print(f"\n🎯 ACTIONS QUOTIDIENNES:")
        
        if not signals:
            print("   Aucune action - pas de signaux")
            return
        
        # Places libres
        places_libres = self.max_positions - len(self.positions)
        
        if places_libres <= 0:
            print(f"   Aucune action - limite positions atteinte ({len(self.positions)}/{self.max_positions})")
            return
        
        print(f"   Places disponibles: {places_libres}")
        
        # Proposition d'achat
        for i, signal in enumerate(signals[:places_libres]):
            symbol = signal['symbol']
            price = signal['price']
            confidence = signal['confidence']
            
            quantity = int(self.max_investment / price)
            cost = quantity * price
            
            print(f"\n🛒 PROPOSITION ACHAT {i+1}:")
            print(f"   Symbole: {symbol}")
            print(f"   Prix: ${price:.2f}")
            print(f"   Quantité: {quantity} actions")
            print(f"   Coût: ${cost:.2f}")
            print(f"   Confiance: {confidence:.1%}")
            
            # Raisons
            reasons = []
            if signal['reasons']['rsi_oversold']:
                reasons.append(f"RSI survendu ({signal['rsi']:.1f})")
            if signal['reasons']['macd_bullish']:
                reasons.append("MACD haussier")
            print(f"   Raisons: {', '.join(reasons)}")
            
            # Demander confirmation
            choice = input(f"   ❓ Acheter {symbol} ? (y/n/q pour quitter): ").strip().lower()
            
            if choice == 'q':
                print("   🛑 Arrêt des achats")
                break
            elif choice == 'y':
                success = self.execute_buy_order(symbol, quantity, price)
                if success:
                    self.scan_results['actions_taken'].append({
                        'action': 'BUY',
                        'symbol': symbol,
                        'quantity': quantity,
                        'price': price,
                        'confidence': confidence
                    })
            else:
                print(f"   ⏭️ {symbol} ignoré")
    
    def execute_buy_order(self, symbol, quantity, price):
        """Exécuter ordre d'achat"""
        try:
            print(f"\n🛒 ACHAT {symbol}...")
            
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            order = MarketOrder('BUY', quantity)
            trade = self.ib.placeOrder(contract, order)
            
            print(f"✅ Ordre passé: BUY {quantity} {symbol}")
            
            # Mise à jour positions
            self.positions[symbol] = {
                'quantity': quantity,
                'entry_price': price,
                'entry_date': datetime.now().isoformat(),
                'order_id': trade.order.orderId
            }
            
            # Sauvegarde
            self.save_state()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur achat {symbol}: {e}")
            return False
    
    def save_state(self):
        """Sauvegarder état"""
        try:
            state = {
                'positions': self.positions,
                'last_update': datetime.now().isoformat()
            }
            with open('bot_state.json', 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde: {e}")
    
    def generate_daily_report(self):
        """Générer rapport quotidien"""
        print(f"\n📋 RAPPORT QUOTIDIEN")
        print("=" * 50)
        
        # Date
        now = datetime.now()
        print(f"📅 Date: {now.strftime('%Y-%m-%d %H:%M')}")
        
        # Résumé positions
        print(f"💼 Portfolio:")
        print(f"   Positions: {len(self.positions)}/{self.max_positions}")
        
        if 'total_pnl' in self.scan_results['portfolio_summary']:
            total_pnl = self.scan_results['portfolio_summary']['total_pnl']
            print(f"   P&L Total: ${total_pnl:+.2f}")
        
        # Signaux
        signals_count = len(self.scan_results['signals_detected'])
        print(f"🎯 Marché:")
        print(f"   Signaux détectés: {signals_count}")
        
        # Actions
        actions_count = len(self.scan_results['actions_taken'])
        print(f"🛒 Actions:")
        print(f"   Ordres passés: {actions_count}")
        
        # Sauvegarde rapport
        report_filename = f"daily_report_{now.strftime('%Y%m%d')}.json"
        try:
            with open(report_filename, 'w') as f:
                json.dump(self.scan_results, f, indent=2, default=str)
            print(f"💾 Rapport sauvé: {report_filename}")
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde rapport: {e}")
    
    def run_daily_scan(self):
        """Exécution scan quotidien complet"""
        print("🌅 SCAN QUOTIDIEN AUTOMATIQUE")
        print("=" * 60)
        
        if not self.connect():
            print("❌ Impossible de se connecter à IB")
            return
        
        try:
            # 1. Vérifier positions actuelles
            self.check_current_positions()
            
            # 2. Scanner le marché
            signals = self.scan_market()
            
            # 3. Exécuter actions si nécessaire
            if signals:
                self.execute_daily_actions(signals)
            
            # 4. Générer rapport
            self.generate_daily_report()
            
        except Exception as e:
            print(f"❌ Erreur scan quotidien: {e}")
        finally:
            self.disconnect()
    
    def disconnect(self):
        if self.ib.isConnected():
            self.ib.disconnect()

def main():
    """Lancement scan quotidien"""
    scanner = DailyTradingScanner()
    scanner.run_daily_scan()

if __name__ == "__main__":
    main()
