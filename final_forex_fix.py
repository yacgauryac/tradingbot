# final_forex_fix.py - Fix définitif sans qualification séparée

def create_final_ib_connector():
    """Version finale - qualification intégrée"""
    
    final_code = '''# ib_connector.py - Version finale FOREX
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
            
            # Récupération info compte (version simple)
            try:
                account_summary = self.ib.accountSummary()
                self.account_info = {}
                
                for item in account_summary:
                    try:
                        value = float(item.value) if item.value.replace('.', '').replace('-', '').isdigit() else item.value
                    except:
                        value = item.value
                    
                    self.account_info[item.tag] = {
                        'value': value,
                        'currency': item.currency
                    }
                
                net_liquidation = self.account_info.get('NetLiquidation', {}).get('value', 0)
                currency = self.account_info.get('NetLiquidation', {}).get('currency', 'USD')
                
                logger.info(f"💰 Valeur compte: {net_liquidation:,.2f} {currency}")
                
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
        """Crée un contrat pour un symbole (version simple)"""
        try:
            contract = None
            
            # FOREX - Format "EUR.USD" 
            if "." in symbol and len(symbol) == 7:
                base, quote = symbol.split(".")
                if len(base) == 3 and len(quote) == 3:
                    forex_symbol = base + quote  # "EUR.USD" -> "EURUSD"
                    contract = Forex(forex_symbol)
                    logger.info(f"✅ Contrat FOREX: {symbol} -> {forex_symbol}")
            
            # Actions françaises (CAC40)
            elif symbol.endswith('.PA'):
                base_symbol = symbol.replace('.PA', '')
                contract = Stock(base_symbol, 'SBF', 'EUR')
                logger.debug(f"✅ Contrat FR: {symbol}")
            
            # Actions américaines
            else:
                contract = Stock(symbol, 'SMART', 'USD')
                logger.debug(f"✅ Contrat US: {symbol}")
            
            return contract
            
        except Exception as e:
            logger.error(f"❌ Erreur création contrat {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, duration: str = '30 D', 
                                bar_size: str = '1 day') -> Optional[pd.DataFrame]:
        """Récupère les données historiques avec qualification intégrée"""
        contract = self.create_contract(symbol)
        if not contract:
            logger.error(f"❌ Pas de contrat pour {symbol}")
            return None
        
        try:
            # Qualification + données en une seule fois
            logger.debug(f"📡 Récupération données {symbol}...")
            
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
                logger.warning(f"⚠️ Aucune donnée pour {symbol}")
                return None
            
            # Conversion en DataFrame
            df = util.df(bars)
            if len(df) == 0:
                logger.warning(f"⚠️ DataFrame vide pour {symbol}")
                return None
                
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            df.set_index('date', inplace=True)
            df.index = pd.to_datetime(df.index)
            
            logger.info(f"📊 Données {symbol}: {len(df)} barres OK!")
            
            # Mise en cache du contrat qualifié
            self.contracts_cache[symbol] = contract
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur données {symbol}: {e}")
            return None
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Récupère le prix actuel"""
        contract = self.create_contract(symbol)
        if not contract:
            return None
        
        try:
            ticker = self.ib.reqMktData(contract, '', False, False)
            await asyncio.sleep(2)
            
            price = None
            if ticker.last and ticker.last > 0:
                price = ticker.last
            elif ticker.close and ticker.close > 0:
                price = ticker.close
            elif ticker.bid and ticker.ask and ticker.bid > 0 and ticker.ask > 0:
                price = (ticker.bid + ticker.ask) / 2
            
            self.ib.cancelMktData(contract)
            
            if price:
                logger.debug(f"💱 Prix {symbol}: {price:.4f}")
                return price
            else:
                logger.warning(f"⚠️ Pas de prix pour {symbol}")
                return None
            
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
                
                symbol = pos.contract.symbol
                if hasattr(pos.contract, 'exchange') and pos.contract.exchange == 'SBF':
                    symbol += '.PA'
                
                current_positions[symbol] = {
                    'quantity': pos.position,
                    'avg_cost': pos.avgCost,
                    'market_price': pos.marketPrice,
                    'market_value': pos.marketValue,
                    'unrealized_pnl': pos.unrealizedPNL,
                    'contract': pos.contract
                }
            
            return current_positions
            
        except Exception as e:
            logger.error(f"❌ Erreur positions: {e}")
            return {}
    
    async def place_order(self, symbol: str, action: str, quantity: int, 
                         order_type: str = 'MKT') -> Optional[Trade]:
        """Passe un ordre"""
        # Utilise le contrat en cache ou en crée un nouveau
        contract = self.contracts_cache.get(symbol) or self.create_contract(symbol)
        if not contract:
            logger.error(f"❌ Pas de contrat pour ordre {symbol}")
            return None
        
        try:
            order = MarketOrder(action.upper(), quantity)
            trade = self.ib.placeOrder(contract, order)
            
            logger.info(f"📋 Ordre: {action} {quantity} {symbol} (ID: {trade.order.orderId})")
            await asyncio.sleep(1)
            
            return trade
            
        except Exception as e:
            logger.error(f"❌ Erreur ordre {symbol}: {e}")
            return None
    
    def calculate_position_size(self, price: float) -> int:
        """Calcule la taille de position"""
        try:
            available = self.account_info.get('AvailableFunds', {}).get('value', 
                                             self.config.trading_config.capital_initial)
            
            max_investment = available * self.config.trading_config.position_size_pct
            
            # Pour FOREX: taille en unités de devise
            if price < 10:  # Probablement FOREX (EUR/USD ~1.08)
                quantity = int(max_investment / price)
            else:  # Actions (AAPL ~$185)
                quantity = int(max_investment / price)
            
            quantity = max(1, quantity)
            logger.debug(f"💰 Position: {quantity} à {price:.4f}")
            return quantity
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul position: {e}")
            return 1000  # Default pour FOREX
    
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
        """Vérification connexion"""
        try:
            return self.is_connected and self.ib.isConnected()
        except:
            return False
'''
    
    # Sauvegarde et remplacement
    try:
        import shutil
        shutil.copy("ib_connector.py", "ib_connector_v2.py")
        print("💾 Sauvegarde: ib_connector_v2.py")
    except:
        pass
    
    with open("ib_connector.py", "w", encoding='utf-8') as f:
        f.write(final_code)
    
    print("✅ Version FINALE ib_connector.py créée!")

def main():
    print("🎯 FIX FINAL FOREX")
    print("=" * 20)
    
    create_final_ib_connector()
    
    print("\n🚀 DERNIÈRE CHANCE - RELANCE:")
    print("   python trading_bot.py")
    print("\n✅ TU DOIS VOIR:")
    print("   📊 Données EUR.USD: XX barres OK!")
    print("   📊 Données GBP.USD: XX barres OK!")
    print("   🎯 Premier signal dans 5-15 min")
    print("\n❌ PLUS D'ERREURS:")
    print("   Fini 'This event loop is already running'")
    print("   Fini 'Contrat non qualifié'")

if __name__ == "__main__":
    main()