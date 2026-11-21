// Exercise the real daemon; pass a roslynq executable to test an installed version.
import assert from "node:assert/strict"
import { execFileSync } from "node:child_process"
import { mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import { fileURLToPath } from "node:url"

const dll = fileURLToPath(new URL("../roslynq/bin/Debug/net10.0/roslynq.dll", import.meta.url))
const cli = process.argv[2] ? [process.argv[2]] : ["dotnet", dll]
const dir = mkdtempSync(join(tmpdir(), "rq-test-"))
const solution = join(dir, "Fixture.slnx")
const options = {
  cwd: dir, encoding: "utf8", timeout: 90_000,
  env: { ...process.env, TMPDIR: dir, TMP: dir, TEMP: dir },
}
const query = (...args) => execFileSync(cli[0], [...cli.slice(1), solution, ...args], options)
const write = (name, data) => writeFileSync(join(dir, name), data)
let started = false
try {
  write("Fixture.slnx", '<Solution><Project Path="Fixture.csproj" /></Solution>')
  write("Fixture.csproj", `<Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup>
    <ItemGroup><Compile Remove="excluded/**/*.cs" /></ItemGroup>
  </Project>`)
  mkdirSync(join(dir, "excluded"))
  write("Included.cs", "public class Included {}")
  write("excluded/Hidden.cs", "public class Hidden {}")
  write("NuGet.Config", "<configuration><packageSources><clear /></packageSources></configuration>")
  execFileSync("dotnet", ["restore", "Fixture.csproj"], options)

  const types = () => query("types")
  const first = types()
  started = true
  assert.match(first, /\bIncluded\b/)
  assert.doesNotMatch(first, /\bHidden\b/)
  const logs = join(dir, "opencode")
  const log = join(logs, readdirSync(logs).find(name => name.endsWith(".log")))
  const reloads = () => readFileSync(log, "utf8").split("solution changed on disk, reloading").length - 1
  assert.equal(types(), first)
  assert.equal(reloads(), 0, "an unchanged excluded source must not reload the workspace")

  write("Added.cs", "public class Added {}")
  assert.match(types(), /\bAdded\b/, "new compile inputs must be visible on the next query")
  assert.doesNotMatch(types(), /\bHidden\b/)
  assert.equal(reloads(), 1, "the added input should cause exactly one reload")
  console.log("ok: excluded source stays excluded; a new compile input is picked up once")
} finally {
  try {
    if (started) query("stop")
  } finally {
    rmSync(dir, { recursive: true, force: true })
  }
}
