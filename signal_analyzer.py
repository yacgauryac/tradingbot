# signal_analyzer.py - Analyse détaillée des signaux forts

from ib_insync import *
import pandas as pd
import time
from datetime import datetime

class SignalAnalyzer:
    """Analyse approfondie des signaux détectés"""
    
    def __init__(self):
        self.ib = IB()
        
        # Signaux forts détectés
        self.strong_signals = {
            'CE': {'signal': 'ACHAT', 'confidence': 31.3},
            'ACVA': {'signal': 'ACHAT', 'confidence': 27.2}, 
            'LBRT': {'signal': 'ACHAT', 'confidence': 10.4}
        }
    
    def connect(self):
        """Connexion à TWS"""
        try:
            print("🔌 Connexion pour analyse détaillée...")
            self.ib.connect('127.0.0.1', 7497, clientId=2)  # ClientId différent
            return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def analyze_signal_details(self, symbol):
        """Analyse détaillée d'un signal"""
        print(f"\n🔍 ANALYSE DÉTAILLÉE - {symbol}")
        print("=" * 40)
        
        try:
            # Contrat
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Données étendues
            df = self.get_extended_data(contract, days=90)
            if df is None:
                return
            
            # Calculs
            df = self.calculate_all_indicators(df)
            
            # Valeurs actuelles
            current = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else current
            
            # Prix et variation
            price_change = ((current['close'] - prev['close']) / prev['close'] * 100)
            
            print(f"💰 Prix: ${current['close']:.2f} ({price_change:+.1f}%)")
            print(f"📊 Volume: {current['volume']:,}")
            
            # RSI détail
            rsi = current['RSI']
            rsi_trend = self.get_rsi_trend(df['RSI'].tail(5))
            print(f"📈 RSI: {rsi:.1f} - {self.rsi_interpretation(rsi)} - Tendance: {rsi_trend}")
            
            # MACD détail  
            macd = current['MACD']
            signal_line = current['MACD_signal']
            macd_hist = macd - signal_line
            macd_trend = self.get_macd_trend(df[['MACD', 'MACD_signal']].tail(3))
            
            print(f"📊 MACD: {macd:.4f}")
            print(f"📊 Signal: {signal_line:.4f}")
            print(f"📊 Histogram: {macd_hist:.4f} - {macd_trend}")
            
            # Raisons du signal
            print(f"\n🎯 RAISONS DU SIGNAL:")
            achat_rsi = rsi < 30
            achat_macd = (macd > signal_line) and (prev['MACD'] <= prev['MACD_signal'])
            
            if achat_rsi:
                print(f"   ✅ RSI Survente: {rsi:.1f} < 30")
            if achat_macd:
                print(f"   ✅ MACD Croisement haussier")
            if not achat_rsi and not achat_macd:
                print(f"   ⚠️ Signal faible ou conditions changeantes")
            
            # Niveaux techniques
            self.show_technical_levels(df, symbol)
            
            # Recommandation
            self.show_recommendation(symbol, rsi, macd_hist, price_change)
            
        except Exception as e:
            print(f"❌ Erreur analyse {symbol}: {e}")
    
    def get_extended_data(self, contract, days=90):
        """Récupération données étendues"""
        try:
            bars = self.ib.reqHistoricalData(
                contract, '', f'{days} D', '1 day', 'TRADES', 1, 1, False
            )
            
            if not bars:
                return None
                
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
            print(f"❌ Erreur données: {e}")
            return None
    
    def calculate_all_indicators(self, df):
        """Calcul tous les indicateurs"""
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
        
        # Moyennes mobiles
        df['MA20'] = df['close'].rolling(20).mean()
        df['MA50'] = df['close'].rolling(50).mean()
        
        return df.fillna(method='ffill').fillna(0)
    
    def rsi_interpretation(self, rsi):
        """Interprétation RSI"""
        if rsi < 20:
            return "🔴 Très survendu"
        elif rsi < 30:
            return "🟠 Survendu"
        elif rsi < 40:
            return "🟡 Faible"
        elif rsi < 60:
            return "🟢 Neutre"
        elif rsi < 70:
            return "🟡 Fort"
        elif rsi < 80:
            return "🟠 Surachat"
        else:
            return "🔴 Très surachat"
    
    def get_rsi_trend(self, rsi_series):
        """Tendance RSI sur 5 périodes"""
        if len(rsi_series) < 3:
            return "Inconnu"
        
        slope = (rsi_series.iloc[-1] - rsi_series.iloc[-3]) / 2
        if slope > 2:
            return "🔥 Hausse forte"
        elif slope > 0.5:
            return "📈 Hausse"
        elif slope > -0.5:
            return "➡️ Stable"
        elif slope > -2:
            return "📉 Baisse"
        else:
            return "❄️ Baisse forte"
    
    def get_macd_trend(self, macd_df):
        """Tendance MACD"""
        if len(macd_df) < 2:
            return "Inconnu"
        
        current_hist = macd_df['MACD'].iloc[-1] - macd_df['MACD_signal'].iloc[-1]
        prev_hist = macd_df['MACD'].iloc[-2] - macd_df['MACD_signal'].iloc[-2]
        
        if current_hist > 0 and prev_hist <= 0:
            return "🚀 Croisement haussier"
        elif current_hist < 0 and prev_hist >= 0:
            return "💥 Croisement baissier"
        elif current_hist > prev_hist:
            return "📈 Divergence croissante"
        elif current_hist < prev_hist:
            return "📉 Divergence décroissante"
        else:
            return "➡️ Stable"
    
    def show_technical_levels(self, df, symbol):
        """Niveaux techniques importants"""
        print(f"\n📊 NIVEAUX TECHNIQUES ({symbol}):")
        
        current_price = df['close'].iloc[-1]
        
        # Support/résistance sur 20 jours
        recent_high = df['high'].tail(20).max()
        recent_low = df['low'].tail(20).min()
        
        # Moyennes mobiles
        ma20 = df['MA20'].iloc[-1]
        ma50 = df['MA50'].iloc[-1]
        
        print(f"   📍 Prix actuel: ${current_price:.2f}")
        print(f"   🔴 Résistance (20j): ${recent_high:.2f} ({((recent_high/current_price-1)*100):+.1f}%)")
        print(f"   🟢 Support (20j): ${recent_low:.2f} ({((recent_low/current_price-1)*100):+.1f}%)")
        print(f"   📊 MA20: ${ma20:.2f} ({((ma20/current_price-1)*100):+.1f}%)")
        print(f"   📊 MA50: ${ma50:.2f} ({((ma50/current_price-1)*100):+.1f}%)")
    
    def show_recommendation(self, symbol, rsi, macd_hist, price_change):
        """Recommandation finale"""
        print(f"\n💡 RECOMMANDATION {symbol}:")
        
        score = 0
        reasons = []
        
        # Score RSI
        if rsi < 25:
            score += 3
            reasons.append("RSI très survendu")
        elif rsi < 30:
            score += 2
            reasons.append("RSI survendu")
        
        # Score MACD
        if macd_hist > 0:
            score += 1
            reasons.append("MACD positif")
        
        # Score prix
        if price_change < -3:
            score += 1
            reasons.append("Prix en baisse récente")
        
        if score >= 3:
            recommendation = "🟢 ACHAT FORT"
        elif score >= 2:
            recommendation = "🟡 ACHAT MODÉRÉ"
        elif score >= 1:
            recommendation = "⚠️ SURVEILLANCE"
        else:
            recommendation = "❌ ÉVITER"
        
        print(f"   {recommendation} (Score: {score}/5)")
        print(f"   Raisons: {', '.join(reasons)}")
    
    def analyze_top_signals(self):
        """Analyse des 3 signaux les plus forts"""
        print("🔍 ANALYSE DÉTAILLÉE DES SIGNAUX FORTS")
        print("=" * 60)
        
        for symbol in self.strong_signals.keys():
            self.analyze_signal_details(symbol)
            time.sleep(1)  # Pause entre analyses
    
    def disconnect(self):
        """Déconnexion"""
        if self.ib.isConnected():
            self.ib.disconnect()

def main():
    analyzer = SignalAnalyzer()
    
    try:
        if analyzer.connect():
            analyzer.analyze_top_signals()
        else:
            print("❌ Impossible de se connecter")
    except KeyboardInterrupt:
        print("\n🛑 Analyse interrompue")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        analyzer.disconnect()

if __name__ == "__main__":
    main()