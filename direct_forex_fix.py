# direct_forex_fix.py - Fix direct sans regex compliqué

def create_new_ib_connector():
    """Crée un nouveau ib_connector.py corrigé"""
    
    new_code = '''# ib_connector.py - Version corrigée pour FOREX
import asyncio
import logging
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from ib_insync import *
from config import ConfigManager

logger = logging.getLogger(__name__)

class IBConnector:
    """Gestionnaire de connexion et communication avec Interactive Brokers"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.ib = IB()
        self.is_connected = False
        self.account_info = {}
        self.contracts_cache = {}
        
    async def connect(self) -> bool:
        """Connexion à Interactive Brokers"""
        try:
            logger.info(f"🔌 Tentative de connexion à IB...")
            logger.info(f"   Host: {self.config.ib_config.host}")
            logger.info(f"   Port: {self.config.ib_config.port}")
            logger.info(f"   Mode: {self.config.get_trading_mode()}")
            
            await self.ib.connectAsync(
                host=self.config.ib_config.host,
                port=self.config.ib_config.port,
                clientId=self.config.ib_config.client_id,
                timeout=20
            )
            
            self.is_connected = True
            logger.info("✅ Connexion IB réussie!")
            
            # Récupération info compte
            try:
                account_summary = self.ib.accountSummary()
                self.account_info = {}
                
                for item in account_summary:
                    self.account_info[item.tag] = {
                        'value': float(item.value) if item.value.replace('.', '').replace('-', '').isdigit() else item.value,
                        'currency': item.currency
                    }
                
                net_liquidation = self.account_info.get('NetLiquidation', {}).get('value', 0)
                available_funds = self.account_info.get('AvailableFunds', {}).get('value', 0)
                currency = self.account_info.get('NetLiquidation', {}).get('currency', 'EUR')
                
                logger.info(f"💰 Valeur compte: {net_liquidation:,.2f} {currency}")
                logger.info(f"💳 Fonds disponibles: {available_funds:,.2f} {currency}")
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur récupération compte (pas grave): {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion IB: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Déconnexion propre"""
        if self.is_connected and self.ib.isConnected():
            self.ib.disconnect()
            self.is_connected = False
            logger.info("🔌 Déconnecté d'IB")
    
    def create_contract(self, symbol: str) -> Optional[Contract]:
        """Crée un contrat pour un symbole (FOREX CORRIGÉ)"""
        # Utilise le cache si disponible
        if symbol in self.contracts_cache:
            return self.contracts_cache[symbol]
        
        try:
            # FOREX - Format "EUR.USD" 
            if "." in symbol and len(symbol) == 7:
                base, quote = symbol.split(".")
                if len(base) == 3 and len(quote) == 3:
                    # Création contrat FOREX (CORRIGÉ)
                    forex_symbol = base + quote  # "EUR.USD" -> "EURUSD"
                    contract = Forex(forex_symbol)
                    
                    # Qualification du contrat
                    self.ib.qualifyContracts(contract)
                    
                    # Mise en cache
                    self.contracts_cache[symbol] = contract
                    
                    logger.info(f"✅ Contrat FOREX créé: {symbol} -> {forex_symbol}")
                    return contract
            
            # Actions françaises (CAC40)
            if symbol.endswith('.PA'):
                base_symbol = symbol.replace('.PA', '')
                contract = Stock(base_symbol, 'SBF', 'EUR')
            # Actions américaines
            elif symbol.endswith('.US'):
                base_symbol = symbol.replace('.US', '')
                contract = Stock(base_symbol, 'SMART', 'USD')
            else:
                # Par défaut, essaie SMART pour actions
                contract = Stock(symbol, 'SMART', 'USD')
            
            # Qualification du contrat
            self.ib.qualifyContracts(contract)
            
            # Mise en cache
            self.contracts_cache[symbol] = contract
            
            logger.debug(f"✅ Contrat créé pour {symbol}: {contract}")
            return contract
            
        except Exception as e:
            logger.error(f"❌ Erreur création contrat {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, duration: str = '30 D', 
                                bar_size: str = '1 day') -> Optional[pd.DataFrame]:
        """Récupère les données historiques"""
        contract = self.create_contract(symbol)
        if not contract:
            return None
        
        try:
            bars = self.ib.reqHistoricalData(
                contract=contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )
            
            if not bars:
                logger.warning(f"⚠️  Aucune donnée historique pour {symbol}")
                return None
            
            # Conversion en DataFrame
            df = util.df(bars)
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            df.set_index('date', inplace=True)
            df.index = pd.to_datetime(df.index)
            
            logger.debug(f"📊 Données {symbol}: {len(df)} barres")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur données historiques {symbol}: {e}")
            return None
    
    def get_positions(self) -> Dict[str, Dict]:
        """Récupère les positions actuelles"""
        try:
            positions = self.ib.positions()
            current_positions = {}
            
            for pos in positions:
                if pos.position == 0:
                    continue
                
                # Reconstruction du symbole
                symbol = pos.contract.symbol
                if pos.contract.exchange == 'SBF':
                    symbol += '.PA'
                elif pos.contract.exchange in ['NASDAQ', 'NYSE']:
                    symbol += '.US'
                
                current_positions[symbol] = {
                    'quantity': pos.position,
                    'avg_cost': pos.avgCost,
                    'market_price': pos.marketPrice,
                    'market_value': pos.marketValue,
                    'unrealized_pnl': pos.unrealizedPNL,
                    'contract': pos.contract
                }
            
            logger.debug(f"📊 Positions actuelles: {len(current_positions)}")
            return current_positions
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération positions: {e}")
            return {}
    
    async def place_order(self, symbol: str, action: str, quantity: int, 
                         order_type: str = 'MKT') -> Optional[Trade]:
        """Passe un ordre"""
        contract = self.create_contract(symbol)
        if not contract:
            logger.error(f"❌ Impossible de créer contrat pour {symbol}")
            return None
        
        try:
            if order_type == 'MKT':
                order = MarketOrder(action.upper(), quantity)
            else:
                order = MarketOrder(action.upper(), quantity)
            
            # Passage de l'ordre
            trade = self.ib.placeOrder(contract, order)
            
            logger.info(f"📋 Ordre passé: {action} {quantity} {symbol} (ID: {trade.order.orderId})")
            
            await asyncio.sleep(1)
            
            return trade
            
        except Exception as e:
            logger.error(f"❌ Erreur ordre {symbol}: {e}")
            return None
    
    def calculate_position_size(self, price: float) -> int:
        """Calcule la taille de position selon la configuration"""
        try:
            available_funds = self.account_info.get('AvailableFunds', {}).get('value', 
                                                   self.config.trading_config.capital_initial)
            
            max_investment = available_funds * self.config.trading_config.position_size_pct
            quantity = int(max_investment / price)
            quantity = max(1, quantity)
            
            logger.debug(f"💰 Taille position: {quantity} à {price:.2f}")
            return quantity
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul position: {e}")
            return 1
    
    def is_market_open(self) -> bool:
        """Vérifie si le marché est ouvert"""
        now = datetime.now()
        current_time = now.hour + now.minute / 60.0
        
        is_weekday = now.weekday() < 5
        is_trading_hours = (self.config.system_config.market_open_hour <= 
                           current_time <= 
                           self.config.system_config.market_close_hour)
        
        return is_weekday and is_trading_hours
    
    async def health_check(self) -> bool:
        """Vérification de l'état de la connexion"""
        try:
            if not self.is_connected or not self.ib.isConnected():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Health check échoué: {e}")
            return False
'''
    
    # Sauvegarde de l'ancien fichier
    try:
        import shutil
        shutil.copy("ib_connector.py", "ib_connector_old.py")
        print("💾 Sauvegarde: ib_connector_old.py")
    except:
        pass
    
    # Écrit le nouveau fichier
    with open("ib_connector.py", "w", encoding='utf-8') as f:
        f.write(new_code)
    
    print("✅ Nouveau ib_connector.py créé avec support FOREX!")

def create_quick_us_stocks_alternative():
    """Alternative rapide: actions US qui marchent"""
    
    config = {
        "ib": {
            "host": "127.0.0.1",
            "port": 7497,
            "client_id": 1
        },
        "trading": {
            "capital_initial": 10000,
            "position_size_pct": 0.05,
            "max_positions": 4,
            "stop_loss_pct": 0.02,
            "take_profit_pct": 0.03,
            "frais_pourcentage": 0.0005
        },
        "strategy": {
            "rsi_window": 14,
            "rsi_oversold": 25,
            "rsi_overbought": 75,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9
        },
        "system": {
            "market_open_hour": 0.0,
            "market_close_hour": 23.99,
            "analysis_interval": 180,
            "log_level": "INFO",
            "tickers": ["AAPL", "MSFT", "GOOGL", "TSLA"]  # Actions qui marchent à coup sûr
        }
    }
    
    import json
    with open("trading_config_us.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Config US Stocks créée: trading_config_us.json")

def main():
    print("🔧 FIX FOREX DIRECT")
    print("=" * 25)
    
    print("\n📊 OPTION 1 - Fix FOREX complet:")
    create_new_ib_connector()
    
    print("\n🇺🇸 OPTION 2 - Alternative US Stocks:")
    create_quick_us_stocks_alternative()
    
    print("\n🚀 CHOIX:")
    print("1. FOREX: python trading_bot.py")
    print("2. US Stocks: Remplace trading_config.json par trading_config_us.json")
    print("   puis: python trading_bot.py")
    
    print("\n💡 RECOMMANDATION:")
    print("   Teste d'abord OPTION 2 (US Stocks) pour voir le bot marcher")
    print("   Puis on reviendra au FOREX après")

if __name__ == "__main__":
    main()