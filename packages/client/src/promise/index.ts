import type { SORAX } from "./client.js"

export * from "./generated/index.js"
export { SORAX } from "./client.js"
export type {
  AgentApi,
  CommandApi,
  ConfigApi,
  EventApi,
  IntegrationApi,
  ModelApi,
  PluginApi,
  ProviderApi,
  ReferenceApi,
  RpcApi,
  RpcCallOptions,
  RpcClient,
  RpcEventPayload,
  WebSearchApi,
  SessionApi,
  SkillApi,
} from "./api.js"
export type { EventSubscribeOutput as SORAXEvent } from "./generated/types.js"
export type SORAXClient = ReturnType<typeof SORAX.make>
