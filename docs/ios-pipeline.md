# The iOS pipeline: Linux to iPhone

Operational runbook for issue
[#8](https://github.com/grez-lucas/poseperfect/issues/8). The reasoning behind
every tool choice here lives in
[`docs/research/ios-signing-from-linux.md`](research/ios-signing-from-linux.md)
(issue [#2](https://github.com/grez-lucas/poseperfect/issues/2)); this file is
the procedure, not the argument.

## Shape

```
Linux (Pop!_OS)                      GitHub Actions (macos-latest)
  builder ios build ───────────────► flutter build ios --debug --no-codesign
       │                               └─ zip Payload/ -> UNSIGNED debug IPA
       └─ downloads to ./dist/ ◄───────┘  (artifact: ipa)
       │
       ▼
  signer (MobAI / iloader / plumesign)
       ├─ Apple ID login via self-hosted anisette
       ├─ mint cert + profile, re-sign the IPA
       └─ install over USB ──────────► iPhone
       │
       ▼
  flutter attach -d mobai-ios --debug-url=<device VM service URL>
```

`flutter run` and `flutter build ios` do **not** work from Linux - they are
gated on `Platform.isMacOS` in six places in `flutter_tools`. Only
`flutter attach`, via a custom device, works. Do not spend time trying to
route around this.

## Pinned versions

| Thing | Version | Why pinned |
|---|---|---|
| Flutter | 3.44.9 (stable) | Same version locally and on the runner, set in `builder.json` and consumed by the workflow's `flutter_version` input. |
| iOS deployment target | 16.0 | Issue [#19](https://github.com/grez-lucas/poseperfect/issues/19) costed RTMDet-Ins-tiny and RTMPose-m against an iOS 16 floor. Set in `app/ios/Runner.xcodeproj/project.pbxproj` and pinned again in `app/ios/Podfile`. |
| `builder` CLI | v0.5.0 | sha256 `a432de1198bf5ed8917505fa6a4b9b45c49f134ef565efd46f2291bcef8ee6c4`, verified against the release `checksums.txt`. |

## Local deviation from the generated workflow

`builder init` generates `.github/workflows/ios-build.yml` assuming **the
Flutter project is the repository root**. Ours is at `app/`, because issue #6
fixed a pub workspace layout. Two steps were patched, both marked
`LOCAL DEVIATION` in the file:

1. The **Build IPA** step - `cd "$GITHUB_WORKSPACE"` became
   `cd "$GITHUB_WORKSPACE/$FLUTTER_PATH"`.
2. The **unsigned IPA** step - the `.app` is found under
   `$FLUTTER_PATH/build/ios/iphoneos`, not `build/ios/iphoneos`.

Both derive `FLUTTER_PATH=$(dirname "$IOS_PATH")`, so `app/ios` gives `app`
while upstream's `ios` and `.` both still give `.`. The patch is therefore
behaviour-preserving for the root layout, and is a candidate to send upstream.

**Re-running `builder init` overwrites the workflow and drops this patch.**
If you regenerate, re-apply it.

`flutter pub get` is left running at the repo root on purpose: that is the pub
workspace root, and resolving from there is what produces the single root
`pubspec.lock`.

## Prerequisites, once

Both come from issue #2's risk findings and are not optional.

1. **A throwaway Apple ID**, created at icloud.com. Never the primary iCloud
   account. Signing tools call `signer.RevokeCertificate` when the free-team
   certificate ceiling is hit, and a revoke invalidates every app signed with
   that certificate - including unrelated sideloaded apps.
2. **A self-hosted anisette server.** SideStore's own docs: shared public
   anisette servers "are known to cause locking of Apple ID's".

   ```
   docker run -d --restart always --name anisette-v3 \
     -p 6969:6969 dadoum/anisette-v3-server
   ```

## Free-team limits that bite

From Apple's own account-basics page:

- Provisioning profiles **expire 7 days from issuance**.
- 10 App IDs, 3 devices, 3 apps per device - all on the same 7-day clock.

The weekly ritual is a **re-sign of the IPA already in `./dist/`**, not a
rebuild, so it costs no macOS Actions minutes. Camera and photo library are
not entitlements at all, so they are unaffected by the free tier.

## Build

**Always run `builder` from the repository root.** It reads `ios.path` from
`builder.json` there. Run it from inside `app/` and it silently re-detects the
layout instead, passing `ios_path: ios`, and the runner fails 20 seconds in
with `cd: ios: No such file or directory` (run
[31630666295](https://github.com/grez-lucas/poseperfect/actions/runs/31630666295)).
The failure is cheap but the message does not point at the cause.

```
builder ios build            # dispatches the workflow, waits, downloads to ./dist/
```

`workflow_dispatch` only runs workflows present on the **default branch**, so
`ios-build.yml` must be merged to `main` before the first build can be
dispatched. The CLI pushes the working tree as a snapshot ref and the workflow
checks that out, so uncommitted local changes do still get built.

macOS runner minutes are free here because the repo is public (map decision
11). The 10x multiplier and the "15-20 builds/month" figure in ios-builder's
README are the private-repo case and do not apply.

## Measurements

Recorded as they are taken. Nothing is filled in from inference.

| Measurement | Value |
|---|---|
| Cold `builder ios build` wall clock | **4m16s** (run [31628984414](https://github.com/grez-lucas/poseperfect/actions/runs/31628984414), 2026-08-12, `build` job 4m10s of it) |
| Unsigned debug IPA size | **30.4 MB** |
| Signed IPA size | **32.8 MB** |
| `flutter attach` hot reload | **works, ~700ms** - `Reloaded 1 of 861 libraries in 706ms (compile: 19 ms, reload: 112 ms, reassemble: 386 ms)`. Needs `tool/dev_ios.sh`; see below |
| Camera on device | **works**, front and back, after the permission prompt |
| Provisioning profile expiry | **7 days exactly.** Issued 2026-08-12 19:12:25, expires **2026-08-19 19:12:25**, `TimeToLive: 7` |
| Team ID | `UUGFKB5GBP`, bundle becomes `com.grezlucas.poseperfect.UUGFKB5GBP` |
| Warm rebuild wall clock | not measured - hot reload made it uninteresting |

Profile entitlements are `application-identifier`, `keychain-access-groups`,
`get-task-allow`, `com.apple.developer.team-identifier`. **No camera
entitlement**, confirming #2: camera is an Info.plist usage string, not a
capability, so the free tier never gates it. `get-task-allow` is what permits
the debugger attach that Flutter's JIT requires.

## The inner loop

**Use `tool/dev_ios.sh`.** Plain `builder dev flutter` does not work on this
repo, for four independent reasons, each verified in #8:

1. **Wrong working directory.** `flutter.go:133` runs `flutter attach` without
   setting `cmd.Dir`, so it inherits builder's cwd. Our Flutter project is
   `app/`, so from the repo root attach dies with
   `Target file "lib/main.dart" not found` - while from `app/`,
   `session.go:66` cannot find `dist/`. The two requirements conflict, so the
   script runs builder from the root and attach from `app/`.
2. **MobAI's port forward relays nothing on Linux.** `POST /forward` returns a
   real host listener, but reading through it gives `Empty reply from server`.
   The same VM service answers **HTTP 200 through `iproxy`** over the same
   system usbmuxd. `tool/iproxy_forward.sh` replaces it, printing the
   `FORWARD_READY` marker that Flutter's `CustomDevicePortForwarder` waits for
   (it requires a `forwardPortSuccessRegex` and blocks forever without a
   match, and iproxy is silent).
3. **`builder dev flutter` rewrites `custom_devices.json` on every run**, via
   `EnsureCustomDevice`, reverting the fix from point 2. The patch must be
   re-applied *after* every builder invocation, which is why it lives in a
   script rather than being configured once.
4. **Widget-creation tracking mismatch.** `flutter build ios` never registers
   `--track-widget-creation`, so the IPA is built with it off, while
   `flutter attach` defaults it on. Every reloaded widget then throws
   `Lookup failed: _location in widget_inspector.dart`. Attach must pass
   `--no-track-widget-creation` to match the build.

```
./tool/dev_ios.sh          # then press r to hot reload
```

Native changes (Swift, Podfile, a new plugin) still need a full
`builder ios build` and reinstall.

**Not fixed:** MobAI offers no way to use a self-hosted anisette server. Its
`settings.json` has no field for it and the server list is compiled into the
binary, so all signing went to `ani.sidestore.io` despite a local
`anisette-v3-server` running on :6969. #2's prerequisite "do not use a shared
public one" is therefore **not satisfied**. Options if this matters: sign with
`iloader` directly (its Settings does expose an anisette field), or point
`ani.sidestore.io` at localhost via `/etc/hosts`.

The 30-minute `timeout-minutes` that ios-builder issue #3 reported hitting was
not close: the first cold build, with no DerivedData cache and no Pods cache,
finished in a seventh of it.

## Device, as detected

MobAI 2.8.0 on Pop!_OS sees the phone over USB without any host-side
libimobiledevice install, because it bundles its own usbmuxd stack:

```
id           00008120-00092D4E2270201E
name         Lucas's iPhone
model        iPhone15,3
osVersion    26.6
transport    USB
state        ready
```

iOS 26.6 is far above the 16.0 floor, so the deployment target is not a
constraint on this device.

**Known Linux defect, not blocking.** MobAI repeatedly fails to bring up its
NCM network interface:

```
NCM interface stopped ... failed activating config for device ...
configuration id 5 not found in the descriptor of the device.
Available config ids: [1 2 3 4]
```

This is the "you are among the first to run this on Linux" risk from #2
materialising (the v2.8.0 Linux tarball had 0 downloads when we fetched it).
NCM is an optional network-over-USB transport; usbmuxd device access, which is
what signing and install use, works regardless.

**MobAI writes to `~/.claude.json` on first launch**, adding a global `mobai`
MCP server entry pointed at `http://127.0.0.1:8686/mcp`, and starts a web proxy
to `https://app.mobai.run`. Neither is requested nor announced. Kept
deliberately - it is a device-automation surface that may be useful when
testing capture flows on device.

## Signing, and why it is not automated here

The signing call is `POST /api/v1/devices/{id}/install-app` with
`{path, resign: true, appleId, password}`. There is **no 2FA field**: MobAI
reads the 2FA code from stdin, so the call only completes from an interactive
terminal. Automating it would mean handling an Apple ID password in a script,
which is both a bad idea and blocked by this repo's agent permissions.

**Run it yourself**, from an interactive shell, and let it prompt:

```
builder dev flutter
```

Answer `Yes` at the `Resign app` prompt, then the Apple ID, password and 2FA
code. First install also needs a tap on the phone: Settings > General >
VPN & Device Management > trust the developer.

**Accepted risk, recorded 2026-08-12.** The Apple ID in use is a real account
on the aynitech.com domain, not the throwaway #2 recommended. Lucas was shown
the certificate-revocation and Apple-ID-lockout consequences and chose to
proceed. Self-hosted anisette is running, which removes the lockout vector #2
rated most likely.
