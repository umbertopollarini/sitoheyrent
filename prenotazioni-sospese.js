/* ══════════════════════════════════════════════════════════════════
   HeyRent! — Prenotazioni temporaneamente sospese
   ------------------------------------------------------------------
   Blocca l'invio delle richieste via WhatsApp e mostra un avviso.
   Il form di richiesta preventivo resta visibile e compilabile.

   PER RIATTIVARE LE PRENOTAZIONI:
   cancella questo file e i tag <script> che lo richiamano nelle
   pagine (cerca "prenotazioni-sospese.js" nel progetto).
   ══════════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    var TRIGGERS = '.btn-whatsapp, a[href*="wa.me"], a[href*="api.whatsapp.com"]';
    var overlay = null;
    var lastFocus = null;

    function injectStyles() {
        if (document.getElementById('hr-paused-style')) return;
        var st = document.createElement('style');
        st.id = 'hr-paused-style';
        st.textContent = [
            '.hr-paused-ov{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;',
            'justify-content:center;padding:20px;background:rgba(7,13,24,0.72);',
            '-webkit-backdrop-filter:blur(5px);backdrop-filter:blur(5px);opacity:0;transition:opacity .22s ease;',
            'font-family:"Montserrat",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;}',
            '.hr-paused-ov.is-open{opacity:1;}',
            '.hr-paused-box{width:100%;max-width:406px;background:#fff;border-radius:22px;padding:34px 26px 26px;',
            'text-align:center;box-shadow:0 26px 60px -14px rgba(0,0,0,.45);transform:translateY(14px) scale(.97);',
            'transition:transform .26s cubic-bezier(.22,1,.36,1);max-height:calc(100vh - 40px);overflow-y:auto;}',
            '.hr-paused-ov.is-open .hr-paused-box{transform:none;}',
            '.hr-paused-ico{width:64px;height:64px;margin:0 auto 20px;border-radius:50%;display:flex;',
            'align-items:center;justify-content:center;background:#fff8e1;border:1px solid #ffe28a;}',
            '.hr-paused-box h3{margin:0 0 12px;font-size:1.24rem;font-weight:800;line-height:1.3;color:#0f172a;',
            'letter-spacing:-.01em;}',
            '.hr-paused-box p{margin:0;font-size:.95rem;font-weight:400;line-height:1.65;color:#475569;}',
            '.hr-paused-box p strong{color:#0f172a;font-weight:700;}',
            '.hr-paused-btn{margin-top:24px;width:100%;padding:14px 20px;border:0;border-radius:13px;cursor:pointer;',
            'background:linear-gradient(135deg,#0066ff,#0056b3);color:#fff;font-family:inherit;font-size:.95rem;',
            'font-weight:700;letter-spacing:.01em;transition:filter .18s ease,transform .18s ease;}',
            '.hr-paused-btn:hover{filter:brightness(1.08);}',
            '.hr-paused-btn:active{transform:translateY(1px);}',
            '.hr-paused-btn:focus-visible{outline:3px solid rgba(0,102,255,.35);outline-offset:2px;}',
            '@media (max-width:380px){.hr-paused-box{padding:28px 20px 22px;}.hr-paused-box h3{font-size:1.1rem;}}',
            '@media (prefers-reduced-motion:reduce){.hr-paused-ov,.hr-paused-box{transition:none;}}'
        ].join('');
        document.head.appendChild(st);
    }

    function build() {
        injectStyles();
        var ov = document.createElement('div');
        ov.className = 'hr-paused-ov';
        ov.setAttribute('role', 'dialog');
        ov.setAttribute('aria-modal', 'true');
        ov.setAttribute('aria-labelledby', 'hr-paused-title');
        ov.innerHTML =
            '<div class="hr-paused-box">' +
            '<div class="hr-paused-ico" aria-hidden="true">' +
            '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#d9a400" stroke-width="2" ' +
            'stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"></circle>' +
            '<line x1="10" y1="9" x2="10" y2="15"></line><line x1="14" y1="9" x2="14" y2="15"></line></svg>' +
            '</div>' +
            '<h3 id="hr-paused-title">Prenotazioni temporaneamente sospese</h3>' +
            '<p>In questo momento <strong>non accettiamo nuove prenotazioni</strong>: ' +
            'l\'attività è temporaneamente ferma. Torneremo presto, grazie per la comprensione!</p>' +
            '<button type="button" class="hr-paused-btn">Ho capito</button>' +
            '</div>';
        document.body.appendChild(ov);

        ov.addEventListener('click', function (e) {
            if (e.target === ov || e.target.classList.contains('hr-paused-btn')) close();
        });
        return ov;
    }

    function onKey(e) {
        if (e.key === 'Escape' || e.key === 'Esc') close();
    }

    function open() {
        if (!overlay) overlay = build();
        if (overlay.classList.contains('is-open')) return;
        lastFocus = document.activeElement;
        overlay.style.display = 'flex';
        // forza il reflow cosi la transizione parte davvero
        void overlay.offsetWidth;
        overlay.classList.add('is-open');
        document.addEventListener('keydown', onKey);
        var btn = overlay.querySelector('.hr-paused-btn');
        if (btn) btn.focus();
    }

    function close() {
        if (!overlay) return;
        overlay.classList.remove('is-open');
        document.removeEventListener('keydown', onKey);
        setTimeout(function () {
            if (overlay && !overlay.classList.contains('is-open')) overlay.style.display = 'none';
        }, 240);
        if (lastFocus && typeof lastFocus.focus === 'function') lastFocus.focus();
        lastFocus = null;
    }

    // Intercetta il click in fase di cattura: cosi non parte ne l'invio
    // del messaggio ne il tracciamento della conversione.
    document.addEventListener('click', function (e) {
        var el = e.target && e.target.closest ? e.target.closest(TRIGGERS) : null;
        if (!el) return;
        e.preventDefault();
        e.stopImmediatePropagation();
        open();
    }, true);

    // Rete di sicurezza: qualsiasi altro tentativo di aprire WhatsApp.
    var nativeOpen = window.open;
    window.open = function (url) {
        if (typeof url === 'string' && /wa\.me|api\.whatsapp\.com/i.test(url)) {
            open();
            return null;
        }
        return nativeOpen.apply(window, arguments);
    };
})();
