import { Agent } from "@sorax/core/agent"
import { AISDK } from "@sorax/core/aisdk"
import { Command } from "@sorax/core/command"
import { Config } from "@sorax/core/config"
import { Credential } from "@sorax/core/credential"
import { Database } from "@sorax/core/database/database"
import { FileAccess } from "@sorax/core/file-access"
import { LayerNodePlatform } from "@sorax/util/effect/app-node-platform"
import { AppProcess } from "@sorax/util/process"
import { LayerNode } from "@sorax/util/effect/layer-node"
import { Bus } from "@sorax/core/bus"
import { FileSystem } from "@sorax/core/filesystem"
import { FSUtil } from "@sorax/util/fs-util"
import { Form } from "@sorax/core/form"
import { Generate } from "@sorax/core/generate"
import { Integration } from "@sorax/core/integration"
import { KV } from "@sorax/core/kv"
import { Location } from "@sorax/core/location"
import { ManagedPolicy } from "@sorax/core/managed-policy"
import { Mcp } from "@sorax/core/mcp/index"
import { Model } from "@sorax/core/model"
import { Npm } from "@sorax/util/npm"
import { Plugin } from "@sorax/core/plugin"
import { PluginHooks } from "@sorax/core/plugin/hooks"
import { Provider } from "@sorax/core/provider"
import { Session } from "@sorax/core/session"
import { PersistentPty } from "@sorax/core/persistent-pty"
import { LocationServiceMap } from "@sorax/core/location-service-map"
import { AppNodeBuilder } from "@sorax/core/effect/app-node-builder"
import { Permission } from "@sorax/core/permission"
import { Reference } from "@sorax/core/reference"
import { Rpc } from "@sorax/core/rpc"
import { Skill } from "@sorax/core/skill"
import { SkillDiscovery } from "@sorax/core/skill/discovery"
import { Watcher } from "@sorax/core/filesystem/watcher"
import { Tool } from "@sorax/core/tool"
import { Vcs } from "@sorax/core/vcs"
import { WebSearch } from "@sorax/core/websearch"
import { Worktree } from "@sorax/core/worktree"
import { WorktreeStrategies } from "@sorax/core/worktree/strategies"
import { Effect, Layer } from "effect"
import { tempLocationLayer } from "../fixture/location"
import { emptyMcpLayer } from "../fixture/mcp"

const npmLayer = Layer.succeed(
  Npm.Service,
  Npm.Service.of({
    add: (name) => Effect.succeed({ directory: "", name }),
    resolve: (name) => Effect.succeed({ directory: "", name }),
    check: () => Effect.succeed(false),
    update: (name) => Effect.succeed({ directory: "", name }),
    which: () => Effect.undefined,
  }),
)

const generateLayer = Layer.succeed(Generate.Service, Generate.Service.of({ text: () => Effect.succeed("") }))

const configLayer = Config.testLayer()

const permissionLayer = Layer.succeed(
  Permission.Service,
  Permission.Service.of({
    close: Effect.void,
    ask: (input) => Effect.succeed({ id: input.id ?? Permission.ID.create(), effect: "ask" }),
    assert: () => Effect.void,
    reply: () => Effect.void,
    get: () => Effect.succeed(undefined),
    forSession: () => Effect.succeed([]),
    list: () => Effect.succeed([]),
  }),
)

export const makePluginTestLayer = (permission = permissionLayer) =>
  AppNodeBuilder.build(
    LayerNode.group([
      AppProcess.node,
      FileSystem.node,
      FSUtil.node,
      Location.node,
      Npm.node,
      Credential.node,
      Config.node,
      Database.node,
      FileAccess.node,
      Bus.node,
      Form.node,
      Generate.node,
      LayerNodePlatform.httpClient,
      Plugin.node,
      Agent.node,
      AISDK.node,
      Provider.node,
      Model.node,
      Command.node,
      Integration.node,
      KV.node,
      ManagedPolicy.node,
      Mcp.node,
      Session.node,
      PersistentPty.node,
      LocationServiceMap.node,
      Permission.node,
      PluginHooks.node,
      Reference.node,
      Rpc.node,
      Skill.node,
      SkillDiscovery.node,
      Tool.node,
      Vcs.node,
      Watcher.node,
      WebSearch.node,
      Worktree.node,
      WorktreeStrategies.node,
    ]),
    [
      Location.node.replace(tempLocationLayer),
      Npm.node.replace(npmLayer),
      Config.node.replace(configLayer),
      Mcp.node.replace(emptyMcpLayer),
      Generate.node.replace(generateLayer),
      Permission.node.replace(permission),
    ],
  ).pipe(Layer.provideMerge(configLayer))

export const PluginTestLayer = makePluginTestLayer()
