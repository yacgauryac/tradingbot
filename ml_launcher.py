# ml_launcher.py
"""
🚀 ML TRADING BOT LAUNCHER
Interface unifiée pour optimisation ML et intégration avec bot autonome
Workflow complet : Collecte → Entraînement → Optimisation → Déploiement
"""

import os
import sys
import json
import time
from datetime import datetime
import subprocess

class MLTradingBotLauncher:
    """
    Lanceur principal pour workflow ML complet
    """
    
    def __init__(self):
        self.current_step = 1
        self.total_steps = 5
        
    def display_header(self):
        """Affichage header principal"""
        print("🤖 ML TRADING BOT LAUNCHER v2.0")
        print("=" * 60)
        print("🎯 Optimisation Random Forest pour Stratégie RSI+MACD")
        print("🔗 Intégration complète avec Bot Autonome existant")
        print("=" * 60)
    
    def check_prerequisites(self):
        """Vérification prérequis"""
        print(f"\n📋 ÉTAPE {self.current_step}/{self.total_steps}: VÉRIFICATION PRÉREQUIS")
        print("-" * 40)
        
        requirements = []
        
        # 1. Vérification fichiers bot existant
        bot_files = [
            'auto_trading_bot.py',
            'bot_state.json',
            'advanced_strategy_config.py'
        ]
        
        for file in bot_files:
            if os.path.exists(file):
                requirements.append(f"✅ {file}")
            else:
                requirements.append(f"❌ {file} MANQUANT")
        
        # 2. Vérification modules Python
        required_modules = [
            'sklearn', 'pandas', 'numpy', 'ib_insync', 'joblib'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                requirements.append(f"✅ Module {module}")
            except ImportError:
                requirements.append(f"❌ Module {module} MANQUANT")
        
        # 3. Vérification TWS/IB
        if os.path.exists('bot_state.json'):
            try:
                with open('bot_state.json', 'r') as f:
                    state = json.load(f)
                positions = state.get('positions', {})
                requirements.append(f"✅ Bot state OK ({len(positions)} positions)")
            except:
                requirements.append(f"⚠️ Bot state illisible")
        
        # Affichage résultats
        print("\n📊 VÉRIFICATION SYSTÈME:")
        for req in requirements:
            print(f"   {req}")
        
        missing_critical = [r for r in requirements if '❌' in r and any(f in r for f in ['auto_trading_bot.py', 'sklearn', 'ib_insync'])]
        
        if missing_critical:
            print(f"\n❌ PRÉREQUIS CRITIQUES MANQUANTS:")
            for missing in missing_critical:
                print(f"   {missing}")
            return False
        
        print(f"\n✅ Prérequis satisfaits - Prêt pour optimisation ML")
        self.current_step += 1
        return True
    
    def configure_ml_optimization(self):
        """Configuration de l'optimisation ML"""
        print(f"\n⚙️ ÉTAPE {self.current_step}/{self.total_steps}: CONFIGURATION ML")
        print("-" * 40)
        
        print("📊 PARAMÈTRES D'OPTIMISATION:")
        print("1. 🎯 Optimisation ciblée (positions actuelles + watchlist)")
        print("2. 🌐 Optimisation étendue (large univers)")
        print("3. ⚡ Optimisation rapide (données réduites)")
        print("4. 🔧 Configuration personnalisée")
        
        choice = input("\nChoix configuration (1/2/3/4) [1]: ").strip() or "1"
        
        config = {}
        
        if choice == "1":
            # Optimisation ciblée
            config = {
                'symbols': ['CE', 'AMZN', 'ACVA', 'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'JPM'],
                'days': 365,
                'description': 'Optimisation ciblée sur positions et watchlist'
            }
            
        elif choice == "2":
            # Optimisation étendue
            config = {
                'symbols': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMZN', 'TSLA',
                           'JPM', 'BAC', 'WFC', 'JNJ', 'PFE', 'XOM', 'CVX',
                           'CE', 'ACVA', 'CSCO', 'BSX', 'APP'],
                'days': 500,
                'description': 'Optimisation étendue multi-secteurs'
            }
            
        elif choice == "3":
            # Optimisation rapide
            config = {
                'symbols': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'CE'],
                'days': 180,
                'description': 'Optimisation rapide pour tests'
            }
            
        elif choice == "4":
            # Configuration personnalisée
            print("\n🔧 CONFIGURATION PERSONNALISÉE:")
            symbols_input = input("Symboles (séparés par virgules) [AAPL,MSFT,GOOGL]: ").strip()
            if symbols_input:
                symbols = [s.strip().upper() for s in symbols_input.split(',')]
            else:
                symbols = ['AAPL', 'MSFT', 'GOOGL']
            
            days_input = input("Jours d'historique (180-730) [365]: ").strip()
            days = int(days_input) if days_input.isdigit() else 365
            
            config = {
                'symbols': symbols,
                'days': days,
                'description': 'Configuration personnalisée utilisateur'
            }
        
        print(f"\n✅ Configuration ML sélectionnée:")
        print(f"   📊 Symboles: {len(config['symbols'])} ({', '.join(config['symbols'][:5])}{'...' if len(config['symbols']) > 5 else ''})")
        print(f"   📅 Historique: {config['days']} jours")
        print(f"   📝 Description: {config['description']}")
        
        # Sauvegarde config
        with open('ml_config_temp.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        self.current_step += 1
        return config
    
    def run_ml_optimization(self, config):
        """Exécution de l'optimisation ML"""
        print(f"\n🤖 ÉTAPE {self.current_step}/{self.total_steps}: OPTIMISATION ML")
        print("-" * 40)
        
        print("🚀 Lancement de l'optimisation Random Forest...")
        print("⏳ Cette étape peut prendre 10-20 minutes selon la configuration")
        print("💡 Vous pouvez suivre les progrès dans les logs")
        
        # Préparation du script d'optimisation
        optimization_script = f"""
# Script d'optimisation généré automatiquement
from ml_strategy_optimizer_v2 import MLStrategyOptimizer
import json

# Chargement configuration
with open('ml_config_temp.json', 'r') as f:
    config = json.load(f)

# Lancement optimisation
optimizer = MLStrategyOptimizer()
results = optimizer.optimize_bot_parameters(
    symbols=config['symbols'],
    days=config['days']
)

# Sauvegarde résultats
if results:
    with open('ml_results_temp.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print("\\n🎉 OPTIMISATION TERMINÉE AVEC SUCCÈS!")
else:
    print("\\n❌ OPTIMISATION ÉCHOUÉE")
"""
        
        # Écriture script temporaire
        with open('run_optimization_temp.py', 'w') as f:
            f.write(optimization_script)
        
        try:
            # Exécution optimisation
            print("\n🔄 Exécution en cours...")
            
            # Option 1: Exécution dans le même processus
            try:
                from ml_strategy_optimizer_v2 import MLStrategyOptimizer
                
                optimizer = MLStrategyOptimizer()
                results = optimizer.optimize_bot_parameters(
                    symbols=config['symbols'],
                    days=config['days']
                )
                
                if results:
                    # Sauvegarde résultats
                    with open('ml_results_temp.json', 'w') as f:
                        json.dump(results, f, indent=2, default=str)
                    
                    print("\n🎉 OPTIMISATION TERMINÉE AVEC SUCCÈS!")
                    print(f"📊 Symboles analysés: {len(results['symbols_analyzed'])}")
                    print(f"📊 Score ML: {results['ml_performance']['test_score']:.4f}")
                    
                    self.current_step += 1
                    return results
                else:
                    print("\n❌ OPTIMISATION ÉCHOUÉE")
                    return None
                    
            except ImportError:
                print("❌ Module ml_strategy_optimizer_v2 non trouvé")
                print("💡 Assurez-vous que le fichier ml_strategy_optimizer_v2.py est présent")
                return None
                
        except Exception as e:
            print(f"❌ Erreur durant optimisation: {e}")
            return None
        
        finally:
            # Nettoyage fichiers temporaires
            for temp_file in ['run_optimization_temp.py']:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
    
    def review_ml_results(self, results):
        """Révision des résultats ML"""
        print(f"\n📊 ÉTAPE {self.current_step}/{self.total_steps}: RÉVISION RÉSULTATS")
        print("-" * 40)
        
        if not results:
            print("❌ Aucun résultat à réviser")
            return False
        
        # Affichage résultats détaillés
        print("🎯 RÉSULTATS OPTIMISATION ML:")
        print(f"   📊 Score test: {results['ml_performance']['test_score']:.4f}")
        print(f"   📊 Score validation croisée: {results['ml_performance']['cv_score_mean']:.4f}")
        print(f"   📊 Taille dataset: {results['dataset_size']} observations")
        
        print(f"\n🔝 TOP FEATURES IMPORTANTES:")
        top_features = results['ml_performance']['top_features']
        for feature, importance in list(top_features.items())[:5]:
            print(f"   {feature}: {importance:.4f}")
        
        print(f"\n⚙️ PARAMÈTRES OPTIMISÉS:")
        optimized = results['optimized_params']
        for param, value in optimized.items():
            print(f"   {param}: {value}")
        
        # Comparaison avec paramètres actuels
        current_params = {}
        if os.path.exists('bot_config.json'):
            with open('bot_config.json', 'r') as f:
                current_params = json.load(f)
        
        print(f"\n🔄 COMPARAISON PARAMÈTRES:")
        comparison_params = {
            'max_positions': 'max_positions',
            'rsi_oversold': 'rsi_oversold', 
            'rsi_overbought': 'rsi_overbought'
        }
        
        for opt_param, cur_param in comparison_params.items():
            if opt_param in optimized and cur_param in current_params:
                old_val = current_params[cur_param]
                new_val = optimized[opt_param]
                if opt_param in ['profit_target', 'stop_loss']:
                    new_val *= 100  # Conversion pour affichage
                
                change = "📈" if new_val > old_val else "📉" if new_val < old_val else "➡️"
                print(f"   {change} {opt_param}: {old_val} → {new_val}")
        
        # Validation utilisateur
        print(f"\n❓ VALIDATION RÉSULTATS:")
        print(f"1. ✅ Appliquer paramètres optimisés")
        print(f"2. 🔍 Révision manuelle des paramètres") 
        print(f"3. ❌ Rejeter optimisation")
        
        choice = input("\nChoix (1/2/3) [1]: ").strip() or "1"
        
        if choice == "1":
            print("✅ Paramètres approuvés pour déploiement")
            self.current_step += 1
            return True
        elif choice == "2":
            print("🔍 Révision manuelle - À implémenter")
            return True
        else:
            print("❌ Optimisation rejetée")
            return False
    
    def deploy_ml_integration(self):
        """Déploiement de l'intégration ML"""
        print(f"\n🚀 ÉTAPE {self.current_step}/{self.total_steps}: DÉPLOIEMENT ML")
        print("-" * 40)
        
        print("🔄 ÉTAPES DE DÉPLOIEMENT:")
        print("1. 🧪 Test d'intégration (sans modification)")
        print("2. 💾 Backup configuration actuelle")
        print("3. ⚙️ Application paramètres optimisés")
        print("4. 🔗 Activation capacités ML dans le bot")
        
        confirm = input("\n❓ Procéder au déploiement ? (y/N): ").strip().lower()
        
        if confirm != 'y':
            print("Déploiement annulé")
            return False
        
        try:
            # Import du bridge d'intégration
            from ml_integration_bridge import MLIntegrationBridge
            
            bridge = MLIntegrationBridge()
            
            # Test d'intégration
            print("\n🧪 Test d'intégration...")
            if not bridge.deploy_ml_integration(dry_run=True):
                print("❌ Test d'intégration échoué")
                return False
            
            # Déploiement réel
            print("\n🚀 Déploiement réel...")
            if bridge.deploy_ml_integration(dry_run=False):
                print("\n🎉 DÉPLOIEMENT ML RÉUSSI!")
                print("\n📋 PROCHAINES ÉTAPES:")
                print("   1. 🔄 Redémarrer le bot autonome")
                print("   2. 👁️ Surveiller performances via dashboard") 
                print("   3. 📊 Comparer avec période pré-ML")
                print("   4. 🔧 Ajuster si nécessaire")
                
                return True
            else:
                print("❌ Déploiement échoué")
                return False
                
        except ImportError:
            print("❌ Module ml_integration_bridge non trouvé")
            return False
        except Exception as e:
            print(f"❌ Erreur déploiement: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Nettoyage fichiers temporaires"""
        temp_files = [
            'ml_config_temp.json',
            'ml_results_temp.json',
            'run_optimization_temp.py'
        ]
        
        for file in temp_files:
            if os.path.exists(file):
                os.remove(file)
    
    def run_complete_workflow(self):
        """Workflow complet ML"""
        self.display_header()
        
        try:
            # Étape 1: Vérification prérequis
            if not self.check_prerequisites():
                print("❌ Prérequis non satisfaits - Arrêt")
                return
            
            input("\n⏸️ Appuyez sur Entrée pour continuer...")
            
            # Étape 2: Configuration
            config = self.configure_ml_optimization()
            if not config:
                print("❌ Configuration échouée - Arrêt")
                return
            
            input("\n⏸️ Appuyez sur Entrée pour lancer l'optimisation...")
            
            # Étape 3: Optimisation ML
            results = self.run_ml_optimization(config)
            if not results:
                print("❌ Optimisation échouée - Arrêt")
                return
            
            input("\n⏸️ Appuyez sur Entrée pour réviser les résultats...")
            
            # Étape 4: Révision résultats
            if not self.review_ml_results(results):
                print("❌ Résultats rejetés - Arrêt")
                return
            
            input("\n⏸️ Appuyez sur Entrée pour déployer...")
            
            # Étape 5: Déploiement
            if self.deploy_ml_integration():
                print("\n🎉 WORKFLOW ML TERMINÉ AVEC SUCCÈS!")
                print("🤖 Votre bot est maintenant optimisé par Machine Learning!")
            else:
                print("❌ Déploiement échoué")
            
        except KeyboardInterrupt:
            print("\n🛑 Workflow ML interrompu par l'utilisateur")
        except Exception as e:
            print(f"❌ Erreur workflow: {e}")
        finally:
            self.cleanup_temp_files()

def main():
    """Point d'entrée principal"""
    launcher = MLTradingBotLauncher()
    
    print("🎯 OPTIONS DE LANCEMENT:")
    print("1. 🚀 Workflow ML complet (Recommandé)")
    print("2. 🔧 Optimisation ML seulement")
    print("3. 🌉 Intégration ML seulement")
    print("4. 📊 Status système ML")
    
    choice = input("\nChoix (1/2/3/4) [1]: ").strip() or "1"
    
    if choice == "1":
        launcher.run_complete_workflow()
    elif choice == "2":
        config = launcher.configure_ml_optimization()
        if config:
            launcher.run_ml_optimization(config)
    elif choice == "3":
        launcher.deploy_ml_integration()
    elif choice == "4":
        launcher.check_prerequisites()
    
    print("\n👋 Merci d'avoir utilisé ML Trading Bot Launcher!")

if __name__ == "__main__":
    main()
