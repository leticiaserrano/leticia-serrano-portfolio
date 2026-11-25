# Leticia Serrano: Portfolio

Static site with no build step. Built from the "Dark room. Light on the proof." design system.

- `index.html`: home (hero, projects, IterateUX, about, process, mentoring, testimonials, contact)
- `case-study/`: MentorHog mentor onboarding (part 1, part 2, outcome)
- `assets/styles.css`: design tokens and components (ink scale, light tokens, type scale)
- `assets/site.js`: nav, scroll reveal, carousel, before/after toggles

## Password-protected case studies

The case studies are **encrypted** with a password (AES-256-GCM, key from PBKDF2-SHA256, 600,000 rounds).
The repo and the live site hold only ciphertext: `case-study/*.html` show a password gate, and the
screenshots are encrypted files in `case-study/media/`. The browser decrypts them after the right password.
One password opens all three parts, and it's remembered for that browser tab only.

The readable source lives in `private/`, which is git-ignored and **never committed**.

To edit a case study (on a fresh clone, first restore `private/`):

    python3 scripts/unprotect.py                # asks for the password, rebuilds private/
    # edit private/build_case.py (text) or private/img/ (screenshots)
    python3 private/build_case.py private       # rebuild readable pages (to check them locally)
    python3 scripts/protect.py                  # re-encrypt; asks for the password

To change the password, run `scripts/protect.py` with the new one. Anyone you've already sent the
old password to will need the new one.

Limits worth knowing: it's as strong as the password (use a long passphrase, since the encrypted
files are public and can be attacked offline), and anyone you give the password to can share it or
save what they see.

## Preview

    python3 -m http.server 8000

## Deploy

Works as-is on GitHub Pages (Settings → Pages → deploy from `main`, root), Netlify or Vercel.

## Still to fill in

Search for `TODO` and `placeholder` in the HTML:

- New resume. Resume links are removed until it exists; add a nav item and a button back when it does
- Verified metrics: `[+X%]` (Alida, Yervana), `[N]` ventures, `[Year]`, `[Your role]`
- Colleague quote in the About section
- One-on-one session length (currently says 20 min, same as the free call)
- "Before" screenshots for the case-study comparisons

## Links

- Mentoring bookings and the QR code: https://mentorhog.com/mentors/mtr_P4smFbxZ8E8dBrhaFeLAexER
  (QR is `assets/img/qr-mentorhog.svg`; regenerate it if that URL changes)
- LinkedIn: https://www.linkedin.com/in/leticiacserrano/

## Contact form (FormSubmit)

The form sends through FormSubmit to the address in `data-endpoint` on `#contact-form` (`index.html`).
The site never displays an email address.

1. Once the site is live, send yourself a test message from the form.
2. FormSubmit emails a one-time **activation link** to that address. Click it; nothing arrives until you do.
3. Optional: FormSubmit then offers a random **alias**. Put `https://formsubmit.co/ajax/<alias>` in
   `data-endpoint` so the address isn't in the page source either.

An empty `data-endpoint` hides the form. If sending fails, the form points visitors to LinkedIn.
