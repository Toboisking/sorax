import type { FileSystem } from "@sorax/core/filesystem"
import { Bus } from "@sorax/core/bus"
import { Image } from "@sorax/core/image"
import { LocationServiceMap } from "@sorax/core/location-service-map"
import type { LocationServices } from "@sorax/core/location-services"
import { Plugin } from "@sorax/core/plugin"
import { PluginHooks } from "@sorax/core/plugin/hooks"
import { Skill } from "@sorax/core/skill"
import type { Location } from "@sorax/schema/location"
import { makeGlobalNode } from "@sorax/util/effect/app-node"
import { LayerNode } from "@sorax/util/effect/layer-node"
import { Effect, Layer, LayerMap } from "effect"

// Plain-prompt unit fixtures use virtual directories.
export const promptLocationNode = makeGlobalNode({
  service: LocationServiceMap.Service,
  layer: Layer.effect(
    LocationServiceMap.Service,
    Effect.gen(function* () {
      const bus = yield* Bus.Service
      return yield* LayerMap.make(
        (_ref: Location.Ref) =>
          LayerNode.compile(LayerNode.group([PluginHooks.node, Image.node, Skill.node, Plugin.node]), {
            replacements: [
              Bus.node.replace(Layer.succeed(Bus.Service, bus)),
              Plugin.node.replace(Layer.mock(Plugin.Service, { awaitActivation: Effect.void })),
            ],
          }) as unknown as Layer.Layer<LocationServices, FileSystem.DirectoryNotFoundError>,
      )
    }),
  ),
  deps: [Bus.node],
})
