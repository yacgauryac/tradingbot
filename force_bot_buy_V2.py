# force_bot_buy.py - Test achat forcé avec vraie logique bot

import json
import os
import pandas as pd  # Import manquant !
import numpy as np
from datetime import datetime
from ib_insync import *

class ForceBotTest:
    """Test achat forcé avec exactement la même logique que le vrai bot"""
    
    def __init__(self):
        self.ib = IB()
        self.load_real_bot_config()
        self.load_real_bot_state()
    
    def load_real_bot_config(self):
        """Charger vraie config bot (même méthode que auto_trading_bot.py)"""
        default_config = {
            'max_positions': 3,
            'max_investment_per_trade': 1000,
            'rsi_window': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9
        }
        
        try:
            if os.path.exists('bot_config.json'):
                with open('bot_config.json', 'r') as f:
                    interface_config = json.load(f)
                
                # Adaptation exacte comme dans auto_trading_bot.py
                if 'max_positions' in interface_config:
                    default_config['max_positions'] = interface_config['max_positions']
                if 'max_investment' in interface_config:
                    default_config['max_investment_per_trade'] = interface_config['max_investment']
                if 'rsi_oversold' in interface_config:
                    default_config['rsi_oversold'] = interface_config['rsi_oversold']
                if 'rsi_overbought' in interface_config:
                    default_config['rsi_overbought'] = interface_config['rsi_overbought']
        except:
            pass
        
        self.config = default_config
        print(f"🔧 Config chargée:")
        print(f"   Max positions: {self.config['max_positions']}")
        print(f"   Max investment: ${self.config['max_investment_per_trade']}")
        print(f"   RSI oversold: {self.config['rsi_oversold']}")
    
    def load_real_bot_state(self):
        """Charger vrai état bot"""
        try:
            if os.path.exists('bot_state.json'):
                with open('bot_state.json', 'r') as f:
                    state = json.load(f)
                self.positions = state.get('positions', {})
            else:
                self.positions = {}
        except:
            self.positions = {}
        
        print(f"📊 État positions:")
        print(f"   Positions actuelles: {len(self.positions)}")
        for symbol in self.positions.keys():
            print(f"     📍 {symbol}")
    
    def connect(self):
        try:
            self.ib.connect('127.0.0.1', 7497, clientId=13)
            return True
        except Exception as e:
            print(f"❌ Connexion: {e}")
            return False
    
    def calculate_indicators_exact(self, df):
        """Calcul indicateurs EXACT comme auto_trading_bot.py"""
        if len(df) < 30:
            return df
        
        # RSI exact
        delta = df['close'].diff()
        gains = delta.where(delta > 0, 0).rolling(self.config['rsi_window']).mean()
        losses = (-delta.where(delta < 0, 0)).rolling(self.config['rsi_window']).mean()
        rs = gains / losses
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD exact
        exp1 = df['close'].ewm(span=self.config['macd_fast']).mean()
        exp2 = df['close'].ewm(span=self.config['macd_slow']).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_signal'] = df['MACD'].ewm(span=self.config['macd_signal']).mean()
        
        return df.fillna(method='ffill').fillna(0)
    
    def analyze_symbol_exact(self, symbol):
        """Analyse EXACTE comme auto_trading_bot.py"""
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Données historiques (même durée que bot)
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
            
            # Indicateurs exacts
            df = self.calculate_indicators_exact(df)
            
            if len(df) < 2:
                return None
            
            # Valeurs actuelles et précédentes (EXACTEMENT comme bot)
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Signaux d'achat (LOGIQUE EXACTE du bot)
            achat_rsi = current['RSI'] < self.config['rsi_oversold']
            achat_macd = (current['MACD'] > current['MACD_signal']) and \
                        (prev['MACD'] <= prev['MACD_signal'])
            
            buy_signal = achat_rsi or achat_macd
            
            # Calcul confiance (EXACT comme bot)
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
                'macd_signal': current['MACD_signal'],
                'buy_signal': buy_signal,
                'confidence': confidence,
                'achat_rsi': achat_rsi,
                'achat_macd': achat_macd,
                'prev_macd': prev['MACD'],
                'prev_signal': prev['MACD_signal']
            }
            
        except Exception as e:
            print(f"❌ Erreur analyse {symbol}: {e}")
            return None
    
    def test_csco_exact(self):
        """Test CSCO avec logique exacte du bot"""
        print(f"\n🧪 TEST CSCO - LOGIQUE EXACTE BOT")
        print("=" * 50)
        
        # Vérifications préalables
        if 'CSCO' in self.positions:
            print(f"❌ CSCO déjà en position")
            return False
        
        if len(self.positions) >= self.config['max_positions']:
            print(f"❌ Limite positions atteinte ({len(self.positions)}/{self.config['max_positions']})")
            return False
        
        # Analyse CSCO
        analysis = self.analyze_symbol_exact('CSCO')
        
        if not analysis:
            print(f"❌ Impossible d'analyser CSCO")
            return False
        
        print(f"📊 ANALYSE CSCO:")
        print(f"   Prix: ${analysis['price']:.2f}")
        print(f"   RSI: {analysis['rsi']:.1f}")
        print(f"   MACD: {analysis['macd']:.4f}")
        print(f"   Signal: {analysis['macd_signal']:.4f}")
        print(f"   MACD précédent: {analysis['prev_macd']:.4f}")
        print(f"   Signal précédent: {analysis['prev_signal']:.4f}")
        
        print(f"\n🎯 CONDITIONS ACHAT:")
        print(f"   RSI < {self.config['rsi_oversold']}: {analysis['achat_rsi']} (RSI: {analysis['rsi']:.1f})")
        print(f"   MACD croisement: {analysis['achat_macd']}")
        if analysis['achat_macd']:
            print(f"     MACD > Signal: {analysis['macd']:.4f} > {analysis['macd_signal']:.4f} = {analysis['macd'] > analysis['macd_signal']}")
            print(f"     Prev MACD <= Prev Signal: {analysis['prev_macd']:.4f} <= {analysis['prev_signal']:.4f} = {analysis['prev_macd'] <= analysis['prev_signal']}")
        
        print(f"   Signal final: {analysis['buy_signal']}")
        print(f"   Confiance: {analysis['confidence']:.1%}")
        
        # Décision finale
        should_buy = analysis['buy_signal'] and analysis['confidence'] > 0.1
        
        print(f"\n🎯 DÉCISION BOT:")
        if should_buy:
            print(f"✅ BOT DEVRAIT ACHETER CSCO!")
            
            # Calcul quantité
            quantity = int(self.config['max_investment_per_trade'] / analysis['price'])
            print(f"   Quantité: {quantity} actions")
            print(f"   Coût: ${quantity * analysis['price']:.2f}")
            
            print(f"\n❓ POURQUOI LE VRAI BOT N'ACHÈTE PAS ?")
            print(f"   1. ❌ Erreur dans auto_trading_bot.py")
            print(f"   2. ❌ Bot pas vraiment actif")
            print(f"   3. ❌ Problème connexion IB du bot")
            print(f"   4. ❌ Condition cachée non respectée")
            
        else:
            print(f"❌ Bot NE DEVRAIT PAS acheter")
            print(f"   Raison: Signal faible ou confiance < 0.1")
        
        return should_buy
    
    def force_buy_test(self):
        """Test achat forcé (simulé)"""
        print(f"\n🚀 TEST ACHAT FORCÉ:")
        
        choice = input("Voulez-vous tester un achat réel simulé de CSCO ? (y/n): ").strip().lower()
        
        if choice == 'y':
            analysis = self.analyze_symbol_exact('CSCO')
            if analysis and analysis['buy_signal']:
                print(f"🛒 SIMULATION ACHAT CSCO...")
                
                # Ici on pourrait passer un vrai ordre
                # Pour test, on simule juste
                print(f"✅ ORDRE SIMULÉ PASSÉ!")
                print(f"   → Le vrai bot aurait dû faire pareil")
            else:
                print(f"❌ Conditions pas remplies pour achat")
    
    def disconnect(self):
        if self.ib.isConnected():
            self.ib.disconnect()

def main():
    print("🧪 TEST ACHAT FORCÉ - LOGIQUE EXACTE BOT")
    print("=" * 50)
    
    tester = ForceBotTest()
    
    try:
        if not tester.connect():
            return
        
        # Test logique exacte
        should_buy = tester.test_csco_exact()
        
        if should_buy:
            tester.force_buy_test()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tester.disconnect()

if __name__ == "__main__":
    main()
