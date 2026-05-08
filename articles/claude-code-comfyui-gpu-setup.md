---
title: "ComfyUIを動かすためのGPU準備＆インストールガイド"
emoji: "🖥️"
type: "tech"
topics: ["comfyui", "gpu", "python", "ubuntu", "windows"]
published: false
---

![GPUでComfyUIを動かす準備のアイキャッチ](/images/claude-code-comfyui-skill/image_gpu_comfyui_setup_eyecatch.png)

---

## この記事でやること

[第1回](https://zenn.dev/miraclest/articles/claude-code-comfyui-skill-intro)では、Claude Code の Skill から自宅 GPU サーバーの ComfyUI を叩く全体像を見ました。
「自分のマシンに GPU が刺さっているのに、なぜ他人の GPU に金を払うのか」問題ですね。はい、そこに刺さった人向けの続きです。

今回は**実際に手を動かします**。ゴールは「ComfyUI が起動し、ブラウザから触れる」ところまで。
画像を1枚出すにはモデルファイルが必要なので、最低限の置き場所と次回で使うモデル名まで確認します。

ここでやるのは、まだ Claude Code Skill の本体ではありません。まずは生成エンジン側、つまり ComfyUI をちゃんと起動できる状態にします。
土台がグラついていると、あとで Skill 側を疑う羽目になります。だいたいこういう時、悪いのは Skill ではなく CUDA かパスかモデル配置です。つらい。

コマンドはコピペで進められるようにしています。ただし GPU 周りは環境差が出ます。
詰まったら「自分の環境だけ変なのでは」と思い込まず、エラーメッセージを見て一個ずつ潰しましょう。変なのはだいたい環境です。

今回つくる土台を図にすると、だいたいこうです。
GPU マシン上で ComfyUI を起動し、ブラウザや後続の Claude Code Skill から叩ける状態にしていきます。

![GPUマシン上のComfyUIをブラウザやClaude Code Skillから使う構成図](/images/claude-code-comfyui-skill/image_gpu_comfyui_architecture.png)

---

## GPU選定 — 2026年5月時点、だいたい地獄

### 結論から

まず結論です。2026年5月時点のざっくりした目安として見てください。
GPU 価格は普通に動きます。昨日の正解が今日の正解とは限らないので、最後は店頭価格と中古相場を見て判断です。めんどくさいですね、ほんとに。

| 予算感 | おすすめ | VRAM | 入手方法・見解 |
|---|---|---|---|
| 3〜4万円 | **RTX 3060 12GB（中古）** | 12GB | メルカリ・ヤフオク・中古PCショップ |
| 〜6万円 | RTX 5060 | 8GB | 新世代だが8GB問題 |
| 9万円〜 | **RTX 5060 Ti 16GB（新品の現実ライン）** | 16GB | 予算があるならこれ |
| 12万円〜 | RTX 4070TiSuper / RTX 5070Ti系 | 16GB | パワーはあるが中古も高い |

この表だけ見ると「じゃあ RTX 3060 12GB でいいじゃん」となります。
なりますが、問題はそこからです。人気があるものはだいたい市場から消える。世の中、そういう雑なバランスでできています。

### RTX 3060 12GB — 2026年でもまだ最適解

SDXL や Illustrious 系を普通に触るなら、**VRAM 12GB**がほぼ必須ラインです。
2026年5月時点で12GBを安めに手に入れるなら、中古の RTX 3060 12GB がまだ現実的な候補になります。
相場はだいたい3〜4万円台。3万円を切るものは掘り出し物か、状態確認がかなり大事な個体だと思って見た方が安全です。

ただし「現実的」と「楽に買える」は別です。
同じ RTX 3060 でも 8GB 版が混じります。商品名だけ見て勢いで買うと、あとで VRAM 表記を見て真顔になります。
買う前に **12GB と明記されているか** は必ず確認してください。

**中古で買うときの注意：**

- マイニング酷使品を避ける（出品者の履歴を確認）
- 「24時間稼働」「マイニング使用」の記載があるものはスルー
- 購入後はまず軽く負荷をかけて、異音・高温・突然の再起動がないか確認

中古 GPU は「安いから勝ち」ではありません。
ファンがうるさい、温度が高い、負荷をかけると落ちる、みたいな個体を引くと、節約した数千円が一瞬で精神の赤字になります。
出品写真、型番、補助電源、保証の有無はちゃんと見ましょう。
Windows なら GPU-Z などのツールで温度を見られますが、初心者は「負荷をかけたらすぐ落ちる」「ファンが異常にうるさい」「温度が90度台に張り付く」あたりを危険サインとして見れば十分です。

### 8GBでも動く？

動きます。ただし：

- 解像度が制限される（1024x1024がギリギリ、場合によってOut of Memoryで動かず…）
- バッチサイズ1固定
- LoRAを重ねると厳しくなる

「とりあえず試したい」なら8GBでも全然OK。
ですが、「快適にやりたい」「LoRA複数使いたい」「高解像度を出したい」、多分そうなるので**12GB**以上を狙ってください。

8GB は「遊べない」ではなく「我慢の場面が増える」です。
設定を詰めれば動きます。でも、生成のたびに解像度やメモリを気にするのは、だんだん生活の質に効いてきます。
AI 画像生成を日常的に回すつもりなら、VRAM は正義です。これは雑な精神論ではなく、真理ですね。

---

## ComfyUIインストール — 3パターン

ここからは、入口を3つに分けます。
手元の PC で試す、Linux サーバーとして置く、Proxmox の VM に載せる、のどれを選ぶかで作業量が変わります。

![Windows、Ubuntu、ProxmoxでComfyUIを導入する3つのルート](/images/claude-code-comfyui-skill/image_gpu_comfyui_setup_routes.png)

### パターンA: Windows（一番手軽）

ゲーミングPCで試すならこれが最短です。
普段使いの Windows に入れて、ブラウザで ComfyUI を開く。最初はこれで十分です。

「専用サーバーじゃないとダメ？」と思うかもしれませんが、そんなことはありません。
第1回の完成形は自宅 GPU サーバー構成でしたが、入口は Windows でも大丈夫です。いきなり逸般の誤家庭を完成させようとすると、休日が溶けます。

#### Windowsの前提ツール（入っていれば飛ばしてOK）

PowerShell を開いて、まず Git と Python が入っているか確認します。

```powershell
git --version
python --version
```

どちらもバージョンが表示されるなら、この枠は飛ばして大丈夫です。
たとえば、こう出ればOKです。

```powershell
PS C:\Users\user\Desktop> git --version
git version 2.53.0.windows.2
PS C:\Users\user\Desktop> python --version
Python 3.12.4
```

`git` や `python` が見つからない場合は、PowerShell で次を実行します。

```powershell
winget install --id Git.Git -e --source winget
winget install --id Python.Python.3.13 -e --source winget
```

インストール後は PowerShell を一度閉じて、開き直してください。
それでも `python --version` が通らない場合は、[python.org](https://www.python.org/downloads/) から Python 3.13 を入れます。
うまくいかない場合は Python 3.12 でも構いません。

#### ComfyUIを入れる

```powershell
# 1. ComfyUIをクローン
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# 2. 仮想環境を作成
python -m venv venv
.\venv\Scripts\activate

# 3. PyTorch（CUDA版）をインストール
#    2026年5月時点のComfyUI公式案内はCUDA 13.0系
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu130

# 4. ComfyUIの依存関係をインストール
pip install -r requirements.txt

# 5. 起動
python main.py
```

ブラウザで `http://localhost:8188` を開けばComfyUIのGUIが表示されます。

ここで GUI が出たら、まず勝ちです。
まだモデルもワークフローも最低限で構いません。最初の目的は「GPU で ComfyUI が起動する」ことです。
いきなり理想の絵を出そうとすると、モデル、LoRA、プロンプト、VAE、全部が一斉に殴ってきます。順番にやりましょう。

### パターンB: Ubuntu / Linux

サーバー用途ならこちら。常時起動・API運用に向いています。
Claude Code から別マシンの ComfyUI を叩くなら、最終的にはこの形がかなり扱いやすいです。
SSH で入れる、systemd で常駐できる、LAN 内 API として置ける。地味ですが強い。

#### Ubuntuの前提ツール（入っていれば飛ばしてOK）

まず Git と Python が入っているか確認します。

```bash
git --version
python3 --version
```

どちらもバージョンが表示されるなら、この枠は飛ばして大丈夫です。
たとえば、こう出ればOKです。

```bash
user@ubuntu:~/atelier/rin$ git --version
git version 2.53.0
user@ubuntu:~/atelier/rin$ python3 --version
Python 3.12.4
```

入っていない場合、または `python3 -m venv` で止まる場合は、先に不足しがちなものを入れます。

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv
```

Ubuntu 24.04 で Python 3.12 を使っている場合、環境によっては追加でこれが必要です。

```bash
sudo apt install -y python3.12-venv
```

#### ComfyUIを入れる

```bash
# 1. NVIDIA ドライバー確認
nvidia-smi
# → ドライバーが入っていなければ先にインストール

# 2. ComfyUIをクローン
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# 3. 仮想環境
python3 -m venv venv
source venv/bin/activate

# 4. PyTorch（CUDA版）
#    2026年5月時点のComfyUI公式案内はCUDA 13.0系
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu130

# 5. 依存関係
pip install -r requirements.txt

# 6. 起動（LAN内からアクセスできるように）
python main.py --listen 0.0.0.0 --port 8188
```

`python3 -m venv venv` で `ensurepip is not available` と出た場合は、前提ツールの `python3-venv` が入っていません。
Ubuntu 24.04 で Python 3.12 を使っているなら、前の枠にある `python3.12-venv` も確認してください。

`nvidia-smi` は、Ubuntu から NVIDIA GPU が見えているかを確認するコマンドです。
GPU 名やドライバーの表が表示されればOKです。
`command not found` やエラーになる場合は、ComfyUI 以前に NVIDIA ドライバーが入っていない、または GPU が OS から見えていない状態です。
ここで先へ進むと、あとで PyTorch や ComfyUI 側のエラーに見えて混乱します。まず OS から GPU が見えている状態にしてください。

CUDA 13.0 系の PyTorch で起動しない場合は、NVIDIA ドライバーが古い可能性があります。
ただ、最初から CUDA の種類を細かく選ぼうとするとかなり大変です。
まずはこの記事のコマンドのまま進めて、失敗したら ComfyUI の起動ログを AI に貼って「NVIDIA ドライバーと PyTorch のCUDA版が合っているか見て」と聞くのが現実的です。

> **ポイント**: `--listen 0.0.0.0` を付けないとlocalhostからしかアクセスできません。
> Claude Codeから別マシンのComfyUIを叩く場合は必須。

`--listen 0.0.0.0` は、「このPC自身だけでなく、同じLAN内の別PCのブラウザからも開けるようにする」指定です。
自宅の同じネットワーク内で使うための設定だと思ってください。
逆に、インターネットへ直接公開するサーバーで雑に `0.0.0.0` を開けるのはやめましょう。
この記事では LAN 内の自宅環境を前提にしています。外から誰でもアクセスできるようにする話ではありません。
自宅 LAN でも、必要ならファイアウォールや VPN 側でアクセス元を絞ってください。

#### systemdで常駐化（コピペ用）

ComfyUI ディレクトリの中で、まずユーザー名と作業ディレクトリを確認します。

```bash
whoami
pwd
```

たとえば、こう出ます。

```bash
user@ubuntu:~/work$ whoami
user
user@ubuntu:~/work$ pwd
/home/user/work
```

そのうえで、次のコマンドを実行します。

```bash
COMFY_USER=$(whoami)
COMFY_DIR=$(pwd)

sudo tee /etc/systemd/system/comfyui.service << EOF
[Unit]
Description=ComfyUI Server
After=network.target

[Service]
Type=simple
User=${COMFY_USER}
WorkingDirectory=${COMFY_DIR}
ExecStart=${COMFY_DIR}/venv/bin/python main.py --listen 0.0.0.0 --port 8188
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now comfyui
sudo systemctl status comfyui --no-pager
```

これで OS 起動時に自動で ComfyUI が立ち上がります。
直接 `YOUR_USERNAME` を書く形にすると置換ミスで止まりやすいので、ここでは `whoami` と `pwd` から service ファイルを作っています。

起動できたか確認する時は、まずこれを実行します。

```bash
sudo systemctl status comfyui --no-pager
```

画面の中に `active (running)` と出ていれば、ひとまず起動しています。
`failed` や `error` が出ている場合は、次のコマンドで直近のログを取り出します。

```bash
journalctl -u comfyui -n 100 --no-pager
```

この出力は、慣れていないとかなり読みにくいです。
自分で全部読もうとしなくて大丈夫です。エラー部分を丸ごと AI に投げるなら、たとえば次のように聞くと原因を探しやすくなります。

```text
UbuntuでComfyUIをsystemd起動しようとしています。
`sudo systemctl status comfyui --no-pager` と
`journalctl -u comfyui -n 100 --no-pager` の結果は以下です。
どこが原因で起動に失敗しているか、初心者向けに確認してください。

（ここに出力を貼る）
```

よくある原因は、`WorkingDirectory` のパス違い、`ExecStart` の Python パス違い、仮想環境を作っていない、依存関係のインストール漏れです。

### パターンC: Proxmox + GPUパススルー

逸般の誤家庭スタイル。VM内でGPUを専有して使う構成。
ここでいう専有は、「GPUを便利に共有できる」という意味ではありません。
特定の VM に GPU を丸ごと割り当てる、という意味です。

メリットは、ComfyUI 用 VM が GPU を安定して使えることです。
他の VM やホスト側の処理に GPU を奪われにくく、CUDA / NVIDIA ドライバー / ComfyUI の環境をその VM の中に閉じ込められます。
「この VM は画像生成専用」と決めてしまえるなら、運用はかなり見通しが良くなります。

一方で、デメリットも大きいです。
パススルーした GPU は、基本的にホストの画面表示や他の VM からは使えません。
複数の VM で気軽に使い回すものではなく、設定も IOMMU グループ、BIOS、起動順、ドライバー周りでシビアです。
GPU が1枚しかない環境では、むしろ使い勝手が悪くなることもあります。

便利ですが、最初の1枚を出すために選ぶルートとしては重めです。
すでに Proxmox があり、GPU パススルーにも抵抗がない人向け。ここから入ると「画像生成したいだけなのに、なぜ私は IOMMU と向き合っているのか」という顔になります。

```
Proxmox ホスト
├── VM: ubuntu-comfyui (GPU パススルー)
│   └── ComfyUI Server (常駐)
├── VM: 他の用途
└── CT: 他の用途
```

GPUパススルーの手順は環境依存が大きいため、ポイントだけ：

1. **IOMMU有効化**: BIOS + GRUB設定（`intel_iommu=on` or `amd_iommu=on`）
2. **vfio-pci**: パススルー対象GPUをvfioドライバーにバインド
3. **VM作成**: Machine Type = q35, BIOS = OVMF (UEFI)
4. **PCI Device追加**: GPU + Audio デバイスをパススルー
5. **VM内**: NVIDIAドライバーインストール → パターンBと同じ手順

> 筆者はこの構成で運用しています。
> ComfyUI専用VMを常時起動、LAN内のどこからでもAPIで叩ける状態。
> やりすぎと思うかもしれませんが、逸般の誤家庭では標準です。

GPU パススルーは、マザーボード、BIOS、GPU、IOMMU グループの分かれ方で難易度が変わります。
うまくいく環境では拍子抜けするほど動きます。ダメな環境では、画面出力、Audio デバイス、起動順、ドライバーのどこかで沼ります。

なのでこの記事では、Proxmox の詳細手順までは深掘りしません。
まずは VM 内で `nvidia-smi` が通るところまでを目標にしてください。そこまで来れば、ComfyUI 側はほぼ Linux パターンと同じです。

---

## venvって何をしているの？

ここまでの手順では、Windows でも Ubuntu でも `venv` という仮想環境を作っています。
これは ComfyUI 専用の Python 作業場所を作るためのものです。

Python のライブラリは、ソフトごとに必要なバージョンが違うことがあります。
PC 全体にまとめて入れると、別の Python ツールとぶつかって壊れることがあります。
`venv` を使うと、ComfyUI 用の PyTorch や依存ライブラリを `ComfyUI/venv/` の中だけに閉じ込められます。

つまり、難しいバージョン管理をあまり考えずに済ませるための保険です。
ComfyUI を起動する前に、Windows なら `.\venv\Scripts\activate`、Ubuntu なら `source venv/bin/activate` を実行しておけばOKです。

---

## 動作確認

ComfyUIが起動したら、ブラウザで `http://<your-ip>:8188` にアクセス。

Linux サーバー側の IP は、だいたいこれで確認できます。

```bash
hostname -I
```

たとえば次のように出たら、最初の `192.168...` の部分を使います。

```bash
192.168.10.53 172.17.0.1
```

この場合、ブラウザで開くURLはこれです。

```text
http://192.168.10.53:8188
```

`172.17...` や `10.0...` など複数出ることがあります。
どれか分からない場合は、同じLAN内のPCから順番に試すか、`ip addr` の出力ごと AI に貼って「ブラウザで開くIPはどれ？」と聞くのが早いです。

ブラウザで開けると、次のような ComfyUI の画面が表示されます。

![ComfyUIの画面がブラウザで表示された状態](/images/claude-code-comfyui-skill/image_comfyui_gui_check.png)

1. GUIが表示される → OK
2. デフォルトのワークフローが読み込まれている
3. モデルを入れた後なら「Queue Prompt」で画像生成まで確認する

この確認は雑に見えて、かなり大事です。
ここで GUI が出るなら、ComfyUI の起動まではつながっています。
画像が1枚出るなら、GPU、PyTorch、モデル配置、ComfyUI の最低限の線までつながっています。
逆にここで失敗するなら、Claude Code Skill 以前の問題です。Skill に罪を着せない。まだ出番じゃないです。

ComfyUI 本体には、生成用のチェックポイントは同梱されていません。
何もモデルを置いていない状態で「Queue Prompt」を押しても、画像は出ません。
この第2回では、まず GUI が開けばOKです。
次回（第3回）では、civitai.com から waiIllustrious 系のモデルを入れて、実際に1枚出すところまで扱います。
まず置き場所だけ覚えておきましょう。

```bash
ComfyUI/models/checkpoints/
```

`waiIllustrious` や `Illustrious` 系の `.safetensors` ファイルは、ここに置きます。

もし詰まったら、まずこの順番で見ます。

- `nvidia-smi` で GPU が見えているか
- ComfyUI 起動ログに CUDA / PyTorch のエラーが出ていないか
- ブラウザで開いている IP とポートが合っているか
- Linux の場合、`--listen 0.0.0.0` を付け忘れていないか
- systemd 起動なら `sudo systemctl status comfyui --no-pager` が `active (running)` になっているか

エラー文はだいたい不親切ですが、完全な無言よりはマシです。
読みにくいだけで、手がかりはあります。たぶん。たぶんね。

**ここまで来たら ComfyUI の起動準備は完了です。**
第1回で見た「Claude Code から ComfyUI を呼ぶ」構成のうち、いちばん重い土台ができました。
次は、ここに実際のモデルと LoRA を入れて、生成したいキャラや絵柄に寄せていきます。

---

## 次回予告

第3回では、SDXLベースモデルとcivitai.comでのLoRA探しを扱います。
本シリーズでは、アニメ・イラスト系の扱いやすさを優先して waiIllustrious 系を使います。
Civitai Red についても軽く触れますが、初心者向けの標準導線としては通常の civitai.com を前提にします。

ComfyUI が起動しただけでは、まだ「画像生成できる箱」です。
次回はその箱に、どのモデルを入れるのか、LoRA をどこから探すのか、そして Civitai Red を標準導線にしない理由も軽く見ます。
技術記事です。技術記事のはずです。

> 第3回: SDXLモデル＆civitaiでLoRAを探す（準備中）

---

*[第1回（Zenn）](https://zenn.dev/miraclest/articles/claude-code-comfyui-skill-intro) から読むと全体像が掴めます。*
