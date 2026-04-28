#!/usr/bin/env python3
"""ComfyUI API経由でキャラクター画像を生成する"""

import sys, json, random, time, os
import urllib.request, urllib.error

# === 設定 ===================================================
COMFYUI_URL = "http://127.0.0.1:8188"  # あなたのComfyUIのアドレスに変更
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "comfyui_generated")

STYLE_PROMPT = "masterpiece, best quality, amazing quality, official art"
NEG_PROMPT = "bad quality, worst quality, bad anatomy, watermark"

# === キャラクター定義 ==========================================
# ここを自分のキャラに書き換えるだけでOK
CHARACTERS = {
    "secretary": {
        "name": "AI秘書",
        "appearance": "1girl, black hair, office lady, glasses, slender",
        "lora": "your_lora.safetensors",  # ← civitaiで入手したLoRAファイル名
        "lora_strength": 0.7,
    },
    # キャラを増やすならここにエントリを追加
}

# === プロンプト合成 ============================================
def build_prompt(character_key, situation):
    char = CHARACTERS[character_key]
    return f"{STYLE_PROMPT}, {char['appearance']}, {situation}"

# === ComfyUI API ==============================================
def queue_prompt(workflow):
    """ComfyUI APIにワークフローJSONを送信"""
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    return resp["prompt_id"]

def wait_for_completion(prompt_id, timeout=120):
    """生成完了を待つ（ポーリング）"""
    for _ in range(timeout):
        resp = json.loads(
            urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}").read()
        )
        if prompt_id in resp:
            return resp[prompt_id]
        time.sleep(1)
    raise TimeoutError("ComfyUI generation timed out")

def download_image(history, prompt_id):
    """生成された画像をダウンロードして保存"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outputs = history["outputs"]
    for node_id in outputs:
        for img in outputs[node_id].get("images", []):
            filename = img["filename"]
            subfolder = img.get("subfolder", "")
            img_type = img.get("type", "output")
            params = urllib.parse.urlencode(
                {"filename": filename, "subfolder": subfolder, "type": img_type}
            )
            url = f"{COMFYUI_URL}/view?{params}"
            save_path = os.path.join(OUTPUT_DIR, filename)
            urllib.request.urlretrieve(url, save_path)
            return save_path
    return None

# === ワークフロー構築 ==========================================
def build_workflow(prompt_text, lora_file, lora_strength, seed):
    """ComfyUI APIフォーマットのワークフローJSON"""
    has_lora = lora_file and lora_file != "your_lora.safetensors"

    if has_lora:
        model_source = ["10", 0]
        clip_source = ["10", 1]
        lora_node = {
            "10": {
                "class_type": "LoraLoader",
                "inputs": {
                    "model": ["4", 0],
                    "clip": ["4", 1],
                    "lora_name": lora_file,
                    "strength_model": lora_strength,
                    "strength_clip": lora_strength,
                },
            }
        }
    else:
        model_source = ["4", 0]
        clip_source = ["4", 1]
        lora_node = {}

    workflow = {
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "waiIllustriousSDXL_v160.safetensors"},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 1024, "height": 1600, "batch_size": 1},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": clip_source, "text": prompt_text},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": clip_source, "text": NEG_PROMPT},
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "model": model_source,
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
                "seed": seed,
                "steps": 30,
                "cfg": 4.0,
                "sampler_name": "euler_ancestral",
                "scheduler": "simple",
                "denoise": 1.0,
            },
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": "article_sample"},
        },
    }
    workflow.update(lora_node)
    return workflow

# === メイン ====================================================
def main():
    import urllib.parse

    if len(sys.argv) < 3:
        print("Usage: python3 generate.py <character> \"<situation>\"")
        print(f"Characters: {', '.join(CHARACTERS.keys())}")
        sys.exit(1)

    char_key = sys.argv[1]
    situation = sys.argv[2]
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else random.randint(0, 2**32 - 1)

    if char_key not in CHARACTERS:
        print(f"Unknown character: {char_key}")
        print(f"Available: {', '.join(CHARACTERS.keys())}")
        sys.exit(1)

    char = CHARACTERS[char_key]
    prompt_text = build_prompt(char_key, situation)
    print(f"Generating: {char['name']} — {situation}")
    print(f"Prompt: {prompt_text}")

    workflow = build_workflow(prompt_text, char["lora"], char["lora_strength"], seed)
    prompt_id = queue_prompt(workflow)
    print(f"Queued: {prompt_id} (waiting...)")

    history = wait_for_completion(prompt_id)
    image_path = download_image(history, prompt_id)

    if image_path:
        print(f"[FILE] {image_path}")
    else:
        print("Error: No image generated")
        sys.exit(1)

if __name__ == "__main__":
    main()
