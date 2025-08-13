# bot_fusion.py - Bot avec vraie stratégie RSI+MACD

from ib_insync import *
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime

# Configuration simple
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradingBot:
    """Bot de trading avec stratégie RSI + MACD intégrée"""
    
    def __init__(self):
        self.ib = IB()
        
        # Paramètres stratégie (identiques à votre backtest)
        self.rsi_window = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        
        print(f"🤖 Bot initialisé avec stratégie RSI+MACD")
        print(f"   RSI: {self.rsi_window} périodes, seuils {self.rsi_oversold}/{self.rsi_overbought}")
        print(f"   MACD: {self.macd_fast}/{self.macd_slow}/{self.macd_signal}")
        
        # Contexte technique des actions breakout
        self.breakout_context = {
            'CSCO': 'En zone d\'achat, breakout',
            'GOOGL': 'Breakout, nouvelle zone d\'achat', 
            'META': 'Dans l\'indice IBD Breakout',
            'MSFT': 'Breakout momentum',
            'APP': 'Proche du point d\'achat',
            'BYDDY': 'Fort momentum EV ; zone favorable',
            'BSX': 'Structure technique favorable + fondamentaux',
            'LBRT': 'Zone d\'achat solide, bon momentum'
        }
        
    def connect(self):
        """Connexion à Interactive Brokers"""
        try:
            print("\n🔌 Connexion à TWS...")
            self.ib.connect('127.0.0.1', 7497, clientId=1)
            print("✅ Connecté à TWS!")
            
            # Vérification compte
            account = self.ib.managedAccounts()[0]
            print(f"💼 Compte: {account}")
            
            return True
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return False
    
    def create_contract(self, symbol, exchange='SMART', currency='USD'):
        """Création contrat pour action"""
        try:
            contract = Stock(symbol, exchange, currency)
            self.ib.qualifyContracts(contract)
            return contract
        except Exception as e:
            print(f"❌ Erreur contrat {symbol}: {e}")
            return None
    
    def get_historical_data(self, contract, days=30):
        """Récupération données historiques"""
        try:
            bars = self.ib.reqHistoricalData(
                contract, 
                endDateTime='', 
                durationStr=f'{days} D', 
                barSizeSetting='1 day', 
                whatToShow='TRADES', 
                useRTH=1, 
                formatDate=1, 
                keepUpToDate=False
            )
            
            if not bars:
                return None
                
            # Conversion en DataFrame
            df = pd.DataFrame([{
                'date': bar.date,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume
            } for bar in bars])
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"❌ Erreur données historiques: {e}")
            return None
    
    def calculate_rsi(self, prices, window=14):
        """Calcul RSI (identique à ta.momentum.RSIIndicator)"""
        if len(prices) < window + 1:
            return pd.Series([50] * len(prices), index=prices.index)
        
        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)
        
        avg_gains = gains.rolling(window=window).mean()
        avg_losses = losses.rolling(window=window).mean()
        
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calcul MACD (identique à ta.trend.MACD)"""
        exp1 = prices.ewm(span=fast).mean()
        exp2 = prices.ewm(span=slow).mean()
        
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal).mean()
        
        return macd_line.fillna(0), signal_line.fillna(0)
    
    def analyze_symbol(self, symbol, exchange='SMART', currency='USD'):
        """Analyse complète d'un symbole selon votre stratégie"""
        print(f"\n📊 Analyse {symbol}...")
        
        try:
            # 1. Création contrat
            contract = self.create_contract(symbol, exchange, currency)
            if not contract:
                return None
            
            # 2. Récupération données
            df = self.get_historical_data(contract, days=60)  # Plus de données pour MACD
            if df is None or len(df) < 30:
                print(f"❌ Pas assez de données pour {symbol}")
                return None
            
            # 3. Calcul indicateurs
            df['RSI'] = self.calculate_rsi(df['close'], self.rsi_window)
            df['MACD'], df['MACD_signal'] = self.calculate_macd(
                df['close'], self.macd_fast, self.macd_slow, self.macd_signal
            )
            
            # 4. Valeurs actuelles et précédentes
            current_rsi = df['RSI'].iloc[-1]
            current_macd = df['MACD'].iloc[-1]
            current_signal = df['MACD_signal'].iloc[-1]
            current_price = df['close'].iloc[-1]
            
            if len(df) >= 2:
                prev_macd = df['MACD'].iloc[-2]
                prev_signal = df['MACD_signal'].iloc[-2]
            else:
                prev_macd = current_macd
                prev_signal = current_signal
            
            # 5. LOGIQUE DE VOTRE BACKTEST - SIGNAUX
            # Achat: RSI < 30 OU croisement MACD haussier
            achat_rsi = current_rsi < self.rsi_oversold
            achat_macd = (current_macd > current_signal) and (prev_macd <= prev_signal)
            buy_signal = achat_rsi or achat_macd
            
            # Vente: RSI > 70 OU croisement MACD baissier  
            vente_rsi = current_rsi > self.rsi_overbought
            vente_macd = (current_macd < current_signal) and (prev_macd >= prev_signal)
            sell_signal = vente_rsi or vente_macd
            
            # 6. Calcul confiance
            confidence = 0.0
            if achat_rsi:
                confidence += (self.rsi_oversold - current_rsi) / self.rsi_oversold
            elif vente_rsi:
                confidence += (current_rsi - self.rsi_overbought) / (100 - self.rsi_overbought)
            
            if achat_macd or vente_macd:
                macd_divergence = abs(current_macd - current_signal)
                confidence += min(macd_divergence / 0.5, 1.0)
            
            # Signal double = confiance max
            if (achat_rsi and achat_macd) or (vente_rsi and vente_macd):
                confidence = 1.0
            
            confidence = min(confidence, 1.0)
            
            # 7. Affichage résultats avec contexte technique
            print(f"💰 {symbol}: ${current_price:.2f}")
            
            # Contexte technique si disponible
            if hasattr(self, 'breakout_context') and symbol in self.breakout_context:
                print(f"🎯 Contexte: {self.breakout_context[symbol]}")
            
            print(f"📈 RSI: {current_rsi:.1f} | MACD: {current_macd:.4f} | Signal: {current_signal:.4f}")
            
            # Signaux
            if buy_signal:
                reasons = []
                if achat_rsi:
                    reasons.append(f"RSI survente ({current_rsi:.1f})")
                if achat_macd:
                    reasons.append("MACD croisement ↗️")
                print(f"🟢 SIGNAL ACHAT - Confiance: {confidence:.1%}")
                print(f"   Raisons: {', '.join(reasons)}")
                
            elif sell_signal:
                reasons = []
                if vente_rsi:
                    reasons.append(f"RSI surachat ({current_rsi:.1f})")
                if vente_macd:
                    reasons.append("MACD croisement ↘️")
                print(f"🔴 SIGNAL VENTE - Confiance: {confidence:.1%}")
                print(f"   Raisons: {', '.join(reasons)}")
                
            else:
                print(f"⏸️ PAS DE SIGNAL - RSI neutre zone")
            
            return {
                'symbol': symbol,
                'price': current_price,
                'rsi': current_rsi,
                'macd': current_macd,
                'macd_signal': current_signal,
                'buy_signal': buy_signal,
                'sell_signal': sell_signal,
                'confidence': confidence,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Erreur analyse {symbol}: {e}")
            return None
    
    def scan_watchlist(self, symbols):
        """Scan d'une liste de symboles"""
        print(f"\n🎯 SCAN DE {len(symbols)} SYMBOLES")
        print("=" * 50)
        
        results = []
        signals_found = []
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}]", end=" ")
            
            result = self.analyze_symbol(symbol)
            if result:
                results.append(result)
                
                # Collecte des signaux
                if result['buy_signal']:
                    signals_found.append(f"🟢 {symbol}: ACHAT (Conf: {result['confidence']:.1%})")
                elif result['sell_signal']:
                    signals_found.append(f"🔴 {symbol}: VENTE (Conf: {result['confidence']:.1%})")
            
            # Pause entre requêtes
            time.sleep(0.5)
        
        # Résumé final avec priorité breakout
        print(f"\n" + "=" * 50)
        print(f"📊 RÉSUMÉ DU SCAN")
        print(f"   Symboles analysés: {len(results)}")
        print(f"   Signaux détectés: {len(signals_found)}")
        
        if signals_found:
            print(f"\n🚨 SIGNAUX ACTIFS:")
            
            # Priorité aux actions breakout avec signaux
            breakout_signals = [s for s in signals_found if any(symbol in s for symbol in self.breakout_context.keys())]
            other_signals = [s for s in signals_found if s not in breakout_signals]
            
            if breakout_signals:
                print(f"   🎯 ACTIONS BREAKOUT:")
                for signal in breakout_signals:
                    print(f"   {signal} ⭐")
            
            if other_signals:
                print(f"   📊 AUTRES ACTIONS:")
                for signal in other_signals:
                    print(f"   {signal}")
        else:
            print(f"\n⏸️ Aucun signal détecté pour le moment")
        
        return results
    
    def disconnect(self):
        """Déconnexion propre"""
        if self.ib.isConnected():
            self.ib.disconnect()
            print(f"\n🔌 Déconnecté de TWS")

def main():
    """Fonction principale"""
    print("🤖 BOT DE TRADING - STRATÉGIE RSI + MACD")
    print("🎯 Reproduction exacte du backtest original")
    print("=" * 60)
    
    # Watchlist - Actions à analyser
    
    # 🎯 WATCHLIST TECHNIQUE PERSONNALISÉE
    BREAKOUT_STOCKS = {
        'CSCO': 'En zone d\'achat, breakout',
        'GOOGL': 'Breakout, nouvelle zone d\'achat', 
        'META': 'Dans l\'indice IBD Breakout',
        'MSFT': 'Breakout momentum',
        'APP': 'Proche du point d\'achat',  # AppLovin
        'BYDDY': 'Fort momentum EV ; zone favorable',  # BYD (ADR)
        'BSX': 'Structure technique favorable + fondamentaux',  # Boston Scientific
        'LBRT': 'Zone d\'achat solide, bon momentum'  # LandBridge
    }
    
    RSI_OVERSOLD = ['ACVA', 'AIV', 'CE']  # Actions RSI < 30 à surveiller
    
    CLASSIC_STOCKS = ['AAPL', 'TSLA', 'NVDA', 'AMZN', 'NFLX']
    FR_STOCKS = ['MC.PA', 'OR.PA', 'SAN.PA', 'AIR.PA']
    
    # Choix de la watchlist
    print("📋 Watchlists disponibles:")
    print("1. 🎯 Actions BREAKOUT technique (CSCO, GOOGL, META, MSFT...)")
    print("2. 📉 Actions RSI < 30 (ACVA, AIV, CE...)")
    print("3. 📊 Actions classiques (AAPL, TSLA, NVDA...)")
    print("4. 🇫🇷 Actions françaises (MC.PA, OR.PA...)")
    print("5. 🔥 TOUT analyser (breakout + RSI + classiques)")
    
    choice = input("\nVotre choix (1/2/3/4/5) [1]: ").strip() or "1"
    
    if choice == "1":
        watchlist = list(BREAKOUT_STOCKS.keys())
        print(f"\n🎯 WATCHLIST BREAKOUT sélectionnée:")
        for symbol, desc in BREAKOUT_STOCKS.items():
            print(f"   {symbol}: {desc}")
    elif choice == "2":
        watchlist = RSI_OVERSOLD
        print(f"\n📉 WATCHLIST RSI < 30 sélectionnée (retournement potentiel)")
    elif choice == "3":
        watchlist = CLASSIC_STOCKS
    elif choice == "4":
        watchlist = FR_STOCKS
    elif choice == "5":
        watchlist = list(BREAKOUT_STOCKS.keys()) + RSI_OVERSOLD + CLASSIC_STOCKS
        print(f"\n🔥 ANALYSE COMPLÈTE: {len(watchlist)} actions")
    else:
        watchlist = list(BREAKOUT_STOCKS.keys())
    
    print(f"\n🎯 Watchlist sélectionnée: {len(watchlist)} symboles")
    
    bot = TradingBot()
    
    try:
        if bot.connect():
            # Scan principal
            results = bot.scan_watchlist(watchlist)
            
            # Proposition de surveillance continue
            if results:
                print(f"\n🔄 Scan terminé! Voulez-vous surveiller en continu ? (y/n): ", end="")
                if input().lower().startswith('y'):
                    print(f"⏰ Surveillance toutes les 5 minutes (Ctrl+C pour arrêter)...")
                    try:
                        while True:
                            time.sleep(300)  # 5 minutes
                            print(f"\n🔄 Nouveau scan - {datetime.now().strftime('%H:%M:%S')}")
                            bot.scan_watchlist(watchlist)
                    except KeyboardInterrupt:
                        print(f"\n🛑 Surveillance arrêtée")
        else:
            print("❌ Impossible de se connecter à TWS")
            print("💡 Vérifiez que TWS est ouvert et configuré pour l'API")
            
    except KeyboardInterrupt:
        print(f"\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        bot.disconnect()

if __name__ == "__main__":
    main()