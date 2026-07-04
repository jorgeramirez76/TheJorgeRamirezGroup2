export type OutboundMessage = {
  contactId: number;
  channel: 'imessage';
  body: string;
  /** Existing BlueBubbles chat GUID. If omitted, `address` is used to create/find the chat. */
  chatGuid?: string | null;
  /** Phone number or email handle, used to create a chat when `chatGuid` is not known yet. */
  address?: string | null;
  attachmentPath?: string | null;
  attachmentName?: string | null;
};

export type SendResult = { externalId: string; chatGuid: string };

export interface Channel {
  send(msg: OutboundMessage): Promise<SendResult>;
}

export type InboundMessage = {
  externalId: string;
  chatGuid: string;
  address: string;
  body: string;
  receivedAt: string;
};

export type OutboundEmail = {
  contactId: number;
  to: string;
  subject: string;
  body: string;
  /** Gmail threadId to reply within. Omit to start a new thread. */
  threadId?: string | null;
  /** RFC 2822 Message-ID header of the message being replied to. */
  inReplyTo?: string | null;
  references?: string[] | null;
  /** Set by campaign sends (§12) — the body must already include the CAN-SPAM footer. */
  listUnsubscribe?: string | null;
};

export type EmailSendResult = { externalId: string; threadId: string };

export interface EmailChannel {
  send(msg: OutboundEmail): Promise<EmailSendResult>;
}

export type InboundEmail = {
  externalId: string;
  threadId: string;
  from: string;
  subject: string | null;
  body: string;
  receivedAt: string;
};
