import { expect, test } from "bun:test"
import { selectTheme, selectThemeMode, supportsThemeMode, themeModes } from "@sorax/theme/tui"
import { getSORAXTheme } from "../../../src/theme"

test("selects complete light and dark themes independently", () => {
  const light = selectTheme(getSORAXTheme(), "light")
  const dark = selectTheme(getSORAXTheme(), "dark")
  expect(selectTheme(getSORAXTheme())).toEqual(light)
  expect(light.hue).toEqual(getSORAXTheme().light.hue)
  expect(dark.text).toEqual(getSORAXTheme().base.text)
  expect(dark.hue).toEqual(getSORAXTheme().dark.hue)
  expect(selectThemeMode(getSORAXTheme(), "dark")).toEqual({ theme: dark, mode: "dark" })
})

test("selects the available mode when the requested mode is missing", () => {
  const lightOnly = { base: getSORAXTheme().base, light: getSORAXTheme().light } as const
  const darkOnly = { base: getSORAXTheme().base, dark: getSORAXTheme().dark } as const

  expect(themeModes(lightOnly)).toEqual(["light"])
  expect(themeModes(darkOnly)).toEqual(["dark"])
  expect(supportsThemeMode(lightOnly, "light")).toBeTrue()
  expect(supportsThemeMode(lightOnly, "dark")).toBeFalse()
  expect(selectThemeMode(lightOnly, "dark")).toEqual({ theme: selectTheme(getSORAXTheme(), "light"), mode: "light" })
  expect(selectThemeMode(darkOnly, "light")).toEqual({ theme: selectTheme(getSORAXTheme(), "dark"), mode: "dark" })
})
