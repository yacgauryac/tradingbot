# auto_fix_eventloop.py - Fix automatique et définitif

def fix_event_loop_in_connector():
    """Fix automatique du problème event loop"""
    
    try:
        # Lecture du fichier actuel
        with open("ib_connector.py", "r", encoding='utf-8') as f:
            content = f.read()
        
        # Sauvegarde de sécurité
        with open("ib_connector_backup.py", "w", encoding='utf-8') as f:
            f.write(content)
        print("💾 Sauvegarde: ib_connector_backup.py")
        
        # Fix simple : enlever les conflits asyncio
        # Remplacement de la méthode problématique
        new_method = '''    async def get_historical_data(self, symbol: str, duration: str = '30 D', 
                                bar_size: str = '1 day') -> Optional[pd.DataFrame]:
        """Récupère les données historiques - VERSION CORRIGÉE"""
        contract = self.create_contract(symbol)
        if not contract:
            return None
        
        try:
            logger.debug(f"📡 Récupération données {symbol}...")
            
            # Utilisation synchrone pour éviter l'event loop conflict
            bars = self.ib.reqHistoricalData(
                contract=contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )
            
            if not bars:
                logger.warning(f"⚠️ Aucune donnée pour {symbol}")
                return None
            
            # Conversion en DataFrame
            df = util.df(bars)
            if len(df) == 0:
                logger.warning(f"⚠️ DataFrame vide pour {symbol}")
                return None
                
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            df.set_index('date', inplace=True)
            df.index = pd.to_datetime(df.index)
            
            logger.info(f"📊 Données {symbol}: {len(df)} barres récupérées !")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur données {symbol}: {e}")
            return None'''
        
        # Fix également get_current_price si elle existe
        price_method = '''    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Récupère le prix actuel - VERSION CORRIGÉE"""
        contract = self.create_contract(symbol)
        if not contract:
            return None
        
        try:
            ticker = self.ib.reqMktData(contract, '', False, False)
            # Attente synchrone simple
            import time
            time.sleep(2)
            
            price = None
            if ticker.last and ticker.last > 0:
                price = ticker.last
            elif ticker.close and ticker.close > 0:
                price = ticker.close
            elif ticker.bid and ticker.ask and ticker.bid > 0 and ticker.ask > 0:
                price = (ticker.bid + ticker.ask) / 2
            
            self.ib.cancelMktData(contract)
            
            if price:
                logger.debug(f"💱 Prix {symbol}: {price:.4f}")
                return price
            else:
                logger.warning(f"⚠️ Pas de prix pour {symbol}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Erreur prix {symbol}: {e}")
            return None'''
        
        # Recherche et remplacement
        import re
        
        # Pattern pour get_historical_data
        pattern1 = r'async def get_historical_data.*?return None'
        if re.search(pattern1, content, re.DOTALL):
            content = re.sub(pattern1, new_method.strip(), content, flags=re.DOTALL)
            print("✅ get_historical_data corrigée")
        
        # Pattern pour get_current_price
        pattern2 = r'async def get_current_price.*?return None'
        if re.search(pattern2, content, re.DOTALL):
            content = re.sub(pattern2, price_method.strip(), content, flags=re.DOTALL)
            print("✅ get_current_price corrigée")
        
        # Fix update_account_info aussi
        account_fix = '''    async def update_account_info(self):
        """Met à jour les informations du compte - VERSION SIMPLE"""
        try:
            account_summary = self.ib.accountSummary()
            self.account_info = {}
            
            for item in account_summary:
                try:
                    value = float(item.value) if item.value.replace('.', '').replace('-', '').isdigit() else item.value
                except:
                    value = item.value
                
                self.account_info[item.tag] = {
                    'value': value,
                    'currency': item.currency
                }
            
            net_liquidation = self.account_info.get('NetLiquidation', {}).get('value', 0)
            currency = self.account_info.get('NetLiquidation', {}).get('currency', 'USD')
            
            logger.info(f"💰 Valeur compte: {net_liquidation:,.2f} {currency}")
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération compte: {e}")'''
        
        pattern3 = r'async def update_account_info.*?logger\.error\(f"❌ Erreur récupération compte: {e}"\)'
        if re.search(pattern3, content, re.DOTALL):
            content = re.sub(pattern3, account_fix.strip(), content, flags=re.DOTALL)
            print("✅ update_account_info corrigée")
        
        # Sauvegarde du fichier corrigé
        with open("ib_connector.py", "w", encoding='utf-8') as f:
            f.write(content)
        
        print("✅ ib_connector.py corrigé pour event loop!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur fix automatique: {e}")
        return False

def main():
    print("🔧 FIX AUTOMATIQUE EVENT LOOP")
    print("=" * 35)
    
    success = fix_event_loop_in_connector()
    
    if success:
        print("\n🎉 FIX TERMINÉ!")
        print("🚀 RELANCE TON BOT:")
        print("   python trading_bot.py")
        print("\n✅ TU DOIS VOIR:")
        print("   📊 Données AAPL: XX barres récupérées !")
        print("   📊 Données MSFT: XX barres récupérées !")
        print("   PLUS d'erreur 'This event loop is already running'")
        
    else:
        print("\n❌ FIX ÉCHOUÉ")
        print("💡 Solution manuelle:")
        print("   Modifie ib_connector.py selon les instructions")

if __name__ == "__main__":
    main()