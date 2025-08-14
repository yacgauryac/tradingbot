# config_debug.py - Debug configs appliquées

import json
import os

def debug_configs():
    """Debug configs par symbole"""
    print("🔍 DEBUG CONFIGURATIONS APPLIQUÉES")
    print("=" * 50)
    
    # Charger config avancée
    if os.path.exists('advanced_strategy_config.json'):
        with open('advanced_strategy_config.json', 'r') as f:
            advanced_data = json.load(f)
        
        symbol_sectors = advanced_data.get('symbol_sectors', {})
        sector_configs = advanced_data.get('sectors', {})
        symbol_configs = advanced_data.get('symbols', {})
        
        print("📊 MAPPING SYMBOLES → SECTEURS:")
        for symbol, sector in symbol_sectors.items():
            print(f"   {symbol} → {sector}")
        
        print("\n🎯 TEST CONFIGS POUR SYMBOLES CLÉS:")
        test_symbols = ['AAPL', 'TSLA', 'JPM', 'CE', 'GOOGL']
        
        for symbol in test_symbols:
            print(f"\n📊 {symbol}:")
            
            # Config de base
            base_config = {
                'rsi_window': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'min_confidence': 0.15
            }
            
            # Secteur
            sector = symbol_sectors.get(symbol, 'aucun')
            print(f"   Secteur: {sector}")
            
            # Config secteur
            if sector in sector_configs:
                sector_config = sector_configs[sector]
                print(f"   Config secteur: {sector_config}")
                
                # Application
                if 'rsi' in sector_config:
                    rsi_config = sector_config['rsi']
                    if 'window' in rsi_config:
                        base_config['rsi_window'] = rsi_config['window']
                    if 'oversold' in rsi_config:
                        base_config['rsi_oversold'] = rsi_config['oversold']
                    if 'overbought' in rsi_config:
                        base_config['rsi_overbought'] = rsi_config['overbought']
                
                if 'thresholds' in sector_config:
                    thresholds = sector_config['thresholds']
                    if 'min_confidence' in thresholds:
                        base_config['min_confidence'] = thresholds['min_confidence']
            
            # Config symbole spécifique
            if symbol in symbol_configs:
                symbol_config = symbol_configs[symbol]
                print(f"   Config symbole: {symbol_config}")
                
                if 'rsi' in symbol_config:
                    rsi_config = symbol_config['rsi']
                    if 'window' in rsi_config:
                        base_config['rsi_window'] = rsi_config['window']
                    if 'oversold' in rsi_config:
                        base_config['rsi_oversold'] = rsi_config['oversold']
                    if 'overbought' in rsi_config:
                        base_config['rsi_overbought'] = rsi_config['overbought']
                
                if 'thresholds' in symbol_config:
                    thresholds = symbol_config['thresholds']
                    if 'min_confidence' in thresholds:
                        base_config['min_confidence'] = thresholds['min_confidence']
            
            # Config finale
            print(f"   Config finale:")
            print(f"     RSI: {base_config['rsi_window']} périodes, {base_config['rsi_oversold']}/{base_config['rsi_overbought']}")
            print(f"     Confiance min: {base_config['min_confidence']:.1%}")
            
            # Comparaison avec standard
            if (base_config['rsi_oversold'] != 30 or 
                base_config['rsi_overbought'] != 70 or 
                base_config['min_confidence'] != 0.15):
                print(f"   ⚠️  DIFFÉRENT du standard (RSI 30/70, conf 15%)")
            else:
                print(f"   ✅ Identique au standard")
    
    else:
        print("❌ Fichier advanced_strategy_config.json non trouvé")

def suggest_fixes():
    """Suggestions d'ajustements"""
    print(f"\n💡 SUGGESTIONS D'AJUSTEMENT:")
    print(f"1. 🎯 SEUILS CONFIANCE trop élevés:")
    print(f"   Tech: 20% → réduire à 12%")
    print(f"   TSLA: 25% → réduire à 15%")
    
    print(f"\n2. 🎯 SEUILS RSI peut-être trop agressifs:")
    print(f"   AAPL: 25/75 → essayer 28/72")
    print(f"   TSLA: 20/80 → essayer 25/75")
    
    print(f"\n3. 🔄 TEST avec configs RELÂCHÉES:")
    print(f"   Temps de marché: peut-être pas assez volatil")
    print(f"   RSI trop bas actuellement")

def create_relaxed_config():
    """Créer version relâchée pour test"""
    print(f"\n🔧 CRÉATION CONFIG RELÂCHÉE...")
    
    relaxed_config = {
        "default": {
            "rsi": {"window": 14, "oversold": 30, "overbought": 70, "weight": 0.4},
            "macd": {"fast": 12, "slow": 26, "signal": 9, "weight": 0.3},
            "thresholds": {"min_confidence": 0.10, "strong_signal": 0.6}  # Réduit de 15% à 10%
        },
        "sectors": {
            "tech": {
                "rsi": {"window": 12, "oversold": 28, "overbought": 72},  # Moins agressif
                "macd": {"fast": 10, "slow": 22, "signal": 7},
                "thresholds": {"min_confidence": 0.12}  # Réduit de 20% à 12%
            },
            "finance": {
                "rsi": {"window": 18, "oversold": 32, "overbought": 68},
                "macd": {"fast": 14, "slow": 28, "signal": 10},
                "thresholds": {"min_confidence": 0.10}
            }
        },
        "symbols": {
            "TSLA": {
                "rsi": {"window": 10, "oversold": 25, "overbought": 75},  # Moins extrême
                "thresholds": {"min_confidence": 0.15}  # Réduit de 25% à 15%
            }
        },
        "symbol_sectors": {
            "AAPL": "tech", "MSFT": "tech", "GOOGL": "tech", "META": "tech", "NVDA": "tech",
            "AMZN": "tech", "NFLX": "tech",
            "JPM": "finance", "BAC": "finance", "WFC": "finance"
        }
    }
    
    with open('advanced_strategy_config_relaxed.json', 'w') as f:
        json.dump(relaxed_config, f, indent=2)
    
    print(f"✅ Config relâchée sauvée: advanced_strategy_config_relaxed.json")
    print(f"💡 Renommez en 'advanced_strategy_config.json' pour tester")

def main():
    debug_configs()
    suggest_fixes()
    create_relaxed_config()

if __name__ == "__main__":
    main()
