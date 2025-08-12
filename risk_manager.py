# risk_manager.py - Gestionnaire de risques et stop loss/take profit
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from config import ConfigManager

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Représentation d'une position"""
    symbol: str
    quantity: int
    avg_cost: float
    entry_time: datetime
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    
    def update_current_price(self, price: float):
        """Met à jour le prix actuel et calcule P&L"""
        self.current_price = price
        if self.avg_cost > 0:
            self.unrealized_pnl = (price - self.avg_cost) * self.quantity
            self.unrealized_pnl_pct = (price - self.avg_cost) / self.avg_cost
    
    def __str__(self):
        return f"{self.symbol}: {self.quantity}@{self.avg_cost:.2f}€ -> {self.current_price:.2f}€ ({self.unrealized_pnl_pct:+.2%})"

@dataclass
class RiskSignal:
    """Signal de gestion de risque"""
    symbol: str
    action: str  # 'STOP_LOSS', 'TAKE_PROFIT', 'REDUCE_POSITION'
    quantity: int
    reason: str
    urgency: str = 'NORMAL'  # 'LOW', 'NORMAL', 'HIGH', 'CRITICAL'
    
    def __str__(self):
        return f"{self.action} {self.symbol}: {self.quantity} - {self.reason}"

class RiskManager:
    """
    Gestionnaire de risques basé sur tes paramètres de backtest:
    - Stop Loss: 5%
    - Take Profit: 8%
    - Gestion de la taille des positions
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.positions: Dict[str, Position] = {}
        self.risk_history: List[RiskSignal] = []
        
        # Paramètres de risque (repris de ton backtest)
        self.stop_loss_pct = config_manager.trading_config.stop_loss_pct
        self.take_profit_pct = config_manager.trading_config.take_profit_pct
        self.max_positions = config_manager.trading_config.max_positions
        self.position_size_pct = config_manager.trading_config.position_size_pct
        
        logger.info(f"🛡️ Risk Manager initialisé:")
        logger.info(f"   Stop Loss: {self.stop_loss_pct:.1%}")
        logger.info(f"   Take Profit: {self.take_profit_pct:.1%}")
        logger.info(f"   Max positions: {self.max_positions}")
    
    def update_position(self, symbol: str, quantity: int, avg_cost: float, 
                       current_price: float, entry_time: datetime = None):
        """Met à jour ou crée une position"""
        if entry_time is None:
            entry_time = datetime.now()
        
        if symbol in self.positions:
            # Mise à jour position existante
            position = self.positions[symbol]
            position.quantity = quantity
            position.avg_cost = avg_cost
            position.update_current_price(current_price)
        else:
            # Nouvelle position
            position = Position(
                symbol=symbol,
                quantity=quantity,
                avg_cost=avg_cost,
                entry_time=entry_time
            )
            position.update_current_price(current_price)
            self.positions[symbol] = position
            
        logger.debug(f"📊 Position mise à jour: {position}")
    
    def remove_position(self, symbol: str):
        """Supprime une position"""
        if symbol in self.positions:
            del self.positions[symbol]
            logger.debug(f"🗑️ Position {symbol} supprimée")
    
    def check_stop_loss_take_profit(self, symbol: str, current_price: float) -> Optional[RiskSignal]:
        """
        Vérifie les stop loss et take profit selon tes paramètres exacts
        """
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        position.update_current_price(current_price)
        
        # Calcul de la variation depuis l'achat
        pnl_pct = position.unrealized_pnl_pct
        
        # STOP LOSS (comme dans ton backtest: -5%)
        if pnl_pct <= -self.stop_loss_pct:
            signal = RiskSignal(
                symbol=symbol,
                action='STOP_LOSS',
                quantity=abs(position.quantity),
                reason=f"Stop Loss déclenché: {pnl_pct:.2%} (seuil: {-self.stop_loss_pct:.1%})",
                urgency='HIGH'
            )
            
            logger.warning(f"🛑 {signal}")
            self.risk_history.append(signal)
            return signal
        
        # TAKE PROFIT (comme dans ton backtest: +8%)
        elif pnl_pct >= self.take_profit_pct:
            signal = RiskSignal(
                symbol=symbol,
                action='TAKE_PROFIT',
                quantity=abs(position.quantity),
                reason=f"Take Profit déclenché: {pnl_pct:.2%} (seuil: {self.take_profit_pct:.1%})",
                urgency='NORMAL'
            )
            
            logger.info(f"🎯 {signal}")
            self.risk_history.append(signal)
            return signal
        
        return None
    
    def check_position_limits(self) -> List[RiskSignal]:
        """Vérifie les limites de positions"""
        signals = []
        
        # Vérification nombre maximum de positions
        active_positions = len([p for p in self.positions.values() if p.quantity > 0])
        
        if active_positions > self.max_positions:
            # Trouve les positions les moins performantes à fermer
            sorted_positions = sorted(
                [(symbol, pos) for symbol, pos in self.positions.items() if pos.quantity > 0],
                key=lambda x: x[1].unrealized_pnl_pct
            )
            
            excess_positions = active_positions - self.max_positions
            for i in range(excess_positions):
                symbol, position = sorted_positions[i]
                signal = RiskSignal(
                    symbol=symbol,
                    action='REDUCE_POSITION',
                    quantity=position.quantity,
                    reason=f"Limite de positions dépassée ({active_positions}/{self.max_positions})",
                    urgency='NORMAL'
                )
                signals.append(signal)
                logger.warning(f"⚠️ {signal}")
        
        return signals
    
    def calculate_position_size(self, symbol: str, price: float, available_capital: float) -> int:
        """
        Calcule la taille de position selon tes paramètres
        """
        try:
            # Investissement maximum par position (10% du capital comme dans ton backtest)
            max_investment = available_capital * self.position_size_pct
            
            # Nombre d'actions à acheter
            quantity = int(max_investment / price)
            
            # Minimum 1 action
            quantity = max(1, quantity)
            
            # Vérification que ça ne dépasse pas les limites
            total_cost = quantity * price
            if total_cost > max_investment * 1.1:  # Marge de 10%
                quantity = int(max_investment / price)
            
            logger.debug(f"💰 Taille position {symbol}: {quantity} actions à {price:.2f}€ = {total_cost:.2f}€")
            return quantity
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul position size: {e}")
            return 1
    
    def check_drawdown(self, total_portfolio_value: float, initial_capital: float) -> Optional[RiskSignal]:
        """Vérifie le drawdown global du portefeuille"""
        if initial_capital <= 0:
            return None
        
        drawdown = (total_portfolio_value - initial_capital) / initial_capital
        
        # Alerte si perte > 20%
        if drawdown <= -0.20:
            signal = RiskSignal(
                symbol="PORTFOLIO",
                action='REDUCE_POSITION',
                quantity=0,
                reason=f"Drawdown critique: {drawdown:.2%}",
                urgency='CRITICAL'
            )
            logger.critical(f"🚨 {signal}")
            return signal
        
        # Avertissement si perte > 10%
        elif drawdown <= -0.10:
            signal = RiskSignal(
                symbol="PORTFOLIO",
                action='REDUCE_POSITION',
                quantity=0,
                reason=f"Drawdown élevé: {drawdown:.2%}",
                urgency='HIGH'
            )
            logger.warning(f"⚠️ {signal}")
            return signal
        
        return None
    
    def can_open_position(self, symbol: str) -> Tuple[bool, str]:
        """Vérifie si on peut ouvrir une nouvelle position"""
        # Vérification nombre de positions
        active_positions = len([p for p in self.positions.values() if p.quantity > 0])
        
        if active_positions >= self.max_positions:
            return False, f"Limite de positions atteinte ({active_positions}/{self.max_positions})"
        
        # Vérification si déjà une position sur ce symbole
        if symbol in self.positions and self.positions[symbol].quantity > 0:
            return False, f"Position déjà ouverte sur {symbol}"
        
        return True, "OK"
    
    def get_portfolio_summary(self) -> Dict:
        """Résumé du portefeuille"""
        active_positions = [p for p in self.positions.values() if p.quantity > 0]
        
        total_unrealized_pnl = sum(p.unrealized_pnl for p in active_positions)
        total_invested = sum(p.quantity * p.avg_cost for p in active_positions)
        
        summary = {
            'total_positions': len(active_positions),
            'total_invested': total_invested,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_unrealized_pnl_pct': (total_unrealized_pnl / total_invested) if total_invested > 0 else 0,
            'positions': [str(p) for p in active_positions],
            'stop_loss_threshold': -self.stop_loss_pct,
            'take_profit_threshold': self.take_profit_pct
        }
        
        return summary
    
    def get_risk_report(self) -> str:
        """Génère un rapport de risque"""
        summary = self.get_portfolio_summary()
        
        report = []
        report.append("=" * 50)
        report.append("📊 RAPPORT DE RISQUE")
        report.append("=" * 50)
        report.append(f"Positions actives: {summary['total_positions']}/{self.max_positions}")
        report.append(f"Capital investi: {summary['total_invested']:,.2f}€")
        report.append(f"P&L non réalisé: {summary['total_unrealized_pnl']:+,.2f}€ ({summary['total_unrealized_pnl_pct']:+.2%})")
        report.append("")
        
        if summary['positions']:
            report.append("📈 Positions détaillées:")
            for pos_str in summary['positions']:
                report.append(f"  {pos_str}")
        else:
            report.append("📭 Aucune position ouverte")
        
        report.append("")
        report.append(f"🛑 Stop Loss: {summary['stop_loss_threshold']:.1%}")
        report.append(f"🎯 Take Profit: {summary['take_profit_threshold']:.1%}")
        
        if self.risk_history:
            recent_signals = self.risk_history[-5:]  # 5 derniers signaux
            report.append("")
            report.append("⚠️ Signaux récents:")
            for signal in recent_signals:
                report.append(f"  {signal}")
        
        report.append("=" * 50)
        
        return "\n".join(report)

# Test du module
if __name__ == "__main__":
    # Configuration des logs
    logging.basicConfig(level=logging.INFO)
    
    # Test du risk manager
    config = ConfigManager()
    risk_manager = RiskManager(config)
    
    print("🧪 Test du Risk Manager...")
    
    # Simulation de positions
    risk_manager.update_position('TTE.PA', 100, 50.0, 52.0)  # +4%
    risk_manager.update_position('MC.PA', 50, 800.0, 760.0)  # -5% (stop loss)
    risk_manager.update_position('AIR.PA', 200, 100.0, 108.5)  # +8.5% (take profit)
    
    print("\n📊 Résumé portefeuille:")
    summary = risk_manager.get_portfolio_summary()
    for key, value in summary.items():
        if key != 'positions':
            print(f"  {key}: {value}")
    
    print("\n🛡️ Test signaux de risque:")
    
    # Test stop loss
    signal = risk_manager.check_stop_loss_take_profit('MC.PA', 760.0)
    if signal:
        print(f"  {signal}")
    
    # Test take profit
    signal = risk_manager.check_stop_loss_take_profit('AIR.PA', 108.5)
    if signal:
        print(f"  {signal}")
    
    # Test limites de positions
    signals = risk_manager.check_position_limits()
    for signal in signals:
        print(f"  {signal}")
    
    print("\n📋 Rapport complet:")
    print(risk_manager.get_risk_report())
    
    print("🎯 Test terminé!")