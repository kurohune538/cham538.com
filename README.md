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
| `content/` | READ BETWEEN YOU・Cascade・Epitaph of the Earthの詳細ページとWorksの紹介カード |
| `content/projects.json` | 追加作品と旧作品アーカイブの日英本文、カテゴリ、画像、公開リンク |
| `content/project-template.html` | 上記のWorks・Lab詳細ページに共通のHTML |
| `content/cv-2026.json` | CVに基づく経歴・学歴・受賞・発表・展示歴と、既存サイトから保持した項目 |
| `assets/` | 移行済みの画像・既存CSSなど354素材。ファイル名は参照元URLから生成したもの |
| `static/` | 共通のナビゲーションJS・補正CSS・404・HTTPヘッダーと、作品の画像・CSS |
| `config/asset-manifest.json` | 同梱素材と元の公開URLの対応 |
| `config/css-assets.json` | CSSから参照される追加素材の元URL |
| `scripts/build_mirror.py` | HTML・フォント・ナビゲーションを組み合わせて`dist/`を再生成 |
| `scripts/validate_site.py` | HTML・CSSのローカル参照とサイトマップを検証 |
| `scripts/cv_content.py` | Home・About・AppearancesのCV情報と共通ダウンロードリンクを生成 |
| `scripts/project_content.py` | `projects.json`からWorks・Labのカード、詳細ページ、サイトマップを生成 |
| `wrangler.jsonc` | 公開Workerと静的ファイル配信の設定 |

READ BETWEEN YOUを更新するときは、`content/read-between-you.html`、`content/read-between-you-card.html`、`static/read-between-you.css`を編集してビルドします。Epitaph of the Earthは`content/epitaph-of-the-earth.html`、`content/epitaph-of-the-earth-card.html`、`static/epitaph-of-the-earth.css`と`static/epitaph-*.jpg`で管理します。Cascadeは`content/cascade.html`、`content/cascade-card.html`、`static/cascade.css`と`static/cascade-key-visual.jpg`で管理します。

追加作品は`content/projects.json`で管理します。`category`を`works`または`lab`に設定すると、一覧カード、詳細ページ、サイトマップをまとめて生成します。画像は`static/`へ置きます。hAIkuの公演動画はDrive上の記録映像をWeb向けのMP4に変換し、同じ動画からポスター画像を取り出しています。`video`を指定した作品は、画像の代わりに操作可能な動画プレイヤーを表示します。インターネット履歴書はDrive上の展示記録から、RAWデータに埋め込まれたJPEGをそのまま取り出して掲載しています。`gallery`には画像1件のオブジェクト、または複数画像の配列を指定でき、配列の見出しは`gallery_heading`で変更できます。横長のUI画面を大きく見せる場合は`gallery_layout`を`wide`にします。hAIkuの図解や駅ナカまっぷの紹介グラフィックは編集可能なSVGで管理します。紹介グラフィックと実際の記録は各キャプションで区別しています。参加者の履歴書や非公開の調査資料は含めません。

StormyのUI画像は、`google-hackathon2026`のコミット`ed7fc7333cf1b6b270e1a903ab6ccbba4f5a31db`をローカルで動かして取得した実画面です。開発用認証とモック応答を使い、テスト用プロフィールを画面から入力しています。実際の利用者情報やライブのAI生成結果は含みません。

WorksのRe:Earthカードの画像`static/reearth-visualizer-ui.jpg`は、2026年10月31日に[reearth.io](https://reearth.io/about)の概要ページから取得したVisualizerの画面です。権利はEukaryaに帰属します。

ComicHolicのランキング・検索、Maptomの地球儀・平面地図のUI画像は、2026年10月31日にそれぞれの公開サイトを操作して取得した実画面です。書影やポケモンの画像・名称の権利は各権利者に帰属します。

旧一覧にあるGyoretsu Ya、Interactive DJ Pillars、Live Ya、Mangaka、Komenoma、Townworkのカードは、各作品の紹介ページにリンクします。本文は`content/projects.json`で管理し、`include_card: false`を指定して既存カードとの重複を防ぎます。画像のファイル名は`static/`、次いで`assets/`から解決できるため、制作当時の移行済み素材をそのまま参照できます。確認済みの資料へのリンクを掲載し、利用できなくなったショップや未確認のデモURLは載せません。

WorksとLabの一覧では、ビルド時に`portfolio-grid`を付け、`static/local-overrides.css`で画像を16:9の共通枠に収めます。画像全体を上下左右の中央に置き、縦横比の異なる素材も高さを揃えます。作品詳細の写真・動画は元の比率を維持します。

CV情報は`content/cv-2026.json`で編集します。ダウンロード用の原本PDFは`static/downloads/Shinnosuke-Komiya-CV-2026.pdf`、表示用CSSは`static/cv.css`です。ビルド時にHome・About・Appearancesへ反映し、PDFを`dist/downloads/`へコピーします。2026年10月8日更新のCVを基準とし、職歴はPDFの期間欄に合わせています。PDF本体は変更していません。

ビルド時に生成する素材対応や移行元HTMLの調査結果は`.local/audit/`に置き、Gitには含めません。旧移行作業の管理画面記録、認証情報、`.wrangler/`、生成済みの`dist/`も管理対象から除いています。

## GitHubでの更新

変更用のブランチで編集し、Pull Requestを作成します。GitHub Actionsは、Pull Requestと`master`へのpushで以下を実行します。

1. 同梱素材からサイトをビルド
2. HTML・CSSの画像やファイル参照、サイトマップ、一覧カードの仮リンク・重複先・リンク先タイトルの整合性を検証
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
- Cascade: <https://www.cham538.com/work/cascade/>
- Epitaph of the Earth: <https://www.cham538.com/work/epitaph-of-the-earth/>
- CV (PDF): <https://www.cham538.com/downloads/Shinnosuke-Komiya-CV-2026.pdf>

## 外部サービス

Adobe Fontsは既存Web Projectの公式埋め込み、Google Fontsは公式CSSを使用しています。フォントファイルはリポジトリに含めません。既存のYouTubeなどの埋め込みは、それぞれのサービスに依存します。問い合わせフォームは移行時の方針に従い、ビルドで除去しています。

画像・作品・ロゴ・外部フォントの権利は、それぞれの権利者に帰属します。旧GatsbyスターターのLICENSEは保持しています。
