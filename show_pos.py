#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webull Japan OpenAPI - ポジション表示スクリプト
現在保有している銘柄のポジション情報を取得して表示します。
"""

import os
import sys
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
from webullsdktrade.api import API
from webullsdkcore.client import ApiClient
from webullsdkcore.common.region import Region


class MarkdownLogger:
    """標準出力とMarkdownファイルの両方に出力するためのクラス"""
    
    def __init__(self, filename):
        self.filename = filename
        self.terminal = sys.stdout
        # ファイルを初期化(既存の内容をクリア)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('')
    
    def write(self, message):
        """標準出力とファイルの両方に書き込む"""
        self.terminal.write(message)
        with open(self.filename, 'a', encoding='utf-8') as f:
            f.write(message)
    
    def flush(self):
        """バッファをフラッシュ"""
        self.terminal.flush()


def format_currency(value, currency="JPY"):
    """
    通貨フォーマット関数
    JPYの場合は整数表示、それ以外は小数点以下2桁まで表示
    """
    try:
        # Decimal型に変換
        if isinstance(value, str):
            # 科学的記数法(0E-10など)をチェック
            if 'E' in value.upper():
                decimal_value = Decimal(value)
                if decimal_value == 0:
                    value = "0"
                else:
                    value = str(decimal_value)
            decimal_value = Decimal(value)
        else:
            decimal_value = Decimal(str(value))
        
        # JPYの場合は整数表示
        if currency == "JPY":
            return f"{int(decimal_value):,}"
        else:
            # その他の通貨は小数点以下2桁
            return f"{float(decimal_value):,.2f}"
    except Exception as e:
        return str(value)


def get_account_id(api):
    """
    アカウントIDを取得
    
    Returns:
        str: アカウントID
    """
    try:
        response = api.account.get_app_subscriptions()
        
        if response.status_code == 200:
            result = response.json()
            if result and len(result) > 0:
                account_id = result[0].get('account_id')
                return account_id
            else:
                print("エラー: アカウント情報が取得できませんでした")
                return None
        else:
            print(f"エラー: APIリクエストが失敗しました (ステータスコード: {response.status_code})")
            if hasattr(response, 'text'):
                print(f"レスポンス: {response.text}")
            return None
            
    except Exception as e:
        print(f"エラー: アカウントIDの取得中に例外が発生しました - {str(e)}")
        return None


def get_positions(api, account_id):
    """
    ポジション情報を取得
    
    Args:
        api: Webull API instance
        account_id: アカウントID
        
    Returns:
        list: ポジション情報のリスト
    """
    try:
        all_positions = []
        last_instrument_id = None
        page_size = 100  # 最大ページサイズ
        
        while True:
            # ページネーションを使用してポジション情報を取得
            if last_instrument_id:
                response = api.account.get_account_position(
                    account_id=account_id,
                    page_size=page_size,
                    last_instrument_id=last_instrument_id
                )
            else:
                response = api.account.get_account_position(
                    account_id=account_id,
                    page_size=page_size
                )
            
            if response.status_code == 200:
                data = response.json()
                holdings = data.get('holdings', [])
                
                # 数量が0でないポジションのみを追加
                for holding in holdings:
                    qty = holding.get('qty', '0')
                    try:
                        qty_decimal = Decimal(qty)
                        if qty_decimal > 0:
                            all_positions.append(holding)
                    except:
                        # 変換できない場合はスキップ
                        continue
                
                # 次のページがあるかチェック
                has_next = data.get('has_next', False)
                if has_next and holdings:
                    # 最後のinstrument_idを取得
                    last_instrument_id = holdings[-1].get('instrument_id')
                else:
                    # 次のページがない、または保有がない場合は終了
                    break
            else:
                print(f"エラー: ポジション情報の取得に失敗しました (ステータスコード: {response.status_code})")
                if hasattr(response, 'text'):
                    print(f"レスポンス: {response.text}")
                break
        
        return all_positions
        
    except Exception as e:
        print(f"エラー: ポジション情報の取得中に例外が発生しました - {str(e)}")
        return []


def display_positions(positions):
    """
    ポジション情報を整形して表示
    
    Args:
        positions: ポジション情報のリスト
    """
    if not positions:
        print("\n現在保有しているポジションはありません。")
        return
    
    print("\n" + "=" * 100)
    print("現在のポジション一覧")
    print("=" * 100)
    
    # テーブルヘッダー
    print(f"\n{'No.':<4} {'Symbol':<8} {'銘柄名':<30} {'数量':<10} {'平均取得価格':<15} {'現在価格':<15}")
    print("-" * 100)
    
    total_positions = len(positions)
    
    for idx, position in enumerate(positions, 1):
        symbol = position.get('symbol', 'N/A')
        instrument_name = position.get('instrument_name', 'N/A')
        qty = position.get('qty', '0')
        avg_price = position.get('cost_price', '0')
        last_price = position.get('last_price', '0')
        currency = position.get('currency', 'USD')
        
        # 数量のフォーマット
        try:
            qty_decimal = Decimal(qty)
            qty_str = f"{float(qty_decimal):,.4f}".rstrip('0').rstrip('.')
        except:
            qty_str = qty
        
        # 価格のフォーマット
        avg_price_str = format_currency(avg_price, currency)
        last_price_str = format_currency(last_price, currency)
        
        # 銘柄名が長すぎる場合は切り詰め
        if len(instrument_name) > 28:
            instrument_name = instrument_name[:27] + "..."
        
        print(f"{idx:<4} {symbol:<8} {instrument_name:<30} {qty_str:<10} {avg_price_str:<15} {last_price_str:<15}")
    
    print("-" * 100)
    print(f"\n合計ポジション数: {total_positions}")
    print("=" * 100 + "\n")
    
    # 詳細情報の表示
    print("\n詳細情報:")
    print("=" * 100)
    
    for idx, position in enumerate(positions, 1):
        print(f"\n--- ポジション {idx} ---")
        print(f"Symbol: {position.get('symbol', 'N/A')}")
        print(f"銘柄名: {position.get('instrument_name', 'N/A')}")
        print(f"Instrument ID: {position.get('instrument_id', 'N/A')}")
        print(f"Instrument Type: {position.get('instrument_type', 'N/A')}")
        
        currency = position.get('currency', 'USD')
        qty = position.get('qty', '0')
        cost_price = position.get('cost_price', '0')
        last_price = position.get('last_price', '0')
        
        # 数量
        try:
            qty_decimal = Decimal(qty)
            print(f"保有数量: {float(qty_decimal):,.4f}".rstrip('0').rstrip('.'))
        except:
            print(f"保有数量: {qty}")
        
        # 平均取得価格
        print(f"平均取得価格: {format_currency(cost_price, currency)} {currency}")
        
        # 現在価格
        print(f"現在価格: {format_currency(last_price, currency)} {currency}")
        
        # 評価額の計算
        try:
            qty_decimal = Decimal(qty)
            last_price_decimal = Decimal(last_price)
            market_value = qty_decimal * last_price_decimal
            print(f"評価額: {format_currency(str(market_value), currency)} {currency}")
            
            # 損益の計算
            cost_price_decimal = Decimal(cost_price)
            profit_loss = (last_price_decimal - cost_price_decimal) * qty_decimal
            profit_loss_pct = ((last_price_decimal - cost_price_decimal) / cost_price_decimal * 100) if cost_price_decimal != 0 else 0
            
            profit_loss_str = format_currency(str(profit_loss), currency)
            if profit_loss >= 0:
                print(f"評価損益: +{profit_loss_str} {currency} (+{float(profit_loss_pct):.2f}%)")
            else:
                print(f"評価損益: {profit_loss_str} {currency} ({float(profit_loss_pct):.2f}%)")
        except Exception as e:
            print(f"評価額・損益: 計算エラー ({str(e)})")
        
        # その他の情報
        if 'market_value' in position:
            print(f"市場評価額: {format_currency(position['market_value'], currency)} {currency}")
        if 'unrealized_profit_loss' in position:
            print(f"未実現損益: {format_currency(position['unrealized_profit_loss'], currency)} {currency}")
        if 'realized_profit_loss' in position:
            print(f"実現損益: {format_currency(position['realized_profit_loss'], currency)} {currency}")
        
        print("-" * 100)


def main():
    """メイン処理"""
    # .envファイルから環境変数を読み込む
    load_dotenv()
    
    # APIキーとシークレットを取得
    app_key = os.getenv('WEBULL_APP_KEY')
    app_secret = os.getenv('WEBULL_APP_SECRET')
    
    # 認証情報のチェック
    if not app_key or not app_secret:
        print("エラー: WEBULL_APP_KEYまたはWEBULL_APP_SECRETが.envファイルに設定されていません。")
        print(".envファイルを確認してください。")
        return
    
    # Markdownファイルへの出力設定
    # スクリプトファイルのディレクトリを取得
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # スクリプトと同じディレクトリにmdファイルを出力
    md_filename = os.path.join(script_dir, f"{script_name}.md")
    sys.stdout = MarkdownLogger(md_filename)
    
    try:
        print(f"# Webull ポジション表示レポート")
        print(f"\n実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "=" * 100)
        print("Webull Japan OpenAPI - ポジション情報取得")
        print("=" * 100)
        
        # APIクライアントの初期化(日本リージョン)
        print("\nAPIクライアントを初期化しています...")
        api_client = ApiClient(app_key, app_secret, Region.JP.value)
        api = API(api_client)
        print("✓ APIクライアントの初期化が完了しました")
        
        # アカウントIDの取得
        print("\nアカウント情報を取得しています...")
        account_id = get_account_id(api)
        
        if not account_id:
            print("エラー: アカウントIDが取得できませんでした。")
            return
        
        print(f"✓ アカウントIDを取得しました")
        
        # ポジション情報の取得
        print("\nポジション情報を取得しています...")
        positions = get_positions(api, account_id)
        print(f"✓ ポジション情報の取得が完了しました({len(positions)}件)")
        
        # ポジション情報の表示
        display_positions(positions)
        
        print("\n処理が正常に完了しました。")
        print(f"\n出力ファイル: {md_filename}")
        
    except Exception as e:
        print(f"\nエラー: 予期しない例外が発生しました - {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 標準出力を元に戻す
        sys.stdout = sys.__stdout__


if __name__ == "__main__":
    main()