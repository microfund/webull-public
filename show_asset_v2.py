#!/usr/bin/env python3
"""
Webull Japan API - 資産表示スクリプト
口座残高、ポジション情報、資産サマリーを表示します
"""

import os
from pathlib import Path
from decimal import Decimal
from webullsdkcore.client import ApiClient
from webullsdktrade.api import API
from webullsdkcore.common.region import Region


def format_amount(value):
    """
    金額を整形する関数
    科学的記数法（0E-10など）を0に変換
    """
    if value is None:
        return "0"
    
    try:
        # 文字列の場合
        if isinstance(value, str):
            # 科学的記数法または非常に小さい値を0として扱う
            decimal_value = Decimal(value)
            if abs(decimal_value) < Decimal('0.01'):
                return "0" if 'JPY' in str(value) or not '.' in value else "0.00"
            return value
        
        # 数値の場合
        if isinstance(value, (int, float)):
            if abs(value) < 0.01:
                return "0" if isinstance(value, int) else "0.00"
            return f"{value:,.2f}" if isinstance(value, float) else str(value)
        
        return str(value)
    except:
        return str(value)


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
                    
                    # 口座ID
                    if 'account_id' in balance_data:
                        print(f"口座ID: {balance_data['account_id']}")
                    
                    # 通貨別の資産情報
                    if 'account_currency_assets' in balance_data:
                        for currency_asset in balance_data['account_currency_assets']:
                            currency = currency_asset.get('currency', 'N/A')
                            print(f"\n💱 {currency} 建て:")
                            print(f"  総現金: {format_amount(currency_asset.get('total_cash', '0'))}")
                            print(f"  確定現金: {format_amount(currency_asset.get('settled_cash', '0'))}")
                            print(f"  未確定現金: {format_amount(currency_asset.get('unsettled_cash', '0'))}")
                            print(f"  凍結資金: {format_amount(currency_asset.get('frozen_cash', '0'))}")
                            print(f"  出金可能額: {format_amount(currency_asset.get('available_to_withdraw', '0'))}")
                            print(f"  買付余力: {format_amount(currency_asset.get('stock_power', '0'))}")
                    
                    # その他の情報があれば表示
                    for key, value in balance_data.items():
                        if key not in ['account_id', 'account_currency_assets']:
                            print(f"{key}: {value}")
                else:
                    print(f"⚠️  残高情報の取得に失敗しました (ステータスコード: {balance_response.status_code})")
                    print(f"レスポンス: {balance_response.text}")
            
            except Exception as e:
                print(f"⚠️  残高取得中にエラーが発生しました: {str(e)}")
            
            # 3. ポジション情報の取得（保有銘柄）
            print(f"\n📈 保有ポジションを取得中...")
            try:
                positions_response = api.account.get_account_position(account_id)
                
                if positions_response.status_code == 200:
                    positions_data = positions_response.json()
                    
                    # レスポンスがリストの場合とオブジェクトの場合に対応
                    positions = []
                    if isinstance(positions_data, list):
                        positions = positions_data
                    elif isinstance(positions_data, dict):
                        # データが 'positions' キーに入っている場合
                        if 'positions' in positions_data:
                            positions = positions_data['positions']
                        # または 'data' キーに入っている場合
                        elif 'data' in positions_data:
                            positions = positions_data['data']
                        else:
                            # オブジェクト全体が1つのポジションの場合
                            positions = [positions_data]
                    
                    # 実際にポジションがあるかチェック（数量が0より大きいもの）
                    valid_positions = []
                    for pos in positions:
                        quantity = pos.get('position', pos.get('quantity', 0))
                        try:
                            quantity_float = float(quantity) if quantity else 0
                            if quantity_float > 0:
                                valid_positions.append(pos)
                        except (ValueError, TypeError):
                            # 数量が取得できない場合もリストに含める
                            valid_positions.append(pos)
                    
                    if valid_positions and len(valid_positions) > 0:
                        print(f"\n🎯 保有銘柄 ({len(valid_positions)}件):")
                        print("-" * 40)
                        
                        for pos in valid_positions:
                            # ticker情報の取得
                            ticker_info = pos.get('ticker', {})
                            symbol = ticker_info.get('symbol', pos.get('symbol', 'N/A'))
                            
                            # 数量と価格情報
                            quantity = pos.get('position', pos.get('quantity', 0))
                            market_value = pos.get('marketValue', pos.get('market_value', 0))
                            cost_price = pos.get('costPrice', pos.get('cost_price', pos.get('cost', 0)))
                            last_price = pos.get('lastPrice', pos.get('last_price', 0))
                            
                            # 損益情報
                            unrealized_pl = pos.get('unrealizedProfitLoss', pos.get('unrealized_profit_loss', None))
                            unrealized_pl_rate = pos.get('unrealizedProfitLossRate', pos.get('unrealized_profit_loss_rate', None))
                            
                            print(f"\nシンボル: {symbol}")
                            
                            # 銘柄名があれば表示
                            if 'name' in ticker_info:
                                print(f"  銘柄名: {ticker_info['name']}")
                            
                            print(f"  数量: {quantity}")
                            
                            # 価格情報
                            try:
                                cost_price_float = float(cost_price) if cost_price else 0
                                last_price_float = float(last_price) if last_price else 0
                                market_value_float = float(market_value) if market_value else 0
                                quantity_float = float(quantity) if quantity else 0
                                
                                if last_price_float > 0:
                                    print(f"  現在価格: ${last_price_float:,.2f}")
                                if cost_price_float > 0:
                                    print(f"  取得単価: ${cost_price_float:,.2f}")
                                if market_value_float > 0:
                                    print(f"  評価額: ${market_value_float:,.2f}")
                                
                                # 損益計算
                                if unrealized_pl is not None and unrealized_pl_rate is not None:
                                    pl_float = float(unrealized_pl)
                                    pl_rate_float = float(unrealized_pl_rate) * 100
                                    print(f"  損益: ${pl_float:,.2f} ({pl_rate_float:+.2f}%)")
                                elif cost_price_float > 0 and last_price_float > 0 and quantity_float > 0:
                                    profit_loss = (last_price_float - cost_price_float) * quantity_float
                                    profit_loss_pct = ((last_price_float - cost_price_float) / cost_price_float * 100)
                                    print(f"  損益: ${profit_loss:,.2f} ({profit_loss_pct:+.2f}%)")
                            except (ValueError, TypeError) as e:
                                # 数値変換エラーの場合は生の値を表示
                                if cost_price:
                                    print(f"  取得単価: {cost_price}")
                                if last_price:
                                    print(f"  現在価格: {last_price}")
                                if market_value:
                                    print(f"  評価額: {market_value}")
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
