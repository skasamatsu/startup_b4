# MD軌跡から拡散係数を計算するチュートリアル

このチュートリアルは、ASEで生成したMD軌跡からMDanalysisを使って拡散係数を計算するための手順です。

## 0. 前提

- 前チュートリアル「ASE + 汎用機械学習ポテンシャル（SevenNet）でMDを体験」を完了している
- `md_ase` ディレクトリに `md_simulation_nvt.extxyz` が存在する
- Miniforgeの `mlip-md` 環境が有効

## 1. 何をやるか

- MDanalysisで軌跡ファイルを読み込む
- Mean Squared Displacement (MSD)を計算
- Einstein関係式から拡散係数Dを算出
- プロット＆数値出力

計算原理:

$$D = \lim_{t \to \infty} \frac{\langle |r(t) - r(0)|^2 \rangle}{6t}$$

## 2. 必要なパッケージをインストール

```bash
conda activate mlip-md
pip install mdanalysis matplotlib
```

## 3. 軌跡ファイルを確認

```bash
cd md_ase
ls -lh md_simulation_nvt.extxyz
```

ファイルがない場合は、前チュートリアルで以下を実行してください。

```bash
ase convert md_simulation_nvt.traj md_simulation_nvt.extxyz
```

## 4. 拡散係数を計算する

### 4.1 基本実行

```bash
python diffusion.py md_simulation_nvt.extxyz
```

初期フレーム（平衡化過程）をスキップしたい場合:

```bash
python diffusion.py md_simulation_nvt.extxyz 100 diffusion
```

- 第1引数: 軌跡ファイル
- 第2引数: スキップするフレーム数（デフォルト0）
- 第3引数: 出力ファイル名プレフィックス（デフォルト"diffusion"）

### 4.2 実行結果

以下が標準出力に表示されます。

```
Loading trajectory: md_simulation_nvt.extxyz
Total frames: 200
Calculating MSD...

--- Diffusion Coefficient ---
D = 1.2345e-05 Angstrom^2/ps
D = 1.2345e-09 cm^2/s
D = 1.2345e-04 x 10^-5 cm^2/s
```

同時に以下のファイルが生成されます。

- `diffusion_msd.png`: MSD vs Time のプロット
- `diffusion_msd.txt`: 数値データ（Time, MSD）

## 5. 出力を確認

### 5.1 プロット確認

`diffusion_msd.png` を開いて、以下を確認:

- MSD が時間とともに増加しているか（拡散している）
- 後半で線形に増加しているか（統計が安定している）
- フィット直線（赤破線）が後半のデータによくフィットしているか

### 5.2 数値の妥当性チェック

拡散係数の目安:

- 液体（室温）: ~1e-5 cm²/s
- ガラス（400K以上）: ~1e-8 - 1e-10 cm²/s
- 固体中の原子拡散: ~1e-12 - 1e-15 cm²/s

計算結果がこの範囲内なら妥当性がありそうです。

## 6. スクリプトの見どころ（`diffusion.py` の読み方）

### 6.1 軌跡読み込み

```python
from MDAnalysis import Universe
u = Universe(traj_file)
```

- MDanalysisで軌跡ファイルを統一的に読み込める
- `.extxyz`, `.traj`, `.dcd` など多くの形式に対応

### 6.2 MSD計算

```python
from MDAnalysis.analysis.msd import EinsteinMSD
msd = EinsteinMSD(u, select='all', msd_type='xyz', start=start_frame)
msd.run()
```

- `select='all'`: 全原子を対象
- `msd_type='xyz'`: 3方向の変位を含める
- `start=start_frame`: 平衡化フレームをスキップ

### 6.3 拡散係数の計算

```python
slope = coeffs[0]  # This is 6*D in Angstrom^2/ps
D_angstrom2_ps = slope / 6.0
D_cm2_s = D_angstrom2_ps * 1e-4  # Convert to SI
```

- MSDが線形な領域で直線フィット
- 傾きは6Dに相当
- 単位変換: Angstrom²/ps → cm²/s

## 7. よくあるつまずき

### 7.1 MDanalysisが見つからない

```bash
pip install mdanalysis
```

で再度インストール確認。

### 7.2 軌跡ファイルが読めない

- `md_simulation_nvt.extxyz` が存在するか確認
- または `ase convert md_simulation_nvt.traj md_simulation_nvt.extxyz` で再生成

### 7.3 拡散係数がおかしく大きい/小さい

- MD時間が短すぎないか（最低でも100 ps）
- 平衡化フレーム数が少なすぎないか（第2引数を増やす）
- 温度が論文値と違っていないか（計算値を確認）

### 7.4 MSDプロットが非線形に見える

- ステップ数を増やして、より長いMDを実行
- フィット領域を手動で調整して再計算（スクリプト内のfit_startを変更）

## 8. 発展例

### 8.1 選択原子のみの拡散係数

`diffusion.py` の `EinsteinMSD` 行を変更:

```python
# 特定の元素のみ（例：Na原子）
msd = EinsteinMSD(u, select='name Na', msd_type='xyz', start=start_frame)
```

### 8.2 温度依存性の計算

異なる温度でMD計算を複数実施し、各Dをプロット:

- Arrhenius プロット: log(D) vs 1/T
- 活性化エネルギー Ea を抽出

### 8.3 論文との比較

計算結果と実験値を比較:

- 単位を確認（cm²/s に統一）
- 温度・物質が同じか確認
- 計算手法の近似度を議論

## 9. 参考資料

- MDanalysis公式: https://www.mdanalysis.org/
- Einstein関係式の説明: 分子動力学の教科書を参照
- ASE軌跡形式: https://wiki.fysik.dtu.dk/ase/ase/io/io.html
