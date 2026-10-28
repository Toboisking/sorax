import { Option, Schema } from "effect"

declare const SORAX_VERSION: string
declare const SORAX_CHANNEL: string
declare const SORAX_ARTIFACT: string
declare const SORAX_RELEASE_HIGHLIGHTS: string

const version = typeof SORAX_VERSION === "string" ? SORAX_VERSION : "local"
const channel = typeof SORAX_CHANNEL === "string" ? SORAX_CHANNEL : "local"
const artifact = typeof SORAX_ARTIFACT === "string" ? SORAX_ARTIFACT : "cli"
// Stable release builds embed the release notes' Highlights; every other build has none.
const highlights =
  typeof SORAX_RELEASE_HIGHLIGHTS === "string"
    ? Option.getOrElse(
        Schema.decodeUnknownOption(
          Schema.fromJsonString(Schema.Array(Schema.Struct({ title: Schema.String, body: Schema.String }))),
        )(SORAX_RELEASE_HIGHLIGHTS),
        () => [],
      )
    : []

export {
  version as SORAX_VERSION,
  channel as SORAX_CHANNEL,
  artifact as SORAX_ARTIFACT,
  highlights as SORAX_HIGHLIGHTS,
}
export const SORAX_LOCAL = channel === "local"
