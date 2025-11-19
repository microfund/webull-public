#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
Webull Japan API - 資産表示スクリプト（Markdown出力版）
================================================================================

このスクリプトは、Webull Japan OpenAPIを使用して以下の情報を取得し、
標準出力とMarkdownファイルの両方に出力します：

主な機能：
    1. 口座サブスクリプション情報の取得
    2. 口座残高の詳細表示（通貨別）
    3. 保有ポジション（銘柄）の一覧表示
    4. 損益計算と表示
    5. 実行結果をMarkdown形式でファイル出力

必要な環境：
    - Python 3.9以上
    - webull-python-sdk-core パッケージ
    - webull-python-sdk-trade パッケージ
    - Webull Japan OpenAPI の App Key と App Secret

認証情報の設定方法：
    スクリプトと同じディレクトリに .env ファイルを作成し、以下を記載：
    
    WEBULL_APP_KEY=your_app_key_here
    WEBULL_APP_SECRET=your_app_secret_here

実行方法：
    python webull_asset_display.py

出力ファイル：
    webull_asset_display.md（スクリプトと同じディレクトリに生成）

作成日: 2025-11-19
バージョン: 2.0
================================================================================
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from webullsdkcore.client import ApiClient
from webullsdktrade.api import API
from webullsdkcore.common.region import Region


class MarkdownLogger:
    """
    標準出力とMarkdownファイルに同時出力するためのクラス
    
    このクラスは、sys.stdoutを置き換えることで、print文の出力を
    ターミナルとファイルの両方に同時に書き込みます。
    
    Attributes:
        terminal (TextIO): 元の標準出力（ターミナル）への参照
        log_file (TextIO): Markdownファイルへのファイルハンドル
    
    使用例:
        logger = MarkdownLogger('output.md')
        sys.stdout = logger
        print("This goes to both terminal and file")
        sys.stdout = logger.terminal  # 元に戻す
        logger.close()
    """
    
    def __init__(self, filename):
        """
        MarkdownLoggerを初期化
        
        Args:
            filename (str or Path): 出力先のMarkdownファイルパス
        """
        self.terminal = sys.stdout
        self.log_file = open(filename, 'w', encoding='utf-8')
        
    def write(self, message):
        """
        メッセージを標準出力とファイルの両方に書き込む
        
        Args:
            message (str): 書き込むメッセージ
        """
        self.terminal.write(message)
        self.log_file.write(message)
        
    def flush(self):
        """
        バッファをフラッシュして、保留中のデータを書き込む
        """
        self.terminal.flush()
        self.log_file.flush()
        
    def close(self):
        """
        ファイルハンドルを閉じる
        
        Note:
            このメソッドを呼び出す前に、sys.stdoutを元に戻すことを推奨
        """
        self.log_file.close()


def format_amount(value, currency='USD'):
    """
    金額を人間が読みやすい形式に整形する関数
    
    この関数は、APIから返される金額データを整形します。
    特に科学的記数法（例：0E-10）や非常に小さい値を適切に処理します。
    
    処理の流れ：
        1. None値は "0" として返す
        2. 文字列の場合：
           - Decimalに変換して絶対値が0.01未満なら "0" または "0.00"
           - それ以外はそのまま返す
        3. 数値（int/float）の場合：
           - 絶対値が0.01未満なら "0" または "0.00"
           - floatの場合はカンマ区切り+小数点2桁でフォーマット（JPYの場合は小数点なし）
           - intの場合は文字列に変換
        4. その他の型：文字列に変換
    
    Args:
        value (str | int | float | None): 整形する金額データ
        currency (str): 通貨コード（'USD', 'JPY' など）デフォルトは'USD'
    
    Returns:
        str: 整形された金額文字列
    
    Examples:
        >>> format_amount("0E-10")
        "0.00"
        >>> format_amount(1234.56, 'USD')
        "1,234.56"
        >>> format_amount(1234.56, 'JPY')
        "1,235"
        >>> format_amount(None)
        "0"
        >>> format_amount(0.001)
        "0.00"
    """
    # None値の処理
    if value is None:
        return "0"
    
    try:
        # 文字列の場合の処理
        if isinstance(value, str):
            # 科学的記数法または非常に小さい値を0として扱う
            # Decimalを使用することで高精度な数値比較が可能
            decimal_value = Decimal(value)
            
            # 0.01未満の値は実質的に0として扱う
            if abs(decimal_value) < Decimal('0.01'):
                # JPY（日本円）の場合は小数点なし
                return "0" if currency == 'JPY' or 'JPY' in str(value) or not '.' in value else "0.00"
            
            # 0.01以上の値の場合
            # JPYの場合は小数点なしで返す
            if currency == 'JPY' or 'JPY' in str(value):
                return str(int(float(value)))
            
            # それ以外はそのまま返す
            return value
        
        # 数値（int または float）の場合の処理
        if isinstance(value, (int, float)):
            # 0.01未満の値は実質的に0として扱う
            if abs(value) < 0.01:
                # JPYの場合は小数点なし、それ以外は小数点付き
                return "0" if currency == 'JPY' or isinstance(value, int) else "0.00"
            
            # JPY（日本円）の場合は小数点なしでフォーマット
            if currency == 'JPY':
                return f"{int(value):,}"
            
            # floatの場合はカンマ区切り+小数点2桁でフォーマット
            # intの場合は文字列に変換
            return f"{value:,.2f}" if isinstance(value, float) else str(value)
        
        # その他の型の場合は文字列に変換
        return str(value)
    
    except Exception:
        # エラーが発生した場合は安全に文字列化
        return str(value)


def load_env_file():
    """
    .envファイルから環境変数を読み込む関数
    
    この関数は、スクリプトと同じディレクトリにある .env ファイルを
    探し、その中に記載されている環境変数を os.environ に設定します。
    
    .env ファイルの形式：
        # コメント行
        WEBULL_APP_KEY=your_app_key
        WEBULL_APP_SECRET="your_app_secret"
        
    処理の流れ：
        1. スクリプトのディレクトリパスを取得
        2. .env ファイルの存在を確認
        3. ファイルが存在する場合：
           - 各行を読み込み
           - コメント行（#で始まる）と空行をスキップ
           - KEY=VALUE 形式をパースして環境変数に設定
           - 引用符（"または'）があれば除去
           - 既存の環境変数は上書きしない
        4. ファイルが存在しない場合：
           - 警告メッセージを表示
    
    Note:
        既に環境変数が設定されている場合、.envファイルの値で
        上書きしません。これにより、システム環境変数が優先されます。
    
    Returns:
        None
    
    Raises:
        なし（エラーが発生しても処理を継続）
    """
    # スクリプトのディレクトリを取得
    # __file__ は現在実行中のスクリプトのパス
    # .parent で親ディレクトリを取得
    # .resolve() で絶対パスに変換
    script_dir = Path(__file__).parent.resolve()
    env_file = script_dir / '.env'
    
    # .envファイルの存在確認
    if env_file.exists():
        # UTF-8エンコーディングでファイルを開く（メッセージは出力しない）
        with open(env_file, 'r', encoding='utf-8') as f:
            # ファイルの各行を処理
            for line in f:
                # 前後の空白を除去
                line = line.strip()
                
                # コメント行（#で始まる）と空行をスキップ
                if line and not line.startswith('#'):
                    # KEY=VALUE形式をパース
                    if '=' in line:
                        # 最初の = で分割（値に = が含まれる可能性を考慮）
                        key, value = line.split('=', 1)
                        
                        # キーと値の前後の空白を除去
                        key = key.strip()
                        value = value.strip()
                        
                        # 引用符の除去処理
                        # ダブルクォート（"）で囲まれている場合
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        # シングルクォート（'）で囲まれている場合
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # 環境変数に設定（既存の環境変数は上書きしない）
                        # キーと値が空でなく、かつ既存の環境変数が設定されていない場合のみ
                        if key and value and not os.getenv(key):
                            os.environ[key] = value


def display_asset_info(app_key: str, app_secret: str):
    """
    Webull口座の資産情報を取得して表示する関数
    
    この関数は、Webull Japan OpenAPIを使用して以下の情報を取得します：
        1. 口座サブスクリプション情報（利用可能な口座のリスト）
        2. 各口座の残高情報（通貨別）
        3. 各口座の保有ポジション（銘柄情報と損益）
    
    取得した情報は、Markdown形式で整形されて標準出力に表示されます。
    
    Args:
        app_key (str): Webull OpenAPI アプリケーションキー
                      https://www.webull.co.jp/center で取得可能
        app_secret (str): Webull OpenAPI アプリケーションシークレット
                         https://www.webull.co.jp/center で取得可能
    
    Returns:
        None
    
    Raises:
        Exception: API呼び出しやデータ処理中にエラーが発生した場合
    
    API エンドポイント使用：
        - api.account.get_app_subscriptions(): 口座一覧取得
        - api.account.get_account_balance(): 残高情報取得
        - api.account.get_account_position(): ポジション情報取得
    """
    
    # ========================================
    # APIクライアントの初期化
    # ========================================
    # Region.JP.value を指定して日本リージョンのAPIに接続
    api_client = ApiClient(app_key, app_secret, Region.JP.value)
    api = API(api_client)
    
    # ========================================
    # ヘッダー表示
    # ========================================
    print("=" * 60)
    print("Webull Japan - 資産情報表示")
    print("=" * 60)
    print()
    
    try:
        # ========================================
        # 1. 口座サブスクリプション情報の取得
        # ========================================
        # このAPIは、ユーザーが利用可能な口座のリストを返します
        print("📋 口座情報を取得中...")
        response = api.account.get_app_subscriptions()
        
        # HTTPステータスコードの確認
        # 200以外の場合はエラー
        if response.status_code != 200:
            print(f"❌ エラー: 口座情報の取得に失敗しました (ステータスコード: {response.status_code})")
            print(f"レスポンス: {response.text}")
            return
        
        # JSON形式でレスポンスをパース
        subscriptions = response.json()
        
        # 口座が存在しない場合のエラーハンドリング
        if not subscriptions:
            print("❌ エラー: 有効な口座が見つかりませんでした")
            return
        
        # 取得した口座数を表示
        print(f"✅ {len(subscriptions)}件の口座が見つかりました\n")
        
        # ========================================
        # 各口座の詳細情報を取得・表示
        # ========================================
        # enumerate()を使用して、口座番号とデータを同時に取得
        # 1から番号を開始（ユーザー向けの表示のため）
        for idx, account in enumerate(subscriptions, 1):
            # 口座IDの取得
            account_id = account.get('account_id')
            
            # ========================================
            # 口座の基本情報を表示
            # ========================================
            print(f"\n{'=' * 60}")
            print(f"## 口座 #{idx}")
            print(f"{'=' * 60}")
            print(f"**口座ID**: {account_id}\n")
            
            # 口座ID以外のその他の情報がある場合は表示
            if len(account) > 1:
                print("### その他の口座情報")
                for key, value in account.items():
                    if key != 'account_id':
                        print(f"- {key}: {value}")
                print()
            
            # ========================================
            # 2. 口座残高の取得
            # ========================================
            print(f"### 💰 口座残高")
            try:
                # 通貨パラメータの指定
                # 'USD': 米ドル建て残高を取得
                # 'JPY': 日本円建て残高を取得（利用可能な場合）
                balance_response = api.account.get_account_balance(account_id, 'USD')
                
                # HTTPステータスコードの確認
                if balance_response.status_code == 200:
                    # JSONレスポンスをパース
                    balance_data = balance_response.json()
                    
                    # 口座IDの表示（確認用）
                    if 'account_id' in balance_data:
                        print(f"\n**口座ID**: {balance_data['account_id']}\n")
                    
                    # ========================================
                    # 通貨別の資産情報を表示
                    # ========================================
                    # account_currency_assets には複数の通貨建て情報が含まれる可能性がある
                    if 'account_currency_assets' in balance_data:
                        for currency_asset in balance_data['account_currency_assets']:
                            # 通貨コード（USD, JPY など）
                            currency = currency_asset.get('currency', 'N/A')
                            
                            # Markdown形式のテーブルで情報を整形
                            print(f"#### 💱 {currency} 建て\n")
                            print(f"| 項目 | 金額 |")
                            print(f"|------|------|")
                            
                            # 各項目を format_amount() で整形して表示
                            # total_cash: 総現金残高
                            print(f"| 総現金 | {format_amount(currency_asset.get('total_cash', '0'), currency)} |")
                            
                            # settled_cash: 確定済み現金（取引完了済み）
                            print(f"| 確定現金 | {format_amount(currency_asset.get('settled_cash', '0'), currency)} |")
                            
                            # unsettled_cash: 未確定現金（取引処理中）
                            print(f"| 未確定現金 | {format_amount(currency_asset.get('unsettled_cash', '0'), currency)} |")
                            
                            # frozen_cash: 凍結資金（注文中など）
                            print(f"| 凍結資金 | {format_amount(currency_asset.get('frozen_cash', '0'), currency)} |")
                            
                            # available_to_withdraw: 出金可能額
                            print(f"| 出金可能額 | {format_amount(currency_asset.get('available_to_withdraw', '0'), currency)} |")
                            
                            # stock_power: 買付余力（株式購入可能額）
                            print(f"| 買付余力 | {format_amount(currency_asset.get('stock_power', '0'), currency)} |")
                            print()
                    
                    # ========================================
                    # その他の残高情報（存在する場合）
                    # ========================================
                    # account_id と account_currency_assets 以外のフィールドを抽出
                    other_info = {k: v for k, v in balance_data.items() 
                                 if k not in ['account_id', 'account_currency_assets']}
                    
                    if other_info:
                        print("#### その他の残高情報\n")
                        for key, value in other_info.items():
                            print(f"- {key}: {value}")
                        print()
                else:
                    # 残高取得が失敗した場合のエラー表示
                    print(f"\n⚠️  残高情報の取得に失敗しました (ステータスコード: {balance_response.status_code})")
                    print(f"レスポンス: {balance_response.text}\n")
            
            except Exception as e:
                # 残高取得中の例外をキャッチして表示
                print(f"\n⚠️  残高取得中にエラーが発生しました: {str(e)}\n")
            
            # ========================================
            # 3. ポジション情報の取得（保有銘柄）
            # ========================================
            print(f"### 📈 保有ポジション")
            try:
                # ポジション情報APIの呼び出し
                # このAPIは保有している株式・ETFなどの情報を返す
                positions_response = api.account.get_account_position(account_id)
                
                # HTTPステータスコードの確認
                if positions_response.status_code == 200:
                    # JSONレスポンスをパース
                    positions_data = positions_response.json()
                    
                    # ========================================
                    # レスポンス形式の正規化
                    # ========================================
                    # APIのレスポンスは以下の3つの形式がある可能性：
                    # 1. リスト形式: [pos1, pos2, ...]
                    # 2. オブジェクト形式（positionsキー）: {"positions": [...]}
                    # 3. オブジェクト形式（dataキー）: {"data": [...]}
                    # 4. 単一オブジェクト: {...}（1つのポジションのみ）
                    
                    positions = []
                    
                    if isinstance(positions_data, list):
                        # ケース1: すでにリスト形式
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
                    
                    # ========================================
                    # 有効なポジションのフィルタリング
                    # ========================================
                    # 数量が0より大きいポジションのみを抽出
                    # （売却済みや空のポジションを除外）
                    valid_positions = []
                    
                    for pos in positions:
                        # 数量フィールドの取得
                        # APIによって 'position' または 'quantity' のキーが使われる
                        quantity = pos.get('position', pos.get('quantity', 0))
                        
                        try:
                            # 数量を浮動小数点数に変換
                            quantity_float = float(quantity) if quantity else 0
                            
                            # 数量が0より大きい場合のみ有効なポジションとして追加
                            if quantity_float > 0:
                                valid_positions.append(pos)
                        except (ValueError, TypeError):
                            # 数量が取得できない場合もリストに含める
                            # （念のため、データの欠損を見逃さないため）
                            valid_positions.append(pos)
                    
                    # ========================================
                    # 有効なポジションの表示
                    # ========================================
                    if valid_positions and len(valid_positions) > 0:
                        print(f"\n🎯 **保有銘柄**: {len(valid_positions)}件\n")
                        
                        # 各ポジションの詳細情報を表示
                        for pos_idx, pos in enumerate(valid_positions, 1):
                            
                            # ========================================
                            # ティッカーシンボルと銘柄名の取得
                            # ========================================
                            # ticker情報はネストされたオブジェクトで返される場合がある
                            ticker_info = pos.get('ticker', {})
                            
                            # シンボル（銘柄コード）の取得
                            # 例: AAPL, TSLA, VOO など
                            symbol = ticker_info.get('symbol', pos.get('symbol', 'N/A'))
                            
                            # ========================================
                            # 数量と価格情報の取得
                            # ========================================
                            # APIによって異なるキー名が使用される可能性に対応
                            # camelCase と snake_case の両方をチェック
                            
                            # 保有数量
                            quantity = pos.get('position', pos.get('quantity', 0))
                            
                            # 現在の市場評価額（現在価格 × 数量）
                            market_value = pos.get('marketValue', pos.get('market_value', 0))
                            
                            # 取得単価（購入時の平均単価）
                            cost_price = pos.get('costPrice', pos.get('cost_price', pos.get('cost', 0)))
                            
                            # 現在価格（最新の市場価格）
                            last_price = pos.get('lastPrice', pos.get('last_price', 0))
                            
                            # ========================================
                            # 損益情報の取得
                            # ========================================
                            # 未実現損益（まだ売却していない利益/損失）
                            unrealized_pl = pos.get('unrealizedProfitLoss', 
                                                   pos.get('unrealized_profit_loss', None))
                            
                            # 未実現損益率（パーセンテージ）
                            unrealized_pl_rate = pos.get('unrealizedProfitLossRate', 
                                                        pos.get('unrealized_profit_loss_rate', None))
                            
                            # ========================================
                            # ポジション情報のMarkdown形式での表示
                            # ========================================
                            print(f"#### 銘柄 #{pos_idx}: {symbol}\n")
                            
                            # 銘柄名があれば表示（日本語名や正式名称）
                            if 'name' in ticker_info:
                                print(f"**銘柄名**: {ticker_info['name']}\n")
                            
                            # Markdownテーブルのヘッダー
                            print(f"| 項目 | 値 |")
                            print(f"|------|------|")
                            
                            # 保有数量の表示
                            print(f"| 数量 | {quantity} |")
                            
                            # ========================================
                            # 価格情報と損益の計算・表示
                            # ========================================
                            try:
                                # 文字列や None を float に変換
                                cost_price_float = float(cost_price) if cost_price else 0
                                last_price_float = float(last_price) if last_price else 0
                                market_value_float = float(market_value) if market_value else 0
                                quantity_float = float(quantity) if quantity else 0
                                
                                # ========================================
                                # 価格情報の表示
                                # ========================================
                                # 現在価格（最新の市場価格）
                                if last_price_float > 0:
                                    print(f"| 現在価格 | ${last_price_float:,.2f} |")
                                
                                # 取得単価（購入時の平均価格）
                                if cost_price_float > 0:
                                    print(f"| 取得単価 | ${cost_price_float:,.2f} |")
                                
                                # 評価額（現在価格 × 数量）
                                if market_value_float > 0:
                                    print(f"| 評価額 | ${market_value_float:,.2f} |")
                                
                                # ========================================
                                # 損益の計算と表示
                                # ========================================
                                # 方法1: APIが損益データを提供している場合
                                if unrealized_pl is not None and unrealized_pl_rate is not None:
                                    # 未実現損益の金額
                                    pl_float = float(unrealized_pl)
                                    
                                    # 未実現損益率をパーセンテージに変換
                                    # （APIは小数で返す場合があるため100倍）
                                    pl_rate_float = float(unrealized_pl_rate) * 100
                                    
                                    # 利益か損失かによって絵文字を変更
                                    pl_sign = "📈" if pl_float >= 0 else "📉"
                                    
                                    # 損益を表示（+/- 記号付き）
                                    print(f"| 損益 | {pl_sign} ${pl_float:,.2f} ({pl_rate_float:+.2f}%) |")
                                
                                # 方法2: 損益データがない場合は手動で計算
                                elif cost_price_float > 0 and last_price_float > 0 and quantity_float > 0:
                                    # 損益計算の公式:
                                    # 損益 = (現在価格 - 取得単価) × 数量
                                    profit_loss = (last_price_float - cost_price_float) * quantity_float
                                    
                                    # 損益率の計算:
                                    # 損益率 = ((現在価格 - 取得単価) / 取得単価) × 100
                                    profit_loss_pct = ((last_price_float - cost_price_float) / cost_price_float * 100)
                                    
                                    # 利益か損失かによって絵文字を変更
                                    pl_sign = "📈" if profit_loss >= 0 else "📉"
                                    
                                    # 損益を表示（+/- 記号付き）
                                    print(f"| 損益 | {pl_sign} ${profit_loss:,.2f} ({profit_loss_pct:+.2f}%) |")
                            
                            except (ValueError, TypeError) as e:
                                # ========================================
                                # 数値変換エラーの処理
                                # ========================================
                                # 価格データが不正な形式の場合は、生の値をそのまま表示
                                if cost_price:
                                    print(f"| 取得単価 | {cost_price} |")
                                if last_price:
                                    print(f"| 現在価格 | {last_price} |")
                                if market_value:
                                    print(f"| 評価額 | {market_value} |")
                            
                            # 銘柄間の区切り
                            print()
                    else:
                        # ========================================
                        # ポジションが存在しない場合
                        # ========================================
                        print("\n📭 保有ポジションはありません\n")
                else:
                    # ========================================
                    # ポジション取得が失敗した場合
                    # ========================================
                    print(f"\n⚠️  ポジション情報の取得に失敗しました (ステータスコード: {positions_response.status_code})\n")
            
            except Exception as e:
                # ========================================
                # ポジション取得中の例外処理
                # ========================================
                print(f"\n⚠️  ポジション取得中にエラーが発生しました: {str(e)}\n")
        
        # ========================================
        # 完了メッセージの表示
        # ========================================
        print(f"\n{'=' * 60}")
        print("✅ 資産情報の取得が完了しました")
        print(f"{'=' * 60}\n")
    
    except Exception as e:
        # ========================================
        # トップレベルの例外処理
        # ========================================
        # 予期しないエラーが発生した場合の処理
        print(f"\n❌ エラーが発生しました: {str(e)}")
        
        # スタックトレースを表示（デバッグ用）
        import traceback
        traceback.print_exc()


def main():
    """
    メイン関数 - スクリプトのエントリーポイント
    
    この関数は以下の処理を実行します：
        1. 出力ファイル名の決定（スクリプト名.md）
        2. 標準出力のファイルへのリダイレクト設定
        3. Markdownヘッダーの出力
        4. 環境変数の読み込み
        5. APIキーの検証
        6. 資産情報の取得と表示
        7. 後処理とクリーンアップ
    
    Returns:
        None
    
    Side Effects:
        - sys.stdoutを一時的に変更
        - カレントディレクトリに .md ファイルを作成
    """
    
    # ========================================
    # 出力ファイル名の決定
    # ========================================
    # スクリプトのフルパスを取得
    script_path = Path(__file__).resolve()
    
    # スクリプトのディレクトリを取得
    script_dir = script_path.parent
    
    # スクリプト名（拡張子なし）を取得
    # 例: webull_asset_display.py → webull_asset_display
    script_name = script_path.stem
    
    # 出力ファイル名を生成（スクリプト名.md）
    # 例: webull_asset_display.md
    output_file = script_dir / f"{script_name}.md"
    
    # ========================================
    # 標準出力のリダイレクト設定
    # ========================================
    # MarkdownLoggerを初期化して、標準出力を置き換え
    # これにより、すべてのprint文がファイルにも書き込まれる
    md_logger = MarkdownLogger(output_file)
    sys.stdout = md_logger
    
    try:
        # ========================================
        # Markdownヘッダーの出力
        # ========================================
        # レポートのタイトル
        print(f"# Webull Japan - 資産情報レポート\n")
        
        # レポートの生成日時を記録
        print(f"**生成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
        
        # 区切り線
        print("---\n")
        
        # ========================================
        # 環境変数の読み込み
        # ========================================
        # .envファイルから環境変数を読み込む
        load_env_file()
        
        # ========================================
        # APIキーの取得
        # ========================================
        # 環境変数からAPIキーとシークレットを取得
        app_key = os.getenv('WEBULL_APP_KEY')
        app_secret = os.getenv('WEBULL_APP_SECRET')
        
        # ========================================
        # APIキーの検証
        # ========================================
        if not app_key or not app_secret:
            # APIキーが設定されていない場合のエラーメッセージ
            print("## ❌ エラー: APIキーとシークレットが設定されていません\n")
            
            print("### 設定方法\n")
            
            # 設定方法1: .envファイルを使用（推奨）
            print("#### 1. .envファイルを使用(推奨)\n")
            print("スクリプトと同じディレクトリに.envファイルを作成し、以下の内容を記載:\n")
            print("```")
            print("WEBULL_APP_KEY=your_actual_key")
            print("WEBULL_APP_SECRET=your_actual_secret")
            print("```\n")
            
            # 設定方法2: 環境変数を使用
            print("#### 2. 環境変数を使用\n")
            print("```bash")
            print("export WEBULL_APP_KEY='your_actual_key'")
            print("export WEBULL_APP_SECRET='your_actual_secret'")
            print("```\n")
            
            # APIキーの取得方法
            print("### APIキーの取得方法\n")
            print("https://www.webull.co.jp/center でOpenAPIを申請してください\n")
            
            # エラーの場合はここで終了
            return
        
        # ========================================
        # 認証情報の確認（表示はしない）
        # ========================================
        # APIキーが正しく読み込まれたことを内部で確認
        # セキュリティのため、画面やファイルには出力しない
        
        # ========================================
        # 資産情報の取得と表示
        # ========================================
        # メイン処理: Webull APIから資産情報を取得して表示
        display_asset_info(app_key, app_secret)
        
        # ========================================
        # フッターの出力
        # ========================================
        print("\n---")
        print(f"\n*このレポートは自動生成されました*")
        
    finally:
        # ========================================
        # 後処理とクリーンアップ
        # ========================================
        # 標準出力を元に戻す
        # これを忘れると、以降のprint文が正しく動作しない
        sys.stdout = md_logger.terminal
        
        # ファイルハンドルを閉じる
        md_logger.close()
        
        # ユーザーに出力ファイルの場所を通知
        print(f"\n✅ 出力ファイルが作成されました: {output_file}")


# ========================================
# スクリプトのエントリーポイント
# ========================================
# このブロックは、スクリプトが直接実行された場合のみ実行される
# （他のスクリプトからインポートされた場合は実行されない）
if __name__ == '__main__':
    main()