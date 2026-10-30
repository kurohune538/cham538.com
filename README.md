# cham538.com

[cham538.com](https://www.cham538.com/) の現在のソースコードです。Webflowから移行した静的サイトを、Cloudflare Workers Static Assets（`cham538-static`）で配信しています。

このリポジトリの `master` を編集元として使います。以前のGatsby版はGitの履歴に残っています。サイト本文・画像・ビルドスクリプトをすべて含むため、ビルド時にWebflowから素材を取得する必要はありません。

## 取得・ビルド

Python 3.10以上が必要です。Pythonの追加パッケージやAPIキーは不要です。

```sh
git clone https://github.com/kurohune538/cham538.com.git
cd cham538.com
python3 scripts/build_mirror.py
python3 scripts/validate_site.py
python3 -m http.server 8087 --directory dist
```

`http://localhost:8087/` で確認できます。`dist/` は毎回生成されるため、直接編集しません。

## 編集するファイル

| 場所 | 内容 |
| --- | --- |
| `original-pages/` | 移行元の11ページとrobots・sitemapの原稿。既存ページの本文を編集する場所 |
| `content/` | READ BETWEEN YOUの詳細ページとWorks先頭の紹介カード |
| `assets/` | 移行済みの画像・既存CSSなど354素材。ファイル名は参照元URLから生成したもの |
| `static/` | 共通のナビゲーションJS・補正CSS・404・HTTPヘッダーと、READ BETWEEN YOUの画像・CSS |
| `config/asset-manifest.json` | 同梱素材と元の公開URLの対応 |
| `config/css-assets.json` | CSSから参照される追加素材の元URL |
| `scripts/build_mirror.py` | HTML・フォント・ナビゲーションを組み合わせて`dist/`を再生成 |
| `scripts/validate_site.py` | HTML・CSSのローカル参照とサイトマップを検証 |
| `wrangler.jsonc` | 公開Workerと静的ファイル配信の設定 |

READ BETWEEN YOUを更新するときは、`content/read-between-you.html`、`content/read-between-you-card.html`、`static/read-between-you.css`を編集してビルドします。新しい作品を追加するときは、原稿・画像に加えてビルド処理とサイトマップへの登録も追加します。

ビルド時に生成する素材対応や移行元HTMLの調査結果は`.local/audit/`に置き、Gitには含めません。旧移行作業の管理画面記録、認証情報、`.wrangler/`、生成済みの`dist/`も管理対象から除いています。

## GitHubでの更新

変更用のブランチで編集し、Pull Requestを作成します。GitHub Actionsは、Pull Requestと`master`へのpushで以下を実行します。

1. 同梱素材からサイトをビルド
2. HTML・CSSの画像やファイル参照、サイトマップの整合性を検証
3. 共通JavaScriptの構文を確認

CIにはデプロイ権限やCloudflareの認証情報を渡していません。

## 公開

1. `master`の最新版を取得し、上記のビルドと検証を実行します。
2. Cloudflare Dashboardで既存の`cham538-static`を開き、**New deployment**から`dist/`フォルダを選びます。
3. Assets directoryは`/`、HTML handlingは`auto-trailing-slash`、Not found handlingは`404-page`を維持して公開します。

リポジトリ全体はアップロードせず、生成した`dist/`だけを配信します。GitHubへのpushやPRのマージでは本番デプロイは行いません。

- 正規URL: <https://www.cham538.com/>
- Worker URL: <https://cham538-static.kurohune538.workers.dev/>
- READ BETWEEN YOU: <https://www.cham538.com/work/read-between-you/>

## 外部サービス

Adobe Fontsは既存Web Projectの公式埋め込み、Google Fontsは公式CSSを使用しています。フォントファイルはリポジトリに含めません。既存のYouTubeなどの埋め込みは、それぞれのサービスに依存します。問い合わせフォームは移行時の方針に従い、ビルドで除去しています。

画像・作品・ロゴ・外部フォントの権利は、それぞれの権利者に帰属します。旧GatsbyスターターのLICENSEは保持しています。
