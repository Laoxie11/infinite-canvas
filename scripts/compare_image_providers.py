#!/usr/bin/env python3
import argparse
import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


PROVIDERS = {
    "foxcode": {
        "url": "https://dm-fox.rjj.cc/codex/v1/images/generations",
        "key_env": "FOXCODE_API_KEY",
        "extra": {},
    },
    "packy": {
        "url": "https://www.packyapi.com/v1/images/generations",
        "key_env": "PACKY_API_KEY",
        "extra": {"output_format": "png", "response_format": "url"},
    },
}


def post_json(url: str, api_key: str, payload: dict, timeout: int) -> tuple[int, str, float]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "*/*",
        },
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", errors="replace"), time.perf_counter() - started
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace"), time.perf_counter() - started


def download_url(url: str, output: Path, timeout: int) -> None:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        output.write_bytes(response.read())


def save_raw_response(provider: str, text: str, output_dir: Path) -> str:
    output = output_dir / f"{provider}.raw.json"
    output.write_text(text, encoding="utf-8")
    return str(output)


def find_image_value(value):
    if isinstance(value, dict):
        for key in ("b64_json", "url", "image_url", "image", "output_url"):
            item = value.get(key)
            if isinstance(item, str) and item:
                return key, item
            if isinstance(item, dict):
                nested = item.get("url")
                if isinstance(nested, str) and nested:
                    return f"{key}.url", nested
        for item in value.values():
            found = find_image_value(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = find_image_value(item)
            if found:
                return found
    return None


def save_image(provider: str, payload: dict, output_dir: Path, timeout: int) -> str:
    found = find_image_value(payload)
    if not found:
        return "no image field found"
    key, value = found
    if key.endswith("b64_json"):
        output = output_dir / f"{provider}.png"
        output.write_bytes(base64.b64decode(value))
        return f"{output} ({key})"
    if value.startswith("data:image/") and "," in value:
        output = output_dir / f"{provider}.png"
        output.write_bytes(base64.b64decode(value.split(",", 1)[1]))
        return f"{output} ({key})"
    if value.startswith("http://") or value.startswith("https://"):
        output = output_dir / f"{provider}.png"
        download_url(value, output, timeout)
        return f"{output} ({key}: {value})"
    return f"unsupported image field {key}"


def error_message(payload: dict | str) -> str:
    if isinstance(payload, str):
        return payload[:500]
    error = payload.get("error")
    if isinstance(error, dict) and error.get("message"):
        return str(error["message"])
    if payload.get("msg"):
        return str(payload["msg"])
    return json.dumps(payload, ensure_ascii=False)[:500]


def run_provider(name: str, args: argparse.Namespace) -> dict:
    provider = PROVIDERS[name]
    api_key = os.getenv(provider["key_env"], "").strip()
    if not api_key:
        return {"provider": name, "ok": False, "error": f"missing env {provider['key_env']}"}

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "n": 1,
        **provider["extra"],
    }
    status, text, elapsed = post_json(provider["url"], api_key, payload, args.timeout)
    raw_path = save_raw_response(name, text, args.output_dir)
    try:
        response = json.loads(text)
    except json.JSONDecodeError:
        response = text

    result = {
        "provider": name,
        "status": status,
        "seconds": round(elapsed, 2),
        "ok": 200 <= status < 300,
        "raw": raw_path,
    }
    if isinstance(response, dict) and response.get("error"):
        result["ok"] = False
        result["error"] = error_message(response)
        return result
    if result["ok"]:
        try:
            result["image"] = save_image(name, response, args.output_dir, args.timeout)
        except Exception as error:
            result["ok"] = False
            result["error"] = f"save image failed: {error}"
    else:
        result["error"] = error_message(response)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare foxcode and PackyAPI gpt-image-2 image generation.")
    parser.add_argument("--prompt", default="一个小男孩", help="Image prompt.")
    parser.add_argument("--size", default="1536x1024", help="Image size, e.g. 1536x1024.")
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high", "auto"], help="Image quality.")
    parser.add_argument("--model", default="gpt-image-2", help="Model name.")
    parser.add_argument("--timeout", type=int, default=300, help="Request timeout seconds.")
    parser.add_argument("--output-dir", type=Path, default=Path("provider-test-output"), help="Output directory.")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Prompt: {args.prompt}")
    print(f"Size: {args.size}, quality: {args.quality}, model: {args.model}")
    print()
    for name in PROVIDERS:
        result = run_provider(name, args)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
