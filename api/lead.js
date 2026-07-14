// Serverless lead handler for The Jorge Ramirez Group.
//
// STATUS: deployed but NOT yet wired to the forms. The website forms currently
// POST directly to FormSubmit (which works from the browser). FormSubmit is behind
// Cloudflare and 403s any *server-side* call, so this function delivers leads via
// first-party channels instead. Flip the form actions to "/api/lead" ONLY AFTER at
// least one channel below is configured in Vercel env vars.
//
// Delivery (best-effort, in parallel — a lead succeeds if ANY channel succeeds):
//   1. Twilio SMS to Jorge   — TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM, LEAD_ALERT_TO
//   2. CRM webhook           — CRM_WEBHOOK_URL
//   3. Email via Resend      — RESEND_API_KEY, LEAD_EMAIL (to), RESEND_FROM (verified sender)
//
// Set these in Vercel → Project → Settings → Environment Variables, then redeploy.

const ORIGIN = "https://thejorgeramirezgroup.com";

function safeNext(next) {
  if (typeof next === "string") {
    if (next.startsWith("/")) return next;
    if (next.startsWith(ORIGIN)) return next.slice(ORIGIN.length) || "/";
  }
  return "/thank-you";
}

async function textJorge(lead) {
  const { TWILIO_ACCOUNT_SID: sid, TWILIO_AUTH_TOKEN: token, TWILIO_FROM: from, LEAD_ALERT_TO: to } = process.env;
  if (!sid || !token || !from || !to) return { skipped: "twilio" };
  const body =
    `New web lead — ${lead.name || "?"}\n` +
    `${lead.phone || "no phone"} · ${lead.email || "no email"}\n` +
    (lead.intent ? `Wants: ${lead.intent}\n` : "") +
    (lead.town ? `Town: ${lead.town}\n` : "") +
    (lead.message ? `"${lead.message.slice(0, 200)}"` : "");
  const auth = Buffer.from(`${sid}:${token}`).toString("base64");
  const res = await fetch(`https://api.twilio.com/2010-04-01/Accounts/${sid}/Messages.json`, {
    method: "POST",
    headers: { Authorization: `Basic ${auth}`, "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ To: to, From: from, Body: body }),
  });
  if (!res.ok) throw new Error(`twilio ${res.status}: ${(await res.text()).slice(0, 200)}`);
  return { ok: "twilio" };
}

async function pushCRM(lead) {
  const url = process.env.CRM_WEBHOOK_URL;
  if (!url) return { skipped: "crm" };
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
    `<p>I put this together from years of helping New Jersey families with the same ${topic}. If a question comes up, just reply to this email or text me at 908-317-3227 — no pressure at all.</p>` +
    `<p>Talk soon,<br>Jorge Ramirez<br>The Jorge Ramirez Group &middot; Keller Williams Premier Properties<br>908-317-3227 &middot; jorge.ramirez@kw.com</p>` +
    `<hr style="border:none;border-top:1px solid #eee;margin:24px 0 12px">` +
    `<p style="font-size:12px;color:#999">You're receiving this because you requested a free guide at thejorgeramirezgroup.com.<br>${addr}<br><a href="${unsub}" style="color:#999">Unsubscribe</a></p>` +
    `</div>`;
  const text =
    `Hi ${first},\n\nThanks for requesting ${guide.name}. Download your copy here:\n${guide.url}\n\n` +
    `I put this together from years of helping NJ families with the same ${topic}. If a question comes up, ` +
    `reply to this email or text me at 908-317-3227 — no pressure.\n\nTalk soon,\nJorge Ramirez\n` +
    `The Jorge Ramirez Group · Keller Williams Premier Properties\n908-317-3227 · jorge.ramirez@kw.com\n\n` +
    `You're receiving this because you requested a free guide at thejorgeramirezgroup.com.\n${addr}\nUnsubscribe: ${unsub}`;
  const res = await fetch("https://api.resend.com/emails", {
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
  const html =
    `<h2>New website lead</h2>` +
    `<p><b>Name:</b> ${lead.name}<br><b>Phone:</b> ${lead.phone}<br><b>Email:</b> ${lead.email}<br>` +
    `<b>Town:</b> ${lead.town}<br><b>Looking to:</b> ${lead.intent}</p>` +
    `<p><b>Message:</b><br>${(lead.message || "").replace(/\n/g, "<br>")}</p>` +
    `<p style="color:#888">Page: ${lead.source} · ${lead.receivedAt}</p>`;
  const res = await fetch("https://api.resend.com/emails", {
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

  const b = (req.body && typeof req.body === "object") ? req.body : {};
  const wantsJson =
    (req.headers.accept || "").includes("application/json") ||
    (req.headers["x-requested-with"] || "").toLowerCase() === "xmlhttprequest";
  const next = safeNext(b._next);

  if (b._honey) {
    return wantsJson ? res.status(200).json({ ok: true }) : res.redirect(303, next);
  }

  const lead = {
    name: (b.name || b.Name || "").toString().slice(0, 200),
    email: (b.email || b.Email || "").toString().slice(0, 200),
    phone: (b.phone || b.Phone || "").toString().slice(0, 60),
    town: (b.town || b.Town || "").toString().slice(0, 120),
    intent: (b.intent || b.interest || b.looking_to || "").toString().slice(0, 120),
    guide: (b.guide || "").toString().slice(0, 40),
    message: (b.message || b.Message || "").toString().slice(0, 2000),
    source: (b._source || req.headers.referer || "").toString().slice(0, 300),
    // SMS opt-in (forwarded to the CRM so ConsentRecord captures the exact language + IP)
    smsConsent: b.smsConsent === true || b.smsConsent === "true" || b.smsConsent === "on",
    consentLanguage: (b.consentLanguage || "").toString().slice(0, 2048),
    receivedAt: new Date().toISOString(),
  };

  const results = await Promise.allSettled([textJorge(lead), pushCRM(lead), emailViaResend(lead), emailGuideToLead(lead)]);
  const delivered = results.some((r) => r.status === "fulfilled" && r.value && r.value.ok);
  results.forEach((r, i) => {
    const label = ["twilio", "crm", "resend", "guide-email"][i];
    if (r.status === "rejected") console.error(`lead delivery failed [${label}]:`, r.reason);
  });
  if (!delivered) console.error("LEAD NOT DELIVERED — no channel configured/succeeded:", JSON.stringify(lead));

  if (!delivered) {
    const sep = next.includes("?") ? "&" : "?";
    return wantsJson ? res.status(502).json({ ok: false }) : res.redirect(303, next + sep + "err=1");
  }
  return wantsJson ? res.status(200).json({ ok: true }) : res.redirect(303, next);
}
