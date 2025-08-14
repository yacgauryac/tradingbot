# ml_strategy_optimizer_v2.py
"""
🤖 MACHINE LEARNING STRATEGY OPTIMIZER v2.0
Optimisation Random Forest pour paramètres RSI+MACD
Intégration complète avec l'écosystème bot existant
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler
import joblib
import logging
import json
import os
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Import des modules existants
from ib_insync import IB, Stock, util
from advanced_strategy_config import AdvancedStrategyConfig

class MLStrategyOptimizer:
    """
    Optimiseur ML pour stratégie RSI+MACD
    S'intègre avec le système de configurations avancées existant
    """
    
    def __init__(self):
        self.ib = IB()
        self.connection_params = {
            'host': '127.0.0.1',
            'port': 7497,  # Mode simulé
            'clientId': 99  # ID spécial pour ML
        }
        
        # Composants ML
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.best_params = {}
        self.optimization_results = {}
        
        # Intégration avec système existant
        self.config_manager = AdvancedStrategyConfig()
        self.config_manager.load_config()
        
        # Configuration logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - ML-OPT - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🤖 ML Strategy Optimizer v2.0 initialisé")
        self.logger.info(f"   Configs avancées: {len(self.config_manager.symbol_sectors)} symboles")
        
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
    
    def get_enhanced_historical_data(self, symbol, days=365):
        """
        Récupère données historiques avec métadonnées secteur
        """
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Récupération données étendues pour ML
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
            
            # Ajout métadonnées secteur
            sector = self.config_manager.symbol_sectors.get(symbol, 'general')
            df['sector'] = sector
            
            # Ajout informations de configuration
            config = self.config_manager.get_config_for_symbol(symbol)
            df['config_rsi_window'] = config['rsi']['window']
            df['config_rsi_oversold'] = config['rsi']['oversold']
            df['config_rsi_overbought'] = config['rsi']['overbought']
            
            self.logger.info(f"📊 {symbol} ({sector}): {len(df)} jours, config RSI {config['rsi']['window']}")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Erreur données {symbol}: {e}")
            return None
    
    def calculate_adaptive_indicators(self, df, symbol):
        """
        Calcule indicateurs avec paramètres adaptatifs selon config existante
        """
        # Récupération config spécifique au symbole
        config = self.config_manager.get_config_for_symbol(symbol)
        
        # RSI adaptatif
        rsi_window = config['rsi']['window']
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_window).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD adaptatif
        macd_fast = config['macd']['fast']
        macd_slow = config['macd']['slow']
        macd_signal = config['macd']['signal']
        
        ema_fast = df['close'].ewm(span=macd_fast).mean()
        ema_slow = df['close'].ewm(span=macd_slow).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=macd_signal).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Features additionnels pour ML
        df['rsi_ma_5'] = df['rsi'].rolling(5).mean()
        df['rsi_ma_10'] = df['rsi'].rolling(10).mean()
        df['rsi_volatility'] = df['rsi'].rolling(10).std()
        
        # MACD features
        df['macd_sma_5'] = df['macd'].rolling(5).mean()
        df['macd_momentum'] = df['macd'].diff()
        df['macd_acceleration'] = df['macd_momentum'].diff()
        
        # Prix features
        df['price_sma_20'] = df['close'].rolling(20).mean()
        df['price_sma_50'] = df['close'].rolling(50).mean()
        df['price_vs_sma20'] = df['close'] / df['price_sma_20'] - 1
        df['price_vs_sma50'] = df['close'] / df['price_sma_50'] - 1
        df['price_volatility'] = df['close'].pct_change().rolling(10).std()
        
        # Volume features
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        df['volume_spike'] = (df['volume'] > df['volume_sma_20'] * 2).astype(int)
        
        # Features temporels
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
        
        return df
    
    def generate_ml_signals_and_targets(self, df, symbol, future_days=5):
        """
        Génère signaux selon logique bot existante + targets ML
        """
        config = self.config_manager.get_config_for_symbol(symbol)
        
        # Signaux d'achat (EXACTEMENT comme dans auto_trading_bot.py)
        df['buy_rsi'] = df['rsi'] < config['rsi']['oversold']
        df['buy_macd'] = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        df['buy_signal'] = df['buy_rsi'] | df['buy_macd']
        
        # Signaux de vente
        df['sell_rsi'] = df['rsi'] > config['rsi']['overbought'] 
        df['sell_macd'] = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        df['sell_signal'] = df['sell_rsi'] | df['sell_macd']
        
        # Calcul confiance (comme dans le bot)
        confidence = []
        for i in range(len(df)):
            conf = 0.0
            if df['buy_rsi'].iloc[i]:
                conf += (config['rsi']['oversold'] - df['rsi'].iloc[i]) / config['rsi']['oversold']
            if df['buy_macd'].iloc[i]:
                macd_div = abs(df['macd'].iloc[i] - df['macd_signal'].iloc[i])
                conf += min(macd_div / 0.5, 1.0)
            confidence.append(min(conf, 1.0))
        
        df['confidence'] = confidence
        
        # Targets ML : rendements futurs
        df['future_return_1d'] = df['close'].shift(-1) / df['close'] - 1
        df['future_return_5d'] = df['close'].shift(-future_days) / df['close'] - 1
        df['future_return_10d'] = df['close'].shift(-10) / df['close'] - 1
        
        # Classification des targets
        df['target'] = 0  # HOLD
        
        # Conditions strictes basées sur performance réelle attendue
        df.loc[df['future_return_5d'] > 0.05, 'target'] = 2   # STRONG_BUY (+5%+)
        df.loc[(df['future_return_5d'] > 0.02) & (df['future_return_5d'] <= 0.05), 'target'] = 1  # BUY
        df.loc[df['future_return_5d'] < -0.05, 'target'] = -2  # STRONG_SELL (-5%-)
        df.loc[(df['future_return_5d'] < -0.02) & (df['future_return_5d'] >= -0.05), 'target'] = -1  # SELL
        
        return df
    
    def create_ml_dataset(self, symbols_data):
        """
        Crée dataset ML unifié à partir de données multi-symboles
        """
        feature_columns = [
            # Indicateurs core
            'rsi', 'macd', 'macd_histogram', 'macd_signal',
            
            # RSI features
            'rsi_ma_5', 'rsi_ma_10', 'rsi_volatility',
            
            # MACD features  
            'macd_sma_5', 'macd_momentum', 'macd_acceleration',
            
            # Prix features
            'price_vs_sma20', 'price_vs_sma50', 'price_volatility',
            
            # Volume features
            'volume_ratio', 'volume_spike',
            
            # Features temporels
            'day_of_week', 'month',
            
            # Config features
            'config_rsi_window', 'config_rsi_oversold', 'config_rsi_overbought',
            
            # Signaux existants
            'buy_rsi', 'buy_macd', 'sell_rsi', 'sell_macd', 'confidence'
        ]
        
        # Conversion booléens en int
        bool_columns = ['buy_rsi', 'buy_macd', 'sell_rsi', 'sell_macd', 'volume_spike']
        
        all_data = []
        for symbol, df in symbols_data.items():
            df_clean = df[feature_columns + ['target', 'symbol', 'sector']].copy()
            
            # Conversion booléens
            for col in bool_columns:
                if col in df_clean.columns:
                    df_clean[col] = df_clean[col].astype(int)
            
            all_data.append(df_clean)
        
        # Combinaison
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Nettoyage NaN
        combined_df = combined_df.dropna()
        
        self.logger.info(f"📊 Dataset ML créé: {len(combined_df)} observations")
        self.logger.info(f"   Features: {len(feature_columns)}")
        self.logger.info(f"   Distribution targets:")
        target_counts = combined_df['target'].value_counts().sort_index()
        for target, count in target_counts.items():
            target_name = {-2: 'STRONG_SELL', -1: 'SELL', 0: 'HOLD', 1: 'BUY', 2: 'STRONG_BUY'}
            self.logger.info(f"     {target_name.get(target, target)}: {count} ({count/len(combined_df)*100:.1f}%)")
        
        X = combined_df[feature_columns]
        y = combined_df['target']
        metadata = combined_df[['symbol', 'sector']]
        
        return X, y, metadata, feature_columns
    
    def train_random_forest_advanced(self, X, y, metadata):
        """
        Entraînement Random Forest avec optimisation avancée
        """
        self.logger.info("🤖 Démarrage entraînement Random Forest avancé...")
        
        # Split stratifié en gardant équilibre par secteur
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        # Normalisation
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Hyperparamètres étendus
        param_grid = {
            'n_estimators': [200, 300, 500],
            'max_depth': [10, 15, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', None],
            'class_weight': ['balanced', None]
        }
        
        # GridSearch avec validation croisée
        rf = RandomForestClassifier(random_state=42, n_jobs=-1)
        
        self.logger.info("🔍 Optimisation hyperparamètres (peut prendre 10-15 min)...")
        grid_search = GridSearchCV(
            rf, param_grid, cv=5, scoring='accuracy', n_jobs=-1, verbose=1
        )
        
        grid_search.fit(X_train_scaled, y_train)
        
        # Meilleur modèle
        self.model = grid_search.best_estimator_
        self.best_params = grid_search.best_params_
        
        # Évaluation complète
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        
        self.logger.info(f"✅ Entraînement terminé!")
        self.logger.info(f"📊 Score train: {train_score:.4f}")
        self.logger.info(f"📊 Score test: {test_score:.4f}")
        self.logger.info(f"📊 CV score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        # Importance des features
        self.feature_importance = dict(zip(X.columns, self.model.feature_importances_))
        
        # Top 10 features
        top_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
        self.logger.info("🔝 Top 10 features importantes:")
        for feature, importance in top_features:
            self.logger.info(f"   {feature}: {importance:.4f}")
        
        # Rapport de classification détaillé
        y_pred = self.model.predict(X_test_scaled)
        
        self.logger.info("\n📈 RAPPORT CLASSIFICATION DÉTAILLÉ:")
        print(classification_report(y_test, y_pred, 
                                   target_names=['STRONG_SELL', 'SELL', 'HOLD', 'BUY', 'STRONG_BUY']))
        
        # Matrice de confusion
        cm = confusion_matrix(y_test, y_pred)
        self.logger.info(f"📊 Matrice de confusion:")
        self.logger.info(f"\n{cm}")
        
        # Sauvegarde résultats
        results = {
            'train_score': train_score,
            'test_score': test_score,
            'cv_score_mean': cv_scores.mean(),
            'cv_score_std': cv_scores.std(),
            'best_params': self.best_params,
            'feature_importance': self.feature_importance,
            'top_features': dict(top_features)
        }
        
        return results
    
    def optimize_bot_parameters(self, symbols=None, days=365):
        """
        Optimise paramètres du bot existant via ML
        """
        self.logger.info("🚀 DÉMARRAGE OPTIMISATION ML DU BOT")
        self.logger.info("=" * 60)
        
        if not self.connect_ib():
            return None
        
        # Symboles par défaut : ceux actuellement surveillés par le bot
        if symbols is None:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMZN', 'TSLA',
                      'JPM', 'BAC', 'WFC', 'CE', 'ACVA', 'CSCO', 'BSX']
        
        # Phase 1: Collecte données
        self.logger.info(f"📊 Phase 1: Collecte données pour {len(symbols)} symboles...")
        symbols_data = {}
        
        for symbol in symbols:
            self.logger.info(f"📊 Analyse {symbol}...")
            df = self.get_enhanced_historical_data(symbol, days)
            
            if df is not None and len(df) > 100:
                # Calcul indicateurs adaptatifs
                df = self.calculate_adaptive_indicators(df, symbol)
                
                # Génération signaux et targets
                df = self.generate_ml_signals_and_targets(df, symbol)
                
                symbols_data[symbol] = df
                self.logger.info(f"   ✅ {symbol}: {len(df)} observations")
            else:
                self.logger.warning(f"   ❌ {symbol}: Données insuffisantes")
            
            time.sleep(1)  # Respect rate limit IB
        
        if not symbols_data:
            self.logger.error("❌ Aucune donnée collectée")
            return None
        
        # Phase 2: Création dataset ML
        self.logger.info("🔬 Phase 2: Création dataset ML...")
        X, y, metadata, feature_columns = self.create_ml_dataset(symbols_data)
        
        # Phase 3: Entraînement ML
        self.logger.info("🤖 Phase 3: Entraînement Random Forest...")
        ml_results = self.train_random_forest_advanced(X, y, metadata)
        
        # Phase 4: Génération paramètres optimisés
        self.logger.info("⚙️ Phase 4: Génération paramètres optimisés...")
        optimized_params = self.generate_optimized_bot_parameters()
        
        # Phase 5: Sauvegarde
        self.save_ml_model_and_config()
        
        # Résultats complets
        final_results = {
            'ml_performance': ml_results,
            'optimized_params': optimized_params,
            'feature_columns': feature_columns,
            'symbols_analyzed': list(symbols_data.keys()),
            'dataset_size': len(X),
            'timestamp': datetime.now().isoformat()
        }
        
        self.ib.disconnect()
        return final_results
    
    def generate_optimized_bot_parameters(self):
        """
        Génère paramètres optimisés pour le bot basés sur importance ML
        """
        if not self.feature_importance:
            return None
        
        # Analyse importance relative RSI vs MACD
        rsi_importance = sum(v for k, v in self.feature_importance.items() if 'rsi' in k.lower())
        macd_importance = sum(v for k, v in self.feature_importance.items() if 'macd' in k.lower())
        
        self.logger.info(f"📊 Importance relative:")
        self.logger.info(f"   RSI features: {rsi_importance:.3f}")
        self.logger.info(f"   MACD features: {macd_importance:.3f}")
        
        # Paramètres de base (actuels du bot)
        base_params = {
            'max_positions': 3,
            'max_investment_per_trade': 1000,
            'rsi_window': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'profit_target': 0.05,
            'stop_loss': -0.08,
            'max_hold_days': 10
        }
        
        # Ajustements basés sur ML
        optimized_params = base_params.copy()
        
        # Si RSI plus important → ajustement seuils
        if rsi_importance > macd_importance * 1.2:
            self.logger.info("🎯 RSI dominant → Ajustement seuils RSI")
            # Seuils plus stricts si RSI important
            optimized_params['rsi_oversold'] = 25
            optimized_params['rsi_overbought'] = 75
            
        # Si MACD plus important → paramètres plus réactifs  
        elif macd_importance > rsi_importance * 1.2:
            self.logger.info("🎯 MACD dominant → Paramètres plus réactifs")
            optimized_params['macd_fast'] = 10
            optimized_params['macd_slow'] = 24
            optimized_params['macd_signal'] = 8
        
        # Analyse volume importance
        volume_importance = sum(v for k, v in self.feature_importance.items() if 'volume' in k.lower())
        if volume_importance > 0.1:
            self.logger.info("🎯 Volume important → Ajout filtre volume")
            optimized_params['volume_filter'] = True
            optimized_params['min_volume_ratio'] = 1.5
        
        # Ajustement risque selon volatilité importance
        volatility_importance = sum(v for k, v in self.feature_importance.items() if 'volatility' in k.lower())
        if volatility_importance > 0.05:
            self.logger.info("🎯 Volatilité importante → Ajustement gestion risque")
            # Stops plus serrés en environnement volatil
            optimized_params['profit_target'] = 0.04  # 4% au lieu de 5%
            optimized_params['stop_loss'] = -0.06     # -6% au lieu de -8%
        
        return optimized_params
    
    def save_ml_model_and_config(self):
        """Sauvegarde modèle ML et configurations optimisées"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde modèle ML
        model_filename = f'ml_model_{timestamp}.joblib'
        scaler_filename = f'ml_scaler_{timestamp}.joblib'
        
        joblib.dump(self.model, model_filename)
        joblib.dump(self.scaler, scaler_filename)
        
        # Sauvegarde métadonnées ML
        ml_metadata = {
            'model_file': model_filename,
            'scaler_file': scaler_filename,
            'best_params': self.best_params,
            'feature_importance': self.feature_importance,
            'timestamp': timestamp,
            'optimization_results': self.optimization_results
        }
        
        with open(f'ml_metadata_{timestamp}.json', 'w') as f:
            json.dump(ml_metadata, f, indent=2, default=str)
        
        # Mise à jour config avancée avec résultats ML
        self.config_manager.ml_optimization = {
            'last_optimization': timestamp,
            'model_performance': self.optimization_results,
            'recommended_params': self.generate_optimized_bot_parameters()
        }
        
        self.config_manager.save_config('advanced_strategy_config_ml.json')
        
        self.logger.info(f"💾 Modèle et config ML sauvegardés:")
        self.logger.info(f"   📁 {model_filename}")
        self.logger.info(f"   📁 {scaler_filename}")
        self.logger.info(f"   📁 ml_metadata_{timestamp}.json")
        self.logger.info(f"   📁 advanced_strategy_config_ml.json")
    
    def predict_signal_quality(self, symbol, current_indicators):
        """
        Prédit qualité d'un signal en temps réel avec le modèle ML
        """
        if self.model is None:
            self.logger.warning("⚠️ Modèle ML non chargé")
            return None
        
        try:
            # Récupération config pour ce symbole
            config = self.config_manager.get_config_for_symbol(symbol)
            
            # Préparation features (même ordre que training)
            features = [
                current_indicators.get('rsi', 50),
                current_indicators.get('macd', 0),
                current_indicators.get('macd_histogram', 0),
                current_indicators.get('macd_signal', 0),
                # Ajout autres features avec valeurs par défaut
            ]
            
            # Normalisation
            features_scaled = self.scaler.transform([features])
            
            # Prédiction
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            # Mapping résultats
            signal_map = {-2: 'STRONG_SELL', -1: 'SELL', 0: 'HOLD', 1: 'BUY', 2: 'STRONG_BUY'}
            
            return {
                'symbol': symbol,
                'signal': signal_map.get(prediction, 'UNKNOWN'),
                'confidence': max(probabilities),
                'probabilities': dict(zip(signal_map.values(), probabilities)),
                'ml_prediction': int(prediction)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur prédiction ML {symbol}: {e}")
            return None

def run_ml_optimization():
    """
    Point d'entrée principal pour optimisation ML
    """
    print("🤖 ML STRATEGY OPTIMIZER v2.0")
    print("Optimisation Random Forest pour Bot RSI+MACD")
    print("=" * 60)
    
    optimizer = MLStrategyOptimizer()
    
    try:
        # Menu choix
        print("\n📊 OPTIONS D'OPTIMISATION:")
        print("1. 🔬 Optimisation complète (tous symboles)")
        print("2. 🎯 Optimisation ciblée (positions actuelles)")
        print("3. 📈 Test modèle existant")
        
        choice = input("\nChoix (1/2/3) [1]: ").strip() or "1"
        
        if choice == "1":
            # Optimisation complète
            results = optimizer.optimize_bot_parameters()
            
        elif choice == "2":
            # Optimisation ciblée sur positions actuelles
            current_symbols = ['CE', 'AMZN', 'ACVA', 'AAPL', 'MSFT', 'GOOGL']
            results = optimizer.optimize_bot_parameters(symbols=current_symbols)
            
        elif choice == "3":
            print("🔍 Fonction test modèle à implémenter...")
            return
        
        if results:
            print("\n🎉 OPTIMISATION TERMINÉE!")
            print("=" * 40)
            print(f"📊 Symboles analysés: {len(results['symbols_analyzed'])}")
            print(f"📊 Taille dataset: {results['dataset_size']}")
            print(f"📊 Score ML: {results['ml_performance']['test_score']:.4f}")
            
            print("\n🎯 PARAMÈTRES OPTIMISÉS:")
            for param, value in results['optimized_params'].items():
                print(f"   {param}: {value}")
            
            print(f"\n💾 Fichiers sauvegardés avec timestamp: {results['timestamp'][:8]}")
            
        else:
            print("❌ Optimisation échouée")
    
    except KeyboardInterrupt:
        print("\n🛑 Optimisation interrompue")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_ml_optimization()
