#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webull Japan OpenAPI - 当日取引履歴取得スクリプト

このスクリプトは、Webull Japan OpenAPIを使用して当日の取引履歴(注文履歴)を取得します。

注意事項:
- Webull Japan OpenAPIには過去の取引履歴を取得するエンドポイントがありません
- このスクリプトは「当日の注文履歴」のみを取得します
- 取得した情報は標準出力とMarkdownファイルに出力されます
- API認証情報は出力から除外されます

必要なパッケージ:
- webull-python-sdk-core
- webull-python-sdk-trade
- python-dotenv

使用方法:
1. .envファイルにWebull APIの認証情報を設定
2. python get_order_history.py を実行
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Webull SDK のインポート
try:
    from webullsdkcore.client import ApiClient
    from webullsdktrade.api import API
    from webullsdkcore.common.region import Region
except ImportError as e:
    print("エラー: 必要なパッケージがインストールされていません。")
    print("以下のコマンドでインストールしてください:")
    print("pip install webull-python-sdk-core webull-python-sdk-trade python-dotenv")
    sys.exit(1)


class MarkdownLogger:
    """
    標準出力とMarkdownファイルへの同時出力を管理するクラス
    
    API認証情報を出力から除外し、セキュアな出力を実現します。
    """
    
    def __init__(self, filename: str):
        """
        Args:
            filename: 出力するMarkdownファイルのパス
        """
        self.filename = filename
        self.lines: List[str] = []
        
    def print(self, message: str = "", to_file: bool = True, to_console: bool = True):
        """
        メッセージを標準出力とファイルに出力
        
        Args:
            message: 出力するメッセージ
            to_file: ファイルに出力するか
            to_console: コンソールに出力するか
        """
        if to_console:
            print(message)
        if to_file:
            self.lines.append(message)
    
    def save(self):
        """Markdownファイルに保存"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.lines))
            print(f"\n✓ 結果を {self.filename} に保存しました")
        except Exception as e:
            print(f"\n✗ ファイル保存エラー: {e}")


class WebullOrderHistory:
    """
    Webull Japan OpenAPIを使用して当日の注文履歴を取得するクラス
    """
    
    def __init__(self, app_key: str, app_secret: str):
        """
        Args:
            app_key: Webull APIアプリケーションキー
            app_secret: Webull APIアプリケーションシークレット
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.api_client = None
        self.api = None
        self.account_id = None
        
    def initialize(self) -> bool:
        """
        APIクライアントを初期化
        
        Returns:
            初期化成功時True、失敗時False
        """
        try:
            # APIクライアントの初期化(日本リージョン)
            self.api_client = ApiClient(
                self.app_key,
                self.app_secret,
                Region.JP.value
            )
            self.api = API(self.api_client)
            return True
        except Exception as e:
            print(f"✗ API初期化エラー: {e}")
            return False
    
    def get_account_id(self) -> Optional[str]:
        """
        アカウントIDを取得
        
        Returns:
            アカウントID、取得失敗時はNone
        """
        try:
            response = self.api.account.get_app_subscriptions()
            
            if response.status_code != 200:
                print(f"✗ アカウント情報取得エラー: ステータスコード {response.status_code}")
                return None
            
            accounts = response.json()
            
            if not accounts or len(accounts) == 0:
                print("✗ アカウントが見つかりません")
                return None
            
            # 最初のアカウントのIDを取得
            self.account_id = accounts[0].get('account_id')
            return self.account_id
            
        except Exception as e:
            print(f"✗ アカウントID取得エラー: {e}")
            return None
    
    def get_today_orders(self, page_size: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        当日の注文履歴を取得
        
        Args:
            page_size: 1回のリクエストで取得する注文数(最大100)
            
        Returns:
            注文リスト、取得失敗時はNone
        """
        if not self.account_id:
            print("✗ アカウントIDが設定されていません")
            return None
        
        try:
            all_orders = []
            last_client_order_id = None
            
            # ページネーションで全ての注文を取得
            while True:
                response = self.api.order.list_today_orders(
                    self.account_id,
                    page_size,
                    last_client_order_id
                )
                
                if response.status_code != 200:
                    print(f"✗ 注文履歴取得エラー: ステータスコード {response.status_code}")
                    return None
                
                data = response.json()
                orders = data.get('data', [])
                
                if not orders:
                    break
                
                all_orders.extend(orders)
                
                # 次のページがあるかチェック
                if len(orders) < page_size:
                    break
                
                # 次のページのために最後の注文IDを保存
                last_client_order_id = orders[-1].get('client_order_id')
            
            return all_orders
            
        except Exception as e:
            print(f"✗ 注文履歴取得エラー: {e}")
            return None
    
    def format_order_status(self, status: str) -> str:
        """
        注文ステータスを日本語に変換
        
        Args:
            status: 注文ステータス(英語)
            
        Returns:
            日本語の注文ステータス
        """
        status_map = {
            'Working': '処理中',
            'Filled': '約定',
            'Cancelled': 'キャンセル',
            'Rejected': '拒否',
            'PendingCancel': 'キャンセル待ち',
            'PartialFilled': '一部約定',
            'Failed': '失敗'
        }
        return status_map.get(status, status)
    
    def format_order_side(self, side: str) -> str:
        """
        売買区分を日本語に変換
        
        Args:
            side: 売買区分(英語)
            
        Returns:
            日本語の売買区分
        """
        side_map = {
            'BUY': '買',
            'SELL': '売'
        }
        return side_map.get(side, side)
    
    def format_order_type(self, order_type: str) -> str:
        """
        注文タイプを日本語に変換
        
        Args:
            order_type: 注文タイプ(英語)
            
        Returns:
            日本語の注文タイプ
        """
        type_map = {
            'LIMIT': '指値',
            'MARKET': '成行',
            'STOP': '逆指値',
            'STOP_LIMIT': '逆指値(指値)'
        }
        return type_map.get(order_type, order_type)


def format_currency_amount(amount: float, currency: str) -> str:
    """
    金額を通貨に応じて適切にフォーマット
    
    Args:
        amount: 金額
        currency: 通貨コード
        
    Returns:
        フォーマットされた金額文字列
    """
    if currency == 'JPY':
        # 日本円は整数で表示
        return f"{int(amount):,}"
    else:
        # その他の通貨は小数点2桁
        return f"{amount:,.2f}"


def main():
    """メイン処理"""
    
    # スクリプトのパスを取得
    script_path = Path(__file__).resolve()
    script_dir = script_path.parent
    script_name = script_path.stem
    
    # Markdownファイルのパス
    md_filename = script_dir / f"{script_name}.md"
    
    # MarkdownLoggerの初期化
    logger = MarkdownLogger(str(md_filename))
    
    # ヘッダー出力
    logger.print("# Webull Japan OpenAPI - 当日取引履歴")
    logger.print()
    logger.print(f"**実行日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    logger.print()
    logger.print("---")
    logger.print()
    
    # .envファイルから環境変数を読み込み
    load_dotenv()
    
    app_key = os.getenv('WEBULL_APP_KEY')
    app_secret = os.getenv('WEBULL_APP_SECRET')
    
    # 認証情報の検証(コンソールのみに出力)
    logger.print("📋 環境変数の確認...", to_file=False)
    
    if not app_key or not app_secret:
        logger.print("✗ エラー: .envファイルにWEBULL_APP_KEYとWEBULL_APP_SECRETを設定してください")
        logger.print()
        logger.print("## エラー")
        logger.print()
        logger.print("環境変数 `WEBULL_APP_KEY` と `WEBULL_APP_SECRET` が設定されていません。")
        logger.print()
        logger.print(".envファイルを作成し、以下の形式で認証情報を設定してください:")
        logger.print()
        logger.print("```")
        logger.print("WEBULL_APP_KEY=your_app_key_here")
        logger.print("WEBULL_APP_SECRET=your_app_secret_here")
        logger.print("```")
        logger.save()
        sys.exit(1)
    
    logger.print("✓ 認証情報を読み込みました", to_file=False)
    logger.print()
    
    # WebullOrderHistoryインスタンスの作成
    logger.print("🔧 API接続を初期化中...", to_file=False)
    webull = WebullOrderHistory(app_key, app_secret)
    
    if not webull.initialize():
        logger.print()
        logger.print("## エラー")
        logger.print()
        logger.print("API接続の初期化に失敗しました。")
        logger.save()
        sys.exit(1)
    
    logger.print("✓ API接続を初期化しました", to_file=False)
    logger.print()
    
    # アカウントIDの取得
    logger.print("🔍 アカウント情報を取得中...", to_file=False)
    account_id = webull.get_account_id()
    
    if not account_id:
        logger.print()
        logger.print("## エラー")
        logger.print()
        logger.print("アカウントIDの取得に失敗しました。")
        logger.save()
        sys.exit(1)
    
    logger.print(f"✓ アカウントID: {account_id[:8]}...", to_file=False)
    logger.print()
    
    # 当日の注文履歴を取得
    logger.print("📊 当日の注文履歴を取得中...", to_file=False)
    orders = webull.get_today_orders()
    
    if orders is None:
        logger.print()
        logger.print("## エラー")
        logger.print()
        logger.print("注文履歴の取得に失敗しました。")
        logger.save()
        sys.exit(1)
    
    logger.print(f"✓ {len(orders)}件の注文を取得しました", to_file=False)
    logger.print()
    
    # 結果の出力
    logger.print("## 取引履歴サマリー")
    logger.print()
    logger.print(f"- **取得件数**: {len(orders)}件")
    logger.print(f"- **対象日**: {datetime.now().strftime('%Y年%m月%d日')}")
    logger.print()
    
    if len(orders) == 0:
        logger.print("## 注文情報")
        logger.print()
        logger.print("当日の注文履歴はありません。")
        logger.print()
    else:
        logger.print("## 注文一覧")
        logger.print()
        
        # 注文を時刻順にソート(新しい順)
        orders_sorted = sorted(
            orders,
            key=lambda x: x.get('create_time', ''),
            reverse=True
        )
        
        for idx, order in enumerate(orders_sorted, 1):
            logger.print(f"### 注文 #{idx}")
            logger.print()
            
            # 基本情報
            symbol = order.get('symbol', 'N/A')
            instrument_name = order.get('instrument_name', 'N/A')
            side = webull.format_order_side(order.get('side', 'N/A'))
            order_type = webull.format_order_type(order.get('order_type', 'N/A'))
            status = webull.format_order_status(order.get('status', 'N/A'))
            
            logger.print(f"- **銘柄**: {symbol} ({instrument_name})")
            logger.print(f"- **売買**: {side}")
            logger.print(f"- **注文種別**: {order_type}")
            logger.print(f"- **ステータス**: {status}")
            
            # 数量と価格
            quantity = order.get('qty', 0)
            filled_qty = order.get('filled_qty', 0)
            limit_price = order.get('limit_price', 0)
            avg_filled_price = order.get('avg_filled_price', 0)
            currency = order.get('currency', 'USD')
            
            logger.print(f"- **注文数量**: {quantity}")
            
            if filled_qty > 0:
                logger.print(f"- **約定数量**: {filled_qty}")
            
            if order_type == '指値' and limit_price > 0:
                logger.print(f"- **指値価格**: {currency} {format_currency_amount(limit_price, currency)}")
            
            if avg_filled_price > 0:
                logger.print(f"- **平均約定価格**: {currency} {format_currency_amount(avg_filled_price, currency)}")
            
            # 時刻情報
            create_time = order.get('create_time', '')
            if create_time:
                try:
                    dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                    logger.print(f"- **注文日時**: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                except:
                    logger.print(f"- **注文日時**: {create_time}")
            
            # 注文ID(参照用)
            client_order_id = order.get('client_order_id', 'N/A')
            logger.print(f"- **注文ID**: `{client_order_id}`")
            
            logger.print()
        
        # 統計情報
        logger.print("---")
        logger.print()
        logger.print("## 統計情報")
        logger.print()
        
        # ステータス別集計
        status_counts = {}
        for order in orders:
            status = webull.format_order_status(order.get('status', 'N/A'))
            status_counts[status] = status_counts.get(status, 0) + 1
        
        logger.print("### ステータス別件数")
        logger.print()
        for status, count in sorted(status_counts.items()):
            logger.print(f"- **{status}**: {count}件")
        logger.print()
        
        # 売買別集計
        side_counts = {'買': 0, '売': 0}
        for order in orders:
            side = webull.format_order_side(order.get('side', ''))
            if side in side_counts:
                side_counts[side] += 1
        
        logger.print("### 売買別件数")
        logger.print()
        logger.print(f"- **買注文**: {side_counts['買']}件")
        logger.print(f"- **売注文**: {side_counts['売']}件")
        logger.print()
    
    logger.print("---")
    logger.print()
    logger.print("## 注意事項")
    logger.print()
    logger.print("- このデータは**当日の注文履歴**のみを表示しています")
    logger.print("- Webull Japan OpenAPIには過去の取引履歴を取得するエンドポイントが存在しません")
    logger.print("- より詳細な取引履歴が必要な場合は、Webullアプリまたはウェブサイトをご利用ください")
    logger.print()
    
    # Markdownファイルに保存
    logger.save()
    
    logger.print()
    logger.print("✓ 処理が完了しました", to_file=False)


if __name__ == "__main__":
    main()