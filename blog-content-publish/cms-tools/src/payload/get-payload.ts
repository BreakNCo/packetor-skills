import config from "@payload-config";
import { getPayload as getPayloadClient, type Payload } from "payload";

let cached: Payload | null = null;

export async function getPayload() {
  if (cached) return cached;
  cached = await getPayloadClient({ config });
  return cached;
}
