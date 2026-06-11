# ASE + 汎用機械学習ポテンシャル (SevenNet) でMDを体験するチュートリアル

このチュートリアルは、`md.py` の実装をベースにして、
「ASEでNVT-Langevin MDを回し、軌道ファイルを保存して確認する」までを最短で体験するための手順です。

## 0. WSLから開始（cloneして作業ディレクトリへ）

まずUbuntu（WSL）を起動して、以下を実行します。

```bash
sudo apt update
sudo apt install -y git

mkdir -p ~/projects
cd ~/projects
git clone https://github.com/skasamatsu/startup_b4.git
cd startup_b4/md_ase
```

すでにclone済みの場合は、最後の `cd startup_b4/md_ase` だけでOKです。

## 1. 何をやるか

- ASEで原子構造を読み込む
- SevenNetの汎用MLポテンシャル（`7net-omat`）を計算器として設定
- NVT（Langevin）でMDを実行
- エネルギー・温度をログ出力
- `.traj` を保存して可視化（OVITOなど）

## 2. 前提

- OS: Ubuntu/WSLを想定
- Python環境: Miniforge/conda推奨
- GPUがない場合はCPU実行でOK

### 2.1 PyTorch導入の前提（重要）

SevenNetは内部でPyTorchを利用します。
そのため、環境構築では「先にPyTorchを入れて、動作確認してから SevenNet を入れる」とトラブルが減ります。

- CPU実行: 最も簡単。まずはここから開始推奨
- GPU実行: NVIDIAドライバとCUDA対応の確認が必要

### 2.2 GPU利用前チェック

GPUを使いたい場合、ホストWindows側で以下を先に確認してください。

- NVIDIAドライバが入っている
- `nvidia-smi` が実行できる
- WSL2でGPU計算が有効になっている

WSL内でも以下で確認できます。

```bash
nvidia-smi
```

ここでGPU情報が出ない場合は、先にCPU版PyTorchで進めてください。

## 3. 環境構築

### 3.1 conda環境作成

```bash
conda create -n mlip-md python=3.11 -y
conda activate mlip-md
pip install --upgrade pip
```

### 3.2 PyTorchを先に導入

まずはCPU版で動かすのが安全です。

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

GPU版を使う場合は、PyTorch公式のインストール案内で
自分の環境に合うコマンドを選んで実行してください。

- 公式: https://pytorch.org/get-started/locally/

例（CUDA 12.1向けの一例）:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### 3.3 PyTorch動作確認

```bash
python - << 'PY'
import torch
print('torch:', torch.__version__)
print('cuda available:', torch.cuda.is_available())
if torch.cuda.is_available():
  print('gpu:', torch.cuda.get_device_name(0))
PY
```

- CPU運用なら `cuda available: False` でも問題ありません
- GPU運用で `False` の場合は、CPUに切り替えるかCUDA周りを再確認してください

### 3.4 ASE / SevenNet導入

```bash
pip install ase sevenn
```

## 4. 入力構造ファイルを用意する

`md.py` はデフォルトで `se2cl2_60A.xyz` を読み込みます。
手元にこのファイルがない場合は、まず練習用構造を作ります。

### 4.1 練習用のSi構造を作る

`md_ase` ディレクトリで以下を実行:

```bash
python - << 'PY'
from ase.build import bulk
atoms = bulk('Si', 'diamond', a=5.43).repeat((3, 3, 3))
atoms.write('si_3x3x3.xyz')
print('wrote si_3x3x3.xyz with', len(atoms), 'atoms')
PY
```

## 5. `md.py` を最小変更して実行する

`md.py` の以下3点をまず変更するのがおすすめです。

1. 入力ファイル名
2. デバイス（CPU/GPU）
3. ステップ数（最初は短く）

### 5.1 変更例

```python
# before
atoms = read("se2cl2_60A.xyz")
device = "cuda"
...
dyn.run(1e5)

# after (tutorial向け)
atoms = read("si_3x3x3.xyz")
device = "cpu"   # GPUが使えるなら "cuda"
...
dyn.run(2000)
```

> `dyn.run(1e5)` は長時間になりやすいので、最初は `1000-5000` ステップ程度で確認すると安全です。

## 6. 実行

```bash
cd md_ase
python md.py
```

100ステップごとに、`md.py` の `print_energy()` が以下のようなログを出します。

- Step
- Temp (K)
- Epot / Ekin / Etot

同時に `md_simulation_nvt.traj` が保存されます。

## 7. 可視化まで実施する

### 7.1 まずファイル生成を確認

```bash
ls -lh md_simulation_nvt.traj
```

ファイルサイズが0でなければ、軌道データは書き出されています。

### 7.1.5 trajをexyzに変換（OVITOフリー版対応）

OVITOのフリー版は`.traj`形式に対応していません。
以下で`.extxyz`形式に変換してから開いてください。

```bash
ase convert md_simulation_nvt.traj md_simulation_nvt.extxyz
```

この後の手順では `md_simulation_nvt.extxyz` を OVITOで開いてください。

### 7.2 OVITOで可視化（推奨）

1. OVITOを起動
2. File -> Load File で `md_simulation_nvt.extxyz` を選択
3. 画面下の再生ボタンで時間発展を確認
4. 表示が重い場合は表示品質を一段下げる

見やすくする設定例:

- Particlesの表示サイズを少し上げる
- Color coding modifierを追加して元素ごとに色分け
- Simulation cellを表示して、境界条件の感覚をつかむ

### 7.3 画像・動画の書き出し

- 静止画: Viewport右クリックまたはRenderからPNG出力
- 動画: Render -> Movie でmp4を書き出し

最初は短いフレーム範囲（例: 0-200）で試すと失敗しにくいです。

### 7.4 ASE標準ビューアで簡易確認（任意）

```bash
python -m ase gui md_simulation_nvt.traj
```

- 再生ボタンで軌道確認
- 軽い確認には便利、発表用の図や動画はOVITOの方が作りやすいです

### 7.5 チェックポイント

- 温度が目標値（例: 300 K）近傍で推移している
- エネルギーが急激に発散していない
- 原子が不自然に飛び散っていない

## 8. `md.py` の見どころ（読み方）

### 8.0 コード全体の流れ（概要）

`md.py` は大きく次の順番で処理しています。

1. 構造読み込み
2. MLポテンシャル（SevenNet）を計算器として設定
3. 初速度を乱数で与えてMD初期化
4. Langevin積分器（NVT）を作成
5. ログ出力関数を `attach` して定期表示
6. `Trajectory` を `attach` して定期保存
7. `dyn.run(...)` で本計算を実行

この流れを覚えると、別の系に差し替えるときも
「入力構造・温度・ステップ数・device」を変更するだけで再利用しやすくなります。

### 8.1 主要部分の見どころ

- `SevenNetCalculator(model='7net-omat', device=device)`
  - 汎用MLポテンシャルの指定
- `Langevin(atoms, timestep, temperature, friction=0.2)`
  - NVT-Langevinの設定
- `dyn.attach(print_energy, interval=100)`
  - 進行ログ出力
- `Trajectory('md_simulation_nvt.traj', 'w', atoms)`
  - 軌道ファイル保存

## 9. よくあるつまずき

### 9.1 `FileNotFoundError: se2cl2_60A.xyz`

- 入力構造ファイルが存在しません
- 4章の手順で `si_3x3x3.xyz` を作って、`md.py` の読み込み先を変更してください

### 9.2 CUDA関連エラー

- `device = "cpu"` に変更して再実行
- GPU利用時はPyTorch/CUDAの対応バージョンを確認

### 9.3 計算が遅い

- 原子数を減らす（小さいセルで試す）
- ステップ数を減らす（例: 1000）
- intervalを大きくしてI/O頻度を下げる

## 10. 次の発展

- `temperature` を変えて温度依存性を見る
- `friction` を変えて熱浴の効き方を比較
- タイムステップを変更して安定性を比較
- 自分の系（CIF/XYZ）に差し替えて同じ手順を実行
