# mini_dashboard.py - Dashboard ultra simple sans erreur

from ib_insync import *
import time
from datetime import datetime

def mini_dashboard():
    """Dashboard simple en CLI"""
    print("📊 MINI DASHBOARD - POSITIONS TEMPS RÉEL")
    print("=" * 50)
    
    try:
        ib = IB()
        ib.connect('127.0.0.1', 7497, clientId=10)
        print("✅ Connecté à IB")
        
        while True:
            print(f"\n🕒 {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 30)
            
            # Récupération positions
            positions = ib.positions()
            portfolio = ib.portfolio()
            
            total_pnl = 0
            active_positions = 0
            
            # Affichage positions
            for pos in positions:
                if pos.position != 0:
                    symbol = pos.contract.symbol
                    qty = pos.position
                    avg_cost = pos.avgCost
                    
                    # Prix actuel
                    try:
                        bars = ib.reqHistoricalData(
                            pos.contract, '', '1 D', '1 day', 'TRADES', 1, 1, False
                        )
                        current_price = bars[-1].close
                    except:
                        current_price = avg_cost
                    
                    # P&L
                    pnl_dollar = (current_price - avg_cost) * qty
                    pnl_pct = (current_price - avg_cost) / avg_cost * 100 if avg_cost > 0 else 0
                    
                    total_pnl += pnl_dollar
                    active_positions += 1
                    
                    # Affichage
                    status_icon = "🟢" if pnl_dollar > 0 else "🔴" if pnl_dollar < 0 else "⚪"
                    
                    print(f"{status_icon} {symbol:6} | {qty:3.0f} @ ${avg_cost:7.2f} | "
                          f"Now: ${current_price:7.2f} | "
                          f"P&L: {pnl_pct:+6.1f}% (${pnl_dollar:+8.2f})")
            
            # Résumé
            print("-" * 30)
            status_total = "🟢" if total_pnl > 0 else "🔴" if total_pnl < 0 else "⚪"
            print(f"{status_total} TOTAL | Positions: {active_positions} | "
                  f"P&L TOTAL: ${total_pnl:+.2f}")
            
            # Portfolio check
            if portfolio:
                print(f"💼 Portfolio items: {len(portfolio)}")
            
            print(f"\n⏳ Prochaine MAJ dans 30s (Ctrl+C pour arrêter)")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Dashboard arrêté")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        if ib.isConnected():
            ib.disconnect()

if __name__ == "__main__":
    mini_dashboard()