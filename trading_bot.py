# trading_bot.py - Bot principal de trading automatique
import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd

# Imports des modules créés
from config import ConfigManager
from ib_connector import IBConnector
from strategies import StrategyManager, StrategyResult
from risk_manager import RiskManager, RiskSignal

# Configuration du logging
def setup_logging(log_level: str = "INFO"):
    """Configuration du système de logs"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('trading_bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Réduction des logs ib_insync (trop verbeux)
    logging.getLogger('ib_insync').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class TradingBot:
    """
    Bot de trading automatique basé sur tes stratégies de backtest
    
    Reproduit exactement la logique de ton script:
    - Stratégie RSI + MACD
    - Stop Loss 5% / Take Profit 8%
    - Frais 0.1%
    - Gestion des positions
    """
    
    def __init__(self, config_file: str = "trading_config.json"):
        self.config_manager = ConfigManager(config_file)
        self.ib_connector = IBConnector(self.config_manager)
        self.strategy_manager = StrategyManager(self.config_manager)
        self.risk_manager = RiskManager(self.config_manager)
        
        # État du bot
        self.is_running = False
        self.cycle_count = 0
        self.start_time = None
        self.last_analysis = {}
        
        # Statistiques
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0
        }
        
        # Configuration des signaux pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signaux pour arrêt propre"""
        logger.info(f"🛑 Signal {signum} reçu, arrêt en cours...")
        self.is_running = False
    
    async def start(self):
        """Démarrage du bot de trading"""
        try:
            logger.info("🚀 DÉMARRAGE DU BOT DE TRADING")
            logger.info("=" * 60)
            
            # Affichage de la configuration
            self.config_manager.display_summary()
            
            # Vérification mode de trading
            if not self.config_manager.is_paper_trading():
                response = input("⚠️  ATTENTION: Mode LIVE TRADING détecté!\n"
                               "Tapez 'CONFIRME' pour continuer: ")
                if response != 'CONFIRME':
                    logger.info("❌ Arrêt demandé par l'utilisateur")
                    return
            
            # Connexion à Interactive Brokers
            logger.info("🔌 Connexion à Interactive Brokers...")
            if not await self.ib_connector.connect():
                logger.error("❌ Impossible de se connecter à IB")
                return
            
            # Initialisation des positions existantes
            await self._sync_positions()
            
            # Affichage état initial
            logger.info(self.risk_manager.get_risk_report())
            
            # Démarrage de la boucle principale
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info("✅ Bot démarré avec succès!")
            logger.info("   Pour arrêter: Ctrl+C")
            
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"❌ Erreur critique: {e}")
        finally:
            await self._shutdown()
    
    async def _sync_positions(self):
        """Synchronise les positions IB avec le risk manager"""
        try:
            positions = self.ib_connector.get_positions()
            
            for symbol, pos_data in positions.items():
                if pos_data['quantity'] > 0:
                    self.risk_manager.update_position(
                        symbol=symbol,
                        quantity=pos_data['quantity'],
                        avg_cost=pos_data['avg_cost'],
                        current_price=pos_data['market_price']
                    )
                    logger.info(f"📊 Position synchronisée: {symbol}")
            
            logger.info(f"✅ {len(positions)} positions synchronisées")
            
        except Exception as e:
            logger.error(f"❌ Erreur synchronisation positions: {e}")
    
    async def _main_loop(self):
        """Boucle principale du bot"""
        logger.info("🔄 Démarrage de la boucle principale")
        
        while self.is_running:
            try:
                self.cycle_count += 1
                cycle_start = datetime.now()
                
                logger.info(f"📊 === CYCLE #{self.cycle_count} - {cycle_start.strftime('%H:%M:%S')} ===")
                
                # Vérification heures de marché
                if not self.ib_connector.is_market_open():
                    logger.info("⏰ Marché fermé - Pause 1h")
                    await asyncio.sleep(3600)
                    continue
                
                # Vérification santé de la connexion
                if not await self.ib_connector.health_check():
                    logger.error("❌ Connexion IB défaillante, tentative de reconnexion...")
                    if not await self.ib_connector.connect():
                        logger.error("❌ Reconnexion échouée, pause 5 min")
                        await asyncio.sleep(300)
                        continue
                
                # Surveillance des positions existantes
                await self._monitor_positions()
                
                # Recherche de nouvelles opportunités
                await self._scan_opportunities()
                
                # Rapport périodique (toutes les 10 boucles)
                if self.cycle_count % 10 == 0:
                    await self._periodic_report()
                
                # Calcul du temps d'attente
                cycle_duration = (datetime.now() - cycle_start).total_seconds()
                sleep_time = max(30, self.config_manager.system_config.analysis_interval - cycle_duration)
                
                logger.info(f"✅ Cycle terminé en {cycle_duration:.1f}s, pause {sleep_time:.0f}s")
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle principale: {e}")
                await asyncio.sleep(60)  # Pause en cas d'erreur
    
    async def _monitor_positions(self):
        """Surveillance des positions ouvertes (SL/TP)"""
        try:
            # Récupération positions IB
            ib_positions = self.ib_connector.get_positions()
            
            if not ib_positions:
                return
            
            logger.debug("🔍 Surveillance des positions...")
            
            for symbol, pos_data in ib_positions.items():
                if pos_data['quantity'] <= 0:
                    continue
                
                # Mise à jour du risk manager
                self.risk_manager.update_position(
                    symbol=symbol,
                    quantity=pos_data['quantity'],
                    avg_cost=pos_data['avg_cost'],
                    current_price=pos_data['market_price']
                )
                
                # Vérification SL/TP (reproduit ta logique exacte)
                risk_signal = self.risk_manager.check_stop_loss_take_profit(
                    symbol, pos_data['market_price']
                )
                
                if risk_signal:
                    # Exécution du signal de risque
                    await self._execute_risk_signal(risk_signal)
        
        except Exception as e:
            logger.error(f"❌ Erreur surveillance positions: {e}")
    
    async def _scan_opportunities(self):
        """Recherche de nouvelles opportunités de trading"""
        try:
            tickers = self.config_manager.system_config.tickers
            
            for symbol in tickers:
                # Vérification si on peut ouvrir une position
                can_open, reason = self.risk_manager.can_open_position(symbol)
                if not can_open:
                    logger.debug(f"⏸️ {symbol}: {reason}")
                    continue
                
                # Récupération des données historiques
                df = await self.ib_connector.get_historical_data(symbol, '30 D', '1 day')
                if df is None or len(df) < 50:
                    logger.debug(f"⚠️ Pas assez de données pour {symbol}")
                    continue
                
                # Analyse stratégique (ta stratégie RSI + MACD)
                result = self.strategy_manager.analyze(symbol, df)
                self.last_analysis[symbol] = result
                
                # Signal d'achat détecté
                if result.buy_signal:
                    await self._execute_buy_signal(symbol, result)
                
                # Petite pause entre symboles
                await asyncio.sleep(0.5)
        
        except Exception as e:
            logger.error(f"❌ Erreur scan opportunités: {e}")
    
    async def _execute_buy_signal(self, symbol: str, result: StrategyResult):
        """Exécute un signal d'achat"""
        try:
            # Récupération du prix actuel
            current_price = await self.ib_connector.get_current_price(symbol)
            if not current_price:
                logger.warning(f"⚠️ Prix non disponible pour {symbol}")
                return
            
            # Calcul de la taille de position
            account_info = self.ib_connector.account_info
            available_funds = account_info.get('AvailableFunds', {}).get('value', 10000)
            
            quantity = self.risk_manager.calculate_position_size(
                symbol, current_price, available_funds
            )
            
            # Estimation des frais (comme dans ton backtest)
            cost = quantity * current_price
            frais = cost * self.config_manager.trading_config.frais_pourcentage
            total_cost = cost + frais
            
            logger.info(f"🟢 SIGNAL D'ACHAT - {symbol}")
            logger.info(f"   Prix: {current_price:.2f}€")
            logger.info(f"   Quantité: {quantity}")
            logger.info(f"   Coût total: {total_cost:.2f}€ (frais: {frais:.2f}€)")
            logger.info(f"   Raison: {result.indicators}")
            
            # Passage de l'ordre
            trade = await self.ib_connector.place_order(symbol, 'BUY', quantity)
            
            if trade:
                logger.info(f"✅ Ordre d'achat passé: {symbol} - ID: {trade.order.orderId}")
                
                # Mise à jour statistiques
                self.stats['total_trades'] += 1
                
                # Attendre un peu pour que l'ordre soit exécuté
                await asyncio.sleep(2)
                
                # Mise à jour des positions
                await self._sync_positions()
            else:
                logger.error(f"❌ Échec ordre d'achat {symbol}")
        
        except Exception as e:
            logger.error(f"❌ Erreur exécution achat {symbol}: {e}")
    
    async def _execute_risk_signal(self, signal: RiskSignal):
        """Exécute un signal de gestion de risque"""
        try:
            if signal.action in ['STOP_LOSS', 'TAKE_PROFIT']:
                logger.info(f"🔴 SIGNAL DE VENTE - {signal}")
                
                # Passage de l'ordre de vente
                trade = await self.ib_connector.place_order(
                    signal.symbol, 'SELL', signal.quantity
                )
                
                if trade:
                    logger.info(f"✅ Ordre de vente passé: {signal.symbol} - ID: {trade.order.orderId}")
                    
                    # Mise à jour statistiques
                    if signal.action == 'TAKE_PROFIT':
                        self.stats['winning_trades'] += 1
                    else:
                        self.stats['losing_trades'] += 1
                    
                    # Attendre un peu pour que l'ordre soit exécuté
                    await asyncio.sleep(2)
                    
                    # Suppression de la position du risk manager
                    self.risk_manager.remove_position(signal.symbol)
                else:
                    logger.error(f"❌ Échec ordre de vente {signal.symbol}")
        
        except Exception as e:
            logger.error(f"❌ Erreur exécution signal de risque: {e}")
    
    async def _periodic_report(self):
        """Rapport périodique du bot"""
        try:
            uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            
            logger.info("=" * 60)
            logger.info("📈 RAPPORT PÉRIODIQUE")
            logger.info("=" * 60)
            logger.info(f"⏰ Uptime: {str(uptime).split('.')[0]}")
            logger.info(f"🔄 Cycles: {self.cycle_count}")
            logger.info(f"📊 Trades: {self.stats['total_trades']} "
                       f"(✅ {self.stats['winning_trades']} / "
                       f"❌ {self.stats['losing_trades']})")
            
            # Rapport de risque
            logger.info(self.risk_manager.get_risk_report())
            
            # Dernières analyses
            if self.last_analysis:
                logger.info("🔍 Dernières analyses:")
                for symbol, result in list(self.last_analysis.items())[-5:]:
                    if result.buy_signal or result.sell_signal:
                        logger.info(f"   {result}")
            
            logger.info("=" * 60)
        
        except Exception as e:
            logger.error(f"❌ Erreur rapport périodique: {e}")
    
    async def _shutdown(self):
        """Arrêt propre du bot"""
        logger.info("🛑 Arrêt du bot en cours...")
        
        try:
            # Rapport final
            if self.start_time:
                total_uptime = datetime.now() - self.start_time
                logger.info(f"⏰ Durée totale: {str(total_uptime).split('.')[0]}")
                logger.info(f"🔄 Cycles total: {self.cycle_count}")
            
            # Rapport final des positions
            logger.info("📊 RAPPORT FINAL:")
            logger.info(self.risk_manager.get_risk_report())
            
            # Déconnexion IB
            await self.ib_connector.disconnect()
            
            logger.info("✅ Bot arrêté proprement")
        
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'arrêt: {e}")

# Point d'entrée principal
async def main():
    """Point d'entrée principal du bot"""
    # Configuration des logs
    setup_logging()
    
    # Affichage de bienvenue
    print("🤖 BOT DE TRADING AUTOMATIQUE")
    print("Basé sur tes stratégies de backtest RSI + MACD")
    print("=" * 50)
    
    # Création et démarrage du bot
    bot = TradingBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)