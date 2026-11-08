(() => {
  const S = window.SITE;
  const $ = (s) => document.querySelector(s);
  const inr = (n) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);
  const num = (el) => Math.max(0, parseFloat(el && el.value) || 0);

  // ---- mailto / tel helpers
  const mailto = (subject, body) => `mailto:${S.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  $('#act-mail').href = mailto(`Enquiry for ${S.name}`, 'Hello,\n\nI would like to know more about your jewellery collections.\n\nName:\nPhone:\n');
  const tryon = $('#tryon');
  if (tryon) tryon.href = mailto('Virtual try-on appointment', `Hello ${S.name},\n\nI would like to book a video try-on.\nPreferred date/time:\nPieces of interest:\n`);

  // ---- rates (sample values are labelled as sample when the live feed is down)
  const SAMPLE = { gold24: 12500, gold22: 11458.33, gold18: 9375, silver: 150 };
  let rates = { ...SAMPLE, live: false, updatedAt: null };
  const listeners = [];
  const rateFor = (metal, p) => metal === 'gold' ? (p === 24 ? rates.gold24 : p === 22 ? rates.gold22 : p === 18 ? rates.gold18 : rates.gold24 * p / 24) : rates.silver * p / 999;
  async function loadRates() {
    try {
      const r = await fetch('/api/rates', { cache: 'no-store' });
      const d = await r.json();
      if (!r.ok || !d.success || !(d.rates.gold24 > 0 && d.rates.silver > 0)) throw new Error('bad');
      rates = { ...d.rates, live: true, updatedAt: d.updatedAt };
    } catch (_) { if (!rates.live) rates = { ...SAMPLE, live: false, updatedAt: null }; }
    listeners.forEach((f) => f());
  }

  // ---- calculator + exchange
  const PURITIES = { gold: [24, 22, 18, 14], silver: [999, 925, 800] };
  const fill = (sel, metal) => { sel.innerHTML = PURITIES[metal].map((p) => `<option value="${p}">${metal === 'gold' ? p + 'K' : p + ' fine'}</option>`).join(''); sel.value = metal === 'gold' ? 22 : 925; };
  let lastTotal = 0;
  const cMetal = $('#c-metal'), cPurity = $('#c-purity'), xMetal = $('#x-metal'), xPurity = $('#x-purity');
  function calc() {
    const metal = cMetal.value, p = +cPurity.value, w = num($('#c-weight')), mk = Math.min(num($('#c-making')), 50);
    const rate = rateFor(metal, p), base = w * rate, making = base * mk / 100, gst = (base + making) * S.gst / 100, total = base + making + gst;
    lastTotal = total;
    $('#r-rate-l').textContent = `Rate (${metal === 'gold' ? p + 'K' : p + ' fine'})`; $('#r-rate').textContent = inr(rate) + ' / g';
    $('#r-base').textContent = inr(base); $('#r-making-l').textContent = `Making / labour (${mk}%)`; $('#r-making').textContent = inr(making);
    $('#r-gst-l').textContent = `GST (${S.gst}%)`; $('#r-gst').textContent = inr(gst); $('#r-total').textContent = inr(total);
    const old = num($('#x-weight')) * rateFor(xMetal.value, +xPurity.value) * (1 - Math.min(num($('#x-loss')), 50) / 100);
    $('#x-value').textContent = inr(old); $('#x-total').textContent = inr(total);
    $('#x-label').textContent = old > total ? 'Credit remaining with us' : 'Balance payable';
    $('#x-result').textContent = inr(Math.abs(total - old));
    const b = $('#rate-badge');
    b.className = 'badge' + (rates.live ? ' live' : '');
    b.textContent = rates.live ? `Live · ${new Date(rates.updatedAt).toLocaleTimeString('en-IN')}` : 'Sample rates (live feed unavailable)';
    document.querySelectorAll('[data-rate]').forEach((el) => { const [m, p] = el.dataset.rate.split(':'); el.textContent = inr(m === 'gold24' ? rates.gold24 : rateFor(m, +p)); });
    const note = $('#rates-note'); if (note) note.textContent = rates.live ? 'Live, per gram' : 'Sample rates, per gram';
  }
  if (cMetal) {
    fill(cPurity, 'gold'); fill(xPurity, 'gold');
    cMetal.addEventListener('change', () => { fill(cPurity, cMetal.value); calc(); });
    xMetal.addEventListener('change', () => { fill(xPurity, xMetal.value); calc(); });
    document.querySelectorAll('#calculator input, #calculator select').forEach((el) => el.addEventListener('input', calc));
    listeners.push(calc); calc();
  }

  // ---- toast
  const toast = (msg) => { const t = $('#toast'); t.textContent = msg; t.hidden = false; setTimeout(() => (t.hidden = true), 6000); };
  const q = new URLSearchParams(location.search).get('prebook');
  if (q === 'success') toast('Thank you! Your deposit payment is being confirmed. We will email you shortly.');
  if (q === 'cancelled') toast('Checkout cancelled. You have not been charged.');

  // ---- pre-booking dialog
  const dlg = $('#prebook'), form = $('#pb-form');
  const val = () => num(form.value), pct = () => +form.pct.value;
  const lockedRate = () => form.metal.value === 'S925' ? rateFor('silver', 925) : rateFor('gold', +form.metal.value);
  function summary() {
    $('#pb-rate-label').textContent = `Rate reference (${rates.live ? 'live' : 'sample'})`;
    $('#pb-rate').textContent = inr(lockedRate()) + '/g'; $('#pb-deposit').textContent = inr(Math.round(val() * pct() / 100));
    $('#pb-submit').textContent = `Pay ${inr(Math.round(val() * pct() / 100))} deposit`;
  }
  function openDialog(prefill) {
    if (prefill && lastTotal) form.value.value = Math.round(lastTotal);
    $('#pb-note').hidden = true; summary(); dlg.showModal();
  }
  $('#open-prebook').addEventListener('click', () => openDialog(false));
  const cp = $('#calc-prebook'); if (cp) cp.addEventListener('click', () => openDialog(true));
  $('#pb-close').addEventListener('click', () => dlg.close());
  dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
  form.addEventListener('input', summary); listeners.push(() => dlg.open && summary());

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const err = {}, f = (n) => form[n].value.trim();
    if (f('name').length < 2) err.name = 'Enter your full name';
    if (!/^[+()\d\s-]{8,16}$/.test(f('phone'))) err.phone = 'Enter a valid phone number';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f('email'))) err.email = 'Enter a valid email';
    if (f('item').length < 3) err.item = 'Describe the item';
    if (val() <= 0) err.value = 'Enter an estimated value';
    form.querySelectorAll('[data-err]').forEach((s) => (s.textContent = err[s.dataset.err] || ''));
    if (Object.keys(err).length) return;
    const btn = $('#pb-submit'); btn.disabled = true; btn.textContent = 'Opening secure checkout…';
    const payload = { name: f('name'), phone: f('phone'), email: f('email'), item: f('item'), metal: form.metal.value, estimatedValue: val(), depositPercent: pct() };
    try {
      const ctrl = new AbortController(); const timer = setTimeout(() => ctrl.abort(), 12000);
      const res = await fetch('/api/prebook', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal: ctrl.signal });
      clearTimeout(timer);
      const d = await res.json();
      if (res.ok && d.success && typeof d.checkoutUrl === 'string' && d.checkoutUrl.startsWith('https://')) { location.assign(d.checkoutUrl); return; }
      throw new Error(d.error || 'checkout failed');
    } catch (_) {
      btn.disabled = false; summary(); $('#pb-note').hidden = false;
      location.href = mailto(`Pre-booking request: ${payload.item}`, `Name: ${payload.name}\nPhone: ${payload.phone}\nEmail: ${payload.email}\nItem: ${payload.item}\nEstimated value: ${inr(payload.estimatedValue)}\nDeposit: ${payload.depositPercent}% (${inr(Math.round(payload.estimatedValue * payload.depositPercent / 100))})\nRate reference: ${inr(lockedRate())}/g (${rates.live ? 'live' : 'sample'})\n`);
    }
  });

  loadRates(); setInterval(loadRates, 60000);
})();
