# ib_connector.py - Gestionnaire de connexion Interactive Brokers
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
        self.contracts_cache = {}  # Cache des contrats pour éviter les re-qualifications
        
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
            await self.update_account_info()
            
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
    
    async def update_account_info(self):
        """Met à jour les informations du compte"""
        try:
            account_summary = self.ib.accountSummary()
            self.account_info = {}
            
            for item in account_summary:
                self.account_info[item.tag] = {
                    'value': float(item.value) if item.value.replace('.', '').replace('-', '').isdigit() else item.value,
                    'currency': item.currency
                }
            
            # Log des infos importantes
            net_liquidation = self.account_info.get('NetLiquidation', {}).get('value', 0)
            available_funds = self.account_info.get('AvailableFunds', {}).get('value', 0)
            currency = self.account_info.get('NetLiquidation', {}).get('currency', 'EUR')
            
            logger.info(f"💰 Valeur compte: {net_liquidation:,.2f} {currency}")
            logger.info(f"💳 Fonds disponibles: {available_funds:,.2f} {currency}")
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération compte: {e}")
    
    def create_contract(self, symbol: str) -> Optional[Contract]:
        """Crée un contrat pour un symbole (FOREX-aware)"""
        # Utilise le cache si disponible
        if symbol in self.contracts_cache:
            return self.contracts_cache[symbol]
        
        try:
            # FOREX - Format "EUR.USD"
            if "." in symbol and len(symbol) == 7:
                base, quote = symbol.split(".")
                if len(base) == 3 and len(quote) == 3:
                    contract = Forex(base + quote)  # "EURUSD"
                    self.ib.qualifyContracts(contract)
                    self.contracts_cache[symbol] = contract
                    logger.debug(f"✅ Contrat FOREX créé: {symbol} -> {contract}")
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
                # Par défaut, essaie SMART
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
            
            logger.debug(f"📊 Données {symbol}: {len(df)} barres de {bars[0].date} à {bars[-1].date}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur données historiques {symbol}: {e}")
            return None
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Récupère le prix actuel d'un symbole"""
        contract = self.create_contract(symbol)
        if not contract:
            return None
        
        try:
            ticker = self.ib.reqMktData(contract, '', False, False)
            await asyncio.sleep(2)  # Attendre les données
            
            if ticker.last and ticker.last > 0:
                price = ticker.last
            elif ticker.close and ticker.close > 0:
                price = ticker.close
            else:
                logger.warning(f"⚠️  Pas de prix disponible pour {symbol}")
                return None
            
            # Arrêt du stream de données
            self.ib.cancelMktData(contract)
            
            logger.debug(f"💱 Prix {symbol}: {price}")
            return price
            
        except Exception as e:
            logger.error(f"❌ Erreur prix {symbol}: {e}")
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
            # Création de l'ordre selon le type
            if order_type == 'MKT':
                order = MarketOrder(action.upper(), quantity)
            elif order_type == 'LMT':
                # Pour les ordres limites, il faudrait ajouter le prix
                order = MarketOrder(action.upper(), quantity)  # Fallback sur market
            else:
                order = MarketOrder(action.upper(), quantity)
            
            # Passage de l'ordre
            trade = self.ib.placeOrder(contract, order)
            
            logger.info(f"📋 Ordre passé: {action} {quantity} {symbol} (ID: {trade.order.orderId})")
            
            # Attente de confirmation
            await asyncio.sleep(1)
            
            return trade
            
        except Exception as e:
            logger.error(f"❌ Erreur ordre {symbol}: {e}")
            return None
    
    def calculate_position_size(self, price: float) -> int:
        """Calcule la taille de position selon la configuration"""
        try:
            # Récupération du capital disponible
            available_funds = self.account_info.get('AvailableFunds', {}).get('value', 
                                                   self.config.trading_config.capital_initial)
            
            # Calcul de l'investissement maximum par position
            max_investment = available_funds * self.config.trading_config.position_size_pct
            
            # Calcul du nombre d'actions
            quantity = int(max_investment / price)
            
            # Minimum 1 action
            quantity = max(1, quantity)
            
            logger.debug(f"💰 Taille position: {quantity} actions à {price:.2f}€ = {quantity * price:.2f}€")
            return quantity
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul position: {e}")
            return 1
    
    def is_market_open(self) -> bool:
        """Vérifie si le marché est ouvert"""
        now = datetime.now()
        current_time = now.hour + now.minute / 60.0
        
        # Vérification jour ouvrable (lundi=0, dimanche=6)
        is_weekday = now.weekday() < 5
        
        # Vérification heures
        is_trading_hours = (self.config.system_config.market_open_hour <= 
                           current_time <= 
                           self.config.system_config.market_close_hour)
        
        return is_weekday and is_trading_hours
    
    async def health_check(self) -> bool:
        """Vérification de l'état de la connexion"""
        try:
            if not self.is_connected or not self.ib.isConnected():
                return False
            
            # Test simple avec une requête
            account_summary = self.ib.accountSummary()
            return len(account_summary) > 0
            
        except Exception as e:
            logger.error(f"❌ Health check échoué: {e}")
            return False

# Test du module
if __name__ == "__main__":
    async def test_connector():
        config = ConfigManager()
        connector = IBConnector(config)
        
        print("🧪 Test du connecteur IB...")
        
        # Test connexion
        if await connector.connect():
            print("✅ Connexion OK")
            
            # Test données historiques
            df = await connector.get_historical_data('TTE.PA', '5 D')
            if df is not None:
                print(f"✅ Données historiques: {len(df)} jours")
                print(f"   Dernier cours: {df['close'].iloc[-1]:.2f}€")
            
            # Test prix actuel
            price = await connector.get_current_price('TTE.PA')
            if price:
                print(f"✅ Prix actuel TTE: {price:.2f}€")
            
            # Test positions
            positions = connector.get_positions()
            print(f"✅ Positions: {len(positions)}")
            
            await connector.disconnect()
        else:
            print("❌ Échec connexion")
    
    # Configuration du logging pour les tests
    logging.basicConfig(level=logging.INFO)
    
    asyncio.run(test_connector())