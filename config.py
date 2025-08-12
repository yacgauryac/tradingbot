# config.py - Configuration centrale du système de trading
import json
import os
from dataclasses import dataclass
from typing import List

@dataclass
class IBConfig:
    """Configuration Interactive Brokers"""
    host: str = '127.0.0.1'
    port: int = 7497  # 7497 = Paper, 7496 = Live
    client_id: int = 1
    
@dataclass
class TradingConfig:
    """Configuration des paramètres de trading"""
    capital_initial: float = 10000.0
    position_size_pct: float = 0.1  # 10% du capital par position
    max_positions: int = 5
    stop_loss_pct: float = 0.05  # 5% comme dans ton backtest
    take_profit_pct: float = 0.08  # 8% comme dans ton backtest
    frais_pourcentage: float = 0.001  # 0.1% comme dans ton backtest

@dataclass
class StrategyConfig:
    """Configuration des indicateurs - reprend tes paramètres"""
    # RSI (comme dans ton script)
    rsi_window: int = 14
    rsi_oversold: int = 30  # Signal achat
    rsi_overbought: int = 70  # Signal vente
    
    # MACD (comme dans ton script)
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

@dataclass
class SystemConfig:
    """Configuration système"""
    market_open_hour: float = 9.0
    market_close_hour: float = 17.5
    analysis_interval: int = 300  # 5 minutes
    log_level: str = "INFO"
    
    # Tickers à surveiller (CAC40 populaires)
    tickers: List[str] = None
    
    def __post_init__(self):
        if self.tickers is None:
            self.tickers = [
                'AIR.PA',    # Airbus
                'MC.PA',     # LVMH
                'OR.PA',     # L'Oréal
                'SAN.PA',    # Sanofi
                'BNP.PA',    # BNP Paribas
                'TTE.PA',    # TotalEnergies
                'CAP.PA',    # Capgemini
                'CS.PA',     # AXA
            ]

class ConfigManager:
    """Gestionnaire de configuration"""
    
    def __init__(self, config_file: str = "trading_config.json"):
        self.config_file = config_file
        self.ib_config = IBConfig()
        self.trading_config = TradingConfig()
        self.strategy_config = StrategyConfig()
        self.system_config = SystemConfig()
        
        self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Mise à jour des configs
                if 'ib' in data:
                    for key, value in data['ib'].items():
                        if hasattr(self.ib_config, key):
                            setattr(self.ib_config, key, value)
                
                if 'trading' in data:
                    for key, value in data['trading'].items():
                        if hasattr(self.trading_config, key):
                            setattr(self.trading_config, key, value)
                
                if 'strategy' in data:
                    for key, value in data['strategy'].items():
                        if hasattr(self.strategy_config, key):
                            setattr(self.strategy_config, key, value)
                
                if 'system' in data:
                    for key, value in data['system'].items():
                        if hasattr(self.system_config, key):
                            setattr(self.system_config, key, value)
                            
                print(f"✅ Configuration chargée depuis {self.config_file}")
                
            except Exception as e:
                print(f"⚠️  Erreur chargement config: {e}")
                print("🔄 Utilisation des paramètres par défaut")
        else:
            print(f"📝 Création de {self.config_file} avec paramètres par défaut")
            self.save_config()
    
    def save_config(self):
        """Sauvegarde la configuration dans le fichier JSON"""
        try:
            config_data = {
                'ib': {
                    'host': self.ib_config.host,
                    'port': self.ib_config.port,
                    'client_id': self.ib_config.client_id
                },
                'trading': {
                    'capital_initial': self.trading_config.capital_initial,
                    'position_size_pct': self.trading_config.position_size_pct,
                    'max_positions': self.trading_config.max_positions,
                    'stop_loss_pct': self.trading_config.stop_loss_pct,
                    'take_profit_pct': self.trading_config.take_profit_pct,
                    'frais_pourcentage': self.trading_config.frais_pourcentage
                },
                'strategy': {
                    'rsi_window': self.strategy_config.rsi_window,
                    'rsi_oversold': self.strategy_config.rsi_oversold,
                    'rsi_overbought': self.strategy_config.rsi_overbought,
                    'macd_fast': self.strategy_config.macd_fast,
                    'macd_slow': self.strategy_config.macd_slow,
                    'macd_signal': self.strategy_config.macd_signal
                },
                'system': {
                    'market_open_hour': self.system_config.market_open_hour,
                    'market_close_hour': self.system_config.market_close_hour,
                    'analysis_interval': self.system_config.analysis_interval,
                    'log_level': self.system_config.log_level,
                    'tickers': self.system_config.tickers
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Configuration sauvegardée dans {self.config_file}")
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde config: {e}")
    
    def is_paper_trading(self) -> bool:
        """Vérifie si on est en mode Paper Trading"""
        return self.ib_config.port == 7497
    
    def get_trading_mode(self) -> str:
        """Retourne le mode de trading"""
        return "Paper Trading" if self.is_paper_trading() else "LIVE TRADING"
    
    def display_summary(self):
        """Affiche un résumé de la configuration"""
        print("=" * 60)
        print("📊 CONFIGURATION DU TRADING BOT")
        print("=" * 60)
        print(f"🔌 Connexion IB : {self.ib_config.host}:{self.ib_config.port}")
        print(f"🎯 Mode : {self.get_trading_mode()}")
        print(f"💰 Capital initial : {self.trading_config.capital_initial:,.2f}€")
        print(f"📊 Taille position : {self.trading_config.position_size_pct:.1%}")
        print(f"🛑 Stop Loss : {self.trading_config.stop_loss_pct:.1%}")
        print(f"🎯 Take Profit : {self.trading_config.take_profit_pct:.1%}")
        print(f"📈 Tickers surveillés : {len(self.system_config.tickers)}")
        print(f"   {', '.join(self.system_config.tickers[:5])}...")
        print(f"⏰ Heures trading : {self.system_config.market_open_hour}h-{self.system_config.market_close_hour}h")
        print("=" * 60)

# Test de la configuration
if __name__ == "__main__":
    config = ConfigManager()
    config.display_summary()
    
    # Test de modification
    print("\n🔧 Test modification...")
    config.trading_config.capital_initial = 5000.0
    config.save_config()
    
    # Test rechargement
    config2 = ConfigManager()
    print(f"Capital après rechargement: {config2.trading_config.capital_initial}€")