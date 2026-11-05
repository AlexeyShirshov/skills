using System.Diagnostics;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.Build.Locator;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.FindSymbols;
using Microsoft.CodeAnalysis.MSBuild;
using Microsoft.CodeAnalysis.Rename;
using Microsoft.CodeAnalysis.Text;

MSBuildLocator.RegisterDefaults();

if (args.Length < 2)
{
    PrintUsage();
    return 1;
}

var slnPath = Path.GetFullPath(args[0]);
if (!File.Exists(slnPath))
{
    Console.Error.WriteLine($"error: solution not found: {slnPath}");
    return 1;
}

var verb = args[1].ToLowerInvariant();
var rest = args.Skip(2).ToArray();

if (verb == "serve") return await ServeAsync(slnPath);
if (verb == "stop") return Stop(slnPath);
return await ClientAsync(slnPath, verb, rest);

// ---------------------------------------------------------------- client

static async Task<int> ClientAsync(string slnPath, string verb, string[] rest)
{
    using var conn = await ConnectAsync(slnPath);
    if (conn is null) return 1;

    using var ns = new NetworkStream(conn, ownsSocket: true);
    using var reader = new StreamReader(ns, Encoding.UTF8);
    using var writer = new StreamWriter(ns, new UTF8Encoding(false)) { AutoFlush = true };

    var request = Request.From(verb, rest);
    await writer.WriteLineAsync(JsonSerializer.Serialize(request, Json.Options));

    var line = await reader.ReadLineAsync();
    if (line is null)
    {
        Console.Error.WriteLine("error: roslynq daemon closed the connection");
        return 1;
    }

    var response = JsonSerializer.Deserialize<Response>(line, Json.Options);
    if (response is null)
    {
        Console.Error.WriteLine("error: malformed response from roslynq daemon");
        return 1;
    }

    if (response.Output.Length > 0)
    {
        Console.Write(response.Output);
        if (!response.Output.EndsWith('\n')) Console.WriteLine();
    }

    return response.Ok ? 0 : 1;
}

static int Stop(string slnPath)
{
    var sock = SocketPath(slnPath);
    if (!File.Exists(sock))
    {
        Console.Error.WriteLine("roslynq daemon is not running");
        return 1;
    }

    try
    {
        using var conn = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);
        conn.Connect(new UnixDomainSocketEndPoint(sock));
        using var ns = new NetworkStream(conn, ownsSocket: true);
        using var writer = new StreamWriter(ns, new UTF8Encoding(false)) { AutoFlush = true };
        writer.WriteLine(JsonSerializer.Serialize(new Request { Action = "__stop" }, Json.Options));
        Console.Error.WriteLine("roslynq daemon stopped");
        return 0;
    }
    catch (Exception ex)
    {
        Console.Error.WriteLine($"error: {ex.Message}");
        return 1;
    }
}

static async Task<Socket?> ConnectAsync(string slnPath)
{
    var sock = SocketPath(slnPath);
    Directory.CreateDirectory(Path.GetDirectoryName(sock)!);

    if (File.Exists(sock) && TryConnect(sock) is { } existing)
        return existing;

    // If another daemon already holds the lock (still loading the solution, so its
    // socket isn't up yet), don't spawn a duplicate -- just wait for it below.
    if (!DaemonOwned(sock))
        SpawnDaemon(slnPath);

    var deadline = DateTime.UtcNow + TimeSpan.FromSeconds(120);
    while (DateTime.UtcNow < deadline)
    {
        if (File.Exists(sock) && TryConnect(sock) is { } conn)
            return conn;
        await Task.Delay(150);
    }

    Console.Error.WriteLine("error: timed out waiting for roslynq daemon");
    return null;
}

static Socket? TryConnect(string sock)
{
    try
    {
        var conn = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);
        conn.Connect(new UnixDomainSocketEndPoint(sock));
        return conn;
    }
    catch
    {
        return null;
    }
}

static void SpawnDaemon(string slnPath)
{
    var self = Environment.ProcessPath;
    if (self is null) return;

    var argv0 = Environment.GetCommandLineArgs().FirstOrDefault() ?? "";
    var hostedByDotnet = string.Equals(Path.GetFileNameWithoutExtension(self), "dotnet", StringComparison.OrdinalIgnoreCase);

    var psi = new ProcessStartInfo
    {
        UseShellExecute = false,
        // Keep the daemon off the caller's stdout/stderr pipes (otherwise a parent
        // reading our output waits for EOF until the daemon exits).
        RedirectStandardOutput = true,
        RedirectStandardError = true,
        WorkingDirectory = Path.GetDirectoryName(slnPath) ?? Environment.CurrentDirectory,
    };

    if (OperatingSystem.IsLinux() && File.Exists("/usr/bin/setsid"))
    {
        // New session so the daemon survives the tool call's process group being killed.
        psi.FileName = "/usr/bin/setsid";
        psi.ArgumentList.Add("-f");
        psi.ArgumentList.Add(self);
    }
    else
    {
        psi.FileName = self;
    }

    if (hostedByDotnet && argv0.EndsWith(".dll", StringComparison.OrdinalIgnoreCase)) psi.ArgumentList.Add(argv0);
    psi.ArgumentList.Add(slnPath);
    psi.ArgumentList.Add("serve");

    try
    {
        Process.Start(psi);
    }
    catch (Exception ex)
    {
        Console.Error.WriteLine($"error: cannot start roslynq daemon: {ex.Message}");
    }
}

static string SocketPath(string slnPath)
{
    var hash = Convert.ToHexString(SHA1.HashData(Encoding.UTF8.GetBytes(slnPath))).ToLowerInvariant()[..16];
    return Path.Combine(Path.GetTempPath(), "opencode", $"roslynq-{hash}.sock");
}

static string LockPath(string sock) => sock + ".lock";

// True when some daemon currently holds the per-solution lock. Uses the OS advisory
// lock (released automatically if the owner dies), so a stale lock file is harmless.
static bool DaemonOwned(string sock)
{
    try
    {
        using var _ = new FileStream(LockPath(sock), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
        return false;
    }
    catch (IOException)
    {
        return true;
    }
}

// ---------------------------------------------------------------- daemon

static async Task<int> ServeAsync(string slnPath)
{
    var sock = SocketPath(slnPath);
    Directory.CreateDirectory(Path.GetDirectoryName(sock)!);

    // Exactly one daemon per solution: the first process to take this exclusive lock
    // wins; later ones exit instead of racing to unlink/re-bind the socket and leaving
    // orphaned daemons that each keep a full solution loaded.
    FileStream guard;
    try
    {
        guard = new FileStream(LockPath(sock), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
    }
    catch (IOException)
    {
        Console.Error.WriteLine("roslynq daemon already running for this solution");
        return 0;
    }

    using var _guard = guard;
    RedirectLog(sock);

    QueryEngine engine;
    try
    {
        engine = await QueryEngine.OpenAsync(slnPath);
    }
    catch (Exception ex)
    {
        Console.Error.WriteLine($"error: cannot open solution: {ex.Message}");
        return 1;
    }

    if (File.Exists(sock))
    {
        try { File.Delete(sock); } catch { /* stale socket */ }
    }

    var listener = new Socket(AddressFamily.Unix, SocketType.Stream, ProtocolType.Unspecified);
    try
    {
        listener.Bind(new UnixDomainSocketEndPoint(sock));
        listener.Listen(8);
    }
    catch (Exception ex)
    {
        Console.Error.WriteLine($"error: cannot bind {sock}: {ex.Message}");
        engine.Dispose();
        return 1;
    }

    Console.Error.WriteLine($"roslynq daemon listening on {sock}");

    var idle = int.TryParse(Environment.GetEnvironmentVariable("ROSLYNQ_IDLE_MS"), out var parsed) && parsed > 0
        ? parsed
        : 10 * 60 * 1000;

    var cts = new CancellationTokenSource();
    var lastActivity = DateTime.UtcNow;

    _ = Task.Run(async () =>
    {
        while (!cts.IsCancellationRequested)
        {
            await Task.Delay(TimeSpan.FromSeconds(15));
            if (DateTime.UtcNow - lastActivity > TimeSpan.FromMilliseconds(idle))
            {
                Console.Error.WriteLine("roslynq daemon idle timeout, shutting down");
                cts.Cancel();
                try { listener.Close(); } catch { /* shutting down */ }
                return;
            }
        }
    });

    while (!cts.IsCancellationRequested)
    {
        Socket conn;
        try
        {
            conn = await listener.AcceptAsync(cts.Token);
        }
        catch
        {
            break;
        }

        lastActivity = DateTime.UtcNow;
        _ = Task.Run(() => HandleConnection(engine, conn, () => lastActivity = DateTime.UtcNow, cts));
    }

    try { listener.Dispose(); } catch { /* already closed */ }
    try { if (File.Exists(sock)) File.Delete(sock); } catch { /* best effort */ }
    engine.Dispose();
    return 0;
}

static async Task HandleConnection(QueryEngine engine, Socket conn, Action touch, CancellationTokenSource cts)
{
    try
    {
        using var ns = new NetworkStream(conn, ownsSocket: true);
        using var reader = new StreamReader(ns, Encoding.UTF8);
        using var writer = new StreamWriter(ns, new UTF8Encoding(false)) { AutoFlush = true };

        string? line;
        while ((line = await reader.ReadLineAsync()) is not null)
        {
            touch();

            Request? request;
            try
            {
                request = JsonSerializer.Deserialize<Request>(line, Json.Options);
            }
            catch
            {
                continue;
            }

            if (request is null) continue;

            if (request.Action == "__stop")
            {
                await writer.WriteLineAsync(JsonSerializer.Serialize(new Response { Ok = true, Output = "stopping" }, Json.Options));
                cts.Cancel();
                return;
            }

            Response response;
            try
            {
                var output = await engine.ExecuteAsync(request);
                response = new Response { Ok = true, Output = output };
            }
            catch (Exception ex)
            {
                response = new Response { Ok = false, Output = $"error: {ex.Message}\n" };
            }

            await writer.WriteLineAsync(JsonSerializer.Serialize(response, Json.Options));
        }
    }
    catch (Exception ex)
    {
        Console.Error.WriteLine($"connection error: {ex.Message}");
    }
}

static void RedirectLog(string sock)
{
    try
    {
        var logPath = Path.ChangeExtension(sock, ".log");
        var log = new StreamWriter(new FileStream(logPath, FileMode.Create, FileAccess.Write, FileShare.ReadWrite))
        {
            AutoFlush = true,
        };
        Console.SetOut(log);
        Console.SetError(log);
    }
    catch
    {
        Console.SetOut(TextWriter.Null);
        Console.SetError(TextWriter.Null);
    }
}

static void PrintUsage()
{
    Console.Error.WriteLine("""
        usage: roslynq <solution.sln> <action> [args]

          structure                     projects and top namespaces
          types <pattern>               find types by simple-name substring
          symbols <name>                definition of a type or member
          members <type>                members of a type
          refs <name>                   all references to a symbol
          callers <name>                call sites of a method/property
          implementations <name>        implementations of an interface/abstract member
          rename <name> <newName> [--apply]
                                        dry-run rename; --apply writes files
          serve                         run a background daemon for this solution
          stop                          stop the background daemon for this solution

        The first action auto-starts a background daemon that keeps the solution
        loaded; subsequent calls reuse it. Set ROSLYNQ_IDLE_MS to change the idle
        timeout (default 600000).
        """);
}

// ---------------------------------------------------------------- types

static class Json
{
    public static readonly JsonSerializerOptions Options = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        PropertyNameCaseInsensitive = true,
        DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull,
    };
}

sealed record Request
{
    public int Id { get; init; }

    public string Action { get; init; } = "";

    public string? Target { get; init; }

    public string? NewName { get; init; }

    public bool Apply { get; init; }

    public static Request From(string verb, string[] rest) => new()
    {
        Action = verb,
        Target = rest.Length > 0 ? rest[0] : null,
        NewName = rest.Length > 1 ? rest[1] : null,
        Apply = rest.Contains("--apply"),
    };
}

sealed record Response
{
    public bool Ok { get; init; }

    public string Output { get; init; } = "";
}

sealed class QueryEngine : IDisposable
{
    readonly string _slnPath;
    readonly string _slnDir;
    readonly SemaphoreSlim _gate = new(1, 1);

    MSBuildWorkspace _workspace;
    Solution _solution;
    Dictionary<string, (long Ticks, int Length)>? _snapshot;
    Dictionary<string, (long Ticks, int Length)>? _projects;

    QueryEngine(string slnPath, MSBuildWorkspace workspace, Solution solution)
    {
        _slnPath = slnPath;
        _slnDir = Path.GetDirectoryName(slnPath)!;
        _workspace = workspace;
        _solution = solution;
    }

    public static async Task<QueryEngine> OpenAsync(string slnPath)
    {
        var (workspace, solution) = await OpenWorkspace(slnPath);
        return new QueryEngine(slnPath, workspace, solution);
    }

    public void Dispose() => _workspace.Dispose();

    public async Task<string> ExecuteAsync(Request request)
    {
        await _gate.WaitAsync();
        try
        {
            await SyncAsync();
            using var output = new StringWriter();
            await Dispatch(request, output);
            return output.ToString();
        }
        finally
        {
            _gate.Release();
        }
    }

    static async Task<(MSBuildWorkspace Workspace, Solution Solution)> OpenWorkspace(string slnPath)
    {
        var workspace = MSBuildWorkspace.Create();
        workspace.RegisterWorkspaceFailedHandler(e =>
        {
            if (e.Diagnostic.Kind == WorkspaceDiagnosticKind.Failure)
                Console.Error.WriteLine($"warn: {e.Diagnostic.Message}");
        });

        var solution = await workspace.OpenSolutionAsync(slnPath);
        return (workspace, solution);
    }

    async Task SyncAsync()
    {
        var known = KnownDocuments().ToDictionary(path => path, Stat, StringComparer.Ordinal);
        var projects = ProjectStamps();
        if (_snapshot is null || _projects is null)
        {
            _snapshot = known;
            _projects = projects;
            return;
        }

        var structural = known.Count != _snapshot.Count
            || known.Keys.Any(key => !_snapshot.ContainsKey(key))
            || _snapshot.Keys.Any(key => !known.ContainsKey(key))
            || known.Keys.Any(path => !File.Exists(path))
            || AnyNewFileOnDisk(known)
            || projects.Count != _projects.Count
            || projects.Any(entry => !_projects.TryGetValue(entry.Key, out var stamp) || stamp != entry.Value);

        if (structural)
        {
            await ReloadAsync();
            return;
        }

        foreach (var (path, stamp) in known)
        {
            if (_snapshot[path] == stamp) continue;
            ApplyText(path);
        }

        _snapshot = known;
        _projects = projects;
    }

    async Task ReloadAsync()
    {
        Console.Error.WriteLine("roslynq: solution changed on disk, reloading");
        _workspace.Dispose();
        var (workspace, solution) = await OpenWorkspace(_slnPath);
        _workspace = workspace;
        _solution = solution;
        _snapshot = KnownDocuments().ToDictionary(path => path, Stat, StringComparer.Ordinal);
        _projects = ProjectStamps();
    }

    Dictionary<string, (long Ticks, int Length)> ProjectStamps()
    {
        var stamps = new Dictionary<string, (long Ticks, int Length)>(StringComparer.Ordinal);
        foreach (var project in _solution.Projects)
        {
            if (project.FilePath is not { } path) continue;
            path = Path.GetFullPath(path);
            stamps[path] = Stat(path);
        }
        return stamps;
    }

    void ApplyText(string path)
    {
        using var stream = File.OpenRead(path);
        var text = SourceText.From(stream);
        foreach (var id in _solution.GetDocumentIdsWithFilePath(path))
            _solution = _solution.WithDocumentText(id, text);
    }

    IEnumerable<string> KnownDocuments()
    {
        var set = new HashSet<string>(StringComparer.Ordinal);
        foreach (var project in _solution.Projects)
        {
            foreach (var document in project.Documents)
            {
                var path = document.FilePath;
                if (path is null) continue;
                if (!path.EndsWith(".cs", StringComparison.OrdinalIgnoreCase)) continue;
                path = Path.GetFullPath(path);
                if (IsIgnored(path)) continue;
                set.Add(path);
            }
        }
        return set;
    }

    bool AnyNewFileOnDisk(Dictionary<string, (long Ticks, int Length)> known)
    {
        foreach (var project in _solution.Projects)
        {
            var dir = project.FilePath is { } projectFile ? Path.GetDirectoryName(projectFile) : null;
            if (dir is null || !Directory.Exists(dir)) continue;
            foreach (var file in EnumerateSourceFiles(dir))
            {
                if (!known.ContainsKey(file)) return true;
            }
        }
        return false;
    }

    static IEnumerable<string> EnumerateSourceFiles(string dir)
    {
        var stack = new Stack<string>();
        stack.Push(dir);
        while (stack.Count > 0)
        {
            var current = stack.Pop();

            string[] subdirs;
            try { subdirs = Directory.GetDirectories(current); } catch { subdirs = []; }
            foreach (var subdir in subdirs)
            {
                var name = Path.GetFileName(subdir);
                if (name is "obj" or "bin" or ".git" or ".vs" or "node_modules") continue;
                stack.Push(subdir);
            }

            string[] files;
            try { files = Directory.GetFiles(current, "*.cs"); } catch { files = []; }
            foreach (var file in files) yield return Path.GetFullPath(file);
        }
    }

    static bool IsIgnored(string path)
    {
        var parts = path.Split(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        return parts.Contains("obj") || parts.Contains("bin") || parts.Contains(".git") || parts.Contains("node_modules");
    }

    static (long Ticks, int Length) Stat(string path)
    {
        var info = new FileInfo(path);
        return info.Exists ? (info.LastWriteTimeUtc.Ticks, (int)info.Length) : (0, -1);
    }

    async Task Dispatch(Request request, TextWriter w)
    {
        switch (request.Action)
        {
            case "structure": await Structure(w); break;
            case "types": await Types(w, request.Target ?? ""); break;
            case "symbols": await Symbols(w, request.Target ?? ""); break;
            case "members": await Members(w, request.Target ?? ""); break;
            case "refs": await Refs(w, request.Target ?? ""); break;
            case "callers": await Callers(w, request.Target ?? ""); break;
            case "implementations": await Implementations(w, request.Target ?? ""); break;
            case "rename": await Rename(w, request.Target ?? "", request.NewName ?? "", request.Apply); break;
            default: throw new ArgumentException($"unknown action '{request.Action}'");
        }
    }

    string Loc(Location? location)
    {
        if (location is null || !location.IsInSource) return "<no location>";
        var span = location.GetLineSpan();
        var file = span.Path;
        try { file = Path.GetRelativePath(_slnDir, file); } catch { /* keep absolute */ }
        return $"{file}:{span.StartLinePosition.Line + 1}:{span.StartLinePosition.Character + 1}";
    }

    static string Kind(ISymbol s) => s switch
    {
        INamedTypeSymbol t => t.TypeKind.ToString().ToLowerInvariant(),
        IMethodSymbol m when m.MethodKind == MethodKind.Constructor => "constructor",
        IMethodSymbol m when m.MethodKind == MethodKind.LocalFunction => "local-function",
        IMethodSymbol => "method",
        IPropertySymbol => "property",
        IFieldSymbol => "field",
        IEventSymbol => "event",
        INamespaceSymbol => "namespace",
        IParameterSymbol => "parameter",
        _ => s.Kind.ToString().ToLowerInvariant(),
    };

    async Task<INamedTypeSymbol?> ResolveType(string name)
    {
        foreach (var project in _solution.Projects)
        {
            var compilation = await project.GetCompilationAsync();
            if (compilation?.GetTypeByMetadataName(name) is INamedTypeSymbol byMeta)
                return byMeta;
        }

        var simple = name.Contains('.') ? name[(name.LastIndexOf('.') + 1)..] : name;
        foreach (var project in _solution.Projects)
        {
            var compilation = await project.GetCompilationAsync();
            if (compilation is null) continue;
            foreach (var candidate in compilation.GetSymbolsWithName(s => s == simple, SymbolFilter.Type))
            {
                if (candidate is not INamedTypeSymbol type) continue;
                var display = type.ToDisplayString();
                if (display == name || display.EndsWith("." + name))
                    return type;
            }
        }

        return null;
    }

    async Task<ISymbol?> Resolve(string name)
    {
        if (await ResolveType(name) is { } exact)
            return exact;

        if (name.Contains('.'))
        {
            var idx = name.LastIndexOf('.');
            var type = await ResolveType(name[..idx]);
            if (type is not null)
            {
                var members = type.GetMembers(name[(idx + 1)..]);
                if (members.Length > 0) return members[0];
            }
        }

        var simple = name.Contains('.') ? name[(name.LastIndexOf('.') + 1)..] : name;
        foreach (var project in _solution.Projects)
        {
            var compilation = await project.GetCompilationAsync();
            if (compilation is null) continue;
            foreach (var candidate in compilation.GetSymbolsWithName(s => s == simple, SymbolFilter.TypeAndMember))
            {
                var display = candidate.ToDisplayString();
                if (display == name || display.EndsWith("." + name) || candidate.Name == simple)
                    return candidate;
            }
        }

        return null;
    }

    string RelPath(string? path)
    {
        if (path is null) return "<unknown>";
        try { return Path.GetRelativePath(_slnDir, path); } catch { return path; }
    }

    async Task Structure(TextWriter w)
    {
        foreach (var project in _solution.Projects.OrderBy(p => p.Name, StringComparer.OrdinalIgnoreCase))
        {
            var compilation = await project.GetCompilationAsync();
            if (compilation is null) continue;
            var global = compilation.GlobalNamespace;
            var types = CountTypes(global);
            var namespaces = SourceNamespaces(global).Select(n => n.ToDisplayString()).OrderBy(n => n, StringComparer.Ordinal).ToList();

            w.WriteLine($"# {project.Name}");
            w.WriteLine($"  path:       {RelPath(project.FilePath)}");
            w.WriteLine($"  types:      {types}");
            w.WriteLine($"  namespaces: {namespaces.Count}");
            foreach (var ns in namespaces.Take(20))
                w.WriteLine($"    {ns}");
            if (namespaces.Count > 20)
                w.WriteLine($"    ... (+{namespaces.Count - 20} more)");
        }
    }

    static IEnumerable<INamespaceSymbol> SourceNamespaces(INamespaceSymbol ns)
    {
        foreach (var child in ns.GetNamespaceMembers())
        {
            if (child.DeclaringSyntaxReferences.Length > 0) yield return child;
            foreach (var nested in SourceNamespaces(child)) yield return nested;
        }
    }

    static int CountTypes(INamespaceSymbol ns)
        => ns.GetTypeMembers().Count(t => t.DeclaringSyntaxReferences.Length > 0)
           + ns.GetNamespaceMembers().Sum(CountTypes);

    async Task Types(TextWriter w, string pattern)
    {
        var found = 0;
        foreach (var project in _solution.Projects.OrderBy(p => p.Name, StringComparer.OrdinalIgnoreCase))
        {
            var compilation = await project.GetCompilationAsync();
            if (compilation is null) continue;
            foreach (var type in compilation.GetSymbolsWithName(
                         n => n.Contains(pattern, StringComparison.OrdinalIgnoreCase),
                         SymbolFilter.Type))
            {
                if (type is not INamedTypeSymbol named) continue;
                w.WriteLine($"{named.ToDisplayString()}  [{Kind(named)}]  {Loc(named.Locations.FirstOrDefault())}");
                if (++found >= 200) { w.WriteLine("... (truncated at 200)"); return; }
            }
        }
        if (found == 0) w.WriteLine($"(no types matching '{pattern}')");
    }

    async Task Symbols(TextWriter w, string name)
    {
        var symbol = await Resolve(name);
        if (symbol is null) { w.WriteLine($"(symbol not found: {name})"); return; }
        w.WriteLine($"{symbol.ToDisplayString()}");
        w.WriteLine($"  kind:      {Kind(symbol)}");
        w.WriteLine($"  namespace: {symbol.ContainingNamespace?.ToDisplayString()}");
        w.WriteLine($"  assembly:  {symbol.ContainingAssembly?.Name}");
        w.WriteLine($"  location:  {Loc(symbol.Locations.FirstOrDefault())}");
        if (symbol is INamedTypeSymbol type)
            w.WriteLine($"  members:   {type.GetMembers().Length}");
    }

    async Task Members(TextWriter w, string name)
    {
        var symbol = await Resolve(name);
        if (symbol is not INamedTypeSymbol type)
        {
            w.WriteLine(symbol is null ? $"(type not found: {name})" : $"(not a type: {name})");
            return;
        }
        w.WriteLine($"{type.ToDisplayString()}");
        foreach (var member in type.GetMembers().OrderBy(m => m.Name, StringComparer.Ordinal))
        {
            if (member is IMethodSymbol { MethodKind: MethodKind.Constructor or MethodKind.StaticConstructor } ctor && ctor.IsImplicitlyDeclared)
                continue;
            var access = member.DeclaredAccessibility.ToString().ToLowerInvariant();
            var loc = member.Locations.FirstOrDefault(l => l.IsInSource);
            w.WriteLine($"  {access} {Kind(member)} {member.ToDisplayString()}  {Loc(loc)}");
        }
    }

    async Task Refs(TextWriter w, string name)
    {
        var symbol = await Resolve(name);
        if (symbol is null) { w.WriteLine($"(symbol not found: {name})"); return; }
        var refs = await SymbolFinder.FindReferencesAsync(symbol, _solution);
        var total = 0;
        foreach (var group in refs)
        {
            w.WriteLine($"def {Loc(group.Definition.Locations.FirstOrDefault())}  {group.Definition.ToDisplayString()}");
            foreach (var loc in group.Locations.OrderBy(l => l.Location.GetLineSpan().Path, StringComparer.Ordinal))
            {
                w.WriteLine($"  {Loc(loc.Location)}");
                total++;
            }
        }
        w.WriteLine($"{total} reference(s)");
    }

    async Task Callers(TextWriter w, string name)
    {
        var symbol = await Resolve(name);
        if (symbol is not IMethodSymbol and not IPropertySymbol)
        {
            w.WriteLine(symbol is null ? $"(symbol not found: {name})" : $"(not callable: {name})");
            return;
        }
        var callers = await SymbolFinder.FindCallersAsync(symbol, _solution);
        var total = 0;
        foreach (var call in callers)
        {
            w.WriteLine($"{call.CallingSymbol.ToDisplayString()}");
            foreach (var loc in call.Locations)
            {
                w.WriteLine($"  {Loc(loc)}");
                total++;
            }
        }
        w.WriteLine($"{total} call site(s)");
    }

    async Task Implementations(TextWriter w, string name)
    {
        var symbol = await Resolve(name);
        if (symbol is null) { w.WriteLine($"(symbol not found: {name})"); return; }
        var impls = await SymbolFinder.FindImplementationsAsync(symbol, _solution);
        var total = 0;
        foreach (var impl in impls)
        {
            w.WriteLine($"{Kind(impl)} {impl.ToDisplayString()}  {Loc(impl.Locations.FirstOrDefault())}");
            total++;
        }
        w.WriteLine($"{total} implementation(s)");
    }

    async Task Rename(TextWriter w, string name, string newName, bool apply)
    {
        var symbol = await Resolve(name);
        if (symbol is null) { w.WriteLine($"(symbol not found: {name})"); return; }
        var renamed = await Renamer.RenameSymbolAsync(_solution, symbol, new SymbolRenameOptions(), newName);

        var changed = 0;
        foreach (var projectChange in renamed.GetChanges(_solution).GetProjectChanges())
        {
            foreach (var docId in projectChange.GetChangedDocuments())
            {
                var oldDoc = _solution.GetDocument(docId);
                var newDoc = renamed.GetDocument(docId);
                if (oldDoc is null || newDoc is null) continue;
                var oldText = await oldDoc.GetTextAsync();
                var newText = await newDoc.GetTextAsync();
                if (oldText.ContentEquals(newText)) continue;

                var path = oldDoc.FilePath ?? "<unknown>";
                try { path = Path.GetRelativePath(_slnDir, path); } catch { /* keep absolute */ }
                w.WriteLine($"~ {path}");

                if (apply && oldDoc.FilePath is not null)
                {
                    var encoding = newText.Encoding ?? new UTF8Encoding(encoderShouldEmitUTF8Identifier: false);
                    await File.WriteAllTextAsync(oldDoc.FilePath, newText.ToString(), encoding);
                }
                changed++;
            }
        }

        if (apply)
        {
            _solution = renamed;
            _snapshot = KnownDocuments().ToDictionary(path => path, Stat, StringComparer.Ordinal);
        }

        w.WriteLine(apply
            ? $"applied rename '{name}' -> '{newName}' in {changed} document(s)"
            : $"dry-run: {changed} document(s) would change (pass --apply to write)");
    }
}
