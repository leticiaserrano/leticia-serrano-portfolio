"""Encrypt the case studies with a password, so the public site and repo only hold ciphertext.

Readable source lives in private/ (git-ignored, never committed):
  private/build_case.py      writes the readable pages into private/case-study/
  private/img/               the case-study screenshots
This script writes the public, encrypted versions:
  case-study/*.html          page shell + password gate + encrypted page content
  case-study/media/*.txt     encrypted screenshots (base64 text, so any host serves them)
  scripts/case-source.bin    encrypted copy of private/build_case.py, so the source survives

Usage (from the repo root):
  python3 private/build_case.py private        # rebuild readable pages after editing content
  python3 scripts/protect.py                   # asks for the password
  PORTFOLIO_PASSWORD='...' python3 scripts/protect.py

Changing the password: run this again with the new one. Restore private/ with scripts/unprotect.py.
Crypto: PBKDF2-HMAC-SHA256 (600,000 iterations) -> AES-256-GCM, random 12-byte IV per item.
"""
import base64, getpass, html, os, re, secrets, shutil, sys
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ROOT = Path(__file__).resolve().parent.parent
PRIVATE, PUBLIC = ROOT / "private", ROOT / "case-study"
ITERATIONS = 600_000

# Public heading on each gate. Everything else on the page is encrypted.
GATE_TITLES = {
    "mentor-onboarding.html": ("Mentor onboarding", "from an hour to 15 minutes"),
    "mentor-onboarding-part-2.html": ("Mentor onboarding,", "part 2"),
    "mentor-onboarding-outcome.html": ("Mentor onboarding:", "the outcome"),
}


def derive(password: str, salt: bytes) -> bytes:
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS).derive(password.encode())


def seal(key: bytes, data: bytes) -> bytes:
    iv = secrets.token_bytes(12)
    return iv + AESGCM(key).encrypt(iv, data, None)


def gate(name: str, salt_b64: str, payload_b64: str) -> str:
    lead, accent = GATE_TITLES.get(name, ("Case study", "protected"))
    return f'''  <main id="main" data-locked data-salt="{salt_b64}" data-iter="{ITERATIONS}">
    <section class="cs-hero gate">
      <div class="wrap">
        <a class="back" href="../index.html#projects"><svg class="arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><path d="M14 8H3M7 4L3 8l4 4"/></svg> All projects</a>
        <h1 class="display gate__title">{html.escape(lead)} <span class="lit">{html.escape(accent)}</span></h1>
        <p class="body-l gate__lede">Enter the password to read this case study. One password opens all three parts.</p>
        <form class="card gate__form" id="gate-form" novalidate>
          <div class="field">
            <label class="label" for="gate-pw">Password</label>
            <input class="input" id="gate-pw" name="password" type="password" autocomplete="current-password" required>
          </div>
          <div class="gate__foot">
            <button class="btn btn--primary btn--lg" type="submit" data-unlock>Unlock</button>
            <p class="small gate__status" role="status" aria-live="polite" data-gate-status></p>
          </div>
        </form>
        <p class="small gate__ask">No password? <a class="link" href="../index.html#contact">Ask me for access</a></p>
        <noscript><p class="body">Turn on JavaScript to unlock this case study.</p></noscript>
      </div>
    </section>
    <script type="text/plain" id="locked-payload">{payload_b64}</script>
  </main>'''


def main():
    pages = sorted((PRIVATE / "case-study").glob("*.html"))
    if not pages:
        sys.exit("No readable pages in private/case-study/. Run: python3 private/build_case.py private")
    password = os.environ.get("PORTFOLIO_PASSWORD") or getpass.getpass("Case-study password: ")
    if len(password) < 12:
        sys.exit("Use at least 12 characters: the encrypted pages are public, so short passwords can be guessed offline.")

    salt = secrets.token_bytes(16)
    key = derive(password, salt)
    salt_b64 = base64.b64encode(salt).decode()

    media = PUBLIC / "media"
    shutil.rmtree(media, ignore_errors=True)
    media.mkdir(parents=True)
    sealed_images = {}

    def lock_img(m):
        name = m.group(1)
        src = PRIVATE / "img" / name
        if not src.exists():
            return m.group(0)  # a public image: leave it alone
        if name not in sealed_images:
            token = secrets.token_hex(8)
            (media / f"{token}.txt").write_bytes(base64.b64encode(seal(key, src.read_bytes())))
            sealed_images[name] = token
        return f'data-locked-src="media/{sealed_images[name]}.txt" data-name="{name}"'

    for page in pages:
        text = page.read_text(encoding="utf-8")
        m = re.search(r'  <main id="main">\n(.*?)\n  </main>', text, re.S)
        if not m:
            sys.exit(f"Couldn't find <main> in {page.name}")
        inner = re.sub(r'src="\.\./assets/img/([^"]+)"', lock_img, m.group(1))
        payload = base64.b64encode(seal(key, inner.encode("utf-8"))).decode()
        shell = text[:m.start()] + gate(page.name, salt_b64, payload) + text[m.end():]
        shell = shell.replace('<meta name="theme-color"', '<meta name="robots" content="noindex">\n  <meta name="theme-color"', 1)
        shell = shell.replace('<script src="../assets/site.js"></script>',
                              '<script src="../assets/site.js"></script>\n  <script src="../assets/gate.js"></script>', 1)
        (PUBLIC / page.name).write_text(shell, encoding="utf-8")

    (ROOT / "scripts" / "case-source.bin").write_bytes(
        base64.b64encode(salt) + b"\n" + base64.b64encode(seal(key, (PRIVATE / "build_case.py").read_bytes())))
    print(f"Encrypted {len(pages)} pages and {len(sealed_images)} images. Same password unlocks all of them.")


if __name__ == "__main__":
    main()
