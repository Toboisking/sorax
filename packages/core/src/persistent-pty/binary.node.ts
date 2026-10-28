export const available = true

export async function resolveBinary() {
  return process.env.SORAX_PTY_BIN || "sorax-pty"
}
