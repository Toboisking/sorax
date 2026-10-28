import { HttpOptions, ProviderID, type ModelID } from "../schema/index.js"
import { AuthOptions, type ProviderAuthOption } from "../route/auth-options.js"
import { SystemOne } from "../protocols/system-one.js"

export const id = ProviderID.make("sorax")
const baseURL = "https://sorax.ai/inference/systemone/v1"

export type Options = ProviderAuthOption<"optional"> & {
  readonly baseURL?: string
  readonly headers?: Record<string, string>
  readonly http?: HttpOptions.Input
}

export const configure = (input: Options = {}) => {
  const route = SystemOne.route.with({
    provider: id,
    providerMetadataKey: "sorax",
    endpoint: { baseURL: input.baseURL ?? baseURL },
    auth: AuthOptions.bearer(input, "SORAX_API_KEY"),
    // Zen forwards TypeSafe's image opt-in header; text-only requests are unchanged with it.
    headers: { "TypeSafe-Danger-Zone-Images": "true", ...input.headers },
    http: input.http,
  })
  const decision = (modelID: string | ModelID) => route.model({ id: modelID })
  return { id, decision, configure }
}

export const provider = configure()
export const decision = provider.decision

export * as SORAX from "./sorax.js"
