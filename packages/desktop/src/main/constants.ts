import { app } from "electron"

type Channel = "local" | "dev" | "beta" | "prod"

const raw = import.meta.env.SORAX_CHANNEL

export const CHANNEL: Channel = raw === "local" || raw === "dev" || raw === "beta" || raw === "prod" ? raw : "dev"

export const VERSION = app.isPackaged ? app.getVersion() : (process.env.SORAX_VERSION ?? app.getVersion())

const appNames: Record<string, string> = {
  dev: "SORAX Dev",
  beta: "SORAX Beta",
  prod: "SORAX",
}

const appIDs: Record<string, string> = {
  dev: "ai.sorax.desktop.dev",
  beta: "ai.sorax.desktop.beta",
  prod: "ai.sorax.desktop",
}

// Local renderer/server mode keeps the dev application identity.
export const APP_NAME = app.isPackaged ? appNames[CHANNEL] : "SORAX Dev"

export const APP_ID = app.isPackaged ? appIDs[CHANNEL] : "ai.sorax.desktop.dev"
