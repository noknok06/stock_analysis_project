# 🧾 コーディング規約

## 📁 一般原則

**DRY原則（Don't Repeat Yourself）**を守る。
→ 同じコード・ロジック・CSSは複製せず共通化する。（重要）

🖼️ HTML
セマンティックなタグを使う（<header>, <main>, <section>, <footer> など）。

🎨 CSS / TailwindCSS

## 共通原則

クラスのコピペを禁止：共通スタイルは共通クラスやCSS変数で管理。

カスタムCSSを使う場合は /styles ディレクトリにまとめ、再利用可能にする。

インラインスタイルは禁止。

同じスタイルを複数箇所に書く場合は @apply を使って共通化。

レスポンシブ対応は sm: md: lg: を適切に使う。

## 🧠 JavaScript

関数は1機能に限定。長くなりすぎたら分割。

変数名・関数名は意味のある英単語で命名（例：fetchUserData, isAuthenticated）。

varは禁止。必ず const or let。

非同期処理は async/await を使い、try/catch でエラーハンドリング。

マジックナンバーは禁止。定数で定義。

## 🐍 Python（Django等）

ビュー関数は短く、ロジックはサービス層やフォームクラスなどへ分離。

バリデーションやDBアクセスは必ず例外処理で囲む。

共通処理はutils.pyやmixins.pyなどに切り出す
