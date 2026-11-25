// Password gate for the case studies. The page content and screenshots are AES-GCM encrypted
// (see scripts/protect.py); this decrypts them in the browser once the right password is entered.
// The derived key is kept for this tab only, so all three parts open with one password.
(function () {
  var main = document.getElementById('main');
  var payloadEl = document.getElementById('locked-payload');
  if (!main || !payloadEl || !main.hasAttribute('data-locked')) return;

  var form = document.getElementById('gate-form');
  var input = document.getElementById('gate-pw');
  var button = form && form.querySelector('[data-unlock]');
  var status = form && form.querySelector('[data-gate-status]');
  var saltB64 = main.getAttribute('data-salt');
  var iterations = parseInt(main.getAttribute('data-iter'), 10);
  var STORE = 'case-study-key';
  var subtle = window.crypto && window.crypto.subtle;

  function fromB64(s) {
    var bin = atob(s.trim()), out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  function toB64(buf) {
    var bytes = new Uint8Array(buf), s = '';
    for (var i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
    return btoa(s);
  }
  function say(msg, bad) {
    if (!status) return;
    status.textContent = msg;
    status.className = 'small gate__status' + (bad ? ' is-error' : '');
  }
  function busy(on) {
    if (!button) return;
    button.disabled = on;
    button.textContent = on ? 'Unlocking…' : 'Unlock';
  }
  function decrypt(key, bytes) {
    return subtle.decrypt({ name: 'AES-GCM', iv: bytes.slice(0, 12) }, key, bytes.slice(12));
  }
  function derive(password) {
    return subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey'])
      .then(function (base) {
        return subtle.deriveKey(
          { name: 'PBKDF2', salt: fromB64(saltB64), iterations: iterations, hash: 'SHA-256' },
          base, { name: 'AES-GCM', length: 256 }, true, ['decrypt']);
      });
  }
  function remember(key) {
    return subtle.exportKey('raw', key).then(function (raw) {
      try { sessionStorage.setItem(STORE, JSON.stringify({ salt: saltB64, key: toB64(raw) })); } catch (e) { /* private mode: just ask again */ }
    });
  }
  function forget() { try { sessionStorage.removeItem(STORE); } catch (e) { /* ignore */ } }
  function recalled() {
    try {
      var saved = JSON.parse(sessionStorage.getItem(STORE) || 'null');
      if (!saved || saved.salt !== saltB64) return null;
      return subtle.importKey('raw', fromB64(saved.key), { name: 'AES-GCM' }, true, ['decrypt']);
    } catch (e) { return null; }
  }

  function loadImages(key) {
    main.querySelectorAll('img[data-locked-src]').forEach(function (img) {
      fetch(img.getAttribute('data-locked-src'))
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
        .then(function (b64) { return decrypt(key, fromB64(b64)); })
        .then(function (plain) {
          img.src = URL.createObjectURL(new Blob([plain], { type: 'image/jpeg' }));
        })
        .catch(function () { img.alt = 'This image could not be loaded. ' + (img.alt || ''); });
    });
  }

  // Resolves true when the page opened, false when the key is wrong.
  function open(key) {
    return decrypt(key, fromB64(payloadEl.textContent)).then(function (plain) {
      main.removeAttribute('data-locked');
      main.innerHTML = new TextDecoder().decode(plain);
      loadImages(key);
      if (window.siteInit) window.siteInit(main);
      var target = location.hash && document.getElementById(location.hash.slice(1));
      if (target) target.scrollIntoView();
      else { var h = main.querySelector('h1'); if (h) { h.setAttribute('tabindex', '-1'); h.focus({ preventScroll: true }); } }
      return true;
    }, function () { return false; });
  }

  if (!subtle || !window.TextEncoder) {
    if (form) form.hidden = true;
    var p = document.createElement('p');
    p.className = 'body';
    p.textContent = 'This browser can’t open protected pages. Try a current version of Chrome, Safari, Firefox or Edge, or ask me for access.';
    if (form) form.parentNode.insertBefore(p, form);
    return;
  }

  // Already unlocked earlier in this tab? Open straight away.
  var saved = recalled();
  if (saved) {
    busy(true);
    saved.then(open).then(function (ok) { if (!ok) { forget(); busy(false); } }, function () { forget(); busy(false); });
  }

  if (form) form.addEventListener('submit', function (e) {
    e.preventDefault();
    var pw = input.value;
    if (!pw) { say('Enter the password, then select Unlock.', true); input.focus(); return; }
    busy(true); say('');
    derive(pw).then(function (key) {
      return open(key).then(function (ok) {
        if (ok) return remember(key);
        busy(false);
        input.setAttribute('aria-invalid', 'true');
        say('That password didn’t work. Check it and try again.', true);
        input.select();
      });
    }).catch(function () {
      busy(false);
      say('Something went wrong while unlocking. Reload the page and try again.', true);
    });
  });
})();
