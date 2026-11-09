#!/usr/bin/env python3
"""Löser konflikter när två hämtningar har committat samtidigt (används av hamta.yml).

Körs mitt i en `git pull --rebase` som stannat på konflikter. För varje fil med konflikt:
  - JSON-listor med dokument (url): unionen, där den här körningens post vinner.
  - JSON-objekt: nycklarna slås ihop rekursivt; den här körningens värde vinner vid krock.
  - Övriga filer (veckolistor, granskningskort): den här körningens version.
Under en rebase är version 2 den som redan ligger på main och version 3 den här körningens.
"""
import json
import subprocess
import sys


def git(*a, check=True):
    return subprocess.run(["git", *a], capture_output=True, text=True, check=check).stdout


def version(steg, fil):
    r = subprocess.run(["git", "show", f":{steg}:{fil}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def slå_ihop(a, b):
    """a = main, b = den här körningen."""
    if isinstance(a, dict) and isinstance(b, dict):
        ut = dict(a)
        for k, v in b.items():
            ut[k] = slå_ihop(a[k], v) if k in a else v
        return ut
    if isinstance(a, list) and isinstance(b, list) and all(isinstance(x, dict) and "url" in x for x in a + b):
        ut = {x["url"]: x for x in a}
        ut.update({x["url"]: x for x in b})
        return list(ut.values())
    return b


def main():
    filer = [f for f in git("diff", "--name-only", "--diff-filter=U").splitlines() if f]
    for f in filer:
        main_v, var_v = version(2, f), version(3, f)
        if var_v is None:  # borttagen i den här körningen
            git("rm", "-q", f, check=False)
            continue
        text = var_v
        if f.endswith(".json") and main_v is not None:
            try:
                text = json.dumps(slå_ihop(json.loads(main_v), json.loads(var_v)), ensure_ascii=False, indent=1) + "\n"
            except json.JSONDecodeError:
                pass
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(text)
        git("add", f)
    print(f"Sammanfogade {len(filer)} filer med konflikt.")
    return 0 if filer else 1


if __name__ == "__main__":
    sys.exit(main())
