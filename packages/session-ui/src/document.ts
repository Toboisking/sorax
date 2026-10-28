import type { FileDiffInfo, SessionMessageInfo, SessionStatus } from "@sorax/client/promise"

export type SessionDocument = {
  sessionID: string
  messages: SessionMessageInfo[]
  status: SessionStatus
  diffs: FileDiffInfo[]
}
