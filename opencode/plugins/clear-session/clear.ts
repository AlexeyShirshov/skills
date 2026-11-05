/**
 * `/clear` — archive the current session and start fresh.
 *
 * The TUI half lives in `tui.tsx`; the decision logic sits here so it can be
 * exercised with plain fakes (`test/smoke.mjs`) instead of a live terminal.
 */

export type ClearVariant = "info" | "success" | "warning" | "error"

export interface ClearToastOptions {
  readonly title?: string
  readonly message: string
  readonly variant?: ClearVariant
  readonly duration?: number
}

export type ClearRoute =
  | { readonly type: "home" }
  | { readonly type: "session"; readonly sessionID: string }
  | { readonly type: "plugin"; readonly name: string; readonly data?: Record<string, unknown> }

/**
 * The slice of the CLI plugin context `/clear` touches. Every field matches the
 * host `Plugin.Context` structurally, so `setup` can pass the real context in.
 */
export interface ClearContext {
  readonly options: Readonly<Record<string, any>>
  readonly client: {
    readonly session: {
      update(input: { readonly sessionID: string; readonly archived: boolean }): Promise<void>
    }
  }
  readonly ui: {
    readonly router: {
      current(): ClearRoute
      navigate(destination: { readonly type: "home" }): void
    }
    readonly tabs?: {
      enabled(): boolean
      close(sessionID?: string): boolean
    }
    readonly toast: {
      show(options: ClearToastOptions): void
    }
  }
}

export type ClearOutcome = "cleared" | "archived" | "skipped" | "failed"

/**
 * V2 already ships a built-in `session.clear` (title "Clear session", slash
 * `clear`) that only navigates home and leaves the session unarchived. Reusing
 * its id with a higher layer priority replaces that command instead of adding a
 * second `/clear` row next to it — which is exactly what a fresh id did.
 *
 * If a future V2 renames the built-in, this degrades to a standalone `/clear`
 * (archiving, as before) rather than breaking.
 */
export const CLEAR_COMMAND_ID = "session.clear"

/** Standalone `/archive` command (same action, its own id — see `createArchiveCommand`). */
export const ARCHIVE_COMMAND_ID = "alexeyshirshov.clear-session.archive"

/** Layer priority that outranks the built-in `session.clear` layer. */
export const CLEAR_LAYER_PRIORITY = 1000

function reason(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

/**
 * Archive the active session, close its tab and land on a fresh one (default),
 * or archive it and stay on it (`newSession: false`).
 *
 * Archiving is reversible — the session keeps its messages and can be restored
 * through the API — unlike deleting it, which is what `/clear` did before the
 * V1 plugin switched to archiving.
 */
export async function clearSession(context: ClearContext): Promise<ClearOutcome> {
  const route = context.ui.router.current()
  if (route.type !== "session") return "skipped"

  try {
    await context.client.session.update({ sessionID: route.sessionID, archived: true })
  } catch (error) {
    context.ui.toast.show({
      title: "Clear",
      message: `Could not archive the session: ${reason(error)}`,
      variant: "error",
    })
    return "failed"
  }

  context.ui.toast.show({ title: "Clear", message: "Session archived", variant: "success" })
  if (context.options.newSession === false) return "archived"

  // An archived session leaves the session list, so its tab goes with it —
  // otherwise the "cleared" session keeps occupying a tab until closed by hand.
  // A host without session tabs simply skips this.
  try {
    if (context.ui.tabs?.enabled()) context.ui.tabs.close(route.sessionID)
  } catch {
    // Tab already closed, or tabs unavailable: the navigation below still applies.
  }

  // The home screen is V2's empty session: it becomes a real session on the next
  // prompt, which is exactly "start fresh" without creating an empty record.
  context.ui.router.navigate({ type: "home" })
  return "cleared"
}

/** Keymap command advertised as the `/clear` slash command and palette entry. */
export function createClearCommand(context: ClearContext) {
  return {
    id: CLEAR_COMMAND_ID,
    title: "Clear session",
    // Deliberately free of the word "archive": slash completion matches
    // descriptions, so `/archive` would otherwise list this row too.
    description: "Start a fresh session, keeping this one recoverable",
    group: "Session",
    palette: true as const,
    slash: { name: "clear" },
    enabled: () => context.ui.router.current().type === "session",
    run: async (): Promise<void> => {
      await clearSession(context)
    },
  }
}

/**
 * `/archive` — the same command under its accurate name.
 *
 * `slash.aliases` would do, but V2 then lists the canonical `/clear` row next
 * to the alias, so `/archive` would show the command twice. A separate id with
 * no palette entry keeps one row per name.
 */
export function createArchiveCommand(context: ClearContext) {
  return {
    id: ARCHIVE_COMMAND_ID,
    title: "Clear session",
    description: "Archive the current session and start fresh",
    group: "Session",
    slash: { name: "archive" },
    enabled: () => context.ui.router.current().type === "session",
    run: async (): Promise<void> => {
      await clearSession(context)
    },
  }
}
