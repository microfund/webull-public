#!/usr/bin/env python3
"""
Webull Japan OpenAPI - 全エンドポイント一覧表示スクリプト

このスクリプトは、Webull Japan OpenAPIで利用可能なすべてのエンドポイントを
カテゴリー別に整理して表示します。

公式ドキュメント: https://developer.webull.co.jp/api-doc/
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

try:
    from webullsdkcore.client import ApiClient
    from webullsdktrade.api import API
    from webullsdkcore.common.region import Region
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


class WebullEndpointLister:
    """Webull Japan OpenAPIエンドポイント一覧表示クラス"""
    
    def __init__(self):
        """初期化"""
        self.output_lines = []
        self.endpoints = self._define_endpoints()
        
    def _define_endpoints(self) -> dict:
        """
        Webull Japan OpenAPIの全エンドポイントを定義
        
        公式ドキュメントに基づいて整理
        """
        return {
            "口座管理 (Account Management)": {
                "description": "口座情報の取得と管理",
                "endpoints": [
                    {
                        "name": "口座購読情報の取得",
                        "method": "GET",
                        "path": "/account/subscriptions",
                        "sdk_method": "api.account.get_app_subscriptions()",
                        "description": "APIアプリケーションに紐づく口座情報の一覧を取得",
                        "parameters": [],
                        "response": "口座ID、購読ID、ステータスなど"
                    },
                    {
                        "name": "口座詳細情報の取得",
                        "method": "GET",
                        "path": "/account/{account_id}",
                        "sdk_method": "api.account.get_account_detail(account_id)",
                        "description": "指定した口座の詳細情報を取得",
                        "parameters": ["account_id: 口座ID"],
                        "response": "口座詳細情報"
                    },
                    {
                        "name": "口座残高の取得",
                        "method": "GET",
                        "path": "/account/{account_id}/balance",
                        "sdk_method": "api.account.get_account_balance(account_id)",
                        "description": "口座の現金残高、購買力、総資産額などを取得",
                        "parameters": ["account_id: 口座ID"],
                        "response": "現金残高、購買力、総資産額など"
                    },
                    {
                        "name": "口座ポジションの取得",
                        "method": "GET",
                        "path": "/account/{account_id}/positions",
                        "sdk_method": "api.account.get_account_positions(account_id)",
                        "description": "保有している株式ポジション情報を取得",
                        "parameters": ["account_id: 口座ID"],
                        "response": "銘柄、数量、平均取得価格、現在価格など"
                    }
                ]
            },
            
            "注文管理 (Order Management)": {
                "description": "注文の作成、変更、キャンセル、照会",
                "endpoints": [
                    {
                        "name": "注文の作成",
                        "method": "POST",
                        "path": "/order",
                        "sdk_method": "api.order.place_order(account_id, order_params)",
                        "description": "新規注文を作成(成行、指値、逆指値など)",
                        "parameters": [
                            "account_id: 口座ID",
                            "order_params: 注文パラメータ(銘柄、数量、価格、注文タイプなど)"
                        ],
                        "response": "注文ID、クライアント注文ID、ステータス"
                    },
                    {
                        "name": "注文の変更",
                        "method": "PUT",
                        "path": "/order/{order_id}",
                        "sdk_method": "api.order.modify_order(account_id, order_id, new_params)",
                        "description": "既存注文の価格や数量を変更",
                        "parameters": [
                            "account_id: 口座ID",
                            "order_id: 注文ID",
                            "new_params: 変更パラメータ"
                        ],
                        "response": "変更後の注文情報"
                    },
                    {
                        "name": "注文のキャンセル",
                        "method": "DELETE",
                        "path": "/order/{order_id}",
                        "sdk_method": "api.order.cancel_order(account_id, order_id)",
                        "description": "指定した注文をキャンセル",
                        "parameters": [
                            "account_id: 口座ID",
                            "order_id: 注文ID"
                        ],
                        "response": "キャンセル結果"
                    },
                    {
                        "name": "注文詳細の取得",
                        "method": "GET",
                        "path": "/order/{order_id}",
                        "sdk_method": "api.order.query_order_detail(account_id, client_order_id)",
                        "description": "指定した注文の詳細情報を取得",
                        "parameters": [
                            "account_id: 口座ID",
                            "client_order_id: クライアント注文ID"
                        ],
                        "response": "注文の詳細情報、ステータス、約定情報など"
                    },
                    {
                        "name": "注文一覧の取得",
                        "method": "GET",
                        "path": "/orders",
                        "sdk_method": "api.order.query_orders(account_id, params)",
                        "description": "口座の注文一覧を取得(フィルタ可能)",
                        "parameters": [
                            "account_id: 口座ID",
                            "params: フィルタパラメータ(日付、ステータスなど)"
                        ],
                        "response": "注文のリスト"
                    },
                    {
                        "name": "未約定注文の取得",
                        "method": "GET",
                        "path": "/orders/open",
                        "sdk_method": "api.order.get_open_orders(account_id)",
                        "description": "現在有効な未約定注文を取得",
                        "parameters": ["account_id: 口座ID"],
                        "response": "未約定注文のリスト"
                    }
                ]
            },
            
            "マーケットデータ (Market Data) - GRPC": {
                "description": "株式情報とマーケットデータの取得",
                "note": "※現在、HTTP経由のマーケットデータリクエストは未サポート。GRPCプロトコルを使用。",
                "endpoints": [
                    {
                        "name": "銘柄情報の取得",
                        "method": "GRPC",
                        "path": "/instrument",
                        "sdk_method": "grpc_api.instrument.get_instrument(symbols, category)",
                        "description": "銘柄コードリストから銘柄の基本情報を取得",
                        "parameters": [
                            "symbols: 銘柄コードのリスト (例: ['AAPL', 'TSLA'])",
                            "category: カテゴリ (例: 'US_STOCK')"
                        ],
                        "response": "銘柄名、ISIN、取引所、セクターなど",
                        "frequency_limit": "60回/分"
                    },
                    {
                        "name": "マーケットスナップショット",
                        "method": "GRPC",
                        "path": "/market-data/snapshot",
                        "sdk_method": "grpc_api.market_data.get_snapshot(symbols, category)",
                        "description": "銘柄の最新価格情報をバッチ取得",
                        "parameters": [
                            "symbols: 銘柄コードのリスト",
                            "category: カテゴリ"
                        ],
                        "response": "最新価格、出来高、高値、安値など",
                        "frequency_limit": "1回/秒"
                    },
                    {
                        "name": "ローソク足データ",
                        "method": "GRPC",
                        "path": "/market-data/bars",
                        "sdk_method": "grpc_api.market_data.get_bars(symbol, category, timeframe, count)",
                        "description": "指定期間のローソク足データを取得",
                        "parameters": [
                            "symbol: 銘柄コード",
                            "category: カテゴリ",
                            "timeframe: 時間足(1m, 5m, 1d等)",
                            "count: データ件数"
                        ],
                        "response": "OHLCV(始値、高値、安値、終値、出来高)データ"
                    }
                ]
            },
            
            "リアルタイム購読 (Real-time Subscriptions)": {
                "description": "注文ステータスとマーケットデータのリアルタイム受信",
                "endpoints": [
                    {
                        "name": "注文イベント購読",
                        "method": "GRPC",
                        "path": "/trade-events",
                        "sdk_method": "EventsClient.do_subscribe([account_ids])",
                        "description": "注文ステータス変更のリアルタイム通知を受信",
                        "parameters": ["account_ids: 監視する口座IDのリスト"],
                        "response": "注文作成、約定、キャンセル等のイベント通知"
                    },
                    {
                        "name": "マーケットデータ購読",
                        "method": "MQTT",
                        "path": "/quotes/subscribe",
                        "sdk_method": "DefaultQuotesClient.connect_and_loop_forever()",
                        "description": "銘柄の価格変動をリアルタイムで受信",
                        "parameters": [
                            "symbol: 監視する銘柄コード",
                            "category: カテゴリ",
                            "subscribe_type: 購読タイプ(SNAPSHOT等)"
                        ],
                        "response": "リアルタイムの価格更新情報"
                    }
                ]
            },
            
            "取引カレンダー (Trading Calendar)": {
                "description": "市場の営業日情報",
                "endpoints": [
                    {
                        "name": "取引カレンダーの取得",
                        "method": "GET",
                        "path": "/trade/calendar",
                        "sdk_method": "api.market.get_trading_calendar(market, start_date, end_date)",
                        "description": "指定期間の取引日と休場日を取得",
                        "parameters": [
                            "market: 市場コード(US等)",
                            "start_date: 開始日",
                            "end_date: 終了日"
                        ],
                        "response": "取引日のリスト、休場日情報"
                    }
                ]
            },
            
            "現在利用不可のエンドポイント": {
                "description": "将来実装予定または条件付きで利用可能",
                "note": "※これらのエンドポイントは現在Webull Japan OpenAPIではサポートされていません",
                "endpoints": [
                    {
                        "name": "入出金履歴の取得",
                        "method": "N/A",
                        "path": "未実装",
                        "sdk_method": "未サポート",
                        "description": "口座の入出金取引履歴を取得",
                        "parameters": ["N/A"],
                        "response": "N/A",
                        "status": "❌ 未実装 - カスタマーサポートへの問い合わせが必要"
                    },
                    {
                        "name": "全銘柄リストの取得",
                        "method": "N/A",
                        "path": "未実装",
                        "sdk_method": "未サポート",
                        "description": "取引可能な全銘柄のリストを取得",
                        "parameters": ["N/A"],
                        "response": "N/A",
                        "status": "❌ 未実装 - 銘柄コード指定が必要"
                    },
                    {
                        "name": "銘柄検索",
                        "method": "N/A",
                        "path": "未実装",
                        "sdk_method": "未サポート",
                        "description": "キーワードで銘柄を検索",
                        "parameters": ["N/A"],
                        "response": "N/A",
                        "status": "❌ 未実装"
                    }
                ]
            }
        }
    
    def add_output(self, line: str):
        """出力行を追加"""
        self.output_lines.append(line)
        print(line)
    
    def display_all_endpoints(self):
        """全エンドポイントを表示"""
        self.add_output("=" * 100)
        self.add_output("Webull Japan OpenAPI - 全エンドポイント一覧")
        self.add_output("=" * 100)
        self.add_output("")
        self.add_output(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.add_output(f"公式ドキュメント: https://developer.webull.co.jp/api-doc/")
        self.add_output(f"SDK GitHub: https://github.com/webull-inc/openapi-python-sdk")
        self.add_output("")
        self.add_output("=" * 100)
        self.add_output("")
        
        # カテゴリーごとにエンドポイントを表示
        for category_num, (category, data) in enumerate(self.endpoints.items(), 1):
            self.add_output("")
            self.add_output("=" * 100)
            self.add_output(f"{category_num}. {category}")
            self.add_output("=" * 100)
            self.add_output(f"説明: {data['description']}")
            
            if 'note' in data:
                self.add_output(f"注意: {data['note']}")
            
            self.add_output("")
            self.add_output("-" * 100)
            
            for endpoint_num, endpoint in enumerate(data['endpoints'], 1):
                self.add_output("")
                self.add_output(f"  [{category_num}-{endpoint_num}] {endpoint['name']}")
                self.add_output(f"  {'─' * 96}")
                self.add_output(f"  HTTPメソッド    : {endpoint['method']}")
                self.add_output(f"  パス           : {endpoint['path']}")
                self.add_output(f"  SDKメソッド    : {endpoint['sdk_method']}")
                self.add_output(f"  説明           : {endpoint['description']}")
                
                if endpoint['parameters']:
                    self.add_output(f"  パラメータ     :")
                    for param in endpoint['parameters']:
                        self.add_output(f"                   - {param}")
                else:
                    self.add_output(f"  パラメータ     : なし")
                
                self.add_output(f"  レスポンス     : {endpoint['response']}")
                
                if 'frequency_limit' in endpoint:
                    self.add_output(f"  頻度制限       : {endpoint['frequency_limit']}")
                
                if 'status' in endpoint:
                    self.add_output(f"  ステータス     : {endpoint['status']}")
                
                self.add_output("")
        
        # サマリー情報
        self.add_output("")
        self.add_output("=" * 100)
        self.add_output("サマリー")
        self.add_output("=" * 100)
        self.add_output("")
        
        total_endpoints = sum(len(data['endpoints']) for data in self.endpoints.values())
        implemented_endpoints = sum(
            len([ep for ep in data['endpoints'] if 'status' not in ep])
            for data in self.endpoints.values()
        )
        
        self.add_output(f"総エンドポイント数        : {total_endpoints}")
        self.add_output(f"実装済みエンドポイント数  : {implemented_endpoints}")
        self.add_output(f"未実装エンドポイント数    : {total_endpoints - implemented_endpoints}")
        self.add_output("")
        
        # プロトコル別
        self.add_output("プロトコル別の分類:")
        self.add_output("  - HTTP  : 口座管理、注文管理、取引カレンダー")
        self.add_output("  - GRPC  : マーケットデータ取得、注文イベント購読")
        self.add_output("  - MQTT  : リアルタイムマーケットデータ購読")
        self.add_output("")
        
        # SDK情報
        self.add_output("必要なPythonパッケージ:")
        self.add_output("  pip install --upgrade webull-python-sdk-core")
        self.add_output("  pip install --upgrade webull-python-sdk-trade")
        self.add_output("  pip install --upgrade webull-python-sdk-quotes-core")
        self.add_output("  pip install --upgrade webull-python-sdk-mdata")
        self.add_output("  pip install --upgrade webull-python-sdk-trade-events-core")
        self.add_output("")
        
        # 重要な注意事項
        self.add_output("=" * 100)
        self.add_output("重要な注意事項")
        self.add_output("=" * 100)
        self.add_output("")
        self.add_output("1. 米国株の全銘柄リストを直接取得するAPIは存在しません")
        self.add_output("   → 銘柄コードを指定して個別に情報を取得する必要があります")
        self.add_output("")
        self.add_output("2. 入出金履歴の取得APIは未実装です")
        self.add_output("   → Webullモバイルアプリまたはカスタマーサポートへの問い合わせが必要")
        self.add_output("")
        self.add_output("3. マーケットデータのHTTPリクエストは現在未サポート")
        self.add_output("   → GRPCプロトコルを使用する必要があります")
        self.add_output("")
        self.add_output("4. APIキーの有効期限はデフォルトで45日間")
        self.add_output("   → 期限切れ前にリセットが必要です")
        self.add_output("")
        self.add_output("5. API呼び出しには頻度制限があります")
        self.add_output("   → 各エンドポイントの制限を確認してください")
        self.add_output("")
        self.add_output("=" * 100)
        self.add_output("")
    
    def display_sdk_check(self):
        """SDKインストール状況を表示"""
        self.add_output("SDK インストール状況チェック")
        self.add_output("-" * 100)
        
        if SDK_AVAILABLE:
            self.add_output("✓ Webull Python SDK がインストールされています")
            try:
                import webullsdkcore
                self.add_output(f"  - webull-python-sdk-core: インストール済み")
            except ImportError:
                self.add_output(f"  - webull-python-sdk-core: 未インストール")
            
            try:
                import webullsdktrade
                self.add_output(f"  - webull-python-sdk-trade: インストール済み")
            except ImportError:
                self.add_output(f"  - webull-python-sdk-trade: 未インストール")
            
            try:
                import webullsdkquotescore
                self.add_output(f"  - webull-python-sdk-quotes-core: インストール済み")
            except ImportError:
                self.add_output(f"  - webull-python-sdk-quotes-core: 未インストール")
        else:
            self.add_output("✗ Webull Python SDK がインストールされていません")
            self.add_output("")
            self.add_output("以下のコマンドでインストールしてください:")
            self.add_output("  pip install --upgrade webull-python-sdk-core")
            self.add_output("  pip install --upgrade webull-python-sdk-trade")
            self.add_output("  pip install --upgrade webull-python-sdk-quotes-core")
        
        self.add_output("")
    
    def save_output(self, filename: str):
        """出力をファイルに保存"""
        script_dir = Path(__file__).parent
        output_path = script_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.output_lines))
        
        print(f"\n出力ファイル: {output_path}")
        print(f"ファイルサイズ: {output_path.stat().st_size:,} bytes")


def main():
    """メイン処理"""
    print("\n" + "=" * 100)
    print("Webull Japan OpenAPI - 全エンドポイント一覧表示ツール")
    print("=" * 100 + "\n")
    
    lister = WebullEndpointLister()
    
    # SDK状況チェック
    lister.display_sdk_check()
    
    # 全エンドポイント表示
    lister.display_all_endpoints()
    
    # 出力をファイルに保存
    output_filename = Path(__file__).stem + '.md'
    lister.save_output(output_filename)
    
    print("\n処理が完了しました。")


if __name__ == "__main__":
    main()