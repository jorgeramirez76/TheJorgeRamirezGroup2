const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CONSENT_LANGUAGE =
  "I agree to receive text messages from The Jorge Ramirez Group about this home valuation request. Message and data rates may apply. Reply STOP to opt out. Consent is optional and is not a condition of service.";

if (typeof document !== "undefined") {
  document.documentElement.classList.add("js-enabled");
}

function trim(value) {
  return String(value || "").trim();
}

export function validateValuationLead(values) {
  const normalized = {
    name: trim(values.name),
    email: trim(values.email).toLowerCase(),
    address: trim(values.address),
    phone: trim(values.phone),
  };
  const fields = [];
  if (normalized.name.length < 2) fields.push("name");
  if (!EMAIL_PATTERN.test(normalized.email)) fields.push("email");
  if (normalized.address.length < 5) fields.push("address");
  if (normalized.phone && normalized.phone.replace(/\D/g, "").length < 7) fields.push("phone");

  if (fields.length) {
    return { ok: false, fields, values: normalized };
  }
  return { ok: true, values: normalized };
}

export function buildValuationPayload(values) {
  const phone = trim(values.phone);
  return {
    leadType: "home-valuation",
    name: trim(values.name),
    email: trim(values.email).toLowerCase(),
    phone,
    address: trim(values.address),
    town: trim(values.town),
    timeframe: trim(values.timeframe),
    message: trim(values.message),
    intent: "Home valuation request",
    smsConsent: Boolean(values.smsConsent && phone),
    consentLanguage: values.smsConsent && phone ? CONSENT_LANGUAGE : "",
    _honey: trim(values._honey),
    _startedAt: trim(values._startedAt),
    _source: "/home-valuation",
  };
}

function defaultTrack(eventName, details) {
  if (typeof window !== "undefined" && typeof window.gtag === "function") {
    window.gtag("event", eventName, details);
  }
}

export async function submitValuationLead(payload, options = {}) {
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  const track = options.track || defaultTrack;
  const response = await fetchImpl("/api/lead", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
    },
    body: JSON.stringify(payload),
    signal: options.signal,
  });

  let data = {};
  try {
    data = await response.json();
  } catch (_error) {
    // A non-JSON response cannot confirm delivery, even if the status is 2xx.
  }

  if (!response.ok || data.ok !== true || data.accepted !== true) {
    return {
      ok: false,
      code: data.code || "unconfirmed",
      fields: Array.isArray(data.fields) ? data.fields : [],
    };
  }

  try {
    const trackingResult = track("generate_lead", {
      form_id: "home_valuation",
      lead_type: "home_valuation",
    });
    if (trackingResult && typeof trackingResult.catch === "function") {
      trackingResult.catch(() => {});
    }
  } catch (_error) {
    // Analytics is best-effort and must never turn a confirmed lead into an error.
  }
  return { ok: true };
}

export function valuationErrorMessage(result = {}) {
  if (result.code === "rate_limited") {
    return "Please wait a few minutes before trying again, or call Jorge at 908-230-7844.";
  }
  if (result.code === "invalid_lead") {
    if (Array.isArray(result.fields) && result.fields.includes("phone")) {
      return "Enter a phone number with at least seven digits, or leave the phone field blank.";
    }
    return "Please check your name, email, and property address, then try again.";
  }
  return "We could not confirm your request. Please try again, or call Jorge at 908-230-7844.";
}

function formValues(form) {
  const data = new FormData(form);
  return {
    name: data.get("name"),
    email: data.get("email"),
    phone: data.get("phone"),
    address: data.get("address"),
    town: data.get("town"),
    timeframe: data.get("timeframe"),
    message: data.get("message"),
    smsConsent: data.get("smsConsent") === "on",
    _honey: data.get("_honey"),
    _startedAt: data.get("_startedAt"),
  };
}

function setStatus(status, state, message) {
  status.hidden = false;
  status.className = `valuation-status is-${state}`;
  status.setAttribute("role", state === "error" ? "alert" : "status");
  status.textContent = message;
  status.focus({ preventScroll: true });
  status.scrollIntoView({ behavior: "smooth", block: "center" });
}

function initializeValuationForm() {
  const form = document.getElementById("valuationForm");
  const status = document.getElementById("valuationStatus");
  if (!form || !status) return;

  const startedAt = form.elements.namedItem("_startedAt");
  if (startedAt) startedAt.value = String(Date.now());

  const query = new URLSearchParams(window.location.search);
  if (query.get("submitted") === "1") {
    form.hidden = true;
    setStatus(
      status,
      "success",
      "Request received. Jorge will review your property details and follow up about your free valuation within 24 to 48 hours.",
    );
    return;
  }
  if (query.has("err")) {
    const message = query.get("err") === "rate"
      ? "Please wait a few minutes before trying again, or call Jorge at 908-230-7844."
      : query.get("err") === "invalid"
        ? "Please check your name, contact information, and property address, then try again."
        : "We could not confirm your request. Please try again, or call Jorge at 908-230-7844.";
    setStatus(status, "error", message);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;

    const values = formValues(form);
    const validation = validateValuationLead(values);
    if (!validation.ok) {
      const firstInvalid = form.elements.namedItem(validation.fields[0]);
      if (firstInvalid && typeof firstInvalid.focus === "function") firstInvalid.focus();
      setStatus(status, "error", valuationErrorMessage({
        code: "invalid_lead",
        fields: validation.fields,
      }));
      return;
    }

    const submitButton = form.querySelector('button[type="submit"]');
    const defaultLabel = submitButton ? submitButton.textContent : "Request My Free Valuation";
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = "Sending request…";
    }
    form.setAttribute("aria-busy", "true");
    status.hidden = true;

    const controller = "AbortController" in window ? new AbortController() : null;
    const timeout = controller ? window.setTimeout(() => controller.abort(), 15_000) : null;

    try {
      const result = await submitValuationLead(buildValuationPayload(values), {
        signal: controller ? controller.signal : undefined,
      });
      if (!result.ok) {
        setStatus(status, "error", valuationErrorMessage(result));
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = defaultLabel;
        }
        return;
      }

      form.hidden = true;
      setStatus(
        status,
        "success",
        "Request received. Jorge will review your property details and follow up about your free valuation within 24 to 48 hours.",
      );
    } catch (_error) {
      setStatus(
        status,
        "error",
        valuationErrorMessage(),
      );
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = defaultLabel;
      }
    } finally {
      if (timeout) window.clearTimeout(timeout);
      form.removeAttribute("aria-busy");
    }
  });
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeValuationForm, { once: true });
  } else {
    initializeValuationForm();
  }
}
