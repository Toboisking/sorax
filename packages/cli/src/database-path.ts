import path from "node:path"
import { SORAX_CHANNEL } from "./version"

export function databasePath(data: string) {
  const filename =
    process.env.SORAX_DB ??
    (["latest", "dev", "beta", "next", "prod"].includes(SORAX_CHANNEL) ||
    process.env.SORAX_DISABLE_CHANNEL_DB === "1" ||
    process.env.SORAX_DISABLE_CHANNEL_DB === "true"
      ? "sorax.db"
      : `sorax-${SORAX_CHANNEL.replace(/[^a-zA-Z0-9._-]/g, "-")}.db`)
  return filename === ":memory:" ? filename : path.resolve(data, filename)
}
