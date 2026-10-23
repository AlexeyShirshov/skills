import { Plugin } from "@opencode/plugin/tui"
import { CLEAR_LAYER_PRIORITY, createArchiveCommand, createClearCommand } from "./clear.ts"

// CLI-only plugin: `/clear` archives the active session and opens a fresh one.
// The command is a keymap layer, so it needs no keybind of its own — the slash
// name and the palette entry are enough.
//
// The layer outranks the built-in `session.clear` layer so the plugin replaces
// that command (one `/clear` row, archiving) instead of competing with it.
export default Plugin.define({
  id: "alexeyshirshov.clear-session",
  setup(context) {
    if (context.options.enabled === false) return
    context.keymap.layer(() => ({
      mode: "global",
      priority: CLEAR_LAYER_PRIORITY,
      commands: [createClearCommand(context), createArchiveCommand(context)],
    }))
  },
})
