/** @jsxImportSource @opentui/solid */
import { execFile } from "node:child_process"
import { createSignal } from "solid-js"
import { Plugin } from "@opencode/plugin/tui"

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

function sessionDirectory(context: Plugin.Context, sessionID?: string) {
  const session = sessionID ? context.data.session.get(sessionID) : undefined
  return (
    session?.location?.directory ||
    context.location?.directory ||
    context.data.location.default()?.directory ||
    ""
  )
}

function pathInfo(context: Plugin.Context, sessionID?: string) {
  const dir = sessionDirectory(context, sessionID)
  if (!dir) return { parent: "", name: "" }
  const shown = context.ui.format.path(dir)
  const parts = shown.split("/")
  return { parent: parts.slice(0, -1).join("/"), name: parts.at(-1) ?? "" }
}

// Replaces the built-in `opencode.sidebar.footer` so path, branch and working-tree
// counters stay on one line, the way the V1 plugin rendered them.
function View(props: { context: Plugin.Context; state: () => GitState; sessionID?: string }) {
  const theme = () => props.context.theme
  const s = () => props.state()
  const p = () => pathInfo(props.context, props.sessionID)
  const muted = () => theme().text.muted
  const base = () => theme().text.base
  const accent = () => theme().hue.accent[500]
  const info = () => theme().text.feedback.info.base
  const error = () => theme().text.feedback.error.base
  const success = () => theme().text.feedback.success.base
  const warning = () => theme().text.feedback.warning.base
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
    <text>
      <span style={{ fg: muted() }}>{p().parent}/</span>
      <span style={{ fg: base() }}>{p().name}</span>
      <span style={{ fg: muted() }}>{s().repo && s().branch ? ":" : ""}</span>
      <span style={{ fg: accent() }}>{s().repo ? s().branch : ""}</span>
      {s().repo && s().ahead > 0 ? <span style={{ fg: info() }}> ↑{s().ahead}</span> : null}
      {s().repo && s().behind > 0 ? <span style={{ fg: info() }}> ↓{s().behind}</span> : null}
      {s().repo && s().conflict > 0 ? <span style={{ fg: error() }}> !{s().conflict}</span> : null}
      {s().repo && s().deleted > 0 ? <span style={{ fg: error() }}> -{s().deleted}</span> : null}
      {s().repo && s().added > 0 ? <span style={{ fg: success() }}> +{s().added}</span> : null}
      {s().repo && s().staged > 0 ? <span style={{ fg: warning() }}> ±{s().staged}</span> : null}
      {s().repo && s().modified > 0 ? <span style={{ fg: warning() }}> ~{s().modified}</span> : null}
      {s().repo && s().untracked > 0 ? <span style={{ fg: muted() }}> ?{s().untracked}</span> : null}
      {s().repo && s().stash > 0 ? <span style={{ fg: muted() }}> ⚑{s().stash}</span> : null}
      {s().repo && clean() ? <span style={{ fg: success() }}> ✓</span> : null}
    </text>
  )
}

export default Plugin.define({
  id: "alexeyshirshov.git-status",
  setup(context) {
    if (context.options.enabled === false) return

    const configured = typeof context.options.interval === "number" ? context.options.interval : 0
    const interval = configured >= 500 ? configured : 2500

    const [state, setState] = createSignal<GitState>(idle)
    let pending = false

    const refresh = () => {
      if (pending) return
      const dir = context.location?.directory || context.data.location.default()?.directory || ""
      if (!dir) return
      pending = true
      read(dir, (next) => {
        pending = false
        setState(next)
      })
    }

    refresh()
    const timer = setInterval(refresh, interval)

    const offs: (() => void)[] = []
    for (const type of ["filesystem.changed", "git", "vcs.branch.updated", "session.idle", "worktree.resolved"] as const) {
      try {
        offs.push(context.data.on(type, refresh))
      } catch {
        // Event type unavailable on this host version; polling still covers it.
      }
    }

    context.ui.slot({
      replace: "sidebar.footer",
      render: (input) => <View context={context} state={state} sessionID={input.sessionID} />,
    })

    return () => {
      clearInterval(timer)
      for (const off of offs) off()
    }
  },
})
