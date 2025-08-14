# real_dashboard.py - Dashboard Python avec vraies données IB

import tkinter as tk
from tkinter import ttk
import json
import os
from datetime import datetime
import threading
import time
from ib_insync import *

class RealTradingDashboard:
    """Dashboard Python avec vraies données IB"""
    
    def __init__(self):
        self.ib = IB()
        self.root = tk.Tk()
        self.positions_data = {}
        self.running = True
        
        self.setup_ui()
        self.connect_ib()
        
    def setup_ui(self):
        """Configuration interface utilisateur"""
        self.root.title("🤖 Trading Bot Dashboard - Données Réelles")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e3c72')
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Header
        header_frame = tk.Frame(self.root, bg='#2a5298', height=80)
        header_frame.pack(fill='x', padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="🤖 TRADING BOT DASHBOARD", 
            font=('Arial', 20, 'bold'),
            bg='#2a5298', 
            fg='white'
        )
        title_label.pack(pady=20)
        
        # Status bar
        self.status_frame = tk.Frame(self.root, bg='#1e3c72')
        self.status_frame.pack(fill='x', padx=10, pady=5)
        
        self.create_status_cards()
        
        # Positions area
        positions_label = tk.Label(
            self.root, 
            text="📊 POSITIONS ACTIVES", 
            font=('Arial', 16, 'bold'),
            bg='#1e3c72', 
            fg='white'
        )
        positions_label.pack(pady=(20,10))
        
        # Treeview pour positions
        columns = ('Symbol', 'Qty', 'Avg Cost', 'Current', 'P&L %', 'P&L $', 'RSI')
        self.positions_tree = ttk.Treeview(self.root, columns=columns, show='headings', height=8)
        
        # Headers
        for col in columns:
            self.positions_tree.heading(col, text=col)
            self.positions_tree.column(col, width=120, anchor='center')
        
        self.positions_tree.pack(padx=20, pady=10, fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.root, orient='vertical', command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bot log area
        log_label = tk.Label(
            self.root, 
            text="📝 LOG BOT", 
            font=('Arial', 14, 'bold'),
            bg='#1e3c72', 
            fg='white'
        )
        log_label.pack(pady=(10,5))
        
        self.log_text = tk.Text(self.root, height=8, bg='#2d2d2d', fg='white', font=('Courier', 10))
        self.log_text.pack(padx=20, pady=5, fill='x')
        
        # Buttons
        button_frame = tk.Frame(self.root, bg='#1e3c72')
        button_frame.pack(pady=10)
        
        refresh_btn = tk.Button(
            button_frame, 
            text="🔄 Actualiser", 
            command=self.manual_refresh,
            bg='#4caf50', 
            fg='white', 
            font=('Arial', 12, 'bold'),
            padx=20
        )
        refresh_btn.pack(side='left', padx=10)
        
        export_btn = tk.Button(
            button_frame, 
            text="💾 Exporter", 
            command=self.export_data,
            bg='#2196f3', 
            fg='white', 
            font=('Arial', 12, 'bold'),
            padx=20
        )
        export_btn.pack(side='left', padx=10)
        
        # Status bar bottom
        self.status_label = tk.Label(
            self.root, 
            text="Démarrage...", 
            bg='#1e3c72', 
            fg='white'
        )
        self.status_label.pack(side='bottom', pady=5)
        
    def create_status_cards(self):
        """Cartes de status en haut"""
        # Total positions
        self.total_pos_var = tk.StringVar(value="0")
        pos_card = tk.Frame(self.status_frame, bg='#34495e', relief='raised', bd=2)
        pos_card.pack(side='left', padx=10, pady=5, fill='both', expand=True)
        
        tk.Label(pos_card, text="POSITIONS", font=('Arial', 10), bg='#34495e', fg='white').pack()
        tk.Label(pos_card, textvariable=self.total_pos_var, font=('Arial', 18, 'bold'), bg='#34495e', fg='#ffd700').pack()
        
        # Total investi
        self.total_inv_var = tk.StringVar(value="$0")
        inv_card = tk.Frame(self.status_frame, bg='#34495e', relief='raised', bd=2)
        inv_card.pack(side='left', padx=10, pady=5, fill='both', expand=True)
        
        tk.Label(inv_card, text="INVESTI", font=('Arial', 10), bg='#34495e', fg='white').pack()
        tk.Label(inv_card, textvariable=self.total_inv_var, font=('Arial', 18, 'bold'), bg='#34495e', fg='#ffd700').pack()
        
        # P&L total
        self.total_pnl_var = tk.StringVar(value="$0")
        pnl_card = tk.Frame(self.status_frame, bg='#34495e', relief='raised', bd=2)
        pnl_card.pack(side='left', padx=10, pady=5, fill='both', expand=True)
        
        tk.Label(pnl_card, text="P&L TOTAL", font=('Arial', 10), bg='#34495e', fg='white').pack()
        self.pnl_label = tk.Label(pnl_card, textvariable=self.total_pnl_var, font=('Arial', 18, 'bold'), bg='#34495e')
        self.pnl_label.pack()
        
        # Status bot
        self.bot_status_var = tk.StringVar(value="🔴 DÉCONNECTÉ")
        status_card = tk.Frame(self.status_frame, bg='#34495e', relief='raised', bd=2)
        status_card.pack(side='left', padx=10, pady=5, fill='both', expand=True)
        
        tk.Label(status_card, text="BOT STATUS", font=('Arial', 10), bg='#34495e', fg='white').pack()
        tk.Label(status_card, textvariable=self.bot_status_var, font=('Arial', 14, 'bold'), bg='#34495e', fg='white').pack()
    
    def connect_ib(self):
        """Connexion à IB"""
        try:
            self.ib.connect('127.0.0.1', 7497, clientId=8)
            self.bot_status_var.set("🟢 CONNECTÉ")
            self.log_message("✅ Connecté à Interactive Brokers")
            return True
        except Exception as e:
            self.bot_status_var.set("🔴 ERREUR")
            self.log_message(f"❌ Erreur connexion IB: {e}")
            return False
    
    def log_message(self, message):
        """Ajout message au log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Limiter à 100 lignes
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            self.log_text.delete("1.0", "2.0")
    
    def get_real_positions(self):
        """Récupération vraies positions IB"""
        try:
            if not self.ib.isConnected():
                return {}
            
            positions = self.ib.positions()
            real_positions = {}
            
            for pos in positions:
                if pos.position != 0:  # Seulement positions non nulles
                    symbol = pos.contract.symbol
                    
                    # Prix actuel via données historiques
                    try:
                        bars = self.ib.reqHistoricalData(
                            pos.contract, '', '1 D', '1 day', 'TRADES', 1, 1, False
                        )
                        current_price = bars[-1].close if bars else pos.avgCost
                        
                        # Calcul RSI
                        rsi = self.get_rsi(pos.contract)
                        
                    except:
                        current_price = pos.avgCost
                        rsi = 50
                    
                    real_positions[symbol] = {
                        'quantity': pos.position,
                        'avg_cost': pos.avgCost,
                        'current_price': current_price,
                        'unrealized_pnl': pos.unrealizedPNL,
                        'market_value': pos.marketValue,
                        'rsi': rsi
                    }
            
            return real_positions
            
        except Exception as e:
            self.log_message(f"❌ Erreur récupération positions: {e}")
            return {}
    
    def get_rsi(self, contract, period=14):
        """Calcul RSI pour un contrat"""
        try:
            bars = self.ib.reqHistoricalData(
                contract, '', '30 D', '1 day', 'TRADES', 1, 1, False
            )
            
            if len(bars) < period + 1:
                return 50
            
            closes = [bar.close for bar in bars]
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 1)
            
        except:
            return 50
    
    def load_bot_state(self):
        """Chargement état du bot autonome"""
        try:
            if os.path.exists('bot_state.json'):
                with open('bot_state.json', 'r') as f:
                    return json.load(f)
            return {}
        except:
            return {}
    
    def update_display(self):
        """Mise à jour affichage"""
        # Clear treeview
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)
        
        # Récupération données réelles
        real_positions = self.get_real_positions()
        bot_state = self.load_bot_state()
        
        total_positions = len(real_positions)
        total_invested = 0
        total_pnl = 0
        
        # Affichage positions
        for symbol, pos in real_positions.items():
            qty = pos['quantity']
            avg_cost = pos['avg_cost']
            current = pos['current_price']
            pnl_dollar = pos['unrealized_pnl']
            pnl_pct = (current - avg_cost) / avg_cost * 100 if avg_cost > 0 else 0
            rsi = pos['rsi']
            
            total_invested += abs(qty * avg_cost)
            total_pnl += pnl_dollar
            
            # Couleur selon P&L
            if pnl_pct > 0:
                tags = ('profit',)
            elif pnl_pct < 0:
                tags = ('loss',)
            else:
                tags = ('neutral',)
            
            self.positions_tree.insert('', 'end', values=(
                symbol,
                f"{qty:.0f}",
                f"${avg_cost:.2f}",
                f"${current:.2f}",
                f"{pnl_pct:+.1f}%",
                f"${pnl_dollar:+.2f}",
                f"{rsi:.1f}"
            ), tags=tags)
        
        # Configuration couleurs
        self.positions_tree.tag_configure('profit', background='#d4edda', foreground='#155724')
        self.positions_tree.tag_configure('loss', background='#f8d7da', foreground='#721c24')
        self.positions_tree.tag_configure('neutral', background='#fff3cd', foreground='#856404')
        
        # Mise à jour status cards
        self.total_pos_var.set(str(total_positions))
        self.total_inv_var.set(f"${total_invested:.0f}")
        self.total_pnl_var.set(f"${total_pnl:+.2f}")
        
        # Couleur P&L
        if total_pnl > 0:
            self.pnl_label.configure(fg='#4caf50')
        elif total_pnl < 0:
            self.pnl_label.configure(fg='#f44336')
        else:
            self.pnl_label.configure(fg='#ffd700')
        
        # Status update
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_label.configure(text=f"Dernière MAJ: {timestamp}")
        
        self.log_message(f"Dashboard mis à jour - {total_positions} positions, P&L: ${total_pnl:+.2f}")
    
    def manual_refresh(self):
        """Actualisation manuelle"""
        self.log_message("🔄 Actualisation manuelle...")
        self.update_display()
    
    def export_data(self):
        """Export des données"""
        try:
            positions = self.get_real_positions()
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'positions': positions,
                'bot_state': self.load_bot_state()
            }
            
            filename = f"dashboard_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.log_message(f"💾 Données exportées: {filename}")
            
        except Exception as e:
            self.log_message(f"❌ Erreur export: {e}")
    
    def auto_update_loop(self):
        """Boucle de mise à jour automatique"""
        while self.running:
            try:
                self.update_display()
                time.sleep(30)  # Mise à jour toutes les 30 secondes
            except Exception as e:
                self.log_message(f"❌ Erreur auto-update: {e}")
                time.sleep(60)
    
    def run(self):
        """Démarrage dashboard"""
        self.log_message("🚀 Dashboard démarré")
        
        # Première mise à jour
        self.update_display()
        
        # Thread pour auto-update
        update_thread = threading.Thread(target=self.auto_update_loop, daemon=True)
        update_thread.start()
        
        # Démarrage interface
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Fermeture propre"""
        self.running = False
        if self.ib.isConnected():
            self.ib.disconnect()
        self.root.destroy()

def main():
    """Lancement dashboard réel"""
    print("🚀 Lancement Dashboard Python - Données Réelles IB")
    dashboard = RealTradingDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()