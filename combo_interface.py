# combo_interface.py - Interface complète bot + monitoring

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import time
import subprocess
import signal
from datetime import datetime
from ib_insync import *

class ComboTradingInterface:
    """Interface complète : contrôle bot + monitoring positions"""
    
    def __init__(self):
        self.ib = IB()
        self.root = tk.Tk()
        self.bot_process = None
        self.running = True
        self.positions_data = {}
        
        # Configuration bot - CHARGER D'ABORD
        self.bot_config = self.load_existing_config()
        
        self.setup_ui()
        self.connect_ib()
        self.start_monitoring()
    
    def load_existing_config(self):
        """Charger config existante ou créer par défaut"""
        default_config = {
            'max_positions': 3,
            'max_investment': 1000,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'profit_target': 5.0,
            'stop_loss': -8.0,
            'scan_interval': 300
        }
        
        try:
            if os.path.exists('bot_config.json'):
                with open('bot_config.json', 'r') as f:
                    loaded_config = json.load(f)
                
                # Merger avec défauts (au cas où nouvelles clés)
                for key, value in loaded_config.items():
                    if key in default_config:
                        default_config[key] = value
                
                print(f"✅ Config chargée depuis bot_config.json")
                print(f"   Max positions: {default_config['max_positions']}")
                
            else:
                print(f"⚠️ Création nouvelle config")
                
        except Exception as e:
            print(f"❌ Erreur chargement config: {e}")
        
        return default_config
        
    def setup_ui(self):
        """Configuration interface utilisateur"""
        self.root.title("🤖 COMBO TRADING INTERFACE")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e3c72')
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Notebook pour onglets
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Onglet 1: Contrôle Bot
        self.create_bot_control_tab()
        
        # Onglet 2: Monitoring Positions
        self.create_monitoring_tab()
        
        # Onglet 3: Signaux & Analytics
        self.create_signals_tab()
        
        # Status bar
        self.status_bar = tk.Label(
            self.root, 
            text="Initialisation...", 
            relief=tk.SUNKEN, 
            anchor='w',
            bg='#2a5298',
            fg='white'
        )
        self.status_bar.pack(side='bottom', fill='x')
        
    def create_bot_control_tab(self):
        """Onglet contrôle du bot"""
        bot_frame = ttk.Frame(self.notebook)
        self.notebook.add(bot_frame, text="🤖 Contrôle Bot")
        
        # Header
        header = tk.Label(
            bot_frame, 
            text="🤖 CONTRÔLE BOT AUTONOME", 
            font=('Arial', 18, 'bold'),
            bg='#2a5298', 
            fg='white',
            padx=20,
            pady=10
        )
        header.pack(fill='x', padx=10, pady=10)
        
        # Status bot
        status_frame = tk.Frame(bot_frame, bg='white', relief='raised', bd=2)
        status_frame.pack(fill='x', padx=20, pady=10)
        
        self.bot_status_label = tk.Label(
            status_frame, 
            text="🔴 BOT ARRÊTÉ", 
            font=('Arial', 16, 'bold'),
            bg='white',
            fg='red'
        )
        self.bot_status_label.pack(pady=10)
        
        # Contrôles bot
        controls_frame = tk.Frame(bot_frame)
        controls_frame.pack(pady=20)
        
        self.start_btn = tk.Button(
            controls_frame,
            text="🚀 DÉMARRER BOT",
            command=self.start_bot,
            bg='#4caf50',
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=10
        )
        self.start_btn.pack(side='left', padx=10)
        
        self.stop_btn = tk.Button(
            controls_frame,
            text="🛑 ARRÊTER BOT",
            command=self.stop_bot,
            bg='#f44336',
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=10,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=10)
        
        # Configuration
        config_frame = tk.LabelFrame(bot_frame, text="⚙️ CONFIGURATION", font=('Arial', 12, 'bold'))
        config_frame.pack(fill='x', padx=20, pady=20)
        
        # Paramètres grid
        params_frame = tk.Frame(config_frame)
        params_frame.pack(pady=10)
        
        # Max positions
        tk.Label(params_frame, text="Max Positions:", width=15, anchor='e').grid(row=0, column=0, padx=5, pady=5)
        self.max_pos_var = tk.StringVar(value=str(self.bot_config['max_positions']))
        max_pos_entry = tk.Entry(params_frame, textvariable=self.max_pos_var, width=10)
        max_pos_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Max investment
        tk.Label(params_frame, text="Max Investment $:", width=15, anchor='e').grid(row=0, column=2, padx=5, pady=5)
        self.max_inv_var = tk.StringVar(value=str(self.bot_config['max_investment']))
        max_inv_entry = tk.Entry(params_frame, textvariable=self.max_inv_var, width=10)
        max_inv_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # RSI seuils
        tk.Label(params_frame, text="RSI Oversold:", width=15, anchor='e').grid(row=1, column=0, padx=5, pady=5)
        self.rsi_over_var = tk.StringVar(value=str(self.bot_config['rsi_oversold']))
        rsi_over_entry = tk.Entry(params_frame, textvariable=self.rsi_over_var, width=10)
        rsi_over_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(params_frame, text="RSI Overbought:", width=15, anchor='e').grid(row=1, column=2, padx=5, pady=5)
        self.rsi_overb_var = tk.StringVar(value=str(self.bot_config['rsi_overbought']))
        rsi_overb_entry = tk.Entry(params_frame, textvariable=self.rsi_overb_var, width=10)
        rsi_overb_entry.grid(row=1, column=3, padx=5, pady=5)
        
        # Profit/Loss
        tk.Label(params_frame, text="Profit Target %:", width=15, anchor='e').grid(row=2, column=0, padx=5, pady=5)
        self.profit_var = tk.StringVar(value=str(self.bot_config['profit_target']))
        profit_entry = tk.Entry(params_frame, textvariable=self.profit_var, width=10)
        profit_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(params_frame, text="Stop Loss %:", width=15, anchor='e').grid(row=2, column=2, padx=5, pady=5)
        self.stop_var = tk.StringVar(value=str(self.bot_config['stop_loss']))
        stop_entry = tk.Entry(params_frame, textvariable=self.stop_var, width=10)
        stop_entry.grid(row=2, column=3, padx=5, pady=5)
        
        # Bouton sauvegarde config
        save_config_btn = tk.Button(
            config_frame,
            text="💾 Sauvegarder Config",
            command=self.save_config,
            bg='#2196f3',
            fg='white',
            font=('Arial', 12),
            padx=20
        )
        save_config_btn.pack(pady=10)
        
        # Log bot
        log_frame = tk.LabelFrame(bot_frame, text="📝 LOG BOT", font=('Arial', 12, 'bold'))
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.bot_log = tk.Text(log_frame, height=10, bg='#2d2d2d', fg='white', font=('Courier', 10))
        self.bot_log.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_monitoring_tab(self):
        """Onglet monitoring positions"""
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text="📊 Positions")
        
        # Header avec résumé
        summary_frame = tk.Frame(monitor_frame, bg='#34495e', height=80)
        summary_frame.pack(fill='x', padx=10, pady=10)
        summary_frame.pack_propagate(False)
        
        # Cards résumé
        cards_frame = tk.Frame(summary_frame, bg='#34495e')
        cards_frame.pack(expand=True)
        
        # Total positions
        pos_card = tk.Frame(cards_frame, bg='#2c3e50', relief='raised', bd=2)
        pos_card.pack(side='left', padx=20, pady=10, fill='both', expand=True)
        
        tk.Label(pos_card, text="POSITIONS", font=('Arial', 10), bg='#2c3e50', fg='white').pack()
        self.total_pos_label = tk.Label(pos_card, text="0", font=('Arial', 20, 'bold'), bg='#2c3e50', fg='#ffd700')
        self.total_pos_label.pack()
        
        # Total P&L
        pnl_card = tk.Frame(cards_frame, bg='#2c3e50', relief='raised', bd=2)
        pnl_card.pack(side='left', padx=20, pady=10, fill='both', expand=True)
        
        tk.Label(pnl_card, text="P&L TOTAL", font=('Arial', 10), bg='#2c3e50', fg='white').pack()
        self.total_pnl_label = tk.Label(pnl_card, text="$0", font=('Arial', 20, 'bold'), bg='#2c3e50', fg='#ffd700')
        self.total_pnl_label.pack()
        
        # Positions table
        table_frame = tk.Frame(monitor_frame)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('Symbol', 'Qty', 'Avg Cost', 'Current', 'P&L %', 'P&L $', 'RSI', 'Status')
        self.positions_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.positions_tree.heading(col, text=col)
            self.positions_tree.column(col, width=100, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=scrollbar.set)
        
        self.positions_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Boutons actions
        actions_frame = tk.Frame(monitor_frame)
        actions_frame.pack(pady=10)
        
        tk.Button(
            actions_frame,
            text="🔄 Actualiser",
            command=self.manual_refresh_positions,
            bg='#4caf50',
            fg='white',
            font=('Arial', 12),
            padx=20
        ).pack(side='left', padx=10)
        
        tk.Button(
            actions_frame,
            text="💾 Export",
            command=self.export_positions,
            bg='#2196f3',
            fg='white',
            font=('Arial', 12),
            padx=20
        ).pack(side='left', padx=10)
        
    def create_signals_tab(self):
        """Onglet signaux et analytics"""
        signals_frame = ttk.Frame(self.notebook)
        self.notebook.add(signals_frame, text="🎯 Signaux")
        
        # Header
        header = tk.Label(
            signals_frame, 
            text="🎯 SIGNAUX TEMPS RÉEL", 
            font=('Arial', 18, 'bold'),
            bg='#2a5298', 
            fg='white',
            padx=20,
            pady=10
        )
        header.pack(fill='x', padx=10, pady=10)
        
        # Signaux actuels
        self.signals_text = tk.Text(
            signals_frame, 
            height=15, 
            bg='#2d2d2d', 
            fg='white', 
            font=('Courier', 11)
        )
        self.signals_text.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Bouton scan manuel
        scan_btn = tk.Button(
            signals_frame,
            text="🔍 SCAN MARCHÉ",
            command=self.manual_market_scan,
            bg='#ff9800',
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=30,
            pady=10
        )
        scan_btn.pack(pady=20)
        
    def connect_ib(self):
        """Connexion IB"""
        try:
            self.ib.connect('127.0.0.1', 7497, clientId=11)
            self.update_status("✅ Connecté à Interactive Brokers")
            return True
        except Exception as e:
            self.update_status(f"❌ Erreur connexion IB: {e}")
            return False
    
    def start_bot(self):
        """Démarrage bot autonome"""
        try:
            self.save_config()  # Sauvegarder config avant démarrage
            
            self.bot_process = subprocess.Popen(
                ['python', 'auto_trading_bot.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.bot_status_label.configure(text="🟢 BOT ACTIF", fg='green')
            self.start_btn.configure(state='disabled')
            self.stop_btn.configure(state='normal')
            
            self.log_bot_message("🚀 Bot autonome démarré")
            self.update_status("🤖 Bot autonome en cours d'exécution")
            
            # Thread pour lire output bot
            threading.Thread(target=self.read_bot_output, daemon=True).start()
            
        except Exception as e:
            self.log_bot_message(f"❌ Erreur démarrage bot: {e}")
    
    def stop_bot(self):
        """Arrêt bot autonome"""
        try:
            if self.bot_process:
                self.bot_process.terminate()
                self.bot_process = None
            
            self.bot_status_label.configure(text="🔴 BOT ARRÊTÉ", fg='red')
            self.start_btn.configure(state='normal')
            self.stop_btn.configure(state='disabled')
            
            self.log_bot_message("🛑 Bot autonome arrêté")
            self.update_status("Bot autonome arrêté")
            
        except Exception as e:
            self.log_bot_message(f"❌ Erreur arrêt bot: {e}")
    
    def save_config(self):
        """Sauvegarde configuration bot"""
        try:
            # Récupération des valeurs des champs
            new_config = {
                'max_positions': int(self.max_pos_var.get()),
                'max_investment': int(self.max_inv_var.get()),
                'rsi_oversold': float(self.rsi_over_var.get()),
                'rsi_overbought': float(self.rsi_overb_var.get()),
                'profit_target': float(self.profit_var.get()),
                'stop_loss': float(self.stop_var.get()),
                'scan_interval': self.bot_config.get('scan_interval', 300)
            }
            
            # Validation
            if new_config['max_positions'] < 1 or new_config['max_positions'] > 10:
                raise ValueError("Max positions doit être entre 1 et 10")
            
            if new_config['rsi_oversold'] >= new_config['rsi_overbought']:
                raise ValueError("RSI oversold doit être < RSI overbought")
            
            # Sauvegarde dans le fichier
            with open('bot_config.json', 'w') as f:
                json.dump(new_config, f, indent=2)
            
            # Mise à jour config interne
            self.bot_config.update(new_config)
            
            # Feedback visuel
            self.log_bot_message("💾 Configuration sauvegardée avec succès!")
            self.log_bot_message(f"   Max positions: {new_config['max_positions']}")
            self.log_bot_message(f"   Max investment: ${new_config['max_investment']}")
            
            # Message popup
            messagebox.showinfo("Succès", 
                f"Configuration sauvegardée!\n"
                f"Max positions: {new_config['max_positions']}\n"
                f"Redémarrez le bot pour appliquer les changements.")
            
            self.update_status(f"💾 Config sauvée - Max pos: {new_config['max_positions']}")
            
        except ValueError as e:
            self.log_bot_message(f"❌ Erreur validation: {e}")
            messagebox.showerror("Erreur", f"Erreur de validation:\n{e}")
        except Exception as e:
            self.log_bot_message(f"❌ Erreur sauvegarde config: {e}")
            messagebox.showerror("Erreur", f"Erreur sauvegarde:\n{e}")
    
    def read_bot_output(self):
        """Lecture output du bot en temps réel"""
        if not self.bot_process:
            return
            
        try:
            while self.bot_process and self.bot_process.poll() is None:
                line = self.bot_process.stdout.readline()
                if line:
                    self.log_bot_message(line.strip())
                time.sleep(0.1)
        except:
            pass
    
    def log_bot_message(self, message):
        """Ajout message au log bot"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.bot_log.insert(tk.END, log_entry)
        self.bot_log.see(tk.END)
        
        # Limiter à 100 lignes
        lines = self.bot_log.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            self.bot_log.delete("1.0", "2.0")
    
    def update_positions_display(self):
        """Mise à jour affichage positions"""
        # Clear table
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)
        
        try:
            positions = self.ib.positions()
            total_positions = 0
            total_pnl = 0
            
            for pos in positions:
                if pos.position != 0:
                    symbol = pos.contract.symbol
                    qty = pos.position
                    avg_cost = pos.avgCost
                    
                    # Prix actuel
                    try:
                        bars = self.ib.reqHistoricalData(
                            pos.contract, '', '1 D', '1 day', 'TRADES', 1, 1, False
                        )
                        current_price = bars[-1].close
                        
                        # RSI
                        rsi = self.get_rsi_simple(pos.contract)
                        
                    except:
                        current_price = avg_cost
                        rsi = 50
                    
                    # Calculs
                    pnl_dollar = (current_price - avg_cost) * qty
                    pnl_pct = (current_price - avg_cost) / avg_cost * 100 if avg_cost > 0 else 0
                    
                    total_positions += 1
                    total_pnl += pnl_dollar
                    
                    # Status
                    if rsi < 30:
                        status = "🔥 OVERSOLD"
                    elif rsi > 70:
                        status = "⚠️ OVERBOUGHT"
                    else:
                        status = "➡️ NEUTRAL"
                    
                    # Couleurs
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
                        f"${current_price:.2f}",
                        f"{pnl_pct:+.1f}%",
                        f"${pnl_dollar:+.2f}",
                        f"{rsi:.1f}",
                        status
                    ), tags=tags)
            
            # Configuration couleurs
            self.positions_tree.tag_configure('profit', background='#d4edda')
            self.positions_tree.tag_configure('loss', background='#f8d7da')
            self.positions_tree.tag_configure('neutral', background='#fff3cd')
            
            # Mise à jour résumé
            self.total_pos_label.configure(text=str(total_positions))
            self.total_pnl_label.configure(
                text=f"${total_pnl:+.2f}",
                fg='#4caf50' if total_pnl > 0 else '#f44336' if total_pnl < 0 else '#ffd700'
            )
            
        except Exception as e:
            self.update_status(f"❌ Erreur positions: {e}")
    
    def get_rsi_simple(self, contract, period=14):
        """Calcul RSI simple"""
        try:
            bars = self.ib.reqHistoricalData(contract, '', '30 D', '1 day', 'TRADES', 1, 1, False)
            
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
    
    def manual_refresh_positions(self):
        """Actualisation manuelle positions"""
        self.update_positions_display()
        self.update_status("🔄 Positions actualisées")
    
    def export_positions(self):
        """Export positions"""
        try:
            positions = self.ib.positions()
            export_data = []
            
            for pos in positions:
                if pos.position != 0:
                    export_data.append({
                        'symbol': pos.contract.symbol,
                        'quantity': pos.position,
                        'avg_cost': pos.avgCost,
                        'timestamp': datetime.now().isoformat()
                    })
            
            filename = f"positions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            messagebox.showinfo("Export", f"Positions exportées: {filename}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur export: {e}")
    
    def manual_market_scan(self):
        """Scan marché manuel"""
        self.signals_text.delete(1.0, tk.END)
        self.signals_text.insert(tk.END, "🔍 SCAN MARCHÉ EN COURS...\n\n")
        
        # Utiliser tkinter.after() au lieu d'un thread
        self.root.after(100, self.perform_market_scan)
    
    def perform_market_scan(self):
        """Exécution scan marché"""
        try:
            watchlist = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMZN', 'META', 'CE', 'ACVA', 'AIV']
            
            signals = []
            scanned = 0
            
            def scan_next_symbol():
                nonlocal scanned
                if scanned >= len(watchlist):
                    # Scan terminé
                    self.display_scan_results(signals)
                    return
                
                symbol = watchlist[scanned]
                scanned += 1
                
                try:
                    contract = Stock(symbol, 'SMART', 'USD')
                    self.ib.qualifyContracts(contract)
                    
                    # RSI
                    rsi = self.get_rsi_simple(contract)
                    
                    # Signal
                    if rsi < 30:
                        signals.append(f"🟢 {symbol}: RSI {rsi:.1f} - ACHAT")
                    elif rsi > 70:
                        signals.append(f"🔴 {symbol}: RSI {rsi:.1f} - VENTE")
                    else:
                        signals.append(f"⚪ {symbol}: RSI {rsi:.1f} - NEUTRE")
                    
                    # Mise à jour progress
                    progress = f"🔍 SCAN EN COURS... {scanned}/{len(watchlist)}\n\n"
                    for signal in signals[-3:]:  # Derniers 3 signaux
                        progress += signal + "\n"
                    
                    self.signals_text.delete(1.0, tk.END)
                    self.signals_text.insert(tk.END, progress)
                    
                except Exception as e:
                    signals.append(f"❌ {symbol}: Erreur - {e}")
                
                # Scanner le prochain symbole dans 200ms
                self.root.after(200, scan_next_symbol)
            
            # Démarrer le scan
            scan_next_symbol()
            
        except Exception as e:
            self.signals_text.delete(1.0, tk.END)
            self.signals_text.insert(tk.END, f"❌ Erreur scan: {e}")
    
    def display_scan_results(self, signals):
        """Affichage résultats scan"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        result_text = f"📊 SCAN TERMINÉ - {timestamp}\n"
        result_text += "=" * 40 + "\n\n"
        
        # Tri des signaux : achats, ventes, neutres
        buy_signals = [s for s in signals if "🟢" in s]
        sell_signals = [s for s in signals if "🔴" in s] 
        neutral_signals = [s for s in signals if "⚪" in s]
        error_signals = [s for s in signals if "❌" in s]
        
        if buy_signals:
            result_text += "🟢 SIGNAUX D'ACHAT:\n"
            for signal in buy_signals:
                result_text += "   " + signal + "\n"
            result_text += "\n"
        
        if sell_signals:
            result_text += "🔴 SIGNAUX DE VENTE:\n"
            for signal in sell_signals:
                result_text += "   " + signal + "\n"
            result_text += "\n"
        
        if neutral_signals:
            result_text += "⚪ SIGNAUX NEUTRES:\n"
            for signal in neutral_signals:
                result_text += "   " + signal + "\n"
            result_text += "\n"
        
        if error_signals:
            result_text += "❌ ERREURS:\n"
            for signal in error_signals:
                result_text += "   " + signal + "\n"
            result_text += "\n"
        
        result_text += "=" * 40 + "\n"
        result_text += f"Résumé: {len(buy_signals)} achats, {len(sell_signals)} ventes, {len(neutral_signals)} neutres\n"
        
        self.signals_text.delete(1.0, tk.END)
        self.signals_text.insert(tk.END, result_text)
    
    def start_monitoring(self):
        """Démarrage monitoring automatique"""
        def monitor_loop():
            while self.running:
                try:
                    self.update_positions_display()
                    time.sleep(30)  # Update toutes les 30s
                except:
                    time.sleep(60)
        
        threading.Thread(target=monitor_loop, daemon=True).start()
    
    def update_status(self, message):
        """Mise à jour status bar"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_bar.configure(text=f"[{timestamp}] {message}")
    
    def on_closing(self):
        """Fermeture propre"""
        self.running = False
        
        if self.bot_process:
            self.bot_process.terminate()
        
        if self.ib.isConnected():
            self.ib.disconnect()
        
        self.root.destroy()
    
    def run(self):
        """Démarrage interface"""
        self.update_status("🚀 Interface combo démarrée")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """Lancement interface combo"""
    print("🚀 Lancement Interface Combo Trading")
    interface = ComboTradingInterface()
    interface.run()

if __name__ == "__main__":
    main()