# ml_strategy_optimizer.py
"""
🤖 RANDOM FOREST OPTIMIZER pour Stratégie RSI+MACD
Optimise automatiquement les paramètres de trading via Machine Learning
Intégration avec le bot existant et données Interactive Brokers
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

# Import des modules existants
from ib_insync import IB, Stock, util
import time

class MLStrategyOptimizer:
    """
    Optimiseur ML pour stratégie RSI+MACD
    """
    
    def __init__(self, connection_params=None):
        self.ib = IB()
        self.connection_params = connection_params or {
            'host': '127.0.0.1',
            'port': 7497,  # Mode simulé TWS
            'clientId': 99  # ID spécial pour ML
        }
        self.model = None
        self.scaler = StandardScaler()
        self.best_params = {}
        self.feature_importance = {}
        
        # Configuration logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - ML-OPT - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def connect_ib(self):
        """Connexion Interactive Brokers"""
        try:
            if not self.ib.isConnected():
                self.ib.connect(**self.connection_params)
                self.logger.info("✅ Connexion IB établie pour ML Optimizer")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erreur connexion IB: {e}")
            return False
    
    def get_historical_data(self, symbol, days=365):
        """
        Récupère données historiques pour entraînement ML
        """
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Récupération données sur 1 an minimum pour ML
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=f'{days} D',
                barSizeSetting='1 day',
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )
            
            if not bars:
                self.logger.warning(f"⚠️ Aucune donnée pour {symbol}")
                return None
                
            # Conversion en DataFrame
            df = util.df(bars)
            df['symbol'] = symbol
            
            self.logger.info(f"📊 {symbol}: {len(df)} jours de données récupérées")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Erreur données {symbol}: {e}")
            return None
    
    def calculate_technical_indicators(self, df, rsi_period=14, macd_fast=12, macd_slow=26, macd_signal=9):
        """
        Calcule tous les indicateurs techniques pour ML
        """
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_fast = df['close'].ewm(span=macd_fast).mean()
        ema_slow = df['close'].ewm(span=macd_slow).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=macd_signal).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Features additionnels pour ML
        df['rsi_sma_20'] = df['rsi'].rolling(20).mean()
        df['price_change_5d'] = df['close'].pct_change(5)
        df['price_change_10d'] = df['close'].pct_change(10)
        df['volatility_10d'] = df['close'].pct_change().rolling(10).std()
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        
        # Moyennes mobiles
        df['sma_20'] = df['close'].rolling(20).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        df['price_vs_sma20'] = df['close'] / df['sma_20'] - 1
        df['price_vs_sma50'] = df['close'] / df['sma_50'] - 1
        
        return df
    
    def generate_trading_signals(self, df, rsi_buy=30, rsi_sell=70):
        """
        Génère signaux d'achat/vente selon stratégie actuelle
        """
        # Signaux d'achat (logique OR comme dans le bot)
        buy_rsi = df['rsi'] < rsi_buy
        buy_macd = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        df['buy_signal'] = buy_rsi | buy_macd
        
        # Signaux de vente (logique OR)
        sell_rsi = df['rsi'] > rsi_sell
        sell_macd = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        df['sell_signal'] = sell_rsi | sell_macd
        
        return df
    
    def create_ml_features_targets(self, df, future_days=5):
        """
        Crée features et targets pour entraînement ML
        """
        # Features d'entrée
        feature_columns = [
            'rsi', 'macd', 'macd_histogram', 'rsi_sma_20',
            'price_change_5d', 'price_change_10d', 'volatility_10d',
            'volume_ratio', 'price_vs_sma20', 'price_vs_sma50'
        ]
        
        # Target : rendement futur (classification)
        df['future_return'] = df['close'].shift(-future_days) / df['close'] - 1
        
        # Classification des rendements
        df['target'] = 0  # Neutre
        df.loc[df['future_return'] > 0.05, 'target'] = 2  # Achat fort (+5%+)
        df.loc[(df['future_return'] > 0.02) & (df['future_return'] <= 0.05), 'target'] = 1  # Achat faible
        df.loc[df['future_return'] < -0.05, 'target'] = -1  # Vente (-5%-)
        
        # Nettoyage des NaN
        df = df.dropna()
        
        X = df[feature_columns]
        y = df['target']
        
        return X, y, feature_columns
    
    def train_random_forest(self, X, y):
        """
        Entraîne modèle Random Forest avec optimisation hyperparamètres
        """
        self.logger.info("🤖 Début entraînement Random Forest...")
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        # Normalisation features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # GridSearch pour optimisation hyperparamètres
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [5, 10, 15, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
        
        rf = RandomForestClassifier(random_state=42, n_jobs=-1)
        
        self.logger.info("🔍 Optimisation hyperparamètres...")
        grid_search = GridSearchCV(
            rf, param_grid, cv=5, scoring='accuracy', n_jobs=-1, verbose=1
        )
        
        grid_search.fit(X_train_scaled, y_train)
        
        # Meilleur modèle
        self.model = grid_search.best_estimator_
        self.best_params = grid_search.best_params_
        
        # Évaluation
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        self.logger.info(f"✅ Entraînement terminé!")
        self.logger.info(f"📊 Score train: {train_score:.4f}")
        self.logger.info(f"📊 Score test: {test_score:.4f}")
        
        # Importance des features
        self.feature_importance = dict(zip(X.columns, self.model.feature_importances_))
        
        # Rapport détaillé
        y_pred = self.model.predict(X_test_scaled)
        self.logger.info("\n📈 RAPPORT CLASSIFICATION:")
        print(classification_report(y_test, y_pred))
        
        return {
            'train_score': train_score,
            'test_score': test_score,
            'best_params': self.best_params,
            'feature_importance': self.feature_importance
        }
    
    def optimize_strategy_parameters(self, symbols=['AAPL', 'MSFT', 'GOOGL'], days=365):
        """
        Optimise paramètres stratégie RSI+MACD via ML
        """
        self.logger.info("🚀 DÉMARRAGE OPTIMISATION ML")
        
        if not self.connect_ib():
            return None
        
        all_data = []
        
        # Collecte données multi-symboles
        for symbol in symbols:
            self.logger.info(f"📊 Analyse {symbol}...")
            df = self.get_historical_data(symbol, days)
            
            if df is not None and len(df) > 100:
                df = self.calculate_technical_indicators(df)
                all_data.append(df)
                time.sleep(1)  # Respect rate limit IB
        
        if not all_data:
            self.logger.error("❌ Aucune donnée collectée")
            return None
        
        # Combinaison toutes les données
        combined_df = pd.concat(all_data, ignore_index=True)
        self.logger.info(f"📊 Dataset final: {len(combined_df)} observations")
        
        # Création features/targets ML
        X, y, feature_columns = self.create_ml_features_targets(combined_df)
        
        # Entraînement modèle
        results = self.train_random_forest(X, y)
        
        # Sauvegarde modèle
        self.save_model()
        
        # Génération paramètres optimisés
        optimized_params = self.generate_optimized_parameters()
        
        results['optimized_params'] = optimized_params
        results['feature_columns'] = feature_columns
        
        self.ib.disconnect()
        return results
    
    def generate_optimized_parameters(self):
        """
        Génère paramètres optimisés basés sur importance features
        """
        if not self.feature_importance:
            return None
            
        # Analyse importance RSI vs MACD
        rsi_importance = self.feature_importance.get('rsi', 0)
        macd_importance = self.feature_importance.get('macd', 0)
        
        # Ajustement paramètres selon importance ML
        base_params = {
            'rsi_window': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9
        }
        
        # Si RSI plus important → seuils plus stricts
        if rsi_importance > macd_importance:
            base_params['rsi_oversold'] = 25  # Plus strict
            base_params['rsi_overbought'] = 75
        else:
            # Si MACD plus important → paramètres plus réactifs
            base_params['macd_fast'] = 10
            base_params['macd_slow'] = 24
        
        # Paramètres risque ajustés selon volatilité moyenne detectée
        vol_importance = self.feature_importance.get('volatility_10d', 0)
        
        if vol_importance > 0.1:  # Forte importance volatilité
            base_params['profit_target'] = 0.06  # +6% au lieu de 5%
            base_params['stop_loss'] = -0.06     # -6% au lieu de 8%
        
        return base_params
    
    def predict_signal_quality(self, current_data):
        """
        Prédit qualité signal en temps réel avec ML
        """
        if self.model is None:
            return None
            
        try:
            # Préparation features
            features = self.scaler.transform([current_data])
            
            # Prédiction
            prediction = self.model.predict(features)[0]
            probabilities = self.model.predict_proba(features)[0]
            
            # Mapping prédictions
            signal_map = {-1: 'SELL', 0: 'HOLD', 1: 'BUY_WEAK', 2: 'BUY_STRONG'}
            
            return {
                'signal': signal_map.get(prediction, 'UNKNOWN'),
                'confidence': max(probabilities),
                'probabilities': dict(zip(signal_map.values(), probabilities))
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur prédiction: {e}")
            return None
    
    def save_model(self):
        """Sauvegarde modèle et paramètres"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'best_params': self.best_params,
            'feature_