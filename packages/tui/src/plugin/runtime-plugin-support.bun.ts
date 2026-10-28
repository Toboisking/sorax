import { ensurePluginRuntime, provides } from "@sorax/plugin/runtime"
import { Plugin, PluginContextProvider, usePlugin } from "@sorax/plugin/tui"
import { ensureRuntimePluginSupport } from "@opentui/solid/runtime-plugin-support/configure"

ensurePluginRuntime()
ensureRuntimePluginSupport({
  additional: {
    "@sorax/plugin/tui": { Plugin, PluginContextProvider, usePlugin },
  },
  preserve: provides,
})
