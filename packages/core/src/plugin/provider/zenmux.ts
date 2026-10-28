import { Effect } from "effect"
import { define } from "@sorax/plugin/effect/plugin"

export const ZenmuxPlugin = define({
  id: "sorax.provider.zenmux",
  effect: Effect.fn(function* (ctx) {
    yield* ctx.provider.transform((evt) => {
      for (const item of evt.list()) {
        if (item.provider.package !== "@sorax/ai/providers/openai-compatible") continue
        if (item.provider.settings?.baseURL !== "https://zenmux.ai/api/v1") continue
        evt.update(item.provider.id, (provider) => {
          provider.headers = {
            "HTTP-Referer": "https://sorax.ai/",
            "X-Title": "sorax",
            ...provider.headers,
          }
        })
      }
    })
  }),
})
