# manual_check.py - Vérification manuelle CSCO

from ib_insync import *
import pandas as pd
from datetime import datetime

def check_csco_manually():
    """Vérification manuelle RSI+MACD de CSCO"""
    print("🔍 VÉRIFICATION MANUELLE CSCO")
    print("=" * 40)
    
    try:
        ib = IB()
        ib.connect('127.0.0.1', 7497, clientId=15)
        
        # CSCO
        contract = Stock('CSCO', 'SMART', 'USD')
        ib.qualifyContracts(contract)
        
        # Données
        bars = ib.reqHistoricalData(contract, '', '30 D', '1 day', 'TRADES', 1, 1, False)
        
        if len(bars) < 15:
            print("❌ Pas assez de données")
            return
        
        # DataFrame
        df = pd.DataFrame([{
            'close': bar.close,
            'date': bar.date
        } for bar in bars])
        
        print(f"📊 CSCO - Prix actuel: ${bars[-1].close:.2f}")
        print(f"📅 Données: {len(bars)} jours")
        
        # RSI manuel (14 périodes)
        delta = df['close'].diff()
        gains = delta.where(delta > 0, 0).rolling(14).mean()
        losses = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        print(f"📈 RSI actuel: {current_rsi:.1f}")
        
        # MACD manuel (12, 26, 9)
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        prev_macd = macd.iloc[-2] if len(macd) > 1 else current_macd
        prev_signal = signal.iloc[-2] if len(signal) > 1 else current_signal
        
        print(f"📊 MACD: {current_macd:.4f}")
        print(f"📊 Signal: {current_signal:.4f}")
        print(f"📊 MACD prev: {prev_macd:.4f}")
        print(f"📊 Signal prev: {prev_signal:.4f}")
        
        # Tests signaux
        print(f"\n🎯 TESTS SIGNAUX:")
        
        # RSI < 30
        rsi_signal = current_rsi < 30
        print(f"   RSI < 30: {rsi_signal} (RSI: {current_rsi:.1f})")
        
        # MACD croisement
        macd_above = current_macd > current_signal
        prev_macd_below = prev_macd <= prev_signal
        macd_cross = macd_above and prev_macd_below
        print(f"   MACD > Signal: {macd_above}")
        print(f"   Prev MACD <= Prev Signal: {prev_macd_below}")
        print(f"   Croisement MACD: {macd_cross}")
        
        # Signal final
        buy_signal = rsi_signal or macd_cross
        print(f"\n🎯 SIGNAL FINAL: {buy_signal}")
        
        if not buy_signal:
            print(f"💡 POURQUOI PAS DE SIGNAL:")
            if not rsi_signal:
                print(f"   - RSI trop haut ({current_rsi:.1f} >= 30)")
            if not macd_cross:
                if not macd_above:
                    print(f"   - MACD en dessous du signal")
                else:
                    print(f"   - Pas de croisement (déjà au-dessus)")
        
        # Comparaison simulation
        print(f"\n🔍 COMPARAISON SIMULATION:")
        print(f"   Simulation disait: MACD+ avec 30% confiance")
        print(f"   Réalité: MACD {current_macd:.4f} vs Signal {current_signal:.4f}")
        
        if current_macd > current_signal:
            print(f"   ✅ MACD > Signal confirmé")
            if not macd_cross:
                print(f"   ❌ MAIS pas de croisement récent")
        else:
            print(f"   ❌ MACD < Signal → simulation FAUSSE")
        
        ib.disconnect()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    check_csco_manually()
