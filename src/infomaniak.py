# -*- coding: utf-8 -*-
"""
infomaniak.py — the sovereign call. One host (Europe), one token, for the lens
(the daily text: the presages and the airs).

Text : OpenAI-compatible endpoint
    {base}/{PRODUCT_ID}/openai/v1/chat/completions   (Authorization: Bearer <token>)

The token and product id come from the environment (GitHub secrets), never code.
The finale's nouvelle uses a stronger model on this SAME host (Apertus by default;
see finale.py and config.yaml) -- everything stays sovereign.
"""
from __future__ import annotations
import os
import json
import time
import urllib.request
import urllib.error

_TOKEN = os.environ.get("INFOMANIAK_TOKEN", "")
_PRODUCT = os.environ.get("INFOMANIAK_PRODUCT_ID", "")


def _base(conf: dict) -> str:
    return f'{conf["infomaniak"]["base_url"]}/{_PRODUCT}'


def text(conf: dict, system: str, task: str, temperature: float = 0.8,
         max_tokens: int = 1200, model: str | None = None) -> str:
    """The daily voice uses infomaniak.text_model; the finale passes model=<Apertus>."""
    url = f"{_base(conf)}/openai/v1/chat/completions"
    body = {
        "model": model or conf["infomaniak"]["text_model"],
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": task}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    return _post(url, body)["choices"][0]["message"]["content"].strip()


def _post(url: str, body: dict, tries: int = 3) -> dict:
    data = json.dumps(body).encode("utf-8")
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=data, method="POST",
                                         headers={"Authorization": f"Bearer {_TOKEN}",
                                                  "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503):
                time.sleep(2 * (k + 1)); continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e; time.sleep(2 * (k + 1))
    raise RuntimeError(f"Infomaniak unreachable after {tries} tries: {last}")
