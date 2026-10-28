// SORAX wordmark in the block font: 4px-wide letters, 1-cell separated.
// Rows 1-3 encode 5 pixel rows (row 3's glyphs are top-half only); row 0 is the
// ascender pad (blank for SORAX) and doubles as the stacked-layout separator.
export const logo = {
  left: ["              ", "█▀▀▀ █▀▀█ █▀▀█", "▀▀▀█ █__█ █▀█▀", "▀▀▀▀ ▀▀▀▀ ▀  ▀"],
  right: ["          ", "▄▀▀▄ ▀▄ ▄▀", "█^^█  ▄▀▄ ", "▀  ▀ ▀   ▀"],
}

// Single-glyph SORAX mark for terminals too narrow for the wordmark.
export const go = {
  left: ["    ", "    ", "    ", "    "],
  right: ["    ", "█▀▀▀", "▀▀▀█", "▀▀▀▀"],
}
