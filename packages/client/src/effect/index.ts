// TODO: Keep additional network capabilities inside Schema and Protocol as the client grows; /effect must never import
// Core or Server. Preserve these datatype exports so internal model reorganizations do not require caller migrations.
import type { Effect } from "effect"
import type { SORAX } from "./client.js"

export * from "./generated/index"
export { SORAX } from "./client.js"
export type {
  AgentApi,
  AppApi,
  CommandApi,
  ConfigApi,
  EventApi,
  IntegrationApi,
  ModelApi,
  PluginApi,
  ProviderApi,
  ReferenceApi,
  RpcApi,
  RpcClient,
  WebSearchApi,
  SessionApi,
  SkillApi,
} from "./api.js"
export { Agent } from "@sorax/schema/agent"
export { Command } from "@sorax/schema/command"
export { Config } from "@sorax/schema/config"
export { Credential } from "@sorax/schema/credential"
export { Event } from "@sorax/schema/event"
export { EventLog } from "@sorax/schema/event-log"
export { FileSystem } from "@sorax/schema/filesystem"
export { Form } from "@sorax/schema/form"
export { Integration } from "@sorax/schema/integration"
export { Location } from "@sorax/schema/location"
export { Model } from "@sorax/schema/model"
export { Permission } from "@sorax/schema/permission"
export { PermissionSaved } from "@sorax/schema/permission-saved"
export { Project } from "@sorax/schema/project"
export { Worktree } from "@sorax/schema/worktree"
export { Vcs } from "@sorax/schema/vcs"
export { Provider } from "@sorax/schema/provider"
export { Pty } from "@sorax/schema/pty"
export { Question } from "@sorax/schema/question"
export { Reference } from "@sorax/schema/reference"
export { WebSearch } from "@sorax/schema/websearch"
export { AbsolutePath, RelativePath } from "@sorax/schema/schema"
export { Session } from "@sorax/schema/session"
export { SessionInbox } from "@sorax/schema/session-inbox"
export { SessionMessage } from "@sorax/schema/session-message"
export { Skill } from "@sorax/schema/skill"
export { Prompt } from "@sorax/schema/prompt"
export { PromptInput } from "@sorax/schema/prompt-input"
export type { SORAXEvent } from "@sorax/protocol/groups/event"
export type SORAXClient = Effect.Success<ReturnType<typeof SORAX.make>>
