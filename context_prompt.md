# 🤖 CONTEXTE PROJET TRADING BOT

## 📊 **ÉTAT ACTUEL DU PROJET**

### **🎯 OBJECTIF PRINCIPAL**
Développement d'un système de trading automatisé basé sur RSI + MACD avec Interactive Brokers (TWS) en mode simulé.

### **✅ SYSTÈME FONCTIONNEL CRÉÉ**

#### **1. STRATÉGIE DE BASE (strategies.py)**
- **RSIMACDStrategy** : Reproduction exacte du backtest utilisateur
- **Signaux d'achat** : RSI < 30 OU croisement MACD haussier
- **Signaux de vente** : RSI > 70 OU croisement MACD baissier
- **Logique OR** (pas AND) pour plus de signaux
- **Calcul de confiance** intelligent

#### **2. BOT AUTONOME (auto_trading_bot.py)**
- **Scan automatique** toutes les 5 minutes
- **Achat automatique** des meilleurs signaux (max 3 positions)
- **$1000 max** par position
- **Surveillance continue** et **vente automatique** selon règles :
  - +5% profit → VENTE
  - -8% stop loss → VENTE  
  - 10 jours max → VENTE
  - RSI > 70 → VENTE
- **Sauvegarde état** dans bot_state.json

#### **3. MONITORING (position_monitor.py + real_dashboard.py)**
- **position_monitor.py** : Surveillance CLI d'une position spécifique
- **real_dashboard.py** : Interface graphique Tkinter avec vraies données IB
- **Connexion IB** directe pour prix temps réel
- **Calcul RSI** automatique
- **Export données** JSON

### **💼 POSITIONS ACTUELLES (MODE SIMULÉ)**
1. **CE (Celanese)** : 46 actions @ $42.21 moyenne (doublée automatiquement)
2. **AMZN (Amazon)** : 4 actions @ $232.97  
3. **ACVA (ACV Auctions)** : 87 actions @ $11.47

### **📈 WATCHLISTS CONFIGURÉES**
- **Breakout** : CSCO, GOOGL, META, MSFT, APP, BSX
- **Oversold** : ACVA, AIV, CE
- **Momentum** : AAPL, TSLA, NVDA, AMZN

## 🔧 **CONFIGURATION TECHNIQUE**

### **Interactive Brokers Setup**
- **TWS mode simulé** (port 7497)
- **API activée** avec popup bypass
- **ClientID** multiples (1-8) pour éviter conflits
- **Données historiques** (gratuites) vs temps réel (payant)

### **Paramètres Stratégie**
```python
'rsi_window': 14,
'rsi_oversold': 30,
'rsi_overbought': 70,
'macd_fast': 12,
'macd_slow': 26,
'macd_signal': 9,
'profit_target': 0.05,     # +5%
'stop_loss': -0.08,        # -8%
'max_hold_days': 10,
'max_positions': 3,
'max_investment_per_trade': 1000
```

## 📁 **STRUCTURE FICHIERS CRÉÉS**

### **Scripts Principaux**
- `strategies.py` - Stratégies RSI+MACD
- `auto_trading_bot.py` - Bot autonome complet
- `position_monitor.py` - Surveillance position simple
- `real_dashboard.py` - Dashboard Tkinter temps réel
- `signal_analyzer.py` - Analyse détaillée signaux
- `order_tester.py` - Test ordres avec stratégie sortie
- `simple_order_test.py` - Test ordre simple sans abonnement
- `minimal_bot.py` - Bot minimal pour tests connexion

### **Fichiers de Données**
- `position_ce.txt` - Position manuelle CE
- `bot_state.json` - État bot autonome (positions, logs)
- `trade_history.txt` - Historique trades fermés

### **Interfaces**
- `trading_dashboard.html` - Dashboard web demo (JavaScript)
- `real_dashboard.py` - Dashboard natif Python (vraies données)

## 🎯 **TESTS RÉALISÉS**

### **✅ Connexion IB** 
- Problème popup TWS → résolu
- Données historiques → OK
- Passage ordres simulés → OK

### **✅ Détection Signaux**
- CE détecté RSI 20.7 (ultra survendu) → acheté
- ACVA détecté RSI 21.8 → acheté par bot
- AMZN détecté RSI 28.5 → acheté par bot

### **✅ Gestion Automatique**
- Bot limite 3/3 positions → arrêt achat automatique ✅
- Surveillance continue → toutes les 60s ✅
- Dashboard temps réel → mise à jour auto ✅

## 🚀 **PROCHAINES ÉTAPES PRÉVUES**

### **Phase 1 : Interface Unifiée**
- Dashboard combo : autotrading + monitoring
- Contrôles bot (start/stop/paramètres)
- Graphiques RSI/MACD temps réel

### **Phase 2 : Machine Learning**
- Random Forest pour optimiser paramètres RSI/MACD
- Backtest automatique sur historique
- Ajustement dynamique seuils

### **Phase 3 : Production**
- Passage en mode réel (si tests concluants)
- Gestion risque avancée
- Reporting performance

## ⚠️ **POINTS D'ATTENTION**

### **Limitations Actuelles**
- Mode simulé seulement (argent fictif)
- Données temps réel nécessitent abonnement IB payant
- Max 3 positions simultanées (paramétrable)

### **Bugs Résolus**
- Popup TWS autorisation → bypass configuré
- Parsing position "23.0" → int(float()) 
- Données temps réel → fallback historiques

## 💡 **QUESTIONS OUVERTES**

1. **Interface combo** autotrading + monitoring ?
2. **Paramètres ML** : features à ajouter (volume, momentum, etc.) ?
3. **Passage réel** : timeline et critères validation ?
4. **Diversification** : autres marchés (crypto, forex) ?

---

**Utilisez ce contexte pour reprendre exactement où on s'est arrêtés !**