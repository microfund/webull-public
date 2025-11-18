#!/usr/bin/env python3
"""
Webull Japan API - 資産表示スクリプト
口座残高、ポジション情報、資産サマリーを表示します
"""

import os
from pathlib import Path
from webullsdkcore.client import ApiClient
from webullsdktrade.api import API
from webullsdkcore.common.region import Region


def load_env_file():
    """
    .envファイルから環境変数を読み込む
    スクリプトと同じディレクトリの.envファイルを探す
    """
    # スクリプトのディレクトリを取得
    script_dir = Path(__file__).parent.resolve()
    env_file = script_dir / '.env'
    
    if env_file.exists():
        print(f"📄 .envファイルを読み込んでいます: {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # コメント行と空行をスキップ
                if line and not line.startswith('#'):
                    # KEY=VALUE形式をパース
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # 引用符を除去
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        # 環境変数に設定（既存の環境変数は上書きしない）
                        if key and value and not os.getenv(key):
                            os.environ[key] = value
        print("✅ .envファイルの読み込みが完了しました\n")
    else:
        print(f"⚠️  .envファイルが見つかりません: {env_file}")
        print("環境変数または直接設定を使用します\n")


def display_asset_info(app_key: str, app_secret: str):
    """
    Webull口座の資産情報を取得して表示する
    
    Args:
        app_key: WebullアプリケーションキーClaude
        app_secret: Webullアプリケーションシークレット
    """
    
    # APIクライアントの初期化（日本リージョン）
    api_client = ApiClient(app_key, app_secret, Region.JP.value)
    api = API(api_client)
    
    print("=" * 60)
    print("Webull Japan - 資産情報表示")
    print("=" * 60)
    print()
    
    try:
        # 1. 口座サブスクリプション情報の取得
        print("📋 口座情報を取得中...")
        response = api.account.get_app_subscriptions()
        
        if response.status_code != 200:
            print(f"❌ エラー: 口座情報の取得に失敗しました (ステータスコード: {response.status_code})")
            print(f"レスポンス: {response.text}")
            return
        
        subscriptions = response.json()
        
        if not subscriptions:
            print("❌ エラー: 有効な口座が見つかりませんでした")
            return
        
        print(f"✅ {len(subscriptions)}件の口座が見つかりました\n")
        
        # 各口座の情報を表示
        for idx, account in enumerate(subscriptions, 1):
            account_id = account.get('account_id')
            print(f"\n{'=' * 60}")
            print(f"口座 #{idx}")
            print(f"{'=' * 60}")
            print(f"口座ID: {account_id}")
            
            # その他の口座情報があれば表示
            for key, value in account.items():
                if key != 'account_id':
                    print(f"{key}: {value}")
            
            # 2. 口座残高の取得
            print(f"\n💰 口座残高を取得中...")
            try:
                # 通貨は'USD'または'JPY'を指定可能
                balance_response = api.account.get_account_balance(account_id, 'USD')
                
                if balance_response.status_code == 200:
                    balance_data = balance_response.json()
                    print("\n📊 残高情報:")
                    print("-" * 40)
                    
                    # 総資産
                    if 'total_asset' in balance_data:
                        print(f"総資産: ${balance_data['total_asset']:,.2f}")
                    
                    # キャッシュバランス
                    if 'cash_balance' in balance_data:
                        print(f"現金残高: ${balance_data['cash_balance']:,.2f}")
                    
                    # 買付可能額
                    if 'buying_power' in balance_data:
                        print(f"買付余力: ${balance_data['buying_power']:,.2f}")
                    
                    # その他の残高情報
                    for key, value in balance_data.items():
                        if key not in ['total_asset', 'cash_balance', 'buying_power']:
                            if isinstance(value, (int, float)):
                                print(f"{key}: ${value:,.2f}")
                            else:
                                print(f"{key}: {value}")
                else:
                    print(f"⚠️  残高情報の取得に失敗しました (ステータスコード: {balance_response.status_code})")
                    print(f"レスポンス: {balance_response.text}")
            
            except Exception as e:
                print(f"⚠️  残高取得中にエラーが発生しました: {str(e)}")
            
            # 3. ポジション情報の取得（保有銘柄）
            print(f"\n📈 保有ポジションを取得中...")
            try:
                positions_response = api.account.get_account_positions(account_id)
                
                if positions_response.status_code == 200:
                    positions = positions_response.json()
                    
                    if positions and len(positions) > 0:
                        print(f"\n🎯 保有銘柄 ({len(positions)}件):")
                        print("-" * 40)
                        
                        for pos in positions:
                            symbol = pos.get('symbol', 'N/A')
                            quantity = pos.get('quantity', 0)
                            market_value = pos.get('market_value', 0)
                            cost_price = pos.get('cost', 0)
                            current_price = pos.get('last_price', 0)
                            
                            # 損益計算
                            if cost_price and current_price and quantity:
                                profit_loss = (current_price - cost_price) * quantity
                                profit_loss_pct = ((current_price - cost_price) / cost_price * 100) if cost_price > 0 else 0
                                
                                print(f"\nシンボル: {symbol}")
                                print(f"  数量: {quantity}")
                                print(f"  現在価格: ${current_price:,.2f}")
                                print(f"  取得単価: ${cost_price:,.2f}")
                                print(f"  評価額: ${market_value:,.2f}")
                                print(f"  損益: ${profit_loss:,.2f} ({profit_loss_pct:+.2f}%)")
                            else:
                                print(f"\nシンボル: {symbol}")
                                print(f"  数量: {quantity}")
                                print(f"  評価額: ${market_value:,.2f}")
                    else:
                        print("📭 保有ポジションはありません")
                else:
                    print(f"⚠️  ポジション情報の取得に失敗しました (ステータスコード: {positions_response.status_code})")
            
            except Exception as e:
                print(f"⚠️  ポジション取得中にエラーが発生しました: {str(e)}")
        
        print(f"\n{'=' * 60}")
        print("✅ 資産情報の取得が完了しました")
        print(f"{'=' * 60}\n")
    
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """メイン関数"""
    
    # .envファイルから環境変数を読み込む
    load_env_file()
    
    # 環境変数から取得
    app_key = os.getenv('WEBULL_APP_KEY')
    app_secret = os.getenv('WEBULL_APP_SECRET')
    
    # APIキーの確認
    if not app_key or not app_secret:
        print("❌ エラー: APIキーとシークレットが設定されていません\n")
        print("設定方法:")
        print("\n1. .envファイルを使用（推奨）:")
        print("   スクリプトと同じディレクトリに.envファイルを作成し、以下の内容を記載:")
        print("   ---")
        print("   WEBULL_APP_KEY=your_actual_key")
        print("   WEBULL_APP_SECRET=your_actual_secret")
        print("   ---")
        print("\n2. 環境変数を使用:")
        print("   export WEBULL_APP_KEY='your_actual_key'")
        print("   export WEBULL_APP_SECRET='your_actual_secret'")
        print("\nAPIキーの取得方法:")
        print("https://www.webull.co.jp/center でOpenAPIを申請してください")
        return
    
    print(f"🔑 APIキーを確認しました")
    print(f"   App Key: {app_key[:8]}...{app_key[-4:] if len(app_key) > 12 else ''}")
    print()
    
    # 資産情報の表示
    display_asset_info(app_key, app_secret)


if __name__ == '__main__':
    main()