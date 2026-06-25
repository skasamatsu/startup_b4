# MD軌跡から動径分布関数（RDF）を計算するチュートリアル（sova-cui版）

このチュートリアルは、ASEで生成したMD軌跡から
`sova-cui`（import名: `sovapy`）を使って
動径分布関数 $g(r)$ と構造因子 $S(Q)$ を計算し、
第一ピークと配位数まで解析する手順です。
ここでは特に、neutron と X-ray の $S(Q)$ を同時に計算して比較します。

## RDFとは何か（先にここだけ読む）

RDF（Radial Distribution Function, 動径分布関数） $g(r)$ は、
「ある原子から距離 $r$ に、どれくらい原子が存在しやすいか」を表す関数です。

- $g(r)=1$:
	完全ランダムな一様分布（理想気体）と同程度の存在確率
- $g(r)>1$:
	その距離に原子が集まりやすい（構造的に好まれる距離）
- $g(r)<1$:
	その距離に原子が少ない（排除体積や殻間の谷）

直感的には、次のように読めます。

- 第一ピーク位置:
	最近接原子間距離の代表値
- 第一ピーク高さ:
	近接殻の秩序の強さ（高いほど局所秩序が強い傾向）
- 第一極小位置:
	第一近接殻の外側境界の目安
- 第一極小までの積分:
	配位数（平均何個の近接原子を持つか）の推定

RDFそのものの代表的な定義式は次です。

$$
g(r)=\frac{1}{4\pi r^2\rho N}\left\langle\sum_{i=1}^{N}\sum_{j\neq i}\delta \left(r-r_{ij}\right)\right\rangle
$$

ここで、 $N$ は原子数、 $\rho$ は数密度、 $r_{ij}$ は原子 $i,j$ の距離、
$\langle\cdots\rangle$ は時間平均（またはアンサンブル平均）です。

配位数はこの $g(r)$ から計算する派生量で、式は次です。

$$
N(r)=4\pi\rho\int_0^r g(r')r'^2 dr'
$$

ここで、 $\rho$ は数密度（atoms/Å $^3$ ）です。

結晶・液体・ガラスでの典型的な違い:

- 結晶: 鋭いピークが長距離まで続く
- 液体: 第一ピークは明瞭だが、遠距離で徐々に $g(r) \to 1$
- ガラス: 短距離秩序はあるが、長距離秩序は弱い

つまりRDFは、
「最近接距離」「局所秩序」「配位数」を一枚で読み取れる
構造解析の基本ツールです。

## 0. 前提

- 前チュートリアル「ASE + 汎用機械学習ポテンシャル（SevenNet）でMDを体験」を完了している
- `md_ase` ディレクトリに `md_simulation_nvt.extxyz` が存在する
- Miniforgeの `mlip-md` 環境が有効

## 1. 何をやるか

- MD軌跡からフレームをサンプリングする
- サンプリングした各フレームのRDFを計算して平均する
- サンプリングした各フレームの $S(Q)$（neutron / X-ray）を計算して平均する
- 第一ピーク位置と第一極小位置を抽出する
- 第一極小まで積分して配位数（coordination number）を見積もる
- プロットと数値データを保存する

基本式（RDFの定義）:

$$
g(r)=\frac{1}{4\pi r^2\rho N}\left\langle\sum_{i=1}^{N}\sum_{j\neq i}\delta \left(r-r_{ij}\right)\right\rangle
$$

このチュートリアルで配位数を見積もるときは、次の積分式を使います。

$$
N(r)=4\pi\rho\int_0^r g(r')r'^2\,dr'
$$

ここで、$\rho$ は数密度（atoms/Å$^3$）です。

## 2. 必要なパッケージをインストール

```bash
conda activate mlip-md
pip install sovapy matplotlib numpy
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

## 4. RDFを計算・可視化・解析する

`rdf_sova.py` は `.traj`（または多フレームextxyz）を直接読み、
指定した間隔でフレームをサンプリングして平均RDFを計算します。
同時に、neutron / X-ray の $S(Q)$ も平均します。

### 4.1 sova-cuiで平均RDF解析を実行

このリポジトリに追加した `rdf_sova.py` を実行します。

```bash
python rdf_sova.py md_simulation_nvt.traj --output-prefix rdf_sova --sample-start 200 --sample-step 10
```

主なオプション:

- `--dr`: RDFのビン幅（Å）
- `--dq`: S(Q)のQビン幅（Å$^{-1}$）
- `--qmin`: S(Q)計算の最小Q（Å$^{-1}$）
- `--qmax`: S(Q)計算の最大Q（Å$^{-1}$）
- `--sample-start`: サンプリング開始フレーム（平衡化前を除外）
- `--sample-stop`: サンプリング終了フレーム（`-1` で末尾まで）
- `--sample-step`: サンプリング間隔（例: 10なら10フレームごと）
- `--max-samples`: 使うサンプルの上限
- `--peak-rmin`: 第一ピーク探索時に無視する低r領域
- `--min-window`: 第一ピーク後の極小探索範囲（Å）

## 5. 出力を確認

生成されるファイル:

- `rdf_sova.png`: RDFプロット
- `rdf_sova.txt`: 列データ（`r`, `g(r)`）
- `rdf_sova_sq.png`: `S(Q)_neutron` と `S(Q)_xray` の比較プロット
- `rdf_sova_sq.txt`: 列データ（`Q`, `S(Q)_neutron`, `S(Q)_xray`）
- `rdf_sova_summary.txt`: 第一ピーク・第一極小・配位数の要約

確認ポイント:

- 第一ピークの位置が既知の最近接距離と整合するか
- 第一極小までの配位数が期待値（例: 結晶構造の理論配位数）に近いか
- 系が液体ならピークが幅広く、結晶ならピークが鋭くなるか
- `S(Q)_neutron` と `S(Q)_xray` のピーク位置・強度差が妥当か
- S(Q) の低Q側で不自然な発散がないか
- 結晶系では鋭いブラッグピーク、非晶質では幅広いピークになるか

## 6. よくあるつまずき

### 6.1 `ImportError: No module named sovapy`

```bash
pip install sovapy
```

### 6.2 セル体積関連エラー

- RDFと配位数解析は、周期セル情報が必要です
- `.extxyz` 変換時にセル情報が保持されているか確認してください
- `.traj` を使う場合は、元のMD計算でセル情報が正しく保存されているか確認してください

### 6.3 第一ピーク検出が不安定

- `valid = np.where(r > 0.8)[0]` の閾値を調整
- `window = int(3.0 / dr)` を増減して、極小探索範囲を調整
- 統計が悪い場合は `--sample-step` を小さくするか `--max-samples` を増やす

## 7. 発展例

### 7.1 元素ごとの部分RDF

複数元素系では、`sovapy.computation.structure_factor` の
`atom_pair_hist` と `pair_dist_func` から部分RDFを扱えます。

```python
from sovapy.computation.structure_factor import atom_pair_hist, pair_dist_func
r, hist = atom_pair_hist(atoms, dr=0.05)
partial_gr = pair_dist_func(atoms, r, hist)
```

### 7.2 温度依存性

異なる温度の軌跡で `rdf_sova.png` を比較し、ピーク高さ・幅・位置の変化を確認します。

### 7.3 時間窓RDF

軌跡を前半/後半に分けて別々にRDFを計算し、構造緩和の進行を評価します。

## 8. 参考資料

- sova-cui: https://github.com/MotokiShiga/sova-cui
- ASE I/O: https://wiki.fysik.dtu.dk/ase/ase/io/io.html
- RDFの基礎: 計算物質科学・液体論の教科書を参照
