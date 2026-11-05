/**
 * Git status for the OpenCode V1 CLI sidebar footer.
 *
 * V1 contract: `default export { id, tui }` loaded from `tui.json` (`plugin: [[spec, options]]`)
 * or a local `.tsx` in `~/.config/opencode/plugins/`. The host renders `sidebar_footer` in
 * `single_winner` mode, so this module owns the whole footer and draws the path and the
 * `• Open Code <version>` line itself, like the built-in footer it replaces.
 */
/** @jsxImportSource @opentui/solid */
import { execFile } from "node:child_process"
import { createSignal } from "solid-js"
import type { TuiPlugin, TuiPluginApi, TuiPluginModule } from "@opencode-ai/plugin/tui"

type GitState = {
  repo: boolean
  branch: string
  detached: boolean
  upstream?: string
  ahead: number
  behind: number
  added: number
  deleted: number
  staged: number
  modified: number
  untracked: number
  conflict: number
  stash: number
}

const idle: GitState = {
  repo: false,
  branch: "",
  detached: false,
  ahead: 0,
  behind: 0,
  added: 0,
  deleted: 0,
  staged: 0,
  modified: 0,
  untracked: 0,
  conflict: 0,
  stash: 0,
}

function parse(text: string): GitState {
  const state: GitState = { ...idle, repo: true }
  for (const line of text.split("\n")) {
    if (!line) continue

    if (line.startsWith("# branch.head ")) {
      const head = line.slice("# branch.head ".length).trim()
      state.detached = head === "(detached)"
      state.branch = state.detached ? "detached" : head
      continue
    }
    if (line.startsWith("# branch.oid ")) {
      const oid = line.slice("# branch.oid ".length).trim()
      if (oid === "(initial)") state.branch = state.branch || "initial"
      else if (state.detached) state.branch = oid.slice(0, 7)
      continue
    }
    if (line.startsWith("# branch.upstream ")) {
      state.upstream = line.slice("# branch.upstream ".length).trim()
      continue
    }
    if (line.startsWith("# branch.ab ")) {
      const match = line.match(/\+(\d+)\s+-(\d+)/)
      if (match) {
        state.ahead = Number(match[1])
        state.behind = Number(match[2])
      }
      continue
    }
    if (line.startsWith("#")) continue

    const kind = line[0]
    const xy = line.slice(2, 4)
    if (kind === "1") {
      if (xy[0] === "A") state.added++
      else if (xy[0] === "D") state.deleted++
      else if (xy[0] !== ".") state.staged++
      if (xy[1] !== ".") state.modified++
    } else if (kind === "2") {
      state.staged++
      if (xy[1] !== ".") state.modified++
    } else if (kind === "u") {
      state.conflict++
    } else if (kind === "?") {
      state.untracked++
    }
  }
  return state
}

function read(dir: string, done: (state: GitState) => void) {
  const options = {
    cwd: dir,
    timeout: 5000,
    maxBuffer: 4 * 1024 * 1024,
    windowsHide: true,
    env: { ...process.env, GIT_OPTIONAL_LOCKS: "0" },
  }

  const finish = (state: GitState, stash: number) => {
    // No upstream: fall back to counting commits that exist on no remote at all.
    if (!state.repo || state.upstream) {
      done({ ...state, stash })
      return
    }
    execFile("git", ["remote"], options, (remoteError, remoteOut) => {
      if (remoteError || !String(remoteOut).trim()) {
        done({ ...state, stash })
        return
      }
      execFile("git", ["rev-list", "--count", "HEAD", "--not", "--remotes"], options, (countError, countOut) => {
        const ahead = countError ? state.ahead : Number(String(countOut).trim()) || 0
        done({ ...state, stash, ahead })
      })
    })
  }

  execFile(
    "git",
    ["status", "--porcelain=v2", "--branch", "--untracked-files=normal"],
    options,
    (error, stdout) => {
      const state = error ? { ...idle } : parse(String(stdout))
      execFile("git", ["stash", "list", "--format=%gd"], options, (stashError, stashOut) => {
        const stash = stashError ? 0 : String(stashOut).split("\n").filter(Boolean).length
        finish(state, stash)
      })
    },
  )
}

function pathInfo(api: TuiPluginApi, sessionID?: string) {
  const session = sessionID ? api.state.session.get(sessionID) : undefined
  const dir = session?.directory || api.state.path.directory || api.state.path.worktree
  if (!dir) return { parent: "", name: "" }
  const home = process.env.HOME
  const shown = home && dir.startsWith(home) ? "~" + dir.slice(home.length) : dir
  const parts = shown.split("/")
  return { parent: parts.slice(0, -1).join("/"), name: parts.at(-1) ?? "" }
}

function View(props: { api: TuiPluginApi; state: () => GitState; sessionID?: string }) {
  const theme = () => props.api.theme.current
  const s = () => props.state()
  const p = () => pathInfo(props.api, props.sessionID)
  const clean = () =>
    s().added === 0 &&
    s().deleted === 0 &&
    s().staged === 0 &&
    s().modified === 0 &&
    s().untracked === 0 &&
    s().conflict === 0 &&
    s().ahead === 0 &&
    s().behind === 0

  return (
    <box flexDirection="column" flexShrink={0}>
      <text>
        <span style={{ fg: theme().textMuted }}>{p().parent}/</span>
        <span style={{ fg: theme().text }}>{p().name}</span>
        <span style={{ fg: theme().textMuted }}>{s().repo && s().branch ? ":" : ""}</span>
        <span style={{ fg: theme().accent }}>{s().repo ? s().branch : ""}</span>
        {s().repo && s().ahead > 0 ? <span style={{ fg: theme().info }}> ↑{s().ahead}</span> : null}
        {s().repo && s().behind > 0 ? <span style={{ fg: theme().info }}> ↓{s().behind}</span> : null}
        {s().repo && s().conflict > 0 ? <span style={{ fg: theme().error }}> !{s().conflict}</span> : null}
        {s().repo && s().deleted > 0 ? <span style={{ fg: theme().error }}> -{s().deleted}</span> : null}
        {s().repo && s().added > 0 ? <span style={{ fg: theme().success }}> +{s().added}</span> : null}
        {s().repo && s().staged > 0 ? <span style={{ fg: theme().warning }}> ±{s().staged}</span> : null}
        {s().repo && s().modified > 0 ? <span style={{ fg: theme().warning }}> ~{s().modified}</span> : null}
        {s().repo && s().untracked > 0 ? <span style={{ fg: theme().textMuted }}> ?{s().untracked}</span> : null}
        {s().repo && s().stash > 0 ? <span style={{ fg: theme().secondary }}> ⚑{s().stash}</span> : null}
        {s().repo && clean() ? <span style={{ fg: theme().success }}> ✓</span> : null}
      </text>
      <text fg={theme().textMuted}>
        <span style={{ fg: theme().success }}>•</span> <b>Open</b>
        <span style={{ fg: theme().text }}>
          <b>Code</b>
        </span>{" "}
        <span>{props.api.app.version}</span>
      </text>
    </box>
  )
}

const tui: TuiPlugin = async (api, options) => {
  if (options?.enabled === false) return

  const configured = typeof options?.interval === "number" ? options.interval : 0
  const interval = configured >= 500 ? configured : 2500

  const [state, setState] = createSignal<GitState>(idle)
  let pending = false

  const refresh = () => {
    if (pending) return
    const path = api.state.path
    const dir = path.worktree && path.worktree !== "/" ? path.worktree : path.directory
    if (!dir) return
    pending = true
    read(dir, (next) => {
      pending = false
      setState(next)
    })
  }

  refresh()
  const timer = setInterval(refresh, interval)
  api.lifecycle.onDispose(() => clearInterval(timer))

  const offs: (() => void)[] = []
  for (const type of ["file.edited", "file.watcher.updated", "vcs.branch.updated", "session.idle"] as const) {
    try {
      offs.push(api.event.on(type, refresh))
    } catch {
      // Event type unavailable on this host version; polling still covers it.
    }
  }
  api.lifecycle.onDispose(() => {
    for (const off of offs) off()
  })

  api.slots.register({
    order: 10,
    slots: {
      sidebar_footer: (_ctx, props) => <View api={api} state={state} sessionID={props.session_id} />,
    },
  })
}

const plugin: TuiPluginModule & { id: string } = {
  id: "git-status",
  tui,
}

export default plugin
