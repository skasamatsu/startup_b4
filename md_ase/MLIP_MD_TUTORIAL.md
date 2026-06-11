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

## 7. 結果確認

- OVITOで `md_simulation_nvt.traj` を開いて原子運動を確認
- 温度が目標値（例: 300 K）近傍で推移するか確認
- エネルギーが発散していないか確認

## 8. `md.py` の見どころ（読み方）

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
