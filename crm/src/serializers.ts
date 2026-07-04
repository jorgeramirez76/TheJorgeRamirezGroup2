import type * as schema from './db/schema.js';

export function serializeContact(contact: typeof schema.contacts.$inferSelect) {
  return contact;
}

export function serializeLead(lead: typeof schema.leads.$inferSelect) {
  return lead;
}

export function serializeMessage(message: typeof schema.messages.$inferSelect) {
  return message;
}

export function parseSettings(rows: Array<typeof schema.settings.$inferSelect>) {
  return Object.fromEntries(rows.map((row) => [row.key, row.value]));
}
