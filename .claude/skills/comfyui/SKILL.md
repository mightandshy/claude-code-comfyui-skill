---
name: comfyui
description: >
  ComfyUIでキャラクター画像を生成するSkill。
  「画像を生成して」「〇〇の絵を描いて」などのキーワードでトリガーする。
---

# ComfyUI Image Generator

ComfyUI APIを使ってキャラクター画像を生成する。

## キャラクター一覧

| キー | キャラ | LoRA |
|------|--------|------|
| `secretary` | AI秘書 | your_lora.safetensors |

## 手順

### Step 1: 意図解析
メッセージからキャラクターとシチュエーションを特定する。
キャラが不明な場合はユーザーに確認する。

### Step 2: シチュエーションを英語タグに変換
日本語の描写を英語プロンプト（20〜40語程度）に翻訳する。

| 日本語 | 英語タグ例 |
|--------|-----------|
| オフィスで微笑む | office, gentle smile, looking at viewer, sitting at desk, warm light |
| 怒ってこちらを見ている | angry expression, staring at viewer, arms crossed |
| 読書中 | reading a book, focused expression, warm light |

### Step 3: generate.py で画像生成を実行

```bash
python3 .claude/skills/comfyui/scripts/generate.py <character_key> "<situation_en>"
```

生成完了後、出力された画像パスを Read ツールで読み込んでユーザーに表示する。
