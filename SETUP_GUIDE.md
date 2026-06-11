# 計算物質科学研究室 PC環境セットアップガイド

このドキュメントは、研究室に配属された学生が各自のPCで解析・可視化・開発を進めるための標準セットアップ手順です。

## 0. 対象とゴール

- 対象: 主にWindows 11ユーザー（WSL2を利用）
- ゴール:
  - WSL2 (Ubuntu) の導入
  - VS Code + Remote Development 環境
  - Python実行環境（Miniforge推奨）
  - 結晶構造可視化: VESTA
  - 原子シミュレーション可視化: OVITO

---

## 1. まず最初に確認すること

1. Windows Updateを最新化して再起動
2. Cドライブ空き容量を **最低30GB以上** 確保
3. 管理者権限があるアカウントで作業
4. 学内ネットワーク制限がある場合は、事前にプロキシ情報を確認

---

## 2. WSL2 (Ubuntu) のインストール

まず、この章ではコマンドを実行する場所が2つあります。

- Windows側: PowerShell（管理者）
- Linux側: Ubuntuターミナル（WSL内）

### 2.1 Windows側: PowerShell (管理者) で実行

```powershell
wsl --install
```

- 実行後、再起動を求められたら再起動
- 初回起動時にLinuxユーザー名・パスワードを設定

### 2.2 Windows側: WSLバージョン確認

```powershell
wsl -l -v
```

- `VERSION` が `2` であることを確認

### 2.3 Ubuntuを起動

- Windowsのスタートメニューから `Ubuntu` を起動
- もしくはPowerShellで `wsl` を実行してUbuntuシェルに入る
- プロンプトが `user@PCNAME:~$` のような表示になればUbuntu側です

### 2.4 Ubuntu側: 初期更新

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y build-essential curl wget unzip zip
```

### 2.5 推奨設定

WSL内ホーム配下にプロジェクトを置くと高速です。

- 推奨: `~/projects/your_repo`
- 非推奨: `/mnt/c/...` で大規模I/Oを頻繁に行う運用

---

## 3. VS Code の導入

### 3.1 Windows側にVS Codeをインストール

- 公式: https://code.visualstudio.com/

### 3.2 推奨拡張機能

VS Codeで以下を導入:

- Remote Development (ms-vscode-remote.vscode-remote-extensionpack)
- Python (ms-python.python)
- Jupyter (ms-toolsai.jupyter)
- Markdown All in One (yzhang.markdown-all-in-one) ※任意

### 3.3 WSLに接続

1. VS Code左下の緑アイコンをクリック
2. `Connect to WSL` を選択
3. WSL側の作業ディレクトリを開く

---

## 4. Python環境（必須、Miniforge推奨）

研究室では、Miniforge + conda環境を標準運用として推奨します。

### 4.0 初学者向け: なぜ環境を分けるのか

同じPCで複数テーマを進めると、必要なパッケージのバージョンが衝突しやすくなります。
環境を分けると、次のメリットがあります。

- あるテーマで更新したパッケージが、別テーマを壊しにくい
- 「この計算はどのライブラリ構成で動いたか」を再現しやすい
- トラブル時に環境ごと作り直せるため、復旧が速い

最初は「テーマごとに1環境」を目安にすると運用しやすいです。

参考資料（公式）:

- conda environment管理: https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html
- VS Code Python environments: https://code.visualstudio.com/docs/python/environments
- conda-forge（パッケージ検索）: https://conda-forge.org/

### 4.1 Miniforge導入（WSL）

```bash
cd ~
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh
```

- インストーラで初期化設定を有効化した場合、ターミナル再起動後に `conda` が使えます

### 4.2 conda初期確認

```bash
conda --version
python --version
```

### 4.3 研究用環境の作成例

```bash
conda create -n mat-sci python=3.11 -y
conda activate mat-sci
conda install -c conda-forge numpy scipy matplotlib pandas ase pymatgen -y
conda install -c conda-forge jupyterlab -y
```

> 研究テーマに応じて追加（例: scikit-learn, seaborn, spglib など）

### 4.4 VS CodeでInterpreterを設定

- 先に拡張機能 `Python (ms-python.python)` がインストール済みか確認
- 未導入なら、Extensionsで `Python` を検索してインストール
- WSLウィンドウ側にも拡張機能のインストール確認（`Install in WSL` が必要な場合あり）
- `Ctrl + Shift + P` → `Python: Select Interpreter`
- `Python 3.11 ('mat-sci': conda)` のようなconda環境を選択

うまくいかない場合:

- `Python: Select Interpreter` がコマンド一覧に出ないときは、ほぼ拡張機能未導入です
- インストール後にVS Codeウィンドウを再読み込み（`Developer: Reload Window`）

### 4.5 環境の使い分け指針

- テーマ・プロジェクトごとにconda環境を分ける
- 迷ったらまず `mat-sci` を作成し、必要に応じて追加環境を作る
- パッケージ構成を共有する場合は `conda env export > environment.yml` を使う

---

## 6. VESTA のセットアップ

VESTAはWindowsアプリとして利用するのが簡単です。

### 6.0 CIFファイルはどこから取得するか

研究で使う結晶構造（CIF）は、まず以下の公開データベースから取得できます。Materials Projectは網羅計算で構成されたデータベースなので、ときどきおかしな結果が混ざっています。CODはそれぞれの構造に原著論文が紐付いているので比較的信頼性は高いです。

- Materials Project: https://materialsproject.org/
- Crystallography Open Database (COD): https://www.crystallography.net/cod/
- NIST、ICSD、CSD など契約型DB（大学契約がある場合）

運用の目安:

- 論文再現では、論文中に明記されたデータベースとIDを優先
- 取得元URL、material ID、取得日をノートに記録
- 利用規約・引用要件を確認（DBごとに異なる）

最初の練習用としては、CODまたはMaterials Projectから単純な結晶（Si, NaCl, Al2O3など）を1件取得し、VESTAで表示確認するのがおすすめです。

### 6.1 インストール

- 公式配布元から最新版をダウンロードしてインストール
- 参考: https://jp-minerals.org/vesta/en/

### 6.2 初期確認

1. CIFファイルを開く
2. 回転・拡大縮小が可能か確認
3. 画像保存（PNG）できるか確認
4. 単位胞パラメータ、元素、空間群が取得元情報と一致するか確認

### 6.3 運用のポイント

- 構造ファイルはフォルダを分けて整理する（raw/processed/figures など）
- 図出力設定（フォント・背景・線幅）を研究室内で統一すると便利

---

## 7. OVITO のセットアップ

### 7.1 インストール

- 公式: https://www.ovito.org/
- Windows版をインストール

### 7.2 初期確認

1. サンプルまたは手元の `dump`, `xyz`, `lammps` 系ファイルを開く
2. `Modifiers` を1つ追加（例: `Common Neighbor Analysis`）
3. 画像または動画を書き出せるか確認

### 7.3 Python連携（任意）

OVITO Pro/環境に応じてPythonスクリプト機能を使う場合:

- Python APIドキュメント: https://www.ovito.org/docs/current/python/

---

## 8. 研究室標準ディレクトリ構成（例）

```text
~/projects/
  lab-common/         # 共通スクリプト
  theme-A/
    data/             # 生データ
    src/              # 解析コード
    notebooks/        # 検証ノート
    results/          # 出力図・表
    README.md
```

---

## 9. 動作確認チェックリスト

以下をすべて満たせば、基本セットアップは完了です。

- [ ] WSL Ubuntuが起動する
- [ ] `python --version` が表示される
- [ ] VS CodeがWSL接続でフォルダを開ける
- [ ] VS Codeで仮想環境Interpreterが選択できる
- [ ] Jupyterノートブックを1つ実行できる
- [ ] VESTAでCIFを開ける
- [ ] OVITOでシミュレーション結果を開ける

---

## 10. よくあるトラブルと対処

### 10.1 `wsl --install` が失敗する

- BIOSで仮想化支援機能（Intel VT-x / AMD-V）を有効化
- Windows機能で「仮想マシンプラットフォーム」「Linux用Windowsサブシステム」を有効化

### 10.2 VS CodeでWSL接続が不安定

- VS CodeとRemote拡張を最新化
- `wsl --shutdown` 後に再起動

### 10.3 pip installで権限エラー

- `conda activate mat-sci` などで対象環境を有効化してから再実行
- `which python` と `which pip` で conda 環境配下を指しているか確認

### 10.4 企業/学内ネットワークでpipが失敗

- プロキシ設定を `pip config` または環境変数に設定
- 教員・先輩に研究室標準の設定値を確認

---

## 11. 研究室に提出すると良い情報

セットアップ完了後、以下を1つのテキストにまとめて教員・先輩へ共有するとサポートが早くなります。

- OSバージョン
- `wsl -l -v` の結果
- `python --version` の結果
- VS Codeバージョン
- VESTA/OVITOバージョン
- 発生したエラー（全文）

---

## 12. 最小コマンド集（コピペ用）

```bash
# WSL Ubuntu 初期化
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential curl wget unzip zip

# Miniforge導入
cd ~
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh

# 研究用conda環境
conda create -n mat-sci python=3.11 -y
conda activate mat-sci
conda install -c conda-forge numpy scipy matplotlib pandas ase pymatgen jupyterlab -y
```

以上で、計算物質科学研究室での基本的なPC環境構築は完了です。
