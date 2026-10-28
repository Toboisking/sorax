import type { ElectronNative } from "../preload/types"

declare global {
  interface ImportMetaEnv {
    readonly SORAX_TEST_ONBOARDING: boolean
  }

  interface Window {
    electron: ElectronNative
    __SORAX__?: {
      deepLinks?: string[]
    }
  }
}
