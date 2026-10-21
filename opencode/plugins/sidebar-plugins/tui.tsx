/** @jsxImportSource @opentui/solid */
import { createMemo, createSignal, For, Show } from "solid-js"
import { Plugin } from "@opencode/plugin/tui"
import { build, groupLabel, groupRank, pluginDirectories, type PluginItem, type PluginStatus } from "./data.ts"

type Scope = "context" | "user" | "all"

type View = { open: boolean; builtin: boolean }

type Row = { key: string; header?: string; item?: PluginItem }

const scopes: Scope[] = ["context", "user", "all"]

function scopeOf(value: unknown): Scope {
  return scopes.includes(value as Scope) ? (value as Scope) : "context"
}

function statusColor(theme: Plugin.Context["theme"], status: PluginStatus) {
  if (status === "failed") return theme.text.feedback.error.base
  if (status === "inactive" || status === "unsupported") return theme.text.muted
  return theme.text.feedback.success.base
}

function statusText(item: PluginItem) {
  if (item.runtime === "cli") return "cli"
  if (item.status === "failed") return "Failed"
  if (item.status === "inactive") return "Inactive"
  if (item.status === "unsupported") return "Unsupported"
  return "Active"
}

function labelOf(item: PluginItem) {
  const name = item.builtin ? item.name.replace(/^opencode\./, "") : item.name
  return item.detail ? `${name} ${item.detail}` : name
}

function Row(props: { context: Plugin.Context; item: PluginItem; indent?: boolean }) {
  const theme = () => props.context.theme
  const color = () => statusColor(theme(), props.item.status)
  const statusFg = () =>
    props.item.runtime === "cli" ? theme().text.muted : props.item.status === "active" ? theme().text.muted : color()

  return (
    <box flexDirection="column">
      <box flexDirection="row" gap={1} paddingLeft={props.indent ? 2 : 0} minWidth={0}>
        <text flexShrink={0} style={{ fg: color() }}>
          •
        </text>
        <text fg={theme().text.base} wrapMode="none" truncate flexGrow={1} flexShrink={1} minWidth={0}>
          {labelOf(props.item)}
        </text>
        <text flexShrink={0} wrapMode="none" style={{ fg: statusFg() }}>
          {statusText(props.item)}
        </text>
      </box>
      <Show when={props.item.error}>
        <text fg={theme().text.feedback.error.base} wrapMode="word" paddingLeft={2}>
          <i>{props.item.error}</i>
        </text>
      </Show>
    </box>
  )
}

function Section(props: {
  context: Plugin.Context
  items: () => PluginItem[]
  scope: Scope
  view: View
  toggle: (key: keyof View) => void
}) {
  const theme = () => props.context.theme
  const visible = createMemo(() => {
    const all = props.items()
    if (props.scope === "all") return all
    if (props.scope === "user") return all.filter((item) => !item.builtin)
    // "context" — только то, что реально уходит в промпт: серверные плагины с
    // контекстными хуками и builtin-группы Tools/Prompt/Config/Agent.
    return all.filter((item) => item.context)
  })
  const user = createMemo(() => visible().filter((item) => !item.builtin))
  const builtin = createMemo(() =>
    visible()
      .filter((item) => item.builtin)
      .toSorted((left, right) => groupRank(left.group) - groupRank(right.group) || left.name.localeCompare(right.name)),
  )
  const builtinTotal = createMemo(() => props.items().filter((item) => item.builtin).length)
  const active = createMemo(() => user().filter((item) => item.runtime !== "cli" && item.status === "active").length)
  const cli = createMemo(() => user().filter((item) => item.runtime === "cli").length)
  const failed = createMemo(() => user().filter((item) => item.status === "failed").length)

  const summary = () => {
    const parts = [`${active()} in context`]
    if (cli() > 0) parts.push(`${cli()} cli`)
    if (failed() > 0) parts.push(`${failed()} failed`)
    return `(${parts.join(", ")})`
  }

  const builtinLabel = () => {
    const shown = builtin().length
    const total = builtinTotal()
    return shown === total ? `Built-in (${shown})` : `Built-in (${shown} of ${total})`
  }

  const builtinRows = createMemo<Row[]>(() => {
    const rows: Row[] = []
    let group = ""
    for (const item of builtin()) {
      if (item.group !== group) {
        group = item.group
        const count = builtin().filter((entry) => entry.group === group).length
        rows.push({ key: `header:${group}`, header: `${groupLabel(group)} (${count})` })
      }
      rows.push({ key: item.key, item })
    }
    return rows
  })

  return (
    <Show when={visible().length > 0}>
      <box>
        <box flexDirection="row" gap={1} onMouseDown={() => props.toggle("open")}>
          <text fg={theme().text.base}>{props.view.open ? "▼" : "▶"}</text>
          <text fg={theme().text.base}>
            <b>Plugins</b>
          </text>
          <text fg={theme().text.muted} wrapMode="none" truncate flexGrow={1} minWidth={0}>
            {summary()}
          </text>
        </box>
        <Show when={props.view.open}>
          <For each={user()}>{(item) => <Row context={props.context} item={item} />}</For>
          <Show when={builtin().length > 0}>
            <box flexDirection="row" gap={1} onMouseDown={() => props.toggle("builtin")}>
              <text fg={theme().text.muted}>
                {props.view.builtin ? "▾" : "▸"} {builtinLabel()}
              </text>
            </box>
          </Show>
          <Show when={props.view.builtin}>
            <For each={builtinRows()}>
              {(row) =>
                row.item ? (
                  <Row context={props.context} item={row.item} indent />
                ) : (
                  <text fg={theme().text.muted} paddingLeft={2}>
                    {row.header}
                  </text>
                )
              }
            </For>
          </Show>
        </Show>
      </box>
    </Show>
  )
}

export default Plugin.define({
  id: "sandbox.sidebar-plugins",
  setup(context) {
    if (context.options.enabled === false) return

    const interval =
      typeof context.options.interval === "number" && context.options.interval >= 1000
        ? context.options.interval
        : 15000
    const scope = scopeOf(context.options.scope)

    const [items, setItems] = createSignal<PluginItem[]>([])
    const [view, setView] = context.storage.store("view", { initial: { open: true, builtin: false } })
    let pending = false

    const refresh = () => {
      if (pending) return
      const location = context.location ?? context.data.location.default()
      if (!location) return
      pending = true
      Promise.resolve(context.client.plugin.list({ location }))
        .then((response: { data?: unknown } | undefined) => {
          const data = Array.isArray(response?.data) ? response.data : []
          const providerID = context.ui.model.current()?.providerID
          setItems(build(data as never, pluginDirectories(location.directory), { providerID }))
        })
        .catch(() => {})
        .finally(() => {
          pending = false
        })
    }

    refresh()
    const timer = setInterval(refresh, interval)

    const offs: (() => void)[] = []
    for (const type of ["plugin.updated", "server.connected"] as const) {
      try {
        offs.push(context.data.on(type, refresh))
      } catch {
        // Event type unavailable on this host version; polling still covers it.
      }
    }

    const toggle = (key: keyof View) => {
      const result = setView((draft) => {
        draft[key] = !draft[key]
      })
      Promise.resolve(result).catch(() => {})
    }

    context.ui.slot({
      append: "sidebar.content",
      render: () => <Section context={context} items={items} scope={scope} view={view} toggle={toggle} />,
    })

    return () => {
      clearInterval(timer)
      for (const off of offs) off()
    }
  },
})
