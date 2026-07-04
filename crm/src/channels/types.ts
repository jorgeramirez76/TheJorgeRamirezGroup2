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
