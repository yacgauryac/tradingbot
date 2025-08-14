# enhanced_trading_bot.py - Bot avec configurations avancées par symbole

from ib_insync import *
import pandas as pd
import numpy as np
import time
import json
import os
from datetime import datetime, timedelta

class EnhancedTradingBot:
    """Bot de trading avec configurations avancées par symbole"""
    
    def __init__(self):
        self.ib = IB()
        self.running = True
        
        # Chargement configurations
        self.load_advanced_configs()
        self.load_basic_config()
        self.load_state()
        
        print(f"🤖 Bot Enhanced initialisé")
        print(f"   Configs avancées: {len(self.advanced_configs)} symboles")
        print(f"   Max positions: {self.config['max_positions']}")
        
    def load_advanced_configs(self):
        """Charger configurations avancées par symbole"""
        try:
            if os.path.exists('advanced_strategy_config.json'):
                with open('advanced_strategy_config.json', 'r') as f:
                    advanced_data = json.load(f)
                
                # Charger les configs spécifiques
                self.advanced_configs = {}
                self.sector_configs = advanced_data.get('sectors', {})
                self.symbol_configs = advanced_data.get('symbols', {})
                self.symbol_sectors = advanced_data.get('symbol_sectors', {})
                
                print(f"✅ Configs avancées chargées")
                print(f"   Secteurs: {list(self.sector_configs.keys())}")
                print(f"   Symboles spéciaux: {list(self.symbol_configs.keys())}")
                
            else:
                print(f"⚠️ Pas de config avancée → paramètres par défaut")
                self.advanced_configs = {}
                self.sector_configs = {}
                self.symbol_configs = {}
                self.symbol_sectors = {}
                
        except Exception as e:
            print(f"❌ Erreur chargement configs avancées: {e}")
            self.advanced_configs = {}
    
    def load_basic_config(self):
        """Charger config de base (interface)"""
        default_config = {
            'max_positions': 3,
            'max_investment_per_trade': 1000,
            'scan_interval': 300,
            'position_check_interval': 60
        }
        
        try:
            if os.path.exists('bot_config.json'):
                with open('bot_config.json', 'r') as f:
                    interface_config = json.load(f)
                
                if 'max_positions' in interface_config:
                    default_config['max_positions'] = interface_config['max_positions']
                if 'max_investment' in interface_config:
                    default_config['max_investment_per_trade'] = interface_config['max_investment']
                
                print(f"✅ Config de base chargée")
        except:
            print(f"⚠️ Config par défaut utilisée")
        
        self.config = default_config
    
    def get_symbol_config(self, symbol):
        """Obtenir configuration optimale pour un symbole"""
        # Config par défaut
        base_config = {
            'rsi_window': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'min_confidence': 0.15
        }
        
        # Appliquer config secteur si disponible
        sector = self.symbol_sectors.get(symbol)
        if sector and sector in self.sector_configs:
            sector_config = self.sector_configs[sector]
            
            # RSI
            if 'rsi' in sector_config:
                rsi_config = sector_config['rsi']
                base_config['rsi_window'] = rsi_config.get('window', base_config['rsi_window'])
                base_config['rsi_oversold'] = rsi_config.get('oversold', base_config['rsi_oversold'])
                base_config['rsi_overbought'] = rsi_config.get('overbought', base_config['rsi_overbought'])
            
            # MACD
            if 'macd' in sector_config:
                macd_config = sector_config['macd']
                base_config['macd_fast'] = macd_config.get('fast', base_config['macd_fast'])
                base_config['macd_slow'] = macd_config.get('slow', base_config['macd_slow'])
                base_config['macd_signal'] = macd_config.get('signal', base_config['macd_signal'])
            
            # Seuils
            if 'thresholds' in sector_config:
                thresholds = sector_config['thresholds']
                base_config['min_confidence'] = thresholds.get('min_confidence', base_config['min_confidence'])
        
        # Appliquer config symbole spécifique si disponible
        if symbol in self.symbol_configs:
            symbol_config = self.symbol_configs[symbol]
            
            if 'rsi' in symbol_config:
                rsi_config = symbol_config['rsi']
                base_config['rsi_window'] = rsi_config.get('window', base_config['rsi_window'])
                base_config['rsi_oversold'] = rsi_config.get('oversold', base_config['rsi_oversold'])
                base_config['rsi_overbought'] = rsi_config.get('overbought', base_config['rsi_overbought'])
            
            if 'macd' in symbol_config:
                macd_config = symbol_config['macd']
                base_config['macd_fast'] = macd_config.get('fast', base_config['macd_fast'])
                base_config['macd_slow'] = macd_config.get('slow', base_config['macd_slow'])
                base_config['macd_signal'] = macd_config.get('signal', base_config['macd_signal'])
            
            if 'thresholds' in symbol_config:
                thresholds = symbol_config['thresholds']
                base_config['min_confidence'] = thresholds.get('min_confidence', base_config['min_confidence'])
        
        return base_config
    
    def calculate_indicators_adaptive(self, df, symbol):
        """Calcul indicateurs avec paramètres adaptatifs"""
        symbol_config = self.get_symbol_config(symbol)
        
        if len(df) < max(symbol_config['rsi_window'], symbol_config['macd_slow']) + 10:
            return df
        
        # RSI adaptatif
        delta = df['close'].diff()
        gains = delta.where(delta > 0, 0).rolling(symbol_config['rsi_window']).mean()
        losses = (-delta.where(delta < 0, 0)).rolling(symbol_config['rsi_window']).mean()
        rs = gains / losses
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD adaptatif
        exp1 = df['close'].ewm(span=symbol_config['macd_fast']).mean()
        exp2 = df['close'].ewm(span=symbol_config['macd_slow']).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_signal'] = df['MACD'].ewm(span=symbol_config['macd_signal']).mean()
        
        return df.fillna(method='ffill').fillna(0)
    
    def analyze_symbol_enhanced(self, symbol):
        """Analyse avec paramètres adaptatifs"""
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
            
            # Indicateurs adaptatifs
            df = self.calculate_indicators_adaptive(df, symbol)
            
            if len(df) < 2:
                return None
            
            # Config pour ce symbole
            symbol_config = self.get_symbol_config(symbol)
            
            # Valeurs actuelles et précédentes
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Signaux avec seuils adaptatifs
            achat_rsi = current['RSI'] < symbol_config['rsi_oversold']
            achat_macd = (current['MACD'] > current['MACD_signal']) and \
                        (prev['MACD'] <= prev['MACD_signal'])
            
            buy_signal = achat_rsi or achat_macd
            
            # Calcul confiance adaptatif
            confidence = 0.0
            if achat_rsi:
                confidence += (symbol_config['rsi_oversold'] - current['RSI']) / symbol_config['rsi_oversold']
            if achat_macd:
                macd_div = abs(current['MACD'] - current['MACD_signal'])
                confidence += min(macd_div / 0.5, 1.0)
            
            confidence = min(confidence, 1.0)
            
            # Vérification seuil de confiance adaptatif
            signal_valid = buy_signal and confidence >= symbol_config['min_confidence']
            
            return {
                'symbol': symbol,
                'price': bars[-1].close,
                'rsi': current['RSI'],
                'macd': current['MACD'],
                'macd_signal': current['MACD_signal'],
                'buy_signal': signal_valid,
                'confidence': confidence,
                'config_used': symbol_config,
                'reasons': {
                    'achat_rsi': achat_rsi,
                    'achat_macd': achat_macd,
                    'confidence_ok': confidence >= symbol_config['min_confidence']
                }
            }
            
        except Exception as e:
            print(f"❌ Erreur analyse {symbol}: {e}")
            return None
    
    def scan_market_enhanced(self):
        """Scan avec configurations adaptatiques"""
        print(f"\n🔍 SCAN ENHANCED - {datetime.now().strftime('%H:%M:%S')}")
        
        # Watchlist étendue
        watchlist = [
            # Tech
            'AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMZN',
            # Finance  
            'JPM', 'BAC', 'WFC',
            # Autres
            'TSLA', 'CE', 'ACVA', 'CSCO', 'BSX'
        ]
        
        signals = []
        
        for symbol in watchlist:
            # Skip si déjà en position
            if symbol in self.positions:
                continue
            
            analysis = self.analyze_symbol_enhanced(symbol)
            if analysis and analysis['buy_signal']:
                signals.append(analysis)
                
                config = analysis['config_used']
                reasons = analysis['reasons']
                
                print(f"🎯 {symbol}: ${analysis['price']:.2f}")
                print(f"   Config: RSI{config['rsi_window']} ({config['rsi_oversold']}/{config['rsi_overbought']})")
                print(f"   RSI: {analysis['rsi']:.1f} | MACD: {analysis['macd']:.4f}")
                print(f"   Confiance: {analysis['confidence']:.1%} (min: {config['min_confidence']:.1%})")
                
                reason_list = []
                if reasons['achat_rsi']:
                    reason_list.append(f"RSI < {config['rsi_oversold']}")
                if reasons['achat_macd']:
                    reason_list.append("MACD↗")
                print(f"   Raisons: {', '.join(reason_list)}")
        
        # Tri par confiance
        signals.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"📊 {len(signals)} signaux détectés")
        return signals[:3]  # Top 3
    
    def load_state(self):
        """Charger état existant"""
        try:
            if os.path.exists('bot_state.json'):
                with open('bot_state.json', 'r') as f:
                    state = json.load(f)
                    self.positions = state.get('positions', {})
                    self.trade_log = state.get('trade_log', [])
            else:
                self.positions = {}
                self.trade_log = []
        except:
            self.positions = {}
            self.trade_log = []
    
    def connect(self):
        """Connexion IB"""
        try:
            self.ib.connect('127.0.0.1', 7497, clientId=14)
            print("✅ Bot Enhanced connecté")
            return True
        except Exception as e:
            print(f"❌ Connexion: {e}")
            return False
    
    def execute_buy_order(self, analysis):
        """Exécution ordre d'achat"""
        symbol = analysis['symbol']
        price = analysis['price']
        
        try:
            print(f"\n🛒 ACHAT ENHANCED: {symbol}")
            print(f"   Config utilisée: RSI{analysis['config_used']['rsi_window']}")
            
            quantity = int(self.config['max_investment_per_trade'] / price)
            if quantity < 1:
                print(f"❌ Prix trop élevé")
                return False
            
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            order = MarketOrder('BUY', quantity)
            trade = self.ib.placeOrder(contract, order)
            
            print(f"✅ Ordre: BUY {quantity} {symbol} @ ~${price:.2f}")
            print(f"   Confiance: {analysis['confidence']:.1%}")
            
            # Enregistrement
            self.positions[symbol] = {
                'quantity': quantity,
                'entry_price': price,
                'entry_date': datetime.now().isoformat(),
                'order_id': trade.order.orderId,
                'config_used': analysis['config_used'],
                'entry_confidence': analysis['confidence']
            }
            
            self.trade_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'BUY',
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'confidence': analysis['confidence'],
                'config': analysis['config_used']
            })
            
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
                'trade_log': self.trade_log,
                'last_update': datetime.now().isoformat()
            }
            with open('enhanced_bot_state.json', 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde: {e}")
    
    def run_single_scan(self):
        """Un seul scan pour test"""
        if not self.connect():
            return
        
        try:
            signals = self.scan_market_enhanced()
            
            if signals:
                print(f"\n🎯 TOP SIGNAUX:")
                for i, signal in enumerate(signals, 1):
                    symbol = signal['symbol']
                    confidence = signal['confidence']
                    price = signal['price']
                    config = signal['config_used']
                    
                    print(f"{i}. {symbol}: ${price:.2f} (Conf: {confidence:.1%})")
                    print(f"   RSI{config['rsi_window']} seuils {config['rsi_oversold']}/{config['rsi_overbought']}")
                
                # Test achat
                if len(self.positions) < self.config['max_positions']:
                    choice = input(f"\nTester achat {signals[0]['symbol']} ? (y/n): ").strip().lower()
                    if choice == 'y':
                        self.execute_buy_order(signals[0])
            else:
                print(f"❌ Aucun signal selon configs avancées")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
        finally:
            self.disconnect()
    
    def disconnect(self):
        if self.ib.isConnected():
            self.ib.disconnect()

def main():
    """Test du bot enhanced"""
    print("🤖 BOT ENHANCED - Configs Avancées Par Symbole")
    print("=" * 60)
    
    bot = EnhancedTradingBot()
    bot.run_single_scan()

if __name__ == "__main__":
    main()
