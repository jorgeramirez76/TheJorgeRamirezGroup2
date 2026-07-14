/* Lead-magnet form handler for The Jorge Ramirez Group.
 * Captures a lead, pushes it to /api/lead (which fans out to the CRM + notifies Jorge),
 * and delivers the e-book to the visitor instantly via download — so the guide arrives
 * even before any email is configured. Reusable across the seller & buyer guide pages
 * via data-attributes on the .lm-form card: data-guide, data-pdf, data-source.
 */
(function () {
  "use strict";
  var card = document.getElementById("lmCard");
  var form = document.getElementById("lmForm");
  var success = document.getElementById("lmSuccess");
  var dl = document.getElementById("lmDownload");
  if (!card || !form || !success) return;

  var guide = card.getAttribute("data-guide") || "guide";
  var pdf = card.getAttribute("data-pdf") || "/guides/nj-home-seller-guide.pdf";
  var source = card.getAttribute("data-source") || (location.pathname || "").replace(/^\//, "");

  function deliver() {
    // Instant download of the e-book (same-origin, download attribute honored)
    try {
      var a = document.createElement("a");
      a.href = pdf;
      a.setAttribute("download", "");
      a.rel = "noopener";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (e) { /* fall back to the manual link below */ }
    if (dl) dl.setAttribute("href", pdf);
    // Swap form for the success/confirmation panel
    card.style.display = "none";
    success.style.display = "block";
    try { success.scrollIntoView({ behavior: "smooth", block: "center" }); } catch (e) {}
    try { if (window.gtag) gtag("event", "generate_lead", { form: "lead-magnet", guide: guide }); } catch (e) {}
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();

    // Honeypot — silently "succeed" for bots without capturing.
    var honey = form.querySelector('input[name="_honey"]');
    if (honey && honey.value) { deliver(); return; }

    var name = (form.querySelector('[name="name"]') || {}).value || "";
    var email = (form.querySelector('[name="email"]') || {}).value || "";
    var phone = (form.querySelector('[name="phone"]') || {}).value || "";
    name = name.trim(); email = email.trim(); phone = phone.trim();

    if (!name) { alert("Please enter your first name."); return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { alert("Please enter a valid email so we can follow up."); return; }

    // Optional SMS opt-in — a lead is only textable if they ticked the box AND gave a phone.
    var smsBox = form.querySelector('[name="smsConsent"]');
    var smsConsent = !!(smsBox && smsBox.checked) && !!phone;
    var consentLanguage = card.getAttribute("data-consent") || "";

    var btn = form.querySelector('button[type="submit"]');
    if (btn) { btn.disabled = true; btn.textContent = "Sending…"; }

    var payload = {
      name: name,
      email: email,
      phone: phone,
      smsConsent: smsConsent,
      emailConsent: true,
      consentLanguage: consentLanguage,
      intent: guide === "buyer" ? "Buyer guide download" : "Seller guide download",
      guide: guide,
      _source: source,
      _next: "/thank-you"
    };

    // Best-effort lead capture; delivery to the visitor is guaranteed regardless.
    var done = false;
    function finish() { if (done) return; done = true; deliver(); }

    var controller = ("AbortController" in window) ? new AbortController() : null;
    var timer = setTimeout(finish, 6000); // never make the user wait on the network

    fetch("/api/lead", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json", "X-Requested-With": "XMLHttpRequest" },
      body: JSON.stringify(payload),
      signal: controller ? controller.signal : undefined
    }).catch(function () { /* swallow — user still gets the guide */ })
      .finally(function () { clearTimeout(timer); finish(); });
  });
})();
