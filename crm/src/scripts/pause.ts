import { openDb } from '../db/client.js';
import * as schema from '../db/schema.js';

const { sqlite, db } = openDb();
db.insert(schema.settings).values({ key: 'global_pause', value: true }).onConflictDoUpdate({
  target: schema.settings.key,
  set: { value: true }
}).run();
sqlite.close();
console.log('JRG-CRM outbound paused (settings.global_pause=true)');
