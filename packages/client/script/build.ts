import { NodeFileSystem } from "@effect/platform-node"
import { compile, emitEffectImported, emitEffectShape, emitPromise, write } from "@sorax/httpapi-codegen"
import { ClientApi, effectOmitEndpoints, groupNames, promiseOmitEndpoints } from "@sorax/protocol/client"
import { Agent } from "@sorax/schema/agent"
import { Command } from "@sorax/schema/command"
import { Config } from "@sorax/schema/config"
import { Credential } from "@sorax/schema/credential"
import { Event } from "@sorax/schema/event"
import { EventLog } from "@sorax/schema/event-log"
import { FileDiff } from "@sorax/schema/file-diff"
import { FileSystem } from "@sorax/schema/filesystem"
import { Form } from "@sorax/schema/form"
import { Instruction } from "@sorax/schema/instruction"
import { InstructionEntry } from "@sorax/schema/instruction-entry"
import { Integration } from "@sorax/schema/integration"
import { Location } from "@sorax/schema/location"
import { Mcp } from "@sorax/schema/mcp"
import { Model } from "@sorax/schema/model"
import { Money } from "@sorax/schema/money"
import { Permission } from "@sorax/schema/permission"
import { PermissionSaved } from "@sorax/schema/permission-saved"
import { Plugin } from "@sorax/schema/plugin"
import { Project } from "@sorax/schema/project"
import { Worktree } from "@sorax/schema/worktree"
import { AgentAttachment, FileAttachment, Prompt, PromptMention } from "@sorax/schema/prompt"
import { PromptInput } from "@sorax/schema/prompt-input"
import { Provider } from "@sorax/schema/provider"
import { Pty } from "@sorax/schema/pty"
import { PtyTicket } from "@sorax/schema/pty-ticket"
import { Question } from "@sorax/schema/question"
import { Reference } from "@sorax/schema/reference"
import { AbsolutePath, RelativePath } from "@sorax/schema/schema"
import { Session } from "@sorax/schema/session"
import { SessionMessage } from "@sorax/schema/session-message"
import { SessionInbox } from "@sorax/schema/session-inbox"
import { Shell } from "@sorax/schema/shell"
import { Skill } from "@sorax/schema/skill"
import { Snapshot } from "@sorax/schema/snapshot"
import { UsageLimits } from "@sorax/schema/usage-limits"
import { Vcs } from "@sorax/schema/vcs"
import { WebSearch } from "@sorax/schema/websearch"
import { Workspace } from "@sorax/schema/workspace"
import { Effect, Schema } from "effect"
import { fileURLToPath } from "url"

const promiseContract = compile(ClientApi, { groupNames, omitEndpoints: promiseOmitEndpoints })
const effectContract = compile(ClientApi, { groupNames, omitEndpoints: effectOmitEndpoints })
const effectTypeReferences = [
  ...namespaceTypes("Agent", "@sorax/schema/agent", Agent),
  ...namespaceTypes("Command", "@sorax/schema/command", Command),
  ...namespaceTypes("Config", "@sorax/schema/config", Config),
  ...namespaceTypes("Credential", "@sorax/schema/credential", Credential),
  ...namespaceTypes("Event", "@sorax/schema/event", Event),
  ...namespaceTypes("EventLog", "@sorax/schema/event-log", EventLog),
  ...namespaceTypes("FileDiff", "@sorax/schema/file-diff", FileDiff),
  ...namespaceTypes("FileSystem", "@sorax/schema/filesystem", FileSystem),
  ...namespaceTypes("Form", "@sorax/schema/form", Form),
  ...namespaceTypes("Instruction", "@sorax/schema/instruction", Instruction),
  ...namespaceTypes("InstructionEntry", "@sorax/schema/instruction-entry", InstructionEntry),
  ...namespaceTypes("Integration", "@sorax/schema/integration", Integration),
  typeReference("Location.PublicRef", "@sorax/schema/location", Location.PublicRef),
  typeReference("Location.PublicInfo", "@sorax/schema/location", Location.PublicInfo),
  ...namespaceTypes("Mcp", "@sorax/schema/mcp", Mcp),
  ...namespaceTypes("Model", "@sorax/schema/model", Model),
  ...namespaceTypes("Money", "@sorax/schema/money", Money),
  ...namespaceTypes("Permission", "@sorax/schema/permission", Permission),
  ...namespaceTypes("PermissionSaved", "@sorax/schema/permission-saved", PermissionSaved),
  ...namespaceTypes("Plugin", "@sorax/schema/plugin", Plugin),
  ...namespaceTypes("Project", "@sorax/schema/project", Project),
  ...namespaceTypes("Worktree", "@sorax/schema/worktree", Worktree),
  ...namespaceTypes("PromptInput", "@sorax/schema/prompt-input", PromptInput),
  ...namespaceTypes("Provider", "@sorax/schema/provider", Provider),
  ...namespaceTypes("Pty", "@sorax/schema/pty", Pty),
  ...namespaceTypes("PtyTicket", "@sorax/schema/pty-ticket", PtyTicket),
  ...namespaceTypes("Question", "@sorax/schema/question", Question),
  ...namespaceTypes("Reference", "@sorax/schema/reference", Reference),
  ...namespaceTypes("Session", "@sorax/schema/session", Session),
  ...namespaceTypes("SessionMessage", "@sorax/schema/session-message", SessionMessage),
  ...namespaceTypes("SessionInbox", "@sorax/schema/session-inbox", SessionInbox),
  ...namespaceTypes("Shell", "@sorax/schema/shell", Shell),
  ...namespaceTypes("Skill", "@sorax/schema/skill", Skill),
  ...namespaceTypes("Snapshot", "@sorax/schema/snapshot", Snapshot),
  ...namespaceTypes("UsageLimits", "@sorax/schema/usage-limits", UsageLimits),
  ...namespaceTypes("Vcs", "@sorax/schema/vcs", Vcs),
  ...namespaceTypes("WebSearch", "@sorax/schema/websearch", WebSearch),
  ...namespaceTypes("Workspace", "@sorax/schema/workspace", Workspace),
  typeReference("Prompt", "@sorax/schema/prompt", Prompt),
  typeReference("PromptMention", "@sorax/schema/prompt", PromptMention),
  typeReference("FileAttachment", "@sorax/schema/prompt", FileAttachment),
  typeReference("AgentAttachment", "@sorax/schema/prompt", AgentAttachment),
  typeReference("AbsolutePath", "@sorax/schema/schema", AbsolutePath),
  typeReference("RelativePath", "@sorax/schema/schema", RelativePath),
]

await Effect.runPromise(
  Effect.all(
    [
      write(
        emitPromise(promiseContract, {
          mutableOutputs: true,
        }),
        fileURLToPath(new URL("../src/promise/generated", import.meta.url)),
      ),
      write(
        emitEffectImported(effectContract, {
          module: "../../contract",
          api: "ClientApi",
          shapeModule: "../api/api.js",
        }),
        fileURLToPath(new URL("../src/effect/generated", import.meta.url)),
      ),
      write(
        emitEffectShape(effectContract, {
          typeReferences: effectTypeReferences,
          outputTypes: {
            "event.subscribe": {
              name: "SORAXEvent",
              import: 'import type { SORAXEvent } from "@sorax/protocol/groups/event"',
            },
          },
        }),
        fileURLToPath(new URL("../src/effect/api", import.meta.url)),
      ),
    ],
    { concurrency: 3, discard: true },
  ).pipe(Effect.provide(NodeFileSystem.layer)),
)

function namespaceTypes(namespace: string, module: string, values: object) {
  return Object.entries(values).flatMap(([name, schema]) =>
    Schema.isSchema(schema) ? [typeReference(`${namespace}.${name}`, module, schema)] : [],
  )
}

function typeReference(name: string, module: string, schema: Schema.Top) {
  return {
    schema,
    name,
    import: `import type { ${name.split(".")[0]} } from ${JSON.stringify(module)}`,
  }
}
