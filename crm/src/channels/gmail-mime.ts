export type BuildRawMessageParams = {
  from: string;
  to: string;
  subject: string;
  body: string;
  inReplyTo?: string | null;
  references?: string[] | null;
  listUnsubscribe?: string | null;
};

function encodeSubject(subject: string): string {
  // Only MIME-encode when non-ASCII is present; plain ASCII subjects stay human-readable in raw form.
  if (/^[\x00-\x7F]*$/.test(subject)) return subject;
  return `=?UTF-8?B?${Buffer.from(subject, 'utf8').toString('base64')}?=`;
}

/** Builds an RFC 2822 message and base64url-encodes it the way `users.messages.send` expects. */
export function buildRawMessage(params: BuildRawMessageParams): string {
  const headers: string[] = [
    `From: ${params.from}`,
    `To: ${params.to}`,
    `Subject: ${encodeSubject(params.subject)}`,
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset="UTF-8"',
    'Content-Transfer-Encoding: 7bit'
  ];

  if (params.inReplyTo) headers.push(`In-Reply-To: ${params.inReplyTo}`);
  if (params.references && params.references.length > 0) headers.push(`References: ${params.references.join(' ')}`);
  if (params.listUnsubscribe) headers.push(`List-Unsubscribe: ${params.listUnsubscribe}`);

  const message = `${headers.join('\r\n')}\r\n\r\n${params.body}`;
  return Buffer.from(message, 'utf8').toString('base64url');
}
