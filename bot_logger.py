# bot_logger.py - Logs simples du bot

import json
import os
import time
from datetime import datetime
from ib_insync import *

class SimpleBotLogger:
    """Logger simple pour voir ce que fait le bot"""
    
    def __init__(self):
        self.ib = IB()
        
    def connect(self):
        try:
            self.ib.connect('127.0.0.1', 7497, clientId=12)
            return True
        except Exception as e:
            print(f"❌ Connexion: {e}")
            return False
    
    def get_bot_state(self):
        """État actuel du bot"""
        try:
            if os.path.exists('bot_state.json'):
                with open('bot_state.json', 'r') as f:
                    return json.load(f)
            return {}
        except:
            return {}
    
    def get_bot_config(self):
        """Config du bot"""
        try:
            if os.path.exists('bot_config.json'):
                with open('bot_config.json', 'r') as f:
                    return json.load(f)
            return {'max_positions': 3}
        except:
            return {'max_positions': 3}
    
    def analyze_symbol_simple(self, symbol):
        """Analyse simple comme le bot"""
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Données
            bars = self.ib.reqHistoricalData(
                contract, '', '30 D', '1 day', 'TRADES', 1, 1, False
            )
            
            if len(bars) < 15:
                return None
            
            # RSI
            closes = [bar.close for bar in bars]
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            
            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # MACD simple
            ema12 = closes[-1]  # Simplifié
            ema26 = sum(closes[-26:]) / 26 if len(closes) >= 26 else closes[-1]
            macd = ema12 - ema26
            
            price = bars[-1].close
            
            # Signaux (même logique que bot)
            achat_rsi = rsi < 30
            achat_macd = macd > 0  # Simplifié
            buy_signal = achat_rsi or achat_macd
            
            confidence = 0.0
            if achat_rsi:
                confidence += (30 - rsi) / 30
            if achat_macd:
                confidence += 0.3
            
            return {
                'symbol': symbol,
                'price': price,
                'rsi': rsi,
                'macd': macd,
                'buy_signal': buy_signal,
                'confidence': confidence,
                'achat_rsi': achat_rsi,
                'achat_macd': achat_macd
            }
            
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
    
    def simulate_bot_scan(self):
        """Simulation du scan du bot"""
        print(f"\n🔍 SIMULATION SCAN BOT - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        # État actuel
        state = self.get_bot_state()
        config = self.get_bot_config()
        
        positions = state.get('positions', {})
        max_pos = config.get('max_positions', 3)
        
        print(f"📊 ÉTAT: {len(positions)}/{max_pos} positions")
        for symbol in positions.keys():
            print(f"   📍 {symbol} (déjà détenu)")
        
        if len(positions) >= max_pos:
            print(f"🚫 LIMITE ATTEINTE → Aucun achat possible")
            return
        
        print(f"✅ {max_pos - len(positions)} places libres")
        
        # Watchlist (même que le bot)
        watchlist = ['CSCO', 'GOOGL', 'META', 'MSFT', 'APP', 'BSX', 'ACVA', 'AIV', 'CE', 'AAPL', 'TSLA', 'NVDA', 'AMZN']
        
        print(f"\n🔍 SCAN {len(watchlist)} SYMBOLES:")
        
        signals = []
        
        for symbol in watchlist:
            # Skip si déjà en position
            if symbol in positions:
                print(f"   ⏭️ {symbol}: Déjà détenu")
                continue
            
            analysis = self.analyze_symbol_simple(symbol)
            
            if analysis and 'error' not in analysis:
                rsi = analysis['rsi']
                price = analysis['price']
                buy_signal = analysis['buy_signal']
                confidence = analysis['confidence']
                
                if buy_signal and confidence > 0.1:
                    signals.append(analysis)
                    reasons = []
                    if analysis['achat_rsi']:
                        reasons.append(f"RSI {rsi:.1f}")
                    if analysis['achat_macd']:
                        reasons.append("MACD+")
                    
                    print(f"   🟢 {symbol}: ${price:.2f} | {' + '.join(reasons)} | Conf: {confidence:.1%}")
                else:
                    print(f"   ⚪ {symbol}: ${price:.2f} | RSI {rsi:.1f} | Pas de signal")
            else:
                error = analysis.get('error', 'Erreur inconnue') if analysis else 'Aucune donnée'
                print(f"   ❌ {symbol}: {error}")
        
        # Résultats
        print(f"\n📊 RÉSULTATS SCAN:")
        if signals:
            print(f"✅ {len(signals)} signaux détectés")
            
            # Tri par confiance
            signals.sort(key=lambda x: x['confidence'], reverse=True)
            
            print(f"🎯 TOP SIGNAUX:")
            for i, signal in enumerate(signals[:3], 1):
                symbol = signal['symbol']
                confidence = signal['confidence']
                price = signal['price']
                print(f"   {i}. {symbol}: ${price:.2f} (Conf: {confidence:.1%})")
            
            # Simulation achat
            places_libres = max_pos - len(positions)
            achats_possibles = min(len(signals), places_libres)
            
            print(f"\n🛒 SIMULATION ACHATS:")
            for i in range(achats_possibles):
                signal = signals[i]
                symbol = signal['symbol']
                price = signal['price']
                quantity = int(1000 / price)  # $1000 par position
                
                print(f"   ✅ ACHÈTERAIT: {quantity} {symbol} @ ${price:.2f}")
        else:
            print(f"❌ Aucun signal d'achat détecté")
            print(f"💡 Raisons possibles:")
            print(f"   - Tous RSI > 30")
            print(f"   - MACD négatifs")
            print(f"   - Confiance trop faible")
    
    def monitor_continuous(self):
        """Monitoring continu"""
        print("👁️ MONITORING CONTINU - Ctrl+C pour arrêter")
        
        try:
            while True:
                self.simulate_bot_scan()
                print(f"\n⏳ Prochain scan dans 5 minutes...")
                time.sleep(300)  # 5 minutes
        except KeyboardInterrupt:
            print(f"\n🛑 Monitoring arrêté")
    
    def disconnect(self):
        if self.ib.isConnected():
            self.ib.disconnect()

def main():
    """Menu principal"""
    print("🤖 BOT LOGGER - Voir ce que fait le bot")
    print("=" * 40)
    print("1. 🔍 Scan unique")
    print("2. 👁️ Monitoring continu (5 min)")
    print("3. 📊 État bot seulement")
    
    choice = input("\nChoix (1/2/3) [1]: ").strip() or "1"
    
    logger = SimpleBotLogger()
    
    try:
        if not logger.connect():
            return
        
        if choice == "1":
            logger.simulate_bot_scan()
        elif choice == "2":
            logger.monitor_continuous()
        elif choice == "3":
            state = logger.get_bot_state()
            config = logger.get_bot_config()
            
            print(f"\n📊 ÉTAT BOT:")
            print(f"   Positions: {len(state.get('positions', {}))}/{config.get('max_positions', 3)}")
            print(f"   Trades: {len(state.get('trade_log', []))}")
            
            for symbol, pos in state.get('positions', {}).items():
                price = pos.get('entry_price', 'N/A')
                qty = pos.get('quantity', 'N/A')
                print(f"   📍 {symbol}: {qty} @ ${price}")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        logger.disconnect()

if __name__ == "__main__":
    main()
