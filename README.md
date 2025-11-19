# Ｗebull証券のAPIレビュー

## このリポジトリについて
* Webull証券のAPIについての動作検証を行うリポジトリです。
* 言語はpython3.9を利用しています。
* ★はカイゼンしてほしいと思った点です。
* mdファイルには.pyファイルを実行して、APIからの出力した結果を出力しています


## API docs
* https://developer.webull.co.jp/api-doc/

## github repo
* https://github.com/microfund/webull-public

## issues
* https://github.com/microfund/webull-public/issues

## 公式サイト
* https://www.webull.co.jp/

## pc版アプリインストール
* https://www.webull.co.jp/platform/desktop-native

## スマホアプリのインストール
* https://www.webull.co.jp/platform/mobile-app

## 入金方法
* https://www.webull.co.jp/service/funding-and-withdrawal
* ★クイック入金にGMOあおぞらネット銀行を入れてほしい
* ★総合振込にGMOあおぞらネット銀行を入れてほしい
* 総合振込で振込入金の場合、３０分から１時間ほど着金にかかる

## 出金方法
* https://www.webull.co.jp/service/funding-and-withdrawal
* スマホアプリでしかできない（★ＷＥＢ版ではできない）

## API Tips (python)
* 入出金履歴を表示する
    * https://github.com/microfund/webull-public/blob/main/show_depo_withdrawal.md
    * ★表示できず

* 資産を表示する
    * 

* 取引履歴を表示する
    * 

* 銘柄と価格を表示する
    * 

* ニュースを取得する
    * 

* ティッカーシンボルをすべて表示する（米国株）
    * 

* 証券コードをすべて表示する（日本株）
    * 
    
### 注文
* 成行買いをする
    * 

### その他 ★
* 取引履歴（Entry/Exitの銘柄名、取引日時（秒単位まであると尚良い）、取引価格等）
* 米国株の銘柄情報
* 米国株の信用取引機能
* リアルタイムでの空売り規制情報
* AIで読み取りやすいディレクトリ等
* GitHubを使用したAPI情報（仕様書）のアップデート
