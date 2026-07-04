import { config } from 'dotenv';
import { resolve } from 'node:path';

config();

export function getDatabasePath() {
  return resolve(process.cwd(), process.env.CRM_DATABASE_PATH ?? './crm.db');
}
