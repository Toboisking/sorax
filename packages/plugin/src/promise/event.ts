import type { EventApi } from "@sorax/client/promise/api"

export interface EventDomain extends Pick<EventApi, "subscribe"> {}
