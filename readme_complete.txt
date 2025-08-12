# 🤖 Bot de Trading Automatique

Un système de trading automatique basé sur tes stratégies de backtest RSI + MACD, conçu pour fonctionner avec Interactive Brokers.

## 🎯 Aperçu

Ce bot reproduit **exactement** la logique de tes scripts de backtest :
- **Stratégie RSI + MACD** : Signaux d'achat/vente selon tes paramètres
- **Stop Loss 5%** / **Take Profit 8%** comme dans ton backtest  
- **Frais 0.1%** par transaction
- **Gestion automatique** des positions et du risque
- **Interface graphique** pour surveillance et contrôle

## 📁 Structure des fichiers

```
📦 trading-bot/
├── 🚀 start.py              # Point d'entrée principal (COMMENCER ICI)
├── ⚙️ config.py             # Configuration centrale
├── 🔌 ib_connector.py       # Connexion Interactive Brokers  
├── 📈 strategies.py         # Stratégies de trading (RSI+MACD)
├── 🛡️ risk_manager.py       # Gestion des risques (SL/TP)
├── 🤖 trading_bot.py        # Bot principal
├── 🖥️ trading_interface.py   # Interface graphique
├── 📋 trading_config.json   # Configuration (créé automatiquement)
├── 📝 trading_bot.log       # Logs du bot
└── 📚 README.md            # Cette documentation
```

## 🔧 Installation et Configuration

### 1. Prérequis

**Python 3.7+** avec les packages suivants :
```bash
pip install ib_insync pandas ta numpy matplotlib
```

**Interactive Brokers :**
- Compte IB (gratuit pour Paper Trading)
- TWS (Trader Workstation) installé
- API activée dans TWS

### 2. Configuration Interactive Brokers

#### Étape 1 : Installation TWS
1. Télécharge TWS : https://www.interactivebrokers.com/fr/trading/tws.php
2. Installe et lance TWS
3. Connecte-toi avec tes identifiants IB

#### Étape 2 : Mode Paper Trading (RECOMMANDÉ)
1. Sur l'écran de connexion TWS, change le mode
2. Sélectionne **"Trading Simulé"** (Paper Trading)
3. Connecte-toi (tu auras 1M€ virtuel pour tester)

#### Étape 3 : Activation API
1. Dans TWS : **File** → **Global Configuration**
2. Clique sur **API** → **Settings**
3. ✅ Coche **"Enable ActiveX and Socket Clients"**
4. Vérifie que le port est **7497** (Paper Trading)
5. **OK** et redémarre TWS

## 🚀 Démarrage Rapide

### Option 1 : Démarrage automatique (RECOMMANDÉ)
```bash
python start.py
```
Le script vérifie tout automatiquement et te guide étape par étape.

### Option 2 : Interface graphique directe
```bash
python trading_interface.py
```

### Option 3 : Bot en ligne de commande
```bash
python trading_bot.py
```

## 🖥️ Interface Graphique

L'interface te permet de :

### 🎮 Contrôle
- **Démarrer/Arrêter** le bot
- **Tester la connexion** IB
- **Configuration rapide** (mode, capital)

### ⚙️ Configuration 
- **Interactive Brokers** : Host, port, client ID
- **Trading** : Capital, % par position, Stop Loss, Take Profit
- **Stratégie** : Paramètres RSI et MACD
- **Tickers** : Actions à surveiller (CAC40)

### 📊 Monitoring
- **Statistiques** en temps réel
- **Positions** détaillées avec P&L
- **Logs** avec coloration syntaxique

## 📈 Stratégie de Trading

### RSI + MACD (Reproduction exacte de ton backtest)

**Signaux d'achat :**
- RSI < 30 (survente) **OU**
- Croisement MACD haussier (MACD > Signal ET MACD précédent ≤ Signal précédent)

**Signaux de vente :**
- RSI > 70 (surachat) **OU** 
- Croisement MACD baissier (MACD < Signal ET MACD précédent ≥ Signal précédent)

**Gestion des risques :**
- Stop Loss automatique à **-5%**
- Take Profit automatique à **+8%**
- Maximum **5 positions** simultanées
- **10% du capital** par position

## ⚙️ Configuration

Le fichier `trading_config.json` contient tous les paramètres :

```json
{
  "ib": {
    "host": "127.0.0.1",
    "port": 7497,          // 7497=Paper, 7496=Live
    "client_id": 1
  },
  "trading": {
    "capital_initial": 10000,
    "position_size_pct": 0.1,    // 10% par position
    "max_positions": 5,
    "stop_loss_pct": 0.05,       // 5% comme ton backtest
    "take_profit_pct": 0.08,     // 8% comme ton backtest
    "frais_pourcentage": 0.001   // 0.1% comme ton backtest
  },
  "strategy": {
    "rsi_window": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9
  },
  "system": {
    "tickers": ["AIR.PA", "MC.PA", "OR.PA", "SAN.PA", "BNP.PA"]
  }
}
```

## 🛡️ Sécurité et Risques

### ⚠️ Mode Paper Trading vs Live

| **Paper Trading (7497)** | **Live Trading (7496)** |
|---------------------------|--------------------------|
| ✅ Argent virtuel (1M€)   | ⚠️ **ARGENT RÉEL**      |
| ✅ Zéro risque            | ⚠️ **RISQUE FINANCIER** |
| ✅ Test parfait           | ⚠️ Confirmations multiples |

### 🔒 Protections intégrées
- **Confirmation obligatoire** pour mode Live
- **Stop Loss automatiques** (-5%)
- **Limite de positions** (5 max)
- **Logs complets** de toutes les opérations
- **Gestion d'erreurs** robuste

## 📋 Utilisation Recommandée

### Phase 1 : Développement (Paper Trading)
1. ✅ **Lance en Paper Trading** (port 7497)
2. ✅ **Teste pendant 1-2 semaines** minimum
3. ✅ **Vérifie les signaux** vs tes backtests
4. ✅ **Valide les performances**

### Phase 2 : Transition (Live petit capital)
1. ⚠️ **Change en Live Trading** (port 7496)
2. ⚠️ **Commence avec 500-1000€** maximum
3. ⚠️ **Surveille CHAQUE trade** manuellement
4. ⚠️ **Compare avec Paper Trading**

### Phase 3 : Déploiement (Après validation)
1. 🚀 **Augmente progressivement** le capital
2. 🚀 **Automatise complètement**
3. 🚀 **Diversifie les stratégies**

## 📊 Surveillance et Logs

### Logs importants à surveiller :
- `🟢 SIGNAL D'ACHAT` : Nouvel achat détecté
- `🔴 SIGNAL DE VENTE` : Vente (signal ou SL/TP)
- `🛑 STOP LOSS` : Perte -5% 
- `🎯 TAKE PROFIT` : Gain +8%
- `❌ ERREUR` : Problèmes techniques

### Fichiers de surveillance :
- `trading_bot.log` : Logs détaillés du bot
- `trading_config.json` : Configuration actuelle

## 🆘 Dépannage

### Problèmes courants

**❌ "Connexion IB échouée"**
- Vérifier que TWS est ouvert et connecté
- Vérifier le port (7497 pour Paper)
- Redémarrer TWS

**❌ "API en lecture seule"**
- Dans TWS, accepter les droits d'écriture pour l'API
- Décocher "Read-Only API" dans la config

**❌ "Aucune donnée historique"**
- Vérifier que le marché est ouvert
- Vérifier les symboles (ex: AIR.PA pour Airbus)

**❌ "Erreur ordre"**
- Vérifier le capital disponible
- Vérifier que l'action est tradable

### Debug étape par étape

1. **Test connexion :**
   ```bash
   python start.py
   # Choix 3 : Test de connexion
   ```

2. **Vérification config :**
   ```bash
   python start.py  
   # Choix 4 : Vérifier configuration
   ```

3. **Logs détaillés :**
   ```bash
   tail -f trading_bot.log
   ```

## 🔄 Comparaison avec ton backtest

| **Aspect** | **Ton Backtest** | **Bot Live** |
|------------|------------------|--------------|
| Stratégie | RSI + MACD | ✅ **Identique** |
| Stop Loss | 5% | ✅ **Identique** |
| Take Profit | 8% | ✅ **Identique** |
| Frais | 0.1% | ✅ **Identique** |
| Logique signaux | OR (RSI OU MACD) | ✅ **Identique** |
| Gestion positions | 1 par ticker | ✅ **Identique** |

## 📞 Support

- **Logs** : Consulter `trading_bot.log`
- **Test** : Utiliser l'option test dans `start.py`
- **Config** : Vérifier `trading_config.json`
- **Interface** : Utiliser l'onglet Monitoring

## 🎯 Prochaines Améliorations

- [ ] **Stratégies supplémentaires** (Bollinger, Stochastic)
- [ ] **Optimisation automatique** des paramètres
- [ ] **Backtesting intégré** avec données live
- [ ] **Notifications** (email, Telegram)
- [ ] **API REST** pour contrôle externe

---

## ⚡ Démarrage en 3 étapes

1. **Lance TWS en Paper Trading**
2. **Active l'API** (File > Global Config > API)
3. **Execute :** `python start.py` et choisis option 1

**🎉 Ton bot sera opérationnel en moins de 5 minutes !**