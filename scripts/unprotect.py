"""Restore the readable case-study source into private/ from the encrypted copies in the repo.

Use this on a fresh clone (private/ is never committed) before editing the case studies:
  python3 scripts/unprotect.py            # asks for the password
  python3 private/build_case.py private   # rebuild readable pages (also done below)
Then edit private/build_case.py or private/img/, and run scripts/protect.py again.
"""
import base64, getpass, os, re, subprocess, sys
from pathlib import Path
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ROOT = Path(__file__).resolve().parent.parent
PRIVATE, PUBLIC = ROOT / "private", ROOT / "case-study"


def open_sealed(key: bytes, blob: bytes) -> bytes:
    return AESGCM(key).decrypt(blob[:12], blob[12:], None)


def main():
    salt_b64, sealed_src = (ROOT / "scripts" / "case-source.bin").read_bytes().split(b"\n", 1)
    salt = base64.b64decode(salt_b64)
    page = (PUBLIC / "mentor-onboarding.html").read_text(encoding="utf-8")
    iterations = int(re.search(r'data-iter="(\d+)"', page).group(1))
    password = os.environ.get("PORTFOLIO_PASSWORD") or getpass.getpass("Case-study password: ")
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations).derive(password.encode())
    try:
        source = open_sealed(key, base64.b64decode(sealed_src))
    except InvalidTag:
        sys.exit("That password didn't decrypt the source. Nothing was changed.")

    (PRIVATE / "img").mkdir(parents=True, exist_ok=True)
    (PRIVATE / "build_case.py").write_bytes(source)
    restored = 0
    for p in PUBLIC.glob("*.html"):
        text = p.read_text(encoding="utf-8")
        payload = re.search(r'<script type="text/plain" id="locked-payload">([^<]+)</script>', text).group(1)
        inner = open_sealed(key, base64.b64decode(payload)).decode("utf-8")
        for token, name in re.findall(r'data-locked-src="media/([0-9a-f]+)\.txt" data-name="([^"]+)"', inner):
            out = PRIVATE / "img" / name
            if not out.exists():
                out.write_bytes(open_sealed(key, base64.b64decode((PUBLIC / "media" / f"{token}.txt").read_bytes())))
                restored += 1
    subprocess.run([sys.executable, str(PRIVATE / "build_case.py"), str(PRIVATE)], check=True)
    print(f"Restored private/build_case.py and {restored} images, and rebuilt private/case-study/.")


if __name__ == "__main__":
    main()
