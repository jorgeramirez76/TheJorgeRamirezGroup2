export type CanSpamIdentity = { businessName: string; businessMailingAddress: string; fromEmail: string };

/**
 * §12: campaign (non-1:1) emails need identification + a physical mailing address +
 * an unsubscribe mechanism. 1:1 conversational replies are exempt (never call this for those).
 */
export function buildCanSpamFooter(identity: CanSpamIdentity): string {
  const addressLine = identity.businessMailingAddress || '[mailing address not yet configured — see settings.business_mailing_address]';
  return [
    '',
    '--',
    identity.businessName,
    addressLine,
    `Don't want these emails? Reply STOP or unsubscribe: mailto:${identity.fromEmail}?subject=unsubscribe`
  ].join('\n');
}

export function appendCanSpamFooter(body: string, identity: CanSpamIdentity): string {
  return `${body}${buildCanSpamFooter(identity)}`;
}

export function buildListUnsubscribeHeader(fromEmail: string): string {
  return `<mailto:${fromEmail}?subject=unsubscribe>`;
}
