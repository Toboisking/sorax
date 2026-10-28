import type { EventApi } from "@sorax/client/effect/api"

export interface EventDomain extends Pick<EventApi<unknown>, "subscribe"> {}
