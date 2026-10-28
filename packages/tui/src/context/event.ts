import type { SORAXEvent } from "@sorax/client"
import { useClient } from "./client"

type EventMetadata = {
  directory: string | undefined
}
type SORAXEventMap = { [Type in SORAXEvent["type"]]: Extract<SORAXEvent, { type: Type }> }

export function useEvent() {
  const client = useClient()

  function subscribe(handler: (event: SORAXEvent, metadata: EventMetadata) => void) {
    return client.event.listen(({ details }) => {
      if (details.type === "server.connected") return
      handler(details, { directory: details.location?.directory })
    })
  }

  function on<T extends SORAXEvent["type"]>(
    type: T,
    handler: (event: SORAXEventMap[T], metadata: EventMetadata) => void,
  ) {
    return client.event.on(type, (event) => {
      handler(event, { directory: event.location?.directory })
    })
  }

  return {
    subscribe,
    on,
  }
}
