export * as SORAXWorkerd from "./workerd"

import { Layer } from "effect"
import type { Config, Scope } from "effect"
import { WorkerdProfile } from "../internal/workerd"
import { SORAX } from "./sorax"

export type Configuration = WorkerdProfile.Configuration

export interface CreateOptions<R = never> extends WorkerdProfile.Options {
  readonly log?: SORAX.CreateOptions["log"]
  readonly plugins?: SORAX.CreateOptions["plugins"]
  readonly workspaceProviders?: SORAX.CreateOptions["workspaceProviders"]
  readonly instances?: SORAX.CreateOptions<R>["instances"]
}

export const create = <R = never>({ log, plugins, workspaceProviders, instances, ...options }: CreateOptions<R>) => {
  const profile = WorkerdProfile.make(options)
  return SORAX.create(
    { ...profile.options, log, plugins, workspaceProviders, instances },
    { overrides: profile.replacements },
  )
}

export const layer = <R = never>(
  options: CreateOptions<R>,
): Layer.Layer<SORAX.Service, Config.ConfigError | Error, Exclude<R, Scope.Scope>> =>
  Layer.effect(SORAX.Service, create(options))

export type Interface = SORAX.Interface
export type Requirements = Scope.Scope
