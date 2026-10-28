import { Plugin } from "@sorax/plugin/tui"
import { createMermaidCodeBlockRenderer } from "./markdown.js"
import { resolveSORAXDiagramPalette } from "./palette.js"

export default Plugin.define({
  id: "sorax.merman",
  setup(context) {
    context.markdown.registerCodeBlockRenderer(
      "mermaid",
      createMermaidCodeBlockRenderer(context.renderer, () => ({
        colors: resolveSORAXDiagramPalette(context.theme, context.themeMode),
      })),
    )
  },
})
