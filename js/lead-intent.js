/* ============================================================
   Jorge Ramirez Group — stage-two lead capture on /thank-you.
   The first form asks the minimum. Once someone has already
   said yes, this asks the two questions that actually decide
   whether Jorge calls today or in six months.
   Self-contained: injects its own style + markup. EN/ES aware.
   ============================================================ */
(function () {
  'use strict';
  if (document.getElementById('jrg-stage2')) return;
  if (!/thank-you/.test(location.pathname)) return;

  var lead = null;
  try { lead = JSON.parse(localStorage.getItem('jrg_last_lead') || 'null'); } catch (e) { /* private mode */ }
  // Only follow a submit from this session; a stale token means a bookmarked page.
  if (!lead || !lead.at || Date.now() - lead.at > 30 * 60 * 1000) return;
  try { if (localStorage.getItem('jrg_stage2_done') === lead.email) return; } catch (e) { /* ignore */ }

  var isES = (document.documentElement.lang || '').toLowerCase().indexOf('es') === 0;
  var T = isES ? {
    eyebrow: 'UNA COSA MÁS',
    head: 'Dos preguntas y ya',
    sub: 'Esto decide si le conviene hablar esta semana o en unos meses. Si prefiere saltarlo, no hay problema.',
    when: '¿Para cuándo está pensando?',
    whenOpts: ['Ya estoy listo', 'En 1 a 3 meses', 'En 3 a 6 meses', 'Más de 6 meses', 'Solo estoy investigando'],
    best: '¿Cuál es el mejor momento para llamarle?',
    bestOpts: ['Mañanas', 'Tardes', 'Noches', 'Fines de semana', 'Prefiero texto'],
    phone: 'Teléfono (opcional)',
    waiver: 'Puede recibir servicios de bienes raíces sin dar su teléfono.',
    send: 'Enviar',
    skip: 'Saltar',
    done: 'Listo. Jorge tendrá esto antes de contactarle.'
  } : {
    eyebrow: 'ONE MORE THING',
    head: 'Two questions and you are done',
    sub: 'This decides whether it makes sense to talk this week or in a few months. Skip it if you would rather not — no problem either way.',
    when: 'What is your timeframe?',
    whenOpts: ['I am ready now', '1 to 3 months', '3 to 6 months', 'More than 6 months', 'Just researching'],
    best: 'When is the best time to reach you?',
    bestOpts: ['Mornings', 'Afternoons', 'Evenings', 'Weekends', 'Text me instead'],
    phone: 'Phone (optional)',
    waiver: 'You can get real estate help without giving your phone number.',
    send: 'Send',
    skip: 'Skip',
    done: 'Got it. Jorge will have this before he reaches out.'
  };

  var css = [
    '#jrg-stage2{margin:28px auto 0;max-width:640px;text-align:left;',
    'border:1px solid var(--border-light,#E8E4DC);background:var(--white,#fff);',
    'border-radius:var(--radius,8px);padding:26px 24px 22px;opacity:0;transform:translateY(12px);',
    'transition:opacity .7s ease-in-out,transform .7s ease-in-out}',
    '#jrg-stage2.jrg-in{opacity:1;transform:none}',
    '#jrg-stage2 .s2-eyebrow{font-family:var(--font-body,Inter,sans-serif);font-size:11px;font-weight:600;',
    'letter-spacing:.14em;text-transform:uppercase;color:var(--gold-text,#8A6D14);margin:0 0 8px}',
    '#jrg-stage2 h2{font-family:var(--font-display,"Playfair Display",Georgia,serif);font-weight:400;',
    'font-size:clamp(1.4rem,3.4vw,1.85rem);line-height:1.25;margin:0 0 8px;color:var(--dark-gray,#1A1A1A)}',
    '#jrg-stage2 .s2-sub{font-family:var(--font-body,Inter,sans-serif);font-size:.95rem;line-height:1.65;',
    'color:var(--text-light,#666);margin:0 0 20px}',
    '#jrg-stage2 label{display:block;font-family:var(--font-body,Inter,sans-serif);font-size:.82rem;',
    'font-weight:600;letter-spacing:.02em;color:var(--text-gray,#2C2C2C);margin:0 0 6px}',
    '#jrg-stage2 .s2-row{margin:0 0 16px}',
    '#jrg-stage2 select,#jrg-stage2 input[type=tel]{width:100%;padding:12px 13px;font-size:16px;',
    'font-family:var(--font-body,Inter,sans-serif);color:var(--text-gray,#2C2C2C);background:#fff;',
    'border:1px solid var(--border-light,#E8E4DC);border-radius:var(--radius,8px);appearance:none}',
    '#jrg-stage2 select:focus-visible,#jrg-stage2 input:focus-visible{outline:2px solid var(--gold-text,#8A6D14);outline-offset:1px}',
    '#jrg-stage2 .s2-waiver{font-size:.74rem;color:#8a8a8a;margin:6px 0 0;line-height:1.5}',
    '#jrg-stage2 .s2-actions{display:flex;align-items:center;gap:14px;margin-top:20px;flex-wrap:wrap}',
    '#jrg-stage2 .s2-send{min-height:48px;padding:0 30px;border:0;cursor:pointer;',
    'background:var(--dark-gray,#1A1A1A);color:#fff;font-family:var(--font-body,Inter,sans-serif);',
    'font-size:.82rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;',
    'border-radius:var(--radius,8px);transition:background-color .2s ease}',
    '#jrg-stage2 .s2-send:hover{background:var(--gold-text,#8A6D14)}',
    '#jrg-stage2 .s2-skip{background:none;border:0;cursor:pointer;font-family:var(--font-body,Inter,sans-serif);',
    'font-size:.85rem;color:var(--text-light,#666);text-decoration:underline;padding:8px 2px}',
    '#jrg-stage2 .s2-done{font-family:var(--font-body,Inter,sans-serif);font-size:1rem;',
    'color:var(--text-gray,#2C2C2C);margin:0;line-height:1.6}',
    '@media (prefers-reduced-motion:reduce){#jrg-stage2{transition:none;opacity:1;transform:none}}'
  ].join('');

  function opts(list) {
    return '<option value="">—</option>' + list.map(function (o) {
      return '<option value="' + o.replace(/"/g, '&quot;') + '">' + o + '</option>';
    }).join('');
  }

  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  var wrap = document.createElement('section');
  wrap.id = 'jrg-stage2';
  wrap.setAttribute('aria-labelledby', 'jrg-s2-head');
  wrap.innerHTML =
    '<p class="s2-eyebrow">' + T.eyebrow + '</p>' +
    '<h2 id="jrg-s2-head">' + T.head + '</h2>' +
    '<p class="s2-sub">' + T.sub + '</p>' +
    '<form id="jrg-s2-form" action="https://formsubmit.co/jorgeramirez76@gmail.com" method="POST">' +
      '<input type="hidden" name="_subject" value="Lead detail — stage 2">' +
      '<input type="hidden" name="_captcha" value="false">' +
      '<input type="hidden" name="_next" value="' + location.origin + location.pathname + '?s2=1">' +
      '<input type="hidden" name="name" value="' + (lead.name || '').replace(/"/g, '&quot;') + '">' +
      '<input type="hidden" name="email" value="' + (lead.email || '').replace(/"/g, '&quot;') + '">' +
      '<input type="hidden" name="interest" value="' + (lead.interest || '').replace(/"/g, '&quot;') + '">' +
      '<div class="s2-row"><label for="jrg-s2-when">' + T.when + '</label>' +
      '<select id="jrg-s2-when" name="timeframe" required>' + opts(T.whenOpts) + '</select></div>' +
      '<div class="s2-row"><label for="jrg-s2-best">' + T.best + '</label>' +
      '<select id="jrg-s2-best" name="best_time">' + opts(T.bestOpts) + '</select></div>' +
      (lead.phone ? '<input type="hidden" name="phone" value="' + lead.phone.replace(/"/g, '&quot;') + '">' :
        '<div class="s2-row"><label for="jrg-s2-phone">' + T.phone + '</label>' +
        '<input id="jrg-s2-phone" type="tel" name="phone" autocomplete="tel">' +
        '<p class="s2-waiver">' + T.waiver + '</p></div>') +
      '<div class="s2-actions">' +
        '<button type="submit" class="s2-send">' + T.send + '</button>' +
        '<button type="button" class="s2-skip">' + T.skip + '</button>' +
      '</div>' +
    '</form>';

  // Sit inside the content column, above the footer — never after it.
  function place(el) {
    var footer = document.querySelector('footer, .site-footer, #footer');
    if (footer && footer.parentNode) { footer.parentNode.insertBefore(el, footer); return; }
    var main = document.querySelector('main');
    if (main) { main.appendChild(el); return; }
    document.body.appendChild(el);
  }

  function mount() {
    place(wrap);
    // Not rAF alone — it is throttled in background tabs, which would strand the panel at opacity 0.
    setTimeout(function () { wrap.classList.add('jrg-in'); }, 30);

    wrap.querySelector('.s2-skip').addEventListener('click', function () {
      try { localStorage.setItem('jrg_stage2_done', lead.email || '1'); } catch (e) { /* ignore */ }
      wrap.remove();
    });
    wrap.querySelector('#jrg-s2-form').addEventListener('submit', function () {
      try { localStorage.setItem('jrg_stage2_done', lead.email || '1'); } catch (e) { /* ignore */ }
    });
  }

  // Returning from the stage-two post: confirm instead of re-asking.
  if (/[?&]s2=1/.test(location.search)) {
    try { localStorage.setItem('jrg_stage2_done', lead.email || '1'); } catch (e) { /* ignore */ }
    var ok = document.createElement('section');
    ok.id = 'jrg-stage2';
    ok.className = 'jrg-in';
    ok.innerHTML = '<p class="s2-done">' + T.done + '</p>';
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { place(ok); });
    else place(ok);
    return;
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
