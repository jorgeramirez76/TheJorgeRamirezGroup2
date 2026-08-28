// Serverless lead handler for The Jorge Ramirez Group.
//
// This first-party endpoint powers the valuation intake and lead-magnet forms.
// It deliberately reports success only after at least one configured delivery
// channel confirms receipt.
//
// Delivery (best-effort, in parallel — a lead succeeds if ANY channel succeeds):
//   1. Twilio SMS to Jorge   — TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM, LEAD_ALERT_TO
//   2. CRM webhook           — CRM_WEBHOOK_URL
//   3. Email via Resend      — RESEND_API_KEY, LEAD_EMAIL (to), RESEND_FROM (verified sender)
//
// Set these in Vercel → Project → Settings → Environment Variables, then redeploy.

const ORIGIN = "https://thejorgeramirezgroup.com";
const SMS_CONSENT_LANGUAGE =
  "I agree to receive text messages from The Jorge Ramirez Group about this home valuation request. Message and data rates may apply. Reply STOP to opt out. Consent is optional and is not a condition of service.";
const GUIDE_CONSENT_LANGUAGE =
  "I agree that Jorge Ramirez, licensed NJ real estate agent (The Jorge Ramirez Group at Keller Williams, brokerage of record), may call and text me, including by automated technology, about my real estate request and to send related updates such as appointment and showing reminders, new-listing and price alerts, home-value follow-ups, and transaction updates. Consent is not a condition of getting the guide or of any purchase. Message frequency varies, typically a few per month. Message and data rates may apply. Reply STOP to opt out, HELP for help.";
const LEAD_RATE_WINDOW_MS = 10 * 60 * 1000;
const LEAD_RATE_MAX = 5;
const leadAttempts = new Map();

function safeNext(next, fallback = "/thank-you") {
  if (typeof next === "string") {
    if (/^\/(?![\\/])[^\r\n]*$/.test(next)) return next;
    if (next === ORIGIN) return "/";
    if (next.startsWith(`${ORIGIN}/`)) {
      const path = next.slice(ORIGIN.length);
      if (/^\/(?![\\/])[^\r\n]*$/.test(path)) return path;
    }
  }
  return fallback;
}

function clean(value, maxLength) {
  if (typeof value !== "string" && typeof value !== "number" && typeof value !== "boolean") {
    return "";
  }
  return String(value).trim().slice(0, maxLength);
}

function hasStructuredValues(body) {
  return Object.values(body).some((value) => value !== null && typeof value === "object");
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  })[character]);
}

function isLikelySpam(body, requireValuationTiming = false) {
  if (body._honey) return true;
  if (clean(body.leadType, 40) !== "home-valuation") return false;
  const timingMarker = clean(body._startedAt, 40);
  if (!timingMarker) return requireValuationTiming;
  const startedAt = Number(timingMarker);
  const elapsed = Date.now() - startedAt;
  return !Number.isFinite(startedAt) || elapsed < 1_500 || elapsed > 86_400_000;
}

function clientIp(headers) {
  const forwarded = clean(headers["x-forwarded-for"], 300).split(",")[0].trim();
  return forwarded || clean(headers["x-real-ip"], 100);
}

function isLeadRateLimited(ip) {
  // Vercel supplies a client IP on production requests. If that identity is
  // unavailable, do not bypass the abuse control and fan out to providers.
  if (!ip) return true;
  const now = Date.now();
  const cutoff = now - LEAD_RATE_WINDOW_MS;

  for (const [key, timestamps] of leadAttempts) {
    const recent = timestamps.filter((timestamp) => timestamp > cutoff);
    if (recent.length) leadAttempts.set(key, recent);
    else leadAttempts.delete(key);
  }

  const attempts = leadAttempts.get(ip) || [];
  if (attempts.length >= LEAD_RATE_MAX) return true;
  attempts.push(now);
  leadAttempts.set(ip, attempts);
  return false;
}

function withState(next, state) {
  return `${next}${next.includes("?") ? "&" : "?"}${state}`;
}

function valuationState(next, state, fragment) {
  return `${withState(next, state)}#${fragment}`;
}

function deliveryTimeoutMs() {
  const configured = Number(process.env.LEAD_DELIVERY_TIMEOUT_MS);
  if (!Number.isFinite(configured) || configured <= 0) return 8_000;
  return Math.max(25, Math.min(configured, 12_000));
}

function consentLanguageFor(leadType, guide) {
  if (leadType === "home-valuation") return SMS_CONSENT_LANGUAGE;
  if (guide === "buyer" || guide === "seller") return GUIDE_CONSENT_LANGUAGE;
  return "";
}

async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  let timeoutId;
  const timeout = new Promise((_, reject) => {
    timeoutId = setTimeout(() => {
      controller.abort();
      reject(new Error("delivery provider timed out"));
    }, deliveryTimeoutMs());
  });

  try {
    return await Promise.race([
      fetch(url, { ...options, signal: controller.signal }),
      timeout,
    ]);
  } finally {
    clearTimeout(timeoutId);
  }
}

function validateLead(lead) {
  const errors = [];
  if (lead.name.length < 2) errors.push("name");
  if (!lead.email && !lead.phone) errors.push("contact");
  if (lead.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(lead.email)) errors.push("email");
  if (lead.phone && lead.phone.replace(/\D/g, "").length < 7) errors.push("phone");
  if (lead.leadType === "home-valuation" && lead.address.length < 5) errors.push("address");
  return errors;
}

async function textJorge(lead) {
  const { TWILIO_ACCOUNT_SID: sid, TWILIO_AUTH_TOKEN: token, TWILIO_FROM: from, LEAD_ALERT_TO: to } = process.env;
  if (!sid || !token || !from || !to) return { skipped: "twilio" };
  const body =
    `New web lead — ${lead.name || "?"}\n` +
    `${lead.phone || "no phone"} · ${lead.email || "no email"}\n` +
    (lead.intent ? `Wants: ${lead.intent}\n` : "") +
    (lead.address ? `Address: ${lead.address}\n` : "") +
    (lead.town ? `Town: ${lead.town}\n` : "") +
    (lead.timeframe ? `Timing: ${lead.timeframe}\n` : "") +
    (lead.message ? `"${lead.message.slice(0, 200)}"` : "");
  const auth = Buffer.from(`${sid}:${token}`).toString("base64");
  const res = await fetchWithTimeout(`https://api.twilio.com/2010-04-01/Accounts/${sid}/Messages.json`, {
    method: "POST",
    headers: { Authorization: `Basic ${auth}`, "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ To: to, From: from, Body: body }),
  });
  if (!res.ok) throw new Error(`twilio ${res.status}`);
  return { ok: "twilio" };
}

async function pushCRM(lead) {
  const url = process.env.CRM_WEBHOOK_URL;
  if (!url) return { skipped: "crm" };
  const headers = { "Content-Type": "application/json" };
  if (process.env.SITE_LEAD_WEBHOOK_SECRET) headers["x-webhook-secret"] = process.env.SITE_LEAD_WEBHOOK_SECRET;
  const res = await fetchWithTimeout(url, {
    method: "POST",
    headers,
    body: JSON.stringify(lead),
  });
  if (!res.ok) throw new Error(`crm ${res.status}`);
  return { ok: "crm" };
}

// Guide (lead magnet) catalog — maps the form's `guide` field to a title + hosted PDF.
const GUIDES = {
  seller: { name: "The NJ Home Seller's Playbook", url: ORIGIN + "/guides/nj-home-seller-guide.pdf" },
  buyer: { name: "The NJ Home Buyer's Guide", url: ORIGIN + "/guides/nj-home-buyer-guide.pdf" },
};

// Emails the requested e-book to the LEAD (not Jorge). Instant download already delivers
// the PDF client-side; this is the email copy + follow-up, active once Resend is configured.
async function emailGuideToLead(lead) {
  const key = process.env.RESEND_API_KEY;
  const from = process.env.RESEND_FROM;
  const guide = GUIDES[lead.guide];
  if (!key || !from || !lead.email || !guide) return { skipped: "guide-email" };
  const first = ((lead.name || "there").split(" ")[0] || "there").replace(/[<>]/g, "");
  const topic = lead.guide === "buyer" ? "home search" : "home sale";
  const unsub = "mailto:jorge@thejorgeramirezgroup.com?subject=unsubscribe";
  const addr = "The Jorge Ramirez Group · 488 Springfield Avenue, Summit, NJ 07901";
  const html =
    `<div style="font-family:-apple-system,Segoe UI,Arial,sans-serif;font-size:15px;line-height:1.6;color:#222;max-width:560px">` +
    `<p>Hi ${first},</p>` +
    `<p>Thanks for requesting <b>${guide.name}</b> — here's your copy to download:</p>` +
    `<p><a href="${guide.url}" style="display:inline-block;padding:12px 22px;background:#1A1A1A;color:#fff;border-radius:8px;text-decoration:none;font-weight:600">Download the guide (PDF)</a></p>` +
    `<p>If the button doesn't work, use this link:<br><a href="${guide.url}">${guide.url}</a></p>` +
    `<p>I put this together from experience helping New Jersey buyers and sellers with the same ${topic}. If a question comes up, just reply to this email or text me at 908-230-7844 — no pressure at all.</p>` +
    `<p>Talk soon,<br>Jorge Ramirez<br>The Jorge Ramirez Group &middot; Keller Williams Premier Properties<br>908-230-7844 &middot; jorge.ramirez@kw.com</p>` +
    `<hr style="border:none;border-top:1px solid #eee;margin:24px 0 12px">` +
    `<p style="font-size:12px;color:#999">You're receiving this because you requested a free guide at thejorgeramirezgroup.com.<br>${addr}<br><a href="${unsub}" style="color:#999">Unsubscribe</a></p>` +
    `</div>`;
  const text =
    `Hi ${first},\n\nThanks for requesting ${guide.name}. Download your copy here:\n${guide.url}\n\n` +
    `I put this together from experience helping New Jersey buyers and sellers with the same ${topic}. If a question comes up, ` +
    `reply to this email or text me at 908-230-7844 — no pressure.\n\nTalk soon,\nJorge Ramirez\n` +
    `The Jorge Ramirez Group · Keller Williams Premier Properties\n908-230-7844 · jorge.ramirez@kw.com\n\n` +
    `You're receiving this because you requested a free guide at thejorgeramirezgroup.com.\n${addr}\nUnsubscribe: ${unsub}`;
  const res = await fetchWithTimeout("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      from, to: lead.email, reply_to: "jorge@thejorgeramirezgroup.com",
      subject: `Your copy of ${guide.name}`, html, text,
      headers: { "List-Unsubscribe": `<${unsub}>`, "List-Unsubscribe-Post": "List-Unsubscribe=One-Click" },
    }),
  });
  if (!res.ok) throw new Error(`guide-email ${res.status}`);
  return { ok: "guide-email" };
}

async function emailViaResend(lead) {
  const key = process.env.RESEND_API_KEY;
  const to = process.env.LEAD_EMAIL;
  const from = process.env.RESEND_FROM;
  if (!key || !to || !from) return { skipped: "resend" };
  const safe = Object.fromEntries(
    Object.entries(lead).map(([keyName, value]) => [keyName, escapeHtml(value)]),
  );
  const html =
    `<h2>New website lead</h2>` +
    `<p><b>Name:</b> ${safe.name}<br><b>Phone:</b> ${safe.phone}<br><b>Email:</b> ${safe.email}<br>` +
    `<b>Address:</b> ${safe.address}<br><b>Town:</b> ${safe.town}<br>` +
    `<b>Timing:</b> ${safe.timeframe}<br><b>Looking to:</b> ${safe.intent}</p>` +
    `<p><b>Message:</b><br>${safe.message.replace(/\n/g, "<br>")}</p>` +
    `<p style="color:#888">Page: ${safe.source} · ${safe.receivedAt}</p>`;
  const res = await fetchWithTimeout("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from, to, reply_to: lead.email || undefined, subject: `New Lead — ${lead.name || "Website"}`, html }),
  });
  if (!res.ok) throw new Error(`resend ${res.status}`);
  return { ok: "resend" };
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).send("Method Not Allowed");
  }

  const b = (req.body && typeof req.body === "object" && !Array.isArray(req.body)) ? req.body : {};
  const headers = req.headers || {};
  const ip = clientIp(headers);
  const wantsJson =
    (headers.accept || "").includes("application/json") ||
    (headers["x-requested-with"] || "").toLowerCase() === "xmlhttprequest";
  if (hasStructuredValues(b)) {
    return wantsJson
      ? res.status(400).json({ ok: false, code: "invalid_payload" })
      : res.redirect(303, "/thank-you?err=invalid");
  }
  const leadType = clean(b.leadType, 40);
  const isValuation = leadType === "home-valuation";
  const next = isValuation
    ? safeNext(b._next, "/home-valuation")
    : safeNext(b._next);
  const errorNext = isValuation
    ? ""
    : safeNext(b._errorNext, withState(next, "err=1"));

  if (isLikelySpam(b, wantsJson)) {
    return wantsJson
      ? res.status(200).json({ ok: true, accepted: false })
      : res.redirect(303, next);
  }

  const phone = clean(b.phone || b.Phone, 60);
  const guide = clean(b.guide, 40);
  const receivedAt = new Date().toISOString();
  const requestedSmsConsent =
    b.smsConsent === true || b.smsConsent === "true" || b.smsConsent === "on";
  const canonicalConsentLanguage = consentLanguageFor(leadType, guide);
  const smsConsent = Boolean(requestedSmsConsent && phone && canonicalConsentLanguage);
  const lead = {
    leadType,
    name: clean(b.name || b.Name, 200),
    email: clean(b.email || b.Email, 200).toLowerCase(),
    phone,
    address: clean(b.address || b.Address, 300),
    town: clean(b.town || b.Town, 120),
    timeframe: clean(b.timeframe, 120),
    intent: clean(b.intent || b.interest || b.looking_to, 120),
    guide,
    message: clean(b.message || b.Message, 2000),
    source: clean(b._source || headers.referer, 300),
    // Canonicalize consent server-side so the CRM receives an auditable record
    // rather than disclosure language supplied by the browser.
    smsConsent,
    consentLanguage: smsConsent ? canonicalConsentLanguage : "",
    consentAt: smsConsent ? receivedAt : "",
    consentIp: smsConsent ? ip : "",
    receivedAt,
  };

  const validationErrors = validateLead(lead);
  if (validationErrors.length) {
    return wantsJson
      ? res.status(400).json({ ok: false, code: "invalid_lead", fields: validationErrors })
      : res.redirect(303, isValuation
        ? valuationState(next, "err=invalid", "valuation-invalid")
        : errorNext);
  }

  if (isLeadRateLimited(ip)) {
    res.setHeader("Retry-After", "600");
    return wantsJson
      ? res.status(429).json({ ok: false, code: "rate_limited" })
      : res.redirect(303, isValuation
        ? valuationState(next, "err=rate", "valuation-rate")
        : errorNext);
  }

  const results = await Promise.allSettled([textJorge(lead), pushCRM(lead), emailViaResend(lead), emailGuideToLead(lead)]);
  const delivered = results.some((r) => r.status === "fulfilled" && r.value && r.value.ok);
  results.forEach((r, i) => {
    const label = ["twilio", "crm", "resend", "guide-email"][i];
    if (r.status === "rejected") console.error(`lead delivery failed [${label}]:`, r.reason);
  });
  if (!delivered) {
    // Keep lead PII out of platform logs; the delivery-channel failures above
    // provide enough operational context to diagnose configuration problems.
    console.error("LEAD NOT DELIVERED — no configured channel confirmed receipt", {
      leadType: lead.leadType,
      receivedAt: lead.receivedAt,
    });
  }

  if (!delivered) {
    return wantsJson
      ? res.status(502).json({ ok: false, code: "delivery_failed" })
      : res.redirect(303, isValuation
        ? valuationState(next, "err=1", "valuation-error")
        : errorNext);
  }
  return wantsJson
    ? res.status(200).json({ ok: true, accepted: true })
    : res.redirect(303, isValuation
      ? valuationState(next, "submitted=1", "valuation-submitted")
      : next);
}
