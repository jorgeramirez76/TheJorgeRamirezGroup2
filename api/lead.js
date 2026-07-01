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
    message: (b.message || b.Message || "").toString().slice(0, 2000),
    source: (b._source || req.headers.referer || "").toString().slice(0, 300),
    receivedAt: new Date().toISOString(),
  };

  const results = await Promise.allSettled([textJorge(lead), pushCRM(lead), emailViaResend(lead)]);
  const delivered = results.some((r) => r.status === "fulfilled" && r.value && r.value.ok);
  results.forEach((r, i) => {
    const label = ["twilio", "crm", "resend"][i];
    if (r.status === "rejected") console.error(`lead delivery failed [${label}]:`, r.reason);
  });
  if (!delivered) console.error("LEAD NOT DELIVERED — no channel configured/succeeded:", JSON.stringify(lead));

  if (!delivered) {
    const sep = next.includes("?") ? "&" : "?";
    return wantsJson ? res.status(502).json({ ok: false }) : res.redirect(303, next + sep + "err=1");
  }
  return wantsJson ? res.status(200).json({ ok: true }) : res.redirect(303, next);
}
