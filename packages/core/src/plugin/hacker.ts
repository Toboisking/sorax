export * as HackerPlugin from "./hacker.js"

import { SystemPart } from "@sorax/ai/effect"
import { define } from "@sorax/plugin/effect/plugin"
import { Agent } from "@sorax/schema/agent"
import type { Model } from "@sorax/schema/model"
import { Global } from "@sorax/util/global"
import { Effect } from "effect"
import fs from "fs"
import path from "path"
import { SessionSystemPrompt } from "../session/system-prompt.js"
import INTRO from "./hacker/intro.txt"

const hacker = Agent.ID.make("hacker")

const SYSTEM = [
  SessionSystemPrompt.make(["shell", "write", "edit"]),
  INTRO,
].join("\n\n")

export const Plugin = define({
  id: "sorax.hacker",
  effect: Effect.fn(function* (ctx) {
    const global = yield* Global.Service
    const packs = path.join(global.config, "packs")
    yield* ctx.agent.transform((editor) => {
      editor.update(hacker, (item) => {
        item.name = Agent.Name.make("Hacker")
        item.description =
          "Offensive-security mode: direct, complete delivery with per-model packs loaded; no persona layer."
        item.mode = "primary"
        item.system = SYSTEM
        item.permissions.push({ action: "question", resource: "*", effect: "allow" })
      })
    })

    // Per-model jailbreak packs: <config>/packs/<stem>.md whose stem appears in the
    // model reference. Only hacker mode reads them so build and plan stay stock.
    yield* ctx.session.hook("context", (event) => {
      if (event.agent !== hacker) return Effect.void
      return Effect.gen(function* () {
        const pack = yield* loadPack(packs, event.model)
        if (pack) event.system.push(SystemPart.make(pack))
      })
    })
  }),
})

const loadPack = (directory: string, ref: Model.Ref) =>
  Effect.promise(async () => {
    const files: string[] = await fs.promises.readdir(directory).catch(() => [])
    const key = `${ref.providerID}/${ref.id}`.toLowerCase()
    // Longest matching stem wins so a model pack beats a family pack.
    const best = files
      .flatMap((file) => (file.endsWith(".md") ? [{ file, stem: file.slice(0, -3).toLowerCase() }] : []))
      .filter((entry) => entry.stem.length > 0 && key.includes(entry.stem))
      .sort((a, b) => b.stem.length - a.stem.length)[0]
    if (!best) return undefined
    return Bun.file(path.join(directory, best.file)).text().catch(() => undefined)
  })
