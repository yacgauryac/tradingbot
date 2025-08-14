# auto_trading_bot.py - Bot de trading 100% autonome

from ib_insync import *
import pandas as pd
import numpy as np
import time
import json
import os
from datetime import datetime, timedelta

class AutoTradingBot:
    """Bot de trading entièrement autonome"""
    
    def __init__(self):
        self.ib = IB()
        self.running = True
        
        # Configuration
        self.config = {
            'max_positions': 3,           # Max 3 positions simultanées
            'max_investment_per_trade': 1000,  # $1000 max par trade
            'scan_interval': 300,         # Scan toutes les 5 minutes
            'position_check_interval': 60, # Check positions toutes les 1 min
            
            # Paramètres stratégie (optimisés)
            'rsi_window': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            
            # Règles de sortie
            'profit_target': 0.05,       # +5%
            'stop_loss': -0.08,          # -8%
            'max_hold_days': 10,         # 10 jours max
            'rsi_exit': 70               # RSI > 70
        }
        
        # Watchlists
        self.watchlists = {
            'breakout': ['CSCO', 'GOOGL', 'META', 'MSFT', 'APP', 'BSX'],
            'oversold': ['ACVA', 'AIV', 'CE'],  # CE déjà acheté
            'momentum': ['AAPL', 'TSLA', 'NVDA', 'AMZN']
        }
        
        # État du bot
        self.positions = {}
        self.trade_log = []
        self.last_scan = None
        
        self.load_state()
    
    def connect(self):
        """Connexion IB"""
        try:
            print("🤖 Démarrage bot autonome...")
            self.ib.connect('127.0.0.1', 7497, clientId=7)
            print("✅ Bot connecté")
            return True
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return False
    
    def load_state(self):
        """Chargement état précédent"""
        try:
            if os.path.exists('bot_state.json'):
                with open('bot_state.json', 'r') as f:
                    state = json.load(f)
                    self.positions = state.get('positions', {})
                    self.trade_log = state.get('trade_log', [])
                print(f"📊 État chargé: {len(self.positions)} positions actives")
            else:
                print("🆕 Nouveau démarrage bot")
        except Exception as e:
            print(f"⚠️ Erreur chargement état: {e}")
    
    def save_state(self):
        """Sauvegarde état"""
        try:
            state = {
                'positions': self.positions,
                'trade_log': self.trade_log,
                'last_update': datetime.now().isoformat()
            }
            with open('bot_state.json', 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde: {e}")
    
    def calculate_indicators(self, df):
        """Calcul RSI + MACD"""
        if len(df) < 30:
            return df
        
        # RSI
        delta = df['close'].diff()
        gains = delta.where(delta > 0, 0).rolling(self.config['rsi_window']).mean()
        losses = (-delta.where(delta < 0, 0)).rolling(self.config['rsi_window']).mean()
        rs = gains / losses
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=self.config['macd_fast']).mean()
        exp2 = df['close'].ewm(span=self.config['macd_slow']).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_signal'] = df['MACD'].ewm(span=self.config['macd_signal']).mean()
        
        return df.fillna(method='ffill').fillna(0)
    
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
            
            # Indicateurs
            df = self.calculate_indicators(df)
            
            if len(df) < 2:
                return None
            
            # Valeurs actuelles
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Signaux d'achat (même logique que votre backtest)
            achat_rsi = current['RSI'] < self.config['rsi_oversold']
            achat_macd = (current['MACD'] > current['MACD_signal']) and \
                        (prev['MACD'] <= prev['MACD_signal'])
            
            buy_signal = achat_rsi or achat_macd
            
            # Signaux de vente
            vente_rsi = current['RSI'] > self.config['rsi_overbought']
            vente_macd = (current['MACD'] < current['MACD_signal']) and \
                        (prev['MACD'] >= prev['MACD_signal'])
            
            sell_signal = vente_rsi or vente_macd
            
            # Calcul confiance
            confidence = 0.0
            if achat_rsi:
                confidence += (self.config['rsi_oversold'] - current['RSI']) / self.config['rsi_oversold']
            if achat_macd:
                macd_div = abs(current['MACD'] - current['MACD_signal'])
                confidence += min(macd_div / 0.5, 1.0)
            
            confidence = min(confidence, 1.0)
            
            return {
                'symbol': symbol,
                'price': bars[-1].close,
                'rsi': current['RSI'],
                'macd': current['MACD'],
                'buy_signal': buy_signal,
                'sell_signal': sell_signal,
                'confidence': confidence,
                'reasons': {
                    'achat_rsi': achat_rsi,
                    'achat_macd': achat_macd,
                    'vente_rsi': vente_rsi,
                    'vente_macd': vente_macd
                }
            }
            
        except Exception as e:
            print(f"❌ Erreur analyse {symbol}: {e}")
            return None
    
    def scan_market(self):
        """Scan complet du marché"""
        print(f"\n🔍 SCAN MARCHÉ - {datetime.now().strftime('%H:%M:%S')}")
        
        all_symbols = []
        for watchlist in self.watchlists.values():
            all_symbols.extend(watchlist)
        
        signals = []
        
        for symbol in set(all_symbols):  # Suppression doublons
            # Skip si déjà en position
            if symbol in self.positions:
                continue
            
            analysis = self.analyze_symbol(symbol)
            if analysis and analysis['buy_signal'] and analysis['confidence'] > 0.1:
                signals.append(analysis)
                print(f"🎯 Signal: {symbol} - Conf: {analysis['confidence']:.1%}")
        
        # Tri par confiance
        signals.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"📊 Scan terminé: {len(signals)} signaux détectés")
        return signals[:3]  # Top 3 seulement
    
    def execute_buy_order(self, analysis):
        """Exécution ordre d'achat automatique"""
        symbol = analysis['symbol']
        price = analysis['price']
        
        try:
            print(f"\n🛒 ACHAT AUTOMATIQUE: {symbol}")
            
            # Calcul quantité
            quantity = int(self.config['max_investment_per_trade'] / price)
            if quantity < 1:
                print(f"❌ Prix trop élevé pour {symbol}")
                return False
            
            # Contrat et ordre
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            order = MarketOrder('BUY', quantity)
            trade = self.ib.placeOrder(contract, order)
            
            print(f"✅ Ordre passé: BUY {quantity} {symbol} @ ~${price:.2f}")
            
            # Enregistrement position
            self.positions[symbol] = {
                'quantity': quantity,
                'entry_price': price,
                'entry_date': datetime.now().isoformat(),
                'order_id': trade.order.orderId,
                'analysis': analysis
            }
            
            # Log trade
            self.trade_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'BUY',
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'confidence': analysis['confidence']
            })
            
            self.save_state()
            return True
            
        except Exception as e:
            print(f"❌ Erreur achat {symbol}: {e}")
            return False
    
    def check_position_exits(self):
        """Vérification sorties positions"""
        if not self.positions:
            return
        
        print(f"\n👁️ CHECK POSITIONS ({len(self.positions)} actives)")
        
        for symbol in list(self.positions.keys()):
            position = self.positions[symbol]
            
            # Analyse actuelle
            current_analysis = self.analyze_symbol(symbol)
            if not current_analysis:
                continue
            
            current_price = current_analysis['price']
            entry_price = position['entry_price']
            entry_date = datetime.fromisoformat(position['entry_date'])
            
            # Calculs
            pnl_pct = (current_price - entry_price) / entry_price
            days_held = (datetime.now() - entry_date).days
            current_rsi = current_analysis['rsi']
            
            print(f"   {symbol}: {pnl_pct:+.1%} | RSI: {current_rsi:.1f} | {days_held}j")
            
            # Conditions de sortie
            should_exit = False
            exit_reason = ""
            
            if pnl_pct >= self.config['profit_target']:
                should_exit = True
                exit_reason = f"Profit target ({pnl_pct:+.1%})"
            elif pnl_pct <= self.config['stop_loss']:
                should_exit = True
                exit_reason = f"Stop loss ({pnl_pct:+.1%})"
            elif days_held >= self.config['max_hold_days']:
                should_exit = True
                exit_reason = f"Durée max ({days_held}j)"
            elif current_rsi >= self.config['rsi_exit']:
                should_exit = True
                exit_reason = f"RSI surachat ({current_rsi:.1f})"
            
            if should_exit:
                self.execute_sell_order(symbol, current_price, exit_reason)
    
    def execute_sell_order(self, symbol, current_price, reason):
        """Exécution ordre de vente automatique"""
        try:
            print(f"\n🔴 VENTE AUTOMATIQUE: {symbol} - {reason}")
            
            position = self.positions[symbol]
            quantity = position['quantity']
            
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            order = MarketOrder('SELL', quantity)
            trade = self.ib.placeOrder(contract, order)
            
            print(f"✅ Ordre vente: SELL {quantity} {symbol} @ ~${current_price:.2f}")
            
            # Calcul P&L
            entry_cost = position['entry_price'] * quantity
            exit_proceeds = current_price * quantity
            pnl = exit_proceeds - entry_cost
            
            print(f"💰 P&L: ${pnl:+.2f}")
            
            # Log trade
            self.trade_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'SELL',
                'symbol': symbol,
                'quantity': quantity,
                'price': current_price,
                'pnl': pnl,
                'reason': reason
            })
            
            # Suppression position
            del self.positions[symbol]
            self.save_state()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur vente {symbol}: {e}")
            return False
    
    def show_status(self):
        """Affichage status bot"""
        print(f"\n📊 STATUS BOT AUTONOME")
        print(f"   Positions actives: {len(self.positions)}")
        print(f"   Trades totaux: {len(self.trade_log)}")
        
        if self.positions:
            total_invested = 0
            for symbol, pos in self.positions.items():
                invested = pos['quantity'] * pos['entry_price']
                total_invested += invested
                print(f"   {symbol}: {pos['quantity']} @ ${pos['entry_price']:.2f}")
            print(f"   Total investi: ${total_invested:.2f}")
    
    def run_autonomous(self):
        """Boucle principale autonome"""
        print(f"\n🤖 BOT AUTONOME DÉMARRÉ")
        print(f"   Scan marché: toutes les {self.config['scan_interval']//60} min")
        print(f"   Check positions: toutes les {self.config['position_check_interval']} sec")
        print(f"   Max positions: {self.config['max_positions']}")
        print(f"   Max par trade: ${self.config['max_investment_per_trade']}")
        print(f"\n🛑 Ctrl+C pour arrêter")
        
        last_market_scan = 0
        last_position_check = 0
        
        try:
            while self.running:
                now = time.time()
                
                # Scan marché (toutes les 5 min)
                if now - last_market_scan >= self.config['scan_interval']:
                    if len(self.positions) < self.config['max_positions']:
                        signals = self.scan_market()
                        
                        for signal in signals:
                            if len(self.positions) >= self.config['max_positions']:
                                break
                            self.execute_buy_order(signal)
                            time.sleep(2)  # Pause entre ordres
                    else:
                        print(f"⏸️ Max positions atteint ({self.config['max_positions']})")
                    
                    last_market_scan = now
                
                # Check positions (toutes les 1 min)
                if now - last_position_check >= self.config['position_check_interval']:
                    self.check_position_exits()
                    last_position_check = now
                
                # Status périodique
                if int(now) % 300 == 0:  # Toutes les 5 min
                    self.show_status()
                
                time.sleep(10)  # Check toutes les 10 secondes
                
        except KeyboardInterrupt:
            print(f"\n🛑 Bot arrêté par l'utilisateur")
        except Exception as e:
            print(f"❌ Erreur bot: {e}")
        finally:
            self.save_state()
    
    def disconnect(self):
        if self.ib.isConnected():
            self.ib.disconnect()

def main():
    """Démarrage bot autonome"""
    bot = AutoTradingBot()
    
    try:
        if bot.connect():
            bot.run_autonomous()
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        bot.disconnect()

if __name__ == "__main__":
    main()