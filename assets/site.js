// Small, dependency-free behaviour layer. Everything here degrades gracefully without JS.
(function () {
  document.documentElement.classList.remove('no-js');

  // Sticky nav: hairline appears once the page scrolls.
  var nav = document.querySelector('.nav');
  if (nav) {
    var onScroll = function () { nav.classList.toggle('is-scrolled', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });

    var toggle = nav.querySelector('.nav__toggle');
    if (toggle) {
      toggle.addEventListener('click', function () {
        var open = nav.classList.toggle('is-open');
        toggle.setAttribute('aria-expanded', String(open));
        toggle.textContent = open ? 'Close' : 'Menu';
      });
      nav.querySelectorAll('.nav__links a').forEach(function (a) {
        a.addEventListener('click', function () {
          nav.classList.remove('is-open');
          toggle.setAttribute('aria-expanded', 'false');
          toggle.textContent = 'Menu';
        });
      });
    }
  }

  // Behaviour for page content. Runs on load, and again on content a case study unlocks.
  function init(scope) {
    // Reveal on scroll.
    var reveals = scope.querySelectorAll('.reveal');
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
      reveals.forEach(function (el) { io.observe(el); });
    } else {
      reveals.forEach(function (el) { el.classList.add('is-in'); });
    }

    // Carousel (About).
    scope.querySelectorAll('[data-carousel]').forEach(function (root) {
      var slides = root.querySelectorAll('.carousel__slide');
      var dots = root.querySelectorAll('.carousel__dot');
      var i = 0;
      function go(n) {
        i = (n + slides.length) % slides.length;
        slides.forEach(function (s, k) {
          s.classList.toggle('is-active', k === i);
          s.setAttribute('aria-hidden', String(k !== i));
        });
        dots.forEach(function (d, k) { d.setAttribute('aria-current', String(k === i)); });
      }
      var prev = root.querySelector('[data-prev]');
      var next = root.querySelector('[data-next]');
      if (prev) prev.addEventListener('click', function () { go(i - 1); });
      if (next) next.addEventListener('click', function () { go(i + 1); });
      dots.forEach(function (d, k) { d.addEventListener('click', function () { go(k); }); });
      root.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft') go(i - 1);
        if (e.key === 'ArrowRight') go(i + 1);
      });
      go(0);
    });

    // Before / After toggles on case study shots.
    scope.querySelectorAll('[data-shot]').forEach(function (shot) {
      var buttons = shot.querySelectorAll('.seg button');
      var views = shot.querySelectorAll('[data-view]');
      function show(name) {
        buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.show === name)); });
        views.forEach(function (v) { v.classList.toggle('is-shown', v.dataset.view === name); });
      }
      buttons.forEach(function (b) { b.addEventListener('click', function () { show(b.dataset.show); }); });
      show('after');

      var noteBtn = shot.querySelector('.note-btn');
      var note = shot.querySelector('.note');
      if (noteBtn && note) {
        noteBtn.addEventListener('click', function () {
          var open = note.hidden;
          note.hidden = !open;
          noteBtn.setAttribute('aria-expanded', String(open));
        });
      }
    });

    // Video facade: swap in the YouTube player only when someone clicks play.
    scope.querySelectorAll('[data-video]').forEach(function (fig) {
      var btn = fig.querySelector('.video__play');
      if (!btn) return;
      // YouTube serves a 120px grey placeholder when a video has no full-size thumbnail: fall back to the
      // always-available one, and drop the image entirely if it can't load (the card styles still show).
      var thumb = btn.querySelector('.video__thumb');
      if (thumb) {
        var useFallback = function () {
          if (thumb.src.indexOf('maxresdefault') > -1) thumb.src = thumb.src.replace('maxresdefault', 'hqdefault');
          else thumb.remove();
        };
        thumb.addEventListener('error', useFallback);
        thumb.addEventListener('load', function () {
          if (thumb.naturalWidth <= 120) useFallback(); else btn.classList.add('has-thumb');
        });
        if (thumb.complete && thumb.naturalWidth > 120) btn.classList.add('has-thumb');
      }
      // muted: true for autoplay on arrival (browsers only allow silent autoplay); a click plays with sound.
      function loadPlayer(muted) {
        if (!btn.isConnected) return;
        var f = document.createElement('iframe');
        f.src = 'https://www.youtube-nocookie.com/embed/' + fig.dataset.video +
          '?start=' + (fig.dataset.start || 0) + '&autoplay=1&playsinline=1&rel=0&modestbranding=1' + (muted ? '&mute=1' : '');
        f.title = btn.getAttribute('aria-label').replace(/^Play /, '');
        f.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
        f.allowFullscreen = true;
        btn.replaceWith(f);
        if (!muted) f.focus();
      }
      btn.addEventListener('click', function () { loadPlayer(false); });
      var calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (fig.hasAttribute('data-autoplay') && !calm) loadPlayer(true);
    });

    // Process flow: "Before AI" / "With AI" views of the same loop.
    // Select a step to read about it; "Play the loop" walks the whole cycle.
    scope.querySelectorAll('[data-flow]').forEach(function (root) {
      var data;
      try { data = JSON.parse(root.querySelector('[data-flow-steps]').textContent); } catch (e) { return; }
      var meta = root.querySelector('[data-flow-meta]');
      var title = root.querySelector('[data-flow-title]');
      var text = root.querySelector('[data-flow-text]');
      var count = root.querySelector('[data-flow-count]');
      var intro = root.querySelector('[data-flow-intro]');
      var playBtn = root.querySelector('[data-flow-play]');
      var tabs = root.querySelectorAll('[data-flow-tab]');
      var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var mode, steps, order, panel, timer = null, current = 0;

      function select(i, trail) {
        current = (i + order.length) % order.length;
        var s = steps[current];
        panel.querySelectorAll('[data-step]').forEach(function (t) {
          var on = t.getAttribute('data-step') === s.id;
          t.classList.toggle('is-active', on);
          t.setAttribute('aria-pressed', String(on));
        });
        panel.querySelectorAll('.flow-edge').forEach(function (e) {
          var k = order.indexOf(e.getAttribute('data-from'));
          e.classList.toggle('is-done', !!trail && k > -1 && k < current);
        });
        if (meta) meta.textContent = s.phase + ' · ' + s.track + (s.ai ? ' · AI-assisted' : '');
        title.textContent = s.label;
        text.textContent = s.text;
        if (count) count.textContent = (current + 1) + ' / ' + order.length;
      }
      function stop() {
        if (timer) { clearInterval(timer); timer = null; }
        playBtn.textContent = 'Play the loop';
      }
      function play() {
        stop();
        select(0, true);
        playBtn.textContent = 'Pause';
        timer = setInterval(function () {
          if (current === order.length - 1) { stop(); select(0, false); return; } // feedback lands back at the start
          select(current + 1, true);
        }, 1300);
      }
      function setMode(m, autoplay) {
        stop();
        mode = m; steps = data[m].steps; order = steps.map(function (s) { return s.id; });
        root.querySelectorAll('[data-flow-mode]').forEach(function (p) { p.hidden = p.getAttribute('data-flow-mode') !== m; });
        root.querySelectorAll('[data-flow-only]').forEach(function (el) { el.hidden = el.getAttribute('data-flow-only') !== m; });
        tabs.forEach(function (t) { t.setAttribute('aria-pressed', String(t.getAttribute('data-flow-tab') === m)); });
        panel = root.querySelector('[data-flow-mode="' + m + '"]');
        intro.textContent = data[m].intro;
        if (autoplay && !reduce) play(); else select(0, false);
      }

      tabs.forEach(function (t) {
        t.addEventListener('click', function () { setMode(t.getAttribute('data-flow-tab'), true); });
      });
      playBtn.addEventListener('click', function () { timer ? stop() : play(); });
      root.querySelectorAll('[data-flow-mode] [data-step]').forEach(function (t) {
        function pick() { stop(); select(order.indexOf(t.getAttribute('data-step')), false); }
        t.addEventListener('click', pick);
        t.addEventListener('keydown', function (e) {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); }
        });
      });
      setMode(tabs.length ? tabs[0].getAttribute('data-flow-tab') : Object.keys(data)[0], false);

      // Play once when the diagram first comes into view, unless reduced motion is requested.
      if (!reduce && 'IntersectionObserver' in window) {
        var seen = new IntersectionObserver(function (entries) {
          if (entries[0].isIntersecting) { seen.disconnect(); if (!timer) play(); }
        }, { threshold: 0.4 });
        seen.observe(root);
      }
    });

  }
  init(document);
  window.siteInit = init;

  // Copy buttons: fall back to selecting the text if the clipboard is refused.
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var el = document.querySelector(btn.getAttribute('data-copy'));
      if (!el) return;
      var value = el.textContent.trim();
      function selectIt() {
        var r = document.createRange(); r.selectNodeContents(el);
        var sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
        btn.textContent = 'Selected';
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(value).then(function () { btn.textContent = 'Copied'; }, selectIt);
      } else { selectIt(); }
      setTimeout(function () { btn.textContent = 'Copy'; }, 2000);
    });
  });

  // Contact form: validate, then send through FormSubmit. Always says what happened.
  var form = document.getElementById('contact-form');
  // No endpoint yet (waiting for a FormSubmit alias): hide the form; LinkedIn stays as the way in.
  if (form && !form.getAttribute('data-endpoint')) form.hidden = true;
  if (form && !form.hidden) {
    var status = form.querySelector('[data-status]');
    var submit = form.querySelector('[data-submit]');
    function say(msg, kind) { status.textContent = msg; status.className = 'small contact-form__status' + (kind ? ' is-' + kind : ''); }
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var fields = ['cf-name', 'cf-email', 'cf-message'].map(function (id) { return document.getElementById(id); });
      var firstBad = null;
      fields.forEach(function (f) {
        var bad = !f.value.trim() || (f.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.value.trim()));
        f.setAttribute('aria-invalid', String(bad));
        if (bad && !firstBad) firstBad = f;
      });
      if (firstBad) {
        say(firstBad.id === 'cf-email' && firstBad.value.trim()
          ? 'That email address looks incomplete. Check it and send again.'
          : 'Add your name, email and a message, then send again.', 'error');
        firstBad.focus();
        return;
      }
      if (form.querySelector('[name="_honey"]').value) { say('Message sent. Thank you.', 'ok'); form.reset(); return; }
      submit.disabled = true; submit.textContent = 'Sending…'; say('');
      fetch(form.getAttribute('data-endpoint'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({
          name: fields[0].value.trim(), email: fields[1].value.trim(), message: fields[2].value.trim(),
          _subject: 'Portfolio message from ' + fields[0].value.trim(), _template: 'table', _captcha: 'false'
        })
      }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (res) {
          var ok = res.ok && String(res.d.success) !== 'false';
          if (!ok) throw new Error('rejected');
          say('Message sent. I’ll reply to ' + fields[1].value.trim() + '.', 'ok');
          form.reset();
          fields.forEach(function (f) { f.removeAttribute('aria-invalid'); });
        })
        .catch(function () {
          say('The message didn’t send. Please message me on LinkedIn instead.', 'error');
        })
        .then(function () { submit.disabled = false; submit.textContent = 'Send message'; });
    });
  }

  // Hero spotlight: a soft light follows the mouse and reveals the portrait's colour.
  var spot = document.querySelector('[data-spotlight]');
  var fine = window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  if (spot && fine) {
    var photo = spot.querySelector('.hero__photo');
    var colour = spot.querySelector('.hero__img--color');
    var tx = 0, ty = 0, cx = 0, cy = 0, raf = 0, still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    function paint() {
      cx += (tx - cx) * (still ? 1 : 0.18); cy += (ty - cy) * (still ? 1 : 0.18);
      colour.style.setProperty('--mx', cx.toFixed(1) + 'px');
      colour.style.setProperty('--my', cy.toFixed(1) + 'px');
      raf = (Math.abs(tx - cx) > 0.5 || Math.abs(ty - cy) > 0.5) ? requestAnimationFrame(paint) : 0;
    }
    spot.addEventListener('pointermove', function (e) {
      if (e.pointerType && e.pointerType !== 'mouse') return;
      var r = colour.getBoundingClientRect();
      tx = e.clientX - r.left; ty = e.clientY - r.top;
      if (!photo.classList.contains('is-lit')) { cx = tx; cy = ty; photo.classList.add('is-lit'); }
      if (!raf) raf = requestAnimationFrame(paint);
    });
    spot.addEventListener('pointerleave', function () { photo.classList.remove('is-lit'); });
  }

  var y = document.querySelector('[data-year]');
  if (y) y.textContent = String(new Date().getFullYear());
})();
