# strategies.py - Stratégies de trading basées sur le backtest original
import pandas as pd
import numpy as np
import logging
from typing import Tuple, Optional
from ta.momentum import RSIIndicator
from ta.trend import MACD
from config import ConfigManager

logger = logging.getLogger(__name__)

class StrategyResult:
    """Résultat d'analyse de stratégie"""
    def __init__(self, symbol: str, buy_signal: bool = False, sell_signal: bool = False,
                 indicators: dict = None, confidence: float = 0.0):
        self.symbol = symbol
        self.buy_signal = buy_signal
        self.sell_signal = sell_signal
        self.indicators = indicators or {}
        self.confidence = confidence
        self.timestamp = pd.Timestamp.now()
    
    def __str__(self):
        signals = []
        if self.buy_signal:
            signals.append("🟢 ACHAT")
        if self.sell_signal:
            signals.append("🔴 VENTE")
        if not signals:
            signals.append("⏸️ ATTENTE")
        
        return f"{self.symbol}: {' | '.join(signals)} (Conf: {self.confidence:.1%})"

class RSIMACDStrategy:
    """
    Stratégie RSI + MACD - Reproduction exacte de ton backtest original
    
    Signaux d'achat:
    - RSI < 30 (survente) OU 
    - Croisement MACD > Signal (et MACD précédent <= Signal précédent)
    
    Signaux de vente:
    - RSI > 70 (surachat) OU
    - Croisement MACD < Signal (et MACD précédent >= Signal précédent)
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager.strategy_config
        self.name = "RSI + MACD"
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule RSI et MACD selon tes paramètres exacts"""
        if df is None or len(df) < 50:
            logger.warning("Pas assez de données pour calculer les indicateurs")
            return df
        
        try:
            # RSI avec tes paramètres
            rsi = RSIIndicator(
                close=df["close"], 
                window=self.config.rsi_window
            )
            df["RSI"] = rsi.rsi()
            
            # MACD avec tes paramètres
            macd = MACD(
                close=df["close"],
                window_fast=self.config.macd_fast,
                window_slow=self.config.macd_slow,
                window_sign=self.config.macd_signal
            )
            df["MACD"] = macd.macd()
            df["MACD_signal"] = macd.macd_signal()
            
            # Nettoyage des NaN (comme dans ton code original)
            df["RSI"] = df["RSI"].fillna(method='ffill')
            df["MACD"] = df["MACD"].fillna(0)
            df["MACD_signal"] = df["MACD_signal"].fillna(0)
            
            logger.debug(f"Indicateurs calculés - RSI: {df['RSI'].iloc[-1]:.2f}, "
                        f"MACD: {df['MACD'].iloc[-1]:.4f}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul indicateurs: {e}")
            return df
    
    def analyze(self, symbol: str, df: pd.DataFrame) -> StrategyResult:
        """
        Analyse selon ta logique exacte du backtest
        """
        try:
            # Calcul des indicateurs
            df = self.calculate_indicators(df)
            
            if len(df) < 2:
                return StrategyResult(symbol)
            
            # Valeurs actuelles et précédentes
            current_rsi = df["RSI"].iloc[-1]
            current_macd = df["MACD"].iloc[-1]
            current_signal = df["MACD_signal"].iloc[-1]
            
            prev_macd = df["MACD"].iloc[-2]
            prev_signal = df["MACD_signal"].iloc[-2]
            
            # SIGNAUX D'ACHAT (logique exacte de ton backtest)
            # Condition 1: RSI < seuil de survente
            achat_rsi = current_rsi < self.config.rsi_oversold
            
            # Condition 2: Croisement MACD haussier
            achat_macd = (current_macd > current_signal) and (prev_macd <= prev_signal)
            
            # Signal d'achat final (OR comme dans ton code)
            buy_signal = achat_rsi or achat_macd
            
            # SIGNAUX DE VENTE (logique exacte de ton backtest)
            # Condition 1: RSI > seuil de surachat
            vente_rsi = current_rsi > self.config.rsi_overbought
            
            # Condition 2: Croisement MACD baissier
            vente_macd = (current_macd < current_signal) and (prev_macd >= prev_signal)
            
            # Signal de vente final (OR comme dans ton code)
            sell_signal = vente_rsi or vente_macd
            
            # Calcul de la confiance
            confidence = self._calculate_confidence(current_rsi, current_macd, current_signal, 
                                                  achat_rsi, achat_macd, vente_rsi, vente_macd)
            
            # Informations détaillées
            indicators = {
                'RSI': current_rsi,
                'MACD': current_macd,
                'MACD_Signal': current_signal,
                'RSI_Oversold': achat_rsi,
                'RSI_Overbought': vente_rsi,
                'MACD_Bullish_Cross': achat_macd,
                'MACD_Bearish_Cross': vente_macd,
                'Price': df["close"].iloc[-1]
            }
            
            result = StrategyResult(
                symbol=symbol,
                buy_signal=buy_signal,
                sell_signal=sell_signal,
                indicators=indicators,
                confidence=confidence
            )
            
            # Log détaillé si signal
            if buy_signal or sell_signal:
                logger.info(f"🎯 {result}")
                if buy_signal:
                    reasons = []
                    if achat_rsi:
                        reasons.append(f"RSI survente ({current_rsi:.1f})")
                    if achat_macd:
                        reasons.append("MACD croisement haussier")
                    logger.info(f"   Raisons achat: {', '.join(reasons)}")
                
                if sell_signal:
                    reasons = []
                    if vente_rsi:
                        reasons.append(f"RSI surachat ({current_rsi:.1f})")
                    if vente_macd:
                        reasons.append("MACD croisement baissier")
                    logger.info(f"   Raisons vente: {', '.join(reasons)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse {symbol}: {e}")
            return StrategyResult(symbol)
    
    def _calculate_confidence(self, rsi: float, macd: float, signal: float,
                            achat_rsi: bool, achat_macd: bool, 
                            vente_rsi: bool, vente_macd: bool) -> float:
        """Calcule un score de confiance pour le signal"""
        confidence = 0.0
        
        try:
            # Confiance basée sur l'intensité du RSI
            if achat_rsi:
                # Plus le RSI est bas, plus la confiance est élevée
                confidence += (self.config.rsi_oversold - rsi) / self.config.rsi_oversold
            elif vente_rsi:
                # Plus le RSI est haut, plus la confiance est élevée
                confidence += (rsi - self.config.rsi_overbought) / (100 - self.config.rsi_overbought)
            
            # Confiance basée sur la divergence MACD
            if achat_macd or vente_macd:
                macd_divergence = abs(macd - signal)
                confidence += min(macd_divergence / 0.5, 1.0)  # Normalisation
            
            # Signal double (RSI + MACD) = confiance maximale
            if (achat_rsi and achat_macd) or (vente_rsi and vente_macd):
                confidence = 1.0
            
            return min(confidence, 1.0)
            
        except:
            return 0.0

class SwingTradingStrategy:
    """
    Stratégie swing trading - Alternative basée sur les moyennes mobiles
    Inspirée de ta fonction strategie_swing_trading
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager.strategy_config
        self.name = "Swing Trading MA"
    
    def analyze(self, symbol: str, df: pd.DataFrame) -> StrategyResult:
        """Stratégie swing avec moyennes mobiles"""
        try:
            # Moyennes mobiles
            df["MA10"] = df["close"].rolling(window=10).mean()
            df["MA20"] = df["close"].rolling(window=20).mean()
            
            # RSI pour filtrage
            rsi = RSIIndicator(close=df["close"], window=14)
            df["RSI"] = rsi.rsi()
            
            if len(df) < 2:
                return StrategyResult(symbol)
            
            # Valeurs actuelles et précédentes
            current_ma10 = df["MA10"].iloc[-1]
            current_ma20 = df["MA20"].iloc[-1]
            prev_ma10 = df["MA10"].iloc[-2]
            prev_ma20 = df["MA20"].iloc[-2]
            current_rsi = df["RSI"].iloc[-1]
            
            # Signaux
            # Achat: croisement MA10 > MA20 avec RSI entre 40 et 70
            buy_signal = (prev_ma10 <= prev_ma20 and current_ma10 > current_ma20 and 
                         40 < current_rsi < 70)
            
            # Vente: croisement MA10 < MA20
            sell_signal = (prev_ma10 >= prev_ma20 and current_ma10 < current_ma20)
            
            indicators = {
                'MA10': current_ma10,
                'MA20': current_ma20,
                'RSI': current_rsi,
                'Price': df["close"].iloc[-1]
            }
            
            return StrategyResult(symbol, buy_signal, sell_signal, indicators, 0.7)
            
        except Exception as e:
            logger.error(f"❌ Erreur swing trading {symbol}: {e}")
            return StrategyResult(symbol)

class StrategyManager:
    """Gestionnaire des stratégies"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        
        # Stratégies disponibles
        self.strategies = {
            'rsi_macd': RSIMACDStrategy(config_manager),
            'swing_trading': SwingTradingStrategy(config_manager)
        }
        
        # Stratégie par défaut (celle de ton backtest)
        self.active_strategy = 'rsi_macd'
    
    def set_strategy(self, strategy_name: str):
        """Change la stratégie active"""
        if strategy_name in self.strategies:
            self.active_strategy = strategy_name
            logger.info(f"🎯 Stratégie active: {self.strategies[strategy_name].name}")
        else:
            logger.error(f"❌ Stratégie inconnue: {strategy_name}")
    
    def analyze(self, symbol: str, df: pd.DataFrame) -> StrategyResult:
        """Analyse avec la stratégie active"""
        strategy = self.strategies[self.active_strategy]
        return strategy.analyze(symbol, df)
    
    def get_strategy_info(self) -> dict:
        """Informations sur la stratégie active"""
        strategy = self.strategies[self.active_strategy]
        return {
            'name': strategy.name,
            'active': self.active_strategy,
            'available': list(self.strategies.keys())
        }

# Test du module
if __name__ == "__main__":
    # Configuration des logs
    logging.basicConfig(level=logging.INFO)
    
    # Test de la stratégie
    config = ConfigManager()
    strategy_manager = StrategyManager(config)
    
    print("🧪 Test des stratégies...")
    
    # Création de données de test
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Simulation prix avec tendance
    price_base = 100
    returns = np.random.normal(0.001, 0.02, 100)
    prices = [price_base]
    
    for ret in returns:
        prices.append(prices[-1] * (1 + ret))
    
    df_test = pd.DataFrame({
        'date': dates,
        'open': prices[:-1],
        'high': [p * 1.02 for p in prices[:-1]],
        'low': [p * 0.98 for p in prices[:-1]],
        'close': prices[1:],
        'volume': np.random.randint(1000, 10000, 100)
    })
    df_test.set_index('date', inplace=True)
    
    # Test stratégie RSI + MACD
    result = strategy_manager.analyze('TEST.PA', df_test)
    print(f"✅ Résultat: {result}")
    print(f"   Indicateurs: {result.indicators}")
    
    # Test changement de stratégie
    strategy_manager.set_strategy('swing_trading')
    result2 = strategy_manager.analyze('TEST.PA', df_test)
    print(f"✅ Swing Trading: {result2}")
    
    print("🎯 Test terminé!")