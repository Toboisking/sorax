interface ImportMetaEnv {
  readonly SORAX_CHANNEL: string
  readonly SORAX_VERSION?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
