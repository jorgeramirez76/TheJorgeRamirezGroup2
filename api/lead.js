// Serverless lead handler for The Jorge Ramirez Group.
// Captures a website lead, then (best-effort, in parallel):
//   1. Texts Jorge instantly via Twilio          (if TWILIO_* env vars set)
//   2. Pushes the lead to the CRM webhook         (if CRM_WEBHOOK_URL set)
//   3. Emails a durable copy via FormSubmit       (always — so a lead is never lost)
// Then redirects the visitor to the thank-you page (or returns JSON for AJAX).
//
// Set these in Vercel → Project → Settings → Environment Variables to enable SMS + CRM:
//   TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM  (a Twilio number, e.g. +1XXXXXXXXXX)
//   LEAD_ALERT_TO   (Jorge's mobile to receive the text, e.g. +19082307844)
//   CRM_WEBHOOK_URL (inbound webhook of the AI Sales Pipeline CRM)
//   LEAD_EMAIL      (optional; defaults to jorgeramirez76@gmail.com)

const ORIGIN = "https://thejorgeramirezgroup.com";

function safeNext(next) {
  if (typeof next === "string") {
    if (next.startsWith("/")) return next;
    if (next.startsWith(ORIGIN)) return next.slice(ORIGIN.length) || "/";
  }
  return "/thank-you";
}

async function textJorge(lead) {
  const sid = process.env.TWILIO_ACCOUNT_SID;
  const token = process.env.TWILIO_AUTH_TOKEN;
  const from = process.env.TWILIO_FROM;
  const to = process.env.LEAD_ALERT_TO;
  if (!sid || !token || !from || !to) return { skipped: "twilio env not set" };
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
  if (!res.ok) throw new Error(`twilio ${res.status}`);
  return { ok: true };
}

async function pushCRM(lead) {
  const url = process.env.CRM_WEBHOOK_URL;
  if (!url) return { skipped: "no CRM_WEBHOOK_URL" };
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(lead),
  });
  if (!res.ok) throw new Error(`crm ${res.status}`);
  return { ok: true };
}

async function emailLead(lead) {
  const email = process.env.LEAD_EMAIL || "jorgeramirez76@gmail.com";
  const res = await fetch(`https://formsubmit.co/ajax/${encodeURIComponent(email)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      _subject: `New Lead — ${lead.name || "Website"} (${lead.source || "site"})`,
      Name: lead.name,
      Email: lead.email,
      Phone: lead.phone,
      Town: lead.town,
      "Looking to": lead.intent,
      Message: lead.message,
      Page: lead.source,
    }),
  });
  if (!res.ok) throw new Error(`email ${res.status}`);
  return { ok: true };
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

  // Honeypot: bots fill the hidden _honey field. Silently accept + drop.
  if (b._honey) {
    return wantsJson ? res.status(200).json({ ok: true }) : res.redirect(303, safeNext(b._next));
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

  const results = await Promise.allSettled([textJorge(lead), pushCRM(lead), emailLead(lead)]);
  const emailResult = results[2];
  results.forEach((r, i) => {
    const label = ["twilio", "crm", "email"][i];
    if (r.status === "rejected") console.error(`lead delivery failed [${label}]:`, r.reason);
  });

  // If even the durable email copy failed, surface a soft error so the lead can retry.
  if (emailResult.status === "rejected") {
    return wantsJson
      ? res.status(502).json({ ok: false, error: "delivery_failed" })
      : res.redirect(303, safeNext(b._next) + (safeNext(b._next).includes("?") ? "&" : "?") + "err=1");
  }

  return wantsJson ? res.status(200).json({ ok: true }) : res.redirect(303, safeNext(b._next));
}
