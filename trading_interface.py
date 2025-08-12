# trading_interface.py - Interface de contrôle du bot de trading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import subprocess
import os
import json
import time
from datetime import datetime
import logging

# Imports des modules de trading
from config import ConfigManager
from ib_connector import IBConnector
from risk_manager import RiskManager
import asyncio

class TradingInterface:
    """Interface graphique pour contrôler le bot de trading"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 Bot de Trading - Interface de Contrôle")
        self.root.geometry("1200x800")
        
        # Variables
        self.bot_process = None
        self.config_manager = ConfigManager()
        self.log_update_thread = None
        self.stop_log_update = False
        
        # Interface
        self.create_interface()
        
        # Mise à jour automatique
        self.update_status()
    
    def create_interface(self):
        """Création de l'interface graphique"""
        # Titre principal
        title_frame = tk.Frame(self.root, bg="#2C3E50", height=80)
        title_frame.pack(fill="x", pady=(0, 10))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🤖 BOT DE TRADING AUTOMATIQUE",
            font=("Arial", 18, "bold"),
            bg="#2C3E50",
            fg="white"
        )
        title_label.pack(expand=True)
        
        subtitle_label = tk.Label(
            title_frame,
            text="Basé sur tes stratégies RSI + MACD",
            font=("Arial", 10),
            bg="#2C3E50",
            fg="#BDC3C7"
        )
        subtitle_label.pack()
        
        # Frame principal avec onglets
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Onglet 1: Contrôle du bot
        self.create_control_tab()
        
        # Onglet 2: Configuration
        self.create_config_tab()
        
        # Onglet 3: Monitoring
        self.create_monitoring_tab()
        
        # Onglet 4: Logs
        self.create_logs_tab()
        
        # Onglet 5: Positions
        self.create_positions_tab()
    
    def create_control_tab(self):
        """Onglet de contrôle du bot"""
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text="🎮 Contrôle")
        
        # Statut du bot
        status_frame = tk.LabelFrame(control_frame, text="📊 Statut du Bot", font=("Arial", 12, "bold"))
        status_frame.pack(fill="x", padx=10, pady=10)
        
        self.status_label = tk.Label(
            status_frame,
            text="🔴 Arrêté",
            font=("Arial", 14, "bold"),
            fg="red"
        )
        self.status_label.pack(pady=10)
        
        self.info_label = tk.Label(
            status_frame,
            text="",
            font=("Arial", 10),
            fg="gray"
        )
        self.info_label.pack()
        
        # Boutons de contrôle
        button_frame = tk.Frame(control_frame)
        button_frame.pack(pady=20)
        
        self.start_button = tk.Button(
            button_frame,
            text="🚀 Démarrer Bot",
            command=self.start_bot,
            bg="#27AE60",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=2
        )
        self.start_button.pack(side="left", padx=10)
        
        self.stop_button = tk.Button(
            button_frame,
            text="🛑 Arrêter Bot",
            command=self.stop_bot,
            bg="#E74C3C",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=2,
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=10)
        
        self.test_button = tk.Button(
            button_frame,
            text="🧪 Test Connexion",
            command=self.test_connection,
            bg="#3498DB",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=2
        )
        self.test_button.pack(side="left", padx=10)
        
        # Configuration rapide
        quick_config_frame = tk.LabelFrame(control_frame, text="⚡ Configuration Rapide", font=("Arial", 12, "bold"))
        quick_config_frame.pack(fill="x", padx=10, pady=10)
        
        # Mode trading
        mode_frame = tk.Frame(quick_config_frame)
        mode_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(mode_frame, text="Mode:", font=("Arial", 10, "bold")).pack(side="left")
        
        self.mode_var = tk.StringVar()
        mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.mode_var,
            values=["Paper Trading (7497)", "LIVE Trading (7496)"],
            state="readonly"
        )
        mode_combo.pack(side="left", padx=10)
        mode_combo.bind("<<ComboboxSelected>>", self.update_mode)
        
        # Capital
        capital_frame = tk.Frame(quick_config_frame)
        capital_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(capital_frame, text="Capital:", font=("Arial", 10, "bold")).pack(side="left")
        
        self.capital_var = tk.StringVar()
        capital_entry = tk.Entry(capital_frame, textvariable=self.capital_var, width=15)
        capital_entry.pack(side="left", padx=10)
        capital_entry.bind("<Return>", self.update_capital)
        
        tk.Label(capital_frame, text="€").pack(side="left")
        
        # Chargement des valeurs actuelles
        self.load_current_config()
    
    def create_config_tab(self):
        """Onglet de configuration détaillée"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="⚙️ Configuration")
        
        # Sous-onglets pour la configuration
        config_notebook = ttk.Notebook(config_frame)
        config_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Connexion IB
        ib_frame = ttk.Frame(config_notebook)
        config_notebook.add(ib_frame, text="🔌 Interactive Brokers")
        self.create_ib_config(ib_frame)
        
        # Trading
        trading_frame = ttk.Frame(config_notebook)
        config_notebook.add(trading_frame, text="💰 Trading")
        self.create_trading_config(trading_frame)
        
        # Stratégie
        strategy_frame = ttk.Frame(config_notebook)
        config_notebook.add(strategy_frame, text="📈 Stratégie")
        self.create_strategy_config(strategy_frame)
        
        # Tickers
        tickers_frame = ttk.Frame(config_notebook)
        config_notebook.add(tickers_frame, text="📊 Tickers")
        self.create_tickers_config(tickers_frame)
    
    def create_ib_config(self, parent):
        """Configuration Interactive Brokers"""
        # Host
        host_frame = tk.Frame(parent)
        host_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(host_frame, text="Host:", width=15, anchor="w").pack(side="left")
        self.ib_host_var = tk.StringVar(value=self.config_manager.ib_config.host)
        tk.Entry(host_frame, textvariable=self.ib_host_var).pack(side="left", padx=5)
        
        # Port
        port_frame = tk.Frame(parent)
        port_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(port_frame, text="Port:", width=15, anchor="w").pack(side="left")
        self.ib_port_var = tk.IntVar(value=self.config_manager.ib_config.port)
        port_spin = tk.Spinbox(port_frame, from_=7496, to=7497, textvariable=self.ib_port_var)
        port_spin.pack(side="left", padx=5)
        
        # Client ID
        client_frame = tk.Frame(parent)
        client_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(client_frame, text="Client ID:", width=15, anchor="w").pack(side="left")
        self.ib_client_var = tk.IntVar(value=self.config_manager.ib_config.client_id)
        tk.Spinbox(client_frame, from_=1, to=100, textvariable=self.ib_client_var).pack(side="left", padx=5)
    
    def create_trading_config(self, parent):
        """Configuration trading"""
        configs = [
            ("Capital initial (€):", "capital_initial", float),
            ("% capital/position:", "position_size_pct", float),
            ("Max positions:", "max_positions", int),
            ("Stop Loss (%):", "stop_loss_pct", float),
            ("Take Profit (%):", "take_profit_pct", float),
            ("Frais (%):", "frais_pourcentage", float)
        ]
        
        self.trading_vars = {}
        
        for label, attr, var_type in configs:
            frame = tk.Frame(parent)
            frame.pack(fill="x", padx=10, pady=5)
            
            tk.Label(frame, text=label, width=20, anchor="w").pack(side="left")
            
            current_value = getattr(self.config_manager.trading_config, attr)
            if var_type == float:
                var = tk.DoubleVar(value=current_value)
            else:
                var = tk.IntVar(value=current_value)
            
            self.trading_vars[attr] = var
            
            if attr.endswith('_pct'):
                # Affichage en pourcentage
                tk.Scale(
                    frame,
                    from_=0,
                    to=1 if 'frais' in attr else 0.5,
                    variable=var,
                    orient="horizontal",
                    resolution=0.001 if 'frais' in attr else 0.01,
                    length=200
                ).pack(side="left", padx=5)
            else:
                tk.Entry(frame, textvariable=var, width=10).pack(side="left", padx=5)
    
    def create_strategy_config(self, parent):
        """Configuration stratégie"""
        tk.Label(parent, text="📈 Stratégie RSI + MACD", font=("Arial", 14, "bold")).pack(pady=10)
        
        configs = [
            ("RSI Window:", "rsi_window", int, 5, 30),
            ("RSI Survente:", "rsi_oversold", int, 10, 40),
            ("RSI Surachat:", "rsi_overbought", int, 60, 90),
            ("MACD Fast:", "macd_fast", int, 5, 20),
            ("MACD Slow:", "macd_slow", int, 20, 50),
            ("MACD Signal:", "macd_signal", int, 5, 15)
        ]
        
        self.strategy_vars = {}
        
        for label, attr, var_type, min_val, max_val in configs:
            frame = tk.Frame(parent)
            frame.pack(fill="x", padx=10, pady=5)
            
            tk.Label(frame, text=label, width=15, anchor="w").pack(side="left")
            
            current_value = getattr(self.config_manager.strategy_config, attr)
            var = tk.IntVar(value=current_value)
            self.strategy_vars[attr] = var
            
            tk.Scale(
                frame,
                from_=min_val,
                to=max_val,
                variable=var,
                orient="horizontal",
                length=200
            ).pack(side="left", padx=5)
            
            tk.Label(frame, textvariable=var).pack(side="left", padx=5)
    
    def create_tickers_config(self, parent):
        """Configuration tickers"""
        tk.Label(parent, text="📊 Actions à surveiller", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Liste des tickers sélectionnés
        self.tickers_listbox = tk.Listbox(parent, height=10)
        self.tickers_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Boutons
        button_frame = tk.Frame(parent)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Ajouter", command=self.add_ticker).pack(side="left", padx=5)
        tk.Button(button_frame, text="Supprimer", command=self.remove_ticker).pack(side="left", padx=5)
        tk.Button(button_frame, text="CAC40 populaires", command=self.load_popular_tickers).pack(side="left", padx=5)
        
        # Chargement des tickers actuels
        self.load_tickers()
    
    def create_monitoring_tab(self):
        """Onglet de monitoring"""
        monitoring_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitoring_frame, text="📊 Monitoring")
        
        # Statistiques en temps réel
        stats_frame = tk.LabelFrame(monitoring_frame, text="📈 Statistiques", font=("Arial", 12, "bold"))
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        self.stats_text = tk.Text(stats_frame, height=8, wrap="word")
        self.stats_text.pack(fill="x", padx=10, pady=10)
        
        # Positions actuelles
        positions_frame = tk.LabelFrame(monitoring_frame, text="💼 Positions", font=("Arial", 12, "bold"))
        positions_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.positions_tree = ttk.Treeview(positions_frame, columns=("qty", "avg_cost", "current", "pnl"), show="tree headings")
        self.positions_tree.heading("#0", text="Symbole")
        self.positions_tree.heading("qty", text="Quantité")
        self.positions_tree.heading("avg_cost", text="Prix moyen")
        self.positions_tree.heading("current", text="Prix actuel")
        self.positions_tree.heading("pnl", text="P&L (%)")
        self.positions_tree.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_logs_tab(self):
        """Onglet des logs"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📋 Logs")
        
        # Contrôles
        controls_frame = tk.Frame(logs_frame)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Button(controls_frame, text="🔄 Actualiser", command=self.refresh_logs).pack(side="left", padx=5)
        tk.Button(controls_frame, text="🗑️ Vider", command=self.clear_logs).pack(side="left", padx=5)
        
        # Auto-scroll
        self.auto_scroll_var = tk.BooleanVar(value=True)
        tk.Checkbutton(controls_frame, text="Auto-scroll", variable=self.auto_scroll_var).pack(side="left", padx=5)
        
        # Zone de logs
        self.logs_text = scrolledtext.ScrolledText(
            logs_frame,
            wrap="word",
            font=("Consolas", 9),
            bg="#1E1E1E",
            fg="#FFFFFF"
        )
        self.logs_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Configuration des couleurs
        self.logs_text.tag_config("INFO", foreground="#00FF00")
        self.logs_text.tag_config("WARNING", foreground="#FFFF00")
        self.logs_text.tag_config("ERROR", foreground="#FF0000")
        self.logs_text.tag_config("DEBUG", foreground="#CCCCCC")
    
    def create_positions_tab(self):
        """Onglet positions détaillées"""
        positions_frame = ttk.Frame(self.notebook)
        self.notebook.add(positions_frame, text="💼 Positions")
        
        # Tableau détaillé des positions
        self.detailed_positions_tree = ttk.Treeview(
            positions_frame,
            columns=("qty", "avg_cost", "current", "value", "pnl", "pnl_pct", "entry_time"),
            show="tree headings"
        )
        
        headers = [
            ("Symbole", "#0"),
            ("Qty", "qty"),
            ("Prix Moy", "avg_cost"),
            ("Prix Act", "current"),
            ("Valeur", "value"),
            ("P&L €", "pnl"),
            ("P&L %", "pnl_pct"),
            ("Entrée", "entry_time")
        ]
        
        for text, col in headers:
            if col == "#0":
                self.detailed_positions_tree.heading("#0", text=text)
            else:
                self.detailed_positions_tree.heading(col, text=text)
                self.detailed_positions_tree.column(col, width=100)
        
        self.detailed_positions_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Boutons d'action
        action_frame = tk.Frame(positions_frame)
        action_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Button(action_frame, text="🔄 Rafraîchir", command=self.refresh_positions).pack(side="left", padx=5)
        tk.Button(action_frame, text="💾 Exporter CSV", command=self.export_positions).pack(side="left", padx=5)
    
    def load_current_config(self):
        """Charge la configuration actuelle"""
        # Mode
        port = self.config_manager.ib_config.port
        mode_text = "Paper Trading (7497)" if port == 7497 else "LIVE Trading (7496)"
        self.mode_var.set(mode_text)
        
        # Capital
        self.capital_var.set(str(int(self.config_manager.trading_config.capital_initial)))
    
    def load_tickers(self):
        """Charge les tickers dans la liste"""
        self.tickers_listbox.delete(0, tk.END)
        for ticker in self.config_manager.system_config.tickers:
            self.tickers_listbox.insert(tk.END, ticker)
    
    def update_mode(self, event=None):
        """Met à jour le mode de trading"""
        mode_text = self.mode_var.get()
        if "7497" in mode_text:
            self.config_manager.ib_config.port = 7497
        else:
            self.config_manager.ib_config.port = 7496
        
        self.config_manager.save_config()
        
        # Avertissement pour mode live
        if self.config_manager.ib_config.port == 7496:
            messagebox.showwarning(
                "Mode LIVE",
                "⚠️ Attention: Mode LIVE TRADING activé!\n"
                "Ceci utilisera de l'ARGENT RÉEL!"
            )
    
    def update_capital(self, event=None):
        """Met à jour le capital"""
        try:
            capital = float(self.capital_var.get())
            self.config_manager.trading_config.capital_initial = capital
            self.config_manager.save_config()
        except ValueError:
            messagebox.showerror("Erreur", "Capital invalide")
    
    def start_bot(self):
        """Démarre le bot de trading"""
        try:
            # Sauvegarde de la configuration
            self.save_all_config()
            
            # Vérification mode live
            if not self.config_manager.is_paper_trading():
                response = messagebox.askyesno(
                    "⚠️ TRADING LIVE",
                    "ATTENTION: Vous allez lancer le bot en mode LIVE TRADING!\n"
                    "Ceci utilisera de l'ARGENT RÉEL!\n\n"
                    "Êtes-vous absolument sûr?"
                )
                if not response:
                    return
            
            # Lancement du bot
            self.bot_process = subprocess.Popen([
                "python", "trading_bot.py"
            ], cwd=os.getcwd())
            
            # Mise à jour de l'interface
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_label.config(text="🟢 En cours", fg="green")
            
            # Démarrage de la mise à jour des logs
            self.start_log_monitoring()
            
            messagebox.showinfo("Bot démarré", "Le bot de trading a été démarré!")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de démarrer le bot: {e}")
    
    def stop_bot(self):
        """Arrête le bot de trading"""
        try:
            if self.bot_process:
                self.bot_process.terminate()
                self.bot_process = None
            
            # Mise à jour de l'interface
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_label.config(text="🔴 Arrêté", fg="red")
            
            # Arrêt de la surveillance des logs
            self.stop_log_monitoring()
            
            messagebox.showinfo("Bot arrêté", "Le bot de trading a été arrêté!")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'arrêt: {e}")
    
    def test_connection(self):
        """Test de connexion à IB"""
        def test_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                connector = IBConnector(self.config_manager)
                result = loop.run_until_complete(connector.connect())
                
                if result:
                    loop.run_until_complete(connector.disconnect())
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Test réussi",
                        "✅ Connexion à Interactive Brokers réussie!"
                    ))
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Test échoué",
                        "❌ Impossible de se connecter à IB.\n"
                        "Vérifiez que TWS est ouvert et l'API activée."
                    ))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Erreur test",
                    f"❌ Erreur lors du test: {e}"
                ))
        
        # Test en arrière-plan
        threading.Thread(target=test_async, daemon=True).start()
    
    def save_all_config(self):
        """Sauvegarde toute la configuration"""
        try:
            # IB Config
            self.config_manager.ib_config.host = self.ib_host_var.get()
            self.config_manager.ib_config.port = self.ib_port_var.get()
            self.config_manager.ib_config.client_id = self.ib_client_var.get()
            
            # Trading Config
            for attr, var in self.trading_vars.items():
                setattr(self.config_manager.trading_config, attr, var.get())
            
            # Strategy Config
            for attr, var in self.strategy_vars.items():
                setattr(self.config_manager.strategy_config, attr, var.get())
            
            # Tickers
            tickers = [self.tickers_listbox.get(i) for i in range(self.tickers_listbox.size())]
            self.config_manager.system_config.tickers = tickers
            
            # Sauvegarde
            self.config_manager.save_config()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur sauvegarde config: {e}")
    
    def add_ticker(self):
        """Ajouter un ticker"""
        ticker = tk.simpledialog.askstring("Nouveau ticker", "Entrez le symbole (ex: AIR.PA):")
        if ticker:
            self.tickers_listbox.insert(tk.END, ticker.upper())
    
    def remove_ticker(self):
        """Supprimer un ticker"""
        selection = self.tickers_listbox.curselection()
        if selection:
            self.tickers_listbox.delete(selection[0])
    
    def load_popular_tickers(self):
        """Charge les tickers CAC40 populaires"""
        popular = ['AIR.PA', 'MC.PA', 'OR.PA', 'SAN.PA', 'BNP.PA', 'TTE.PA', 'CAP.PA', 'CS.PA']
        self.tickers_listbox.delete(0, tk.END)
        for ticker in popular:
            self.tickers_listbox.insert(tk.END, ticker)
    
    def start_log_monitoring(self):
        """Démarre la surveillance des logs"""
        self.stop_log_update = False
        self.log_update_thread = threading.Thread(target=self.update_logs_thread, daemon=True)
        self.log_update_thread.start()
    
    def stop_log_monitoring(self):
        """Arrête la surveillance des logs"""
        self.stop_log_update = True
    
    def update_logs_thread(self):
        """Thread de mise à jour des logs"""
        log_file = "trading_bot.log"
        last_position = 0
        
        while not self.stop_log_update:
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        f.seek(last_position)
                        new_lines = f.readlines()
                        last_position = f.tell()
                        
                        if new_lines and self.auto_scroll_var.get():
                            self.root.after(0, lambda: self.append_logs(new_lines))
                
                time.sleep(2)
                
            except Exception as e:
                print(f"Erreur lecture logs: {e}")
                time.sleep(5)
    
    def append_logs(self, lines):
        """Ajoute des lignes aux logs"""
        try:
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Détection du niveau de log
                tag = "INFO"
                if "ERROR" in line:
                    tag = "ERROR"
                elif "WARNING" in line:
                    tag = "WARNING"
                elif "DEBUG" in line:
                    tag = "DEBUG"
                
                self.logs_text.insert(tk.END, line + "\n", tag)
            
            # Auto-scroll
            if self.auto_scroll_var.get():
                self.logs_text.see(tk.END)
                
        except Exception as e:
            print(f"Erreur affichage logs: {e}")
    
    def refresh_logs(self):
        """Actualise les logs"""
        try:
            self.logs_text.delete(1.0, tk.END)
            
            if os.path.exists("trading_bot.log"):
                with open("trading_bot.log", 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.logs_text.insert(tk.END, content)
                    self.logs_text.see(tk.END)
                    
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire les logs: {e}")
    
    def clear_logs(self):
        """Vide les logs"""
        self.logs_text.delete(1.0, tk.END)
    
    def refresh_positions(self):
        """Actualise les positions"""
        # TODO: Implémenter la récupération des positions en temps réel
        pass
    
    def export_positions(self):
        """Exporte les positions en CSV"""
        # TODO: Implémenter l'export CSV
        pass
    
    def update_status(self):
        """Met à jour le statut périodiquement"""
        try:
            # Vérification si le bot est en cours
            if self.bot_process and self.bot_process.poll() is None:
                self.status_label.config(text="🟢 En cours", fg="green")
                mode = self.config_manager.get_trading_mode()
                self.info_label.config(text=f"Mode: {mode}")
            else:
                if self.bot_process:
                    # Le processus s'est arrêté
                    self.start_button.config(state="normal")
                    self.stop_button.config(state="disabled")
                    self.status_label.config(text="🔴 Arrêté", fg="red")
                    self.bot_process = None
                    self.stop_log_monitoring()
                
                self.info_label.config(text="")
            
        except Exception as e:
            print(f"Erreur update status: {e}")
        
        # Programmer la prochaine mise à jour
        self.root.after(2000, self.update_status)
    
    def run(self):
        """Lance l'interface"""
        self.root.mainloop()

# Point d'entrée
if __name__ == "__main__":
    # Import nécessaire pour les dialogs
    import tkinter.simpledialog
    
    interface = TradingInterface()
    interface.run()