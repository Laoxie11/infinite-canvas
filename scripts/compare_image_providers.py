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


def save_image(provider: str, payload: dict, output_dir: Path, timeout: int) -> str:
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return "no data[0]"
    item = data[0]
    if not isinstance(item, dict):
        return "data[0] is not object"
    if isinstance(item.get("b64_json"), str):
        output = output_dir / f"{provider}.png"
        output.write_bytes(base64.b64decode(item["b64_json"]))
        return str(output)
    if isinstance(item.get("url"), str):
        output = output_dir / f"{provider}.png"
        download_url(item["url"], output, timeout)
        return f"{output} ({item['url']})"
    return "no b64_json/url"


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
    try:
        response = json.loads(text)
    except json.JSONDecodeError:
        response = text

    result = {
        "provider": name,
        "status": status,
        "seconds": round(elapsed, 2),
        "ok": 200 <= status < 300,
    }
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
