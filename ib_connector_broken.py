# ib_connector.py - Version corrigée pour FOREX
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
