import { expect, test } from "bun:test"
import { Env } from "../src/env"

test("session environment omits server credentials", () => {
  const previousPassword = process.env.SORAX_PASSWORD
  const previousLegacyPassword = process.env.SORAX_SERVER_PASSWORD
  const previousValue = process.env.SORAX_SESSION_ENV_TEST
  process.env.SORAX_PASSWORD = "password"
  process.env.SORAX_SERVER_PASSWORD = "legacy"
  process.env.SORAX_SESSION_ENV_TEST = "included"

  const environment = Env.session()

  if (previousPassword === undefined) delete process.env.SORAX_PASSWORD
  else process.env.SORAX_PASSWORD = previousPassword
  if (previousLegacyPassword === undefined) delete process.env.SORAX_SERVER_PASSWORD
  else process.env.SORAX_SERVER_PASSWORD = previousLegacyPassword
  if (previousValue === undefined) delete process.env.SORAX_SESSION_ENV_TEST
  else process.env.SORAX_SESSION_ENV_TEST = previousValue

  expect(environment.SORAX_PASSWORD).toBeUndefined()
  expect(environment.SORAX_SERVER_PASSWORD).toBeUndefined()
  expect(environment.SORAX_SESSION_ENV_TEST).toBe("included")
})
