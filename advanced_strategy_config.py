# advanced_strategy_config.py - Configuration avancée des indicateurs

import json
import os
from datetime import datetime

class AdvancedStrategyConfig:
    """Configuration avancée des stratégies par secteur/symbole"""
    
    def __init__(self):
        self.default_config = {
            'rsi': {
                'window': 14,
                'oversold': 30,
                'overbought': 70,
                'weight': 0.4  # Poids dans la décision finale
            },
            'macd': {
                'fast': 12,
                'slow': 26,
                'signal': 9,
                'weight': 0.3
            },
            'bollinger': {
                'window': 20,
                'std_dev': 2,
                'weight': 0.2
            },
            'volume': {
                'sma_window': 20,
                'volume_threshold': 1.5,  # 1.5x volume moyen
                'weight': 0.1
            },
            'thresholds': {
                'min_confidence': 0.15,  # Seuil minimum
                'strong_signal': 0.6     # Signal fort
            }
        }
        
        # Configurations spécialisées par secteur
        self.sector_configs = {
            'tech': {  # AAPL, MSFT, GOOGL, META, NVDA
                'rsi': {'window': 10, 'oversold': 25, 'overbought': 75},
                'macd': {'fast': 8, 'slow': 21, 'signal': 5},
                'thresholds': {'min_confidence': 0.20}
            },
            'finance': {  # JPM, BAC, WFC
                'rsi': {'window': 21, 'oversold': 35, 'overbought': 65},
                'macd': {'fast': 15, 'slow': 30, 'signal': 12},
                'volume': {'volume_threshold': 2.0}
            },
            'healthcare': {  # JNJ, PFE, UNH
                'rsi': {'window': 18, 'oversold': 28, 'overbought': 72},
                'bollinger': {'window': 25, 'std_dev': 2.5}
            },
            'energy': {  # XOM, CVX
                'rsi': {'window': 12, 'oversold': 20, 'overbought': 80},
                'volume': {'volume_threshold': 2.5}
            }
        }
        
        # Configurations spécifiques par symbole
        self.symbol_configs = {
            'TSLA': {  # Très volatil
                'rsi': {'window': 8, 'oversold': 20, 'overbought': 80},
                'bollinger': {'std_dev': 3.0},
                'thresholds': {'min_confidence': 0.25}
            },
            'BRK.A': {  # Moins volatil
                'rsi': {'window': 25, 'oversold': 40, 'overbought': 60},
                'macd': {'fast': 20, 'slow': 40, 'signal': 15}
            }
        }
        
        # Mapping symboles → secteurs
        self.symbol_sectors = {
            'AAPL': 'tech', 'MSFT': 'tech', 'GOOGL': 'tech', 'META': 'tech', 'NVDA': 'tech',
            'AMZN': 'tech', 'NFLX': 'tech', 'CRM': 'tech', 'ORCL': 'tech',
            'JPM': 'finance', 'BAC': 'finance', 'WFC': 'finance', 'GS': 'finance',
            'JNJ': 'healthcare', 'PFE': 'healthcare', 'UNH': 'healthcare', 'ABT': 'healthcare',
            'XOM': 'energy', 'CVX': 'energy', 'SLB': 'energy', 'COP': 'energy'
        }
    
    def get_config_for_symbol(self, symbol):
        """Obtenir configuration optimale pour un symbole"""
        # Base : config par défaut
        config = self.deep_copy_config(self.default_config)
        
        # Spécialisation par secteur
        sector = self.symbol_sectors.get(symbol)
        if sector and sector in self.sector_configs:
            config = self.merge_configs(config, self.sector_configs[sector])
        
        # Spécialisation par symbole
        if symbol in self.symbol_configs:
            config = self.merge_configs(config, self.symbol_configs[symbol])
        
        return config
    
    def deep_copy_config(self, config):
        """Copie profonde de la config"""
        return json.loads(json.dumps(config))
    
    def merge_configs(self, base_config, overlay_config):
        """Merger deux configurations"""
        result = self.deep_copy_config(base_config)
        
        for section, params in overlay_config.items():
            if section in result:
                if isinstance(params, dict):
                    result[section].update(params)
                else:
                    result[section] = params
            else:
                result[section] = params
        
        return result
    
    def save_config(self, filename='advanced_strategy_config.json'):
        """Sauvegarder toute la configuration"""
        full_config = {
            'default': self.default_config,
            'sectors': self.sector_configs,
            'symbols': self.symbol_configs,
            'symbol_sectors': self.symbol_sectors,
            'last_update': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(full_config, f, indent=2)
    
    def load_config(self, filename='advanced_strategy_config.json'):
        """Charger configuration sauvegardée"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                full_config = json.load(f)
            
            self.default_config = full_config.get('default', self.default_config)
            self.sector_configs = full_config.get('sectors', self.sector_configs)
            self.symbol_configs = full_config.get('symbols', self.symbol_configs)
            self.symbol_sectors = full_config.get('symbol_sectors', self.symbol_sectors)
    
    def optimize_for_symbol(self, symbol, backtest_results):
        """Optimiser config pour un symbole basé sur backtest"""
        best_params = self.extract_best_params(backtest_results)
        
        if symbol not in self.symbol_configs:
            self.symbol_configs[symbol] = {}
        
        # Mise à jour des paramètres optimaux
        self.symbol_configs[symbol].update(best_params)
        
        # Sauvegarde
        self.save_config()
    
    def extract_best_params(self, backtest_results):
        """Extraire meilleurs paramètres du backtest"""
        # Tri par performance (profit, sharpe ratio, etc.)
        best_result = max(backtest_results, key=lambda x: x.get('sharpe_ratio', 0))
        
        return {
            'rsi': {
                'window': best_result.get('rsi_window', 14),
                'oversold': best_result.get('rsi_oversold', 30),
                'overbought': best_result.get('rsi_overbought', 70)
            },
            'macd': {
                'fast': best_result.get('macd_fast', 12),
                'slow': best_result.get('macd_slow', 26),
                'signal': best_result.get('macd_signal', 9)
            },
            'thresholds': {
                'min_confidence': best_result.get('min_confidence', 0.15)
            }
        }
    
    def get_all_symbols_configs(self):
        """Obtenir config pour tous les symboles surveillés"""
        watchlist = ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMZN', 'TSLA', 
                    'JPM', 'JNJ', 'XOM', 'CE', 'ACVA', 'CSCO']
        
        configs = {}
        for symbol in watchlist:
            configs[symbol] = self.get_config_for_symbol(symbol)
        
        return configs
    
    def print_config_summary(self):
        """Afficher résumé des configurations"""
        print("📊 CONFIGURATIONS AVANCÉES")
        print("=" * 50)
        
        print("\n🎯 PAR SECTEUR:")
        for sector, config in self.sector_configs.items():
            print(f"   {sector.upper()}:")
            if 'rsi' in config:
                rsi = config['rsi']
                print(f"     RSI: {rsi.get('window', 'def')} périodes, {rsi.get('oversold', 'def')}/{rsi.get('overbought', 'def')}")
        
        print("\n🎯 PAR SYMBOLE:")
        for symbol, config in self.symbol_configs.items():
            print(f"   {symbol}:")
            if 'rsi' in config:
                rsi = config['rsi']
                print(f"     RSI: {rsi.get('window', 'def')} périodes, {rsi.get('oversold', 'def')}/{rsi.get('overbought', 'def')}")

def demo_advanced_config():
    """Démonstration configuration avancée"""
    config_manager = AdvancedStrategyConfig()
    
    print("🧪 DEMO CONFIGURATION AVANCÉE")
    print("=" * 40)
    
    # Test différents symboles
    test_symbols = ['AAPL', 'TSLA', 'JPM', 'CE']
    
    for symbol in test_symbols:
        print(f"\n📊 CONFIG POUR {symbol}:")
        config = config_manager.get_config_for_symbol(symbol)
        
        rsi = config['rsi']
        macd = config['macd']
        thresholds = config['thresholds']
        
        print(f"   RSI: {rsi['window']} périodes, seuils {rsi['oversold']}/{rsi['overbought']}")
        print(f"   MACD: {macd['fast']}/{macd['slow']}/{macd['signal']}")
        print(f"   Confiance min: {thresholds['min_confidence']:.1%}")
        
        # Secteur
        sector = config_manager.symbol_sectors.get(symbol, 'général')
        print(f"   Secteur: {sector}")
    
    # Sauvegarde
    config_manager.save_config()
    print(f"\n💾 Configuration sauvegardée dans 'advanced_strategy_config.json'")

if __name__ == "__main__":
    demo_advanced_config()
