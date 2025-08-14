# simple_bot_debug.py - Debug simple sans psutil

import os
import json
from datetime import datetime

def check_bot_files():
    """Vérifier les fichiers du bot"""
    print("🔍 DIAGNOSTIC BOT SIMPLE")
    print("=" * 40)
    
    # 1. Config
    print("📊 1. CONFIGURATION:")
    if os.path.exists('bot_config.json'):
        with open('bot_config.json', 'r') as f:
            config = json.load(f)
        print(f"✅ bot_config.json trouvé:")
        print(f"   Max positions: {config.get('max_positions', 'N/A')}")
        print(f"   Max investment: ${config.get('max_investment', 'N/A')}")
        print(f"   RSI seuils: {config.get('rsi_oversold', 'N/A')}/{config.get('rsi_overbought', 'N/A')}")
    else:
        print("❌ bot_config.json MANQUANT")
        print("   → Sauvegardez config dans l'interface!")
        return False
    
    # 2. État
    print("\n📊 2. ÉTAT BOT:")
    if os.path.exists('bot_state.json'):
        with open('bot_state.json', 'r') as f:
            state = json.load(f)
        
        positions = state.get('positions', {})
        trade_log = state.get('trade_log', [])
        
        print(f"✅ bot_state.json trouvé:")
        print(f"   Positions actuelles: {len(positions)}")
        
        if positions:
            for symbol, pos in positions.items():
                price = pos.get('entry_price', 'N/A')
                qty = pos.get('quantity', 'N/A')
                print(f"     📍 {symbol}: {qty} @ ${price}")
        
        print(f"   Total trades: {len(trade_log)}")
        
        # Dernière activité
        last_update = state.get('last_update', 'Jamais')
        if last_update != 'Jamais':
            print(f"   Dernière MAJ: {last_update}")
        else:
            print("   ⚠️ Aucune activité bot détectée")
        
        # Calcul places libres
        max_pos = config.get('max_positions', 3)
        places_libres = max_pos - len(positions)
        
        print(f"\n🎯 ANALYSE:")
        print(f"   Max configuré: {max_pos}")
        print(f"   Positions: {len(positions)}")
        print(f"   Places libres: {places_libres}")
        
        if places_libres > 0:
            print(f"   ✅ Bot PEUT acheter ({places_libres} places)")
        else:
            print(f"   🚫 Bot NE PEUT PAS acheter (limite atteinte)")
            
    else:
        print("❌ bot_state.json MANQUANT")
        print("   → Bot jamais démarré!")
        return False
    
    return True

def check_bot_should_buy():
    """Vérifier si bot devrait acheter selon simulation"""
    print("\n🤖 3. ANALYSE LOGIQUE:")
    
    # Récap simulation précédente
    print("   Simulation bot_logger.py a trouvé:")
    print("   ✅ 8 signaux détectés")
    print("   ✅ CSCO: 30% confiance") 
    print("   ✅ Devrait acheter 14 CSCO @ $69.39")
    
    # État réel
    if os.path.exists('bot_state.json') and os.path.exists('bot_config.json'):
        with open('bot_state.json', 'r') as f:
            state = json.load(f)
        with open('bot_config.json', 'r') as f:
            config = json.load(f)
        
        positions = state.get('positions', {})
        max_pos = config.get('max_positions', 3)
        
        # CSCO déjà détenu ?
        if 'CSCO' in positions:
            print("   ❌ CSCO déjà en portefeuille")
            return
        
        # Places libres ?
        if len(positions) >= max_pos:
            print("   ❌ Limite positions atteinte")
            return
        
        print("   ✅ CSCO pas détenu")
        print("   ✅ Places libres disponibles")
        print("   🎯 LE BOT DEVRAIT ACHETER CSCO!")

def check_bot_timing():
    """Vérifier timing bot"""
    print("\n⏰ 4. TIMING BOT:")
    print("   Bot autonome scan toutes les 5 minutes")
    print("   Dernière simulation manuelle: maintenant")
    
    if os.path.exists('bot_state.json'):
        with open('bot_state.json', 'r') as f:
            state = json.load(f)
        
        last_update = state.get('last_update', None)
        if last_update:
            print(f"   Dernière activité bot: {last_update}")
            print("   💡 Si > 10 min → Bot probablement arrêté")
        else:
            print("   ❌ Aucune trace d'activité bot")

def recommendations():
    """Recommandations"""
    print("\n💡 RECOMMANDATIONS:")
    
    if not os.path.exists('bot_config.json'):
        print("🔧 1. PRIORITÉ: Sauvegarder config")
        print("   → Interface combo → Contrôle Bot → Sauvegarder Config")
        return
    
    if not os.path.exists('bot_state.json'):
        print("🚀 2. PRIORITÉ: Démarrer bot")
        print("   → Interface combo → Contrôle Bot → Démarrer Bot")
        return
    
    print("🔄 3. REDÉMARRAGE BOT:")
    print("   → Interface combo → Contrôle Bot")
    print("   → 🛑 Arrêter Bot (attendre 5s)")
    print("   → 🚀 Démarrer Bot")
    print("   → Vérifier log bot pour erreurs")
    
    print("\n👁️ 4. MONITORING:")
    print("   → python bot_logger.py → option 2")
    print("   → Voir si bot scanne vraiment")
    
    print("\n⏱️ 5. PATIENCE:")
    print("   → Prochain scan bot dans max 5 min")
    print("   → Si CSCO toujours signal fort → achat automatique")

def main():
    print("🔧 DIAGNOSTIC SIMPLE BOT")
    print("Pourquoi pas d'achat CSCO ?")
    print("=" * 50)
    
    files_ok = check_bot_files()
    
    if files_ok:
        check_bot_should_buy()
        check_bot_timing()
    
    recommendations()
    
    print("\n" + "=" * 50)
    if files_ok:
        print("✅ FICHIERS OK → Vérifiez interface et redémarrez bot")
    else:
        print("❌ FICHIERS MANQUANTS → Sauvegardez config et démarrez bot")

if __name__ == "__main__":
    main()
