# iOS signing and install from Linux with a free Apple ID

Research resolving [issue #2](https://github.com/grez-lucas/poseperfect/issues/2).
Date: 2026-08-07. Environment assumed: Pop!_OS x86_64, one physical iPhone, no Mac, no paid Apple Developer Program membership.

## Bottom line

**The pipeline exists and every load-bearing component was verified to be present and Linux-native. It has not been verified to run, because that requires the physical iPhone.**

- **MobAI is not mandatory for signing.** Two independent, actively maintained, Linux-native tools do the same job: `plumesign` (headless CLI, `claration/Impactor`) and `iloader` (`nab138/iloader`). In fact MobAI's Linux binary *embeds* `iloader-cli` and links the same open-source crates - its signing is a packaging of iloader, not a proprietary capability. **MobAI is mandatory only for the hot-reload inner loop**, because it also supplies the debugger launch and the USB port forward.
- **MobAI costs nothing for this use case.** Published pricing is Free ($0, "1 device at a time") / Pro ($9.99/mo, $99/yr). Every Pro differentiator is about *device count and parallelism*. iOS signing is not a priced feature - it is not mentioned on the pricing page at all. One device is exactly what this project has.
- **A free Apple ID genuinely suffices**, with hard limits Apple documents: 10 App IDs, 3 devices per platform, 3 apps per device, and **provisioning profiles that expire 7 days from issuance**. Camera and photo-library access are not entitlements at all, so they work. Background modes, App Groups and HealthKit are also free, contrary to common belief.
- **`flutter attach` hot reload over USB from Linux is real**, traced end to end through Flutter's own source. It is not mDNS and not WiFi - it is a usbmuxd TCP tunnel driven by Flutter's `custom_devices` port-forwarder. Note sharply: **`flutter run` and `flutter build ios` remain impossible from Linux**, gated on `Platform.isMacOS` in six places. Only `attach` works, and only via a custom device.
- **Biggest risk: the whole signing step depends on undocumented Apple private APIs plus community-run third-party anisette servers.** Apple documents no supported way for a non-Xcode client to obtain a free-team certificate, and every tool listed here hits the same private endpoints - so switching tools does not diversify the risk. See [Risks](#risks).

**Recommendation, for the human to decide:** proceed with MobAI as the day-to-day tool (it is free and turnkey), but treat `plumesign` as the automation target for the weekly re-sign and as the designated fallback, and self-host an anisette server before the first sign. Run the [validation checklist](#what-would-settle-the-open-questions) before any further iOS delivery decisions.

## Evidence standard

Load-bearing claims come from: the `MobAI-App/ios-builder` source and issue tracker, the shipped MobAI Linux binary itself (`MobAI_2.7.2_linux_amd64.tar.gz`, disassembled for symbols and strings), mobai.run, Apple's own developer documentation, and the `flutter/flutter` source. Community sources are marked as such and are never the sole basis for a claim.

Every claim below is tagged **VERIFIED**, **INFERRED**, or **COULD NOT ESTABLISH**.

---

## The pipeline, as it actually works

```
Linux (Pop!_OS)                     GitHub Actions (macos-latest)
  builder ios build ──────────────► flutter build ios --debug --no-codesign
       │                              └─ zip Payload/ -> UNSIGNED debug IPA
       │                                        │
       └─ downloads to ./dist/ ◄────────────────┘  (artifact: ipa)
       │
       ▼
  MobAI desktop app (Linux .deb/.rpm/tar.gz)
       ├─ Apple ID login: SRP + GrandSlam + anisette  ─────► gsa.apple.com
       ├─ mint cert + profile                        ─────► developerservices2.apple.com
       ├─ re-sign IPA with embedded zsign
       └─ install + launch-with-debugger over bundled usbmuxd ──► iPhone (USB)
       │
       ▼
  flutter attach -d mobai-ios --debug-url=<device VM service URL>
       └─ custom-device portForwarder -> MobAI /forward -> usbmuxd tunnel
       └─ hot reload on file save
```

**VERIFIED** that the GitHub Actions half produces an *unsigned* IPA by default and that `Debug` is the default configuration: `internal/workflow/templates/ios-build.yml` lines 31-35 (`configuration` default `'Debug'`), lines 263-271 (`flutter build ios --debug --no-codesign`), lines 418-439 (unsigned path zips `Payload/`). The workflow's own build summary says: `"Signing: Unsigned (sign locally with AltStore/Sideloadly)"` (line 481). Source: <https://github.com/MobAI-App/ios-builder/blob/main/internal/workflow/templates/ios-build.yml>

**VERIFIED** that the documented `builder signing setup` path (p12 + mobileprovision in GitHub Secrets) is genuinely optional and defaults off: `use_signing` input defaults to `false` (line 26-30). The README's signing section is for people who already have a Mac-produced certificate. The ticket's framing is correct: that path is unusable without a Mac, and it is not the path we take.

---

## 1. Is MobAI mandatory?

**Answer: no, but the realistic alternative set is small, and only MobAI covers the whole loop.**

The signing step is not magic and not proprietary to MobAI. Inspecting the shipped MobAI Linux binary shows it is a Go application that statically links three Rust crates and one C++ codesigner, all of which are public:

| Component in the MobAI Linux binary | Purpose |
|---|---|
| `nab138_srp-0.6.0` | SRP handshake against Apple's GrandSlam auth |
| `nab138_icloud_auth-0.1.9` (`src/anisette.rs`, `src/client.rs`) | Apple ID login, 2FA |
| `nab138_omnisette-0.1.7` (`src/remote_anisette_v3.rs`) | anisette headers from a remote anisette-v3 server |
| `zsign-rust-0.1.7` (wrapping `zsign.cpp`, `ZSignAsset::GenerateCMS`) | re-sign the IPA, no macOS `codesign` needed |
| `resources/linux-amd64/iloader-cli` | embedded signer CLI (nab138/iloader) |
| `resources/linux-amd64/usbmuxd/` + `libimobiledevice-1.0.so.6`, `libusbmuxd-2.0.so.7`, `libplist-2.0.so.4`, `libtatsu.so.0`, `libusb-1.0.so.0` | bundled USB device stack for Linux |
| `github.com/danielpaulus/go-ios v1.0.191` (vendored fork) | lockdown / DVT / debugserver protocol |

**VERIFIED** by `strings` and Go build metadata over `MobAI_2.7.2_linux_amd64.tar.gz` (SHA-tracked release asset, published 2026-08-03): <https://github.com/MobAI-App/releases/releases/tag/v2.7.2>

The Apple endpoints embedded in the binary are the classic free-provisioning set:

- `https://gsa.apple.com/grandslam/GsService2` with client id `com.apple.gs.xcode.auth`
- `https://developerservices2.apple.com/services/QH65B2/listTeams.action`
- `https://developer.apple.com/account/resources/{certificates,devices,profiles}/list`

**VERIFIED**. This is the same mechanism AltStore, SideStore and Sideloadly use. Nothing about it is MobAI-specific.

The MobAI signer package exposes exactly the operations the free-team lifecycle needs:

```
mobai/internal/signer.ListCertificates      .RevokeCertificate    .ErrTooManyCertificates
                      .NeedsResigning       .ProfileValidForDevice
                      .SignWithCachedCredentials  .SignCustomIPA   .ConvertPKCS12
                      .anisetteServers
```

**VERIFIED** (Go symbol table of the Linux binary).

Undocumented HTTP endpoints found in the binary that the public docs do not list:

- `POST /api/v1/devices/{id}/sign` - described internally as "Sign IPA or file"
- `POST /api/v1/devices/{id}/sign/offline` - offline signing, with env vars `MOBAI_SIGN_P12_B64` / `MOBAI_SIGN_KEY_B64`

**VERIFIED** (strings). **INFERRED**: `sign/offline` plus `SignWithCachedCredentials` is the hook a scripted weekly re-sign would use. Its request schema is not published - see [Q5](#5-the-7-day-refresh-loop-in-practice).

**What MobAI uniquely provides beyond signing**, and why swapping it out is not free:

1. `POST /devices/{id}/debug` - launches the app under a debugger. Flutter debug mode needs JIT, and iOS only grants JIT to a process running under a debugger. Without this, a debug Flutter build will not start.
2. `POST /devices/{id}/forward` - the usbmuxd TCP tunnel that `flutter attach`'s port forwarder drives.
3. The `mobai-ios` Flutter custom device that `builder dev flutter` writes to `~/.config/flutter/custom_devices.json`.

A signer-only replacement gets you an installed app but **not** the hot-reload loop, unless you rebuild items 1 and 2 yourself on top of `libimobiledevice` / `go-ios`. **INFERRED** from `internal/dev/flutter.go` and `internal/dev/session.go`.

**Two Linux-native signers were verified to do the same job as MobAI's signer, independently:**

- **`plumesign`** (part of `claration/Impactor`, MIT, v2.6.0 2026-07-02) - ships `plumesign-linux-x86_64`, a **headless CLI** that logs into an Apple ID, requests certificates and profiles, registers the device, signs and installs. **VERIFIED** via the release asset list and the command surface in `apps/plumesign/src/commands/`.
- **`iloader`** (`nab138/iloader`, MIT, v2.3.1 2026-08-01) - ships `.deb`, `.rpm` and AppImage for amd64 and arm64. Signs with a free Apple ID via the `isideload` Rust library. **VERIFIED** via the release asset list.

Note the circularity: `iloader-cli` is the binary MobAI itself embeds for `linux-amd64`, and MobAI links the same `nab138_*` crates. **MobAI's signing is a packaging of iloader, not a proprietary capability.** That is reassuring for vendor risk (the core is open source and independently distributed) and unhelpful for structural risk (both hit the same private Apple endpoints).

**So the honest answer to "is MobAI mandatory":** for signing, no - `plumesign` or `iloader` will do it, and `plumesign` is scriptable where MobAI's equivalent endpoint is undocumented. For the *hot reload inner loop* as `ios-builder` ships it, yes, MobAI is currently the only turnkey option; the alternative is assembling `iproxy` + `pymobiledevice3` behind Flutter's custom-device config yourself.

> Full fallback ranking is in [Q7](#7-fallbacks-if-mobai-is-paid-only-or-broken).

---

## 2. What does MobAI cost?

**Answer: $0 for this use case. Pricing is published, not hidden.**

Verbatim from <https://mobai.run/#pricing>:

| Tier | Price | Includes |
|---|---|---|
| **Free** | `$0 · unlimited usage, 1 device at a time` | 1 device at a time; Unlimited daily AI usage; Testing mode; AI test generation & fix |
| **Pro** | `$9.99/mo · $99/yr` | Everything in Free, plus: Unlimited devices; Parallel suite runs; Multi-device runs; Cloud device farms (BrowserStack, Sauce Labs, AWS); Distributed device farm |

Footnote on the same page: `"Distributed and cloud farms are Pro."`

The FAQ (<https://mobai.run/faq/>) states: `"Is MobAI free to use? Yes. The free tier has unlimited daily usage on 1 device at a time. Pro is $9.99/mo for unlimited devices, test suites, parallel and multi-device runs, and cloud device farms."`

The download page (<https://mobai.run/download>) says `"Free tier, no credit card"`.

**VERIFIED**: iOS code signing is **not mentioned anywhere** in the pricing tiers, the FAQ, or the marketing site. The only paid axis is device count and parallelism.

**VERIFIED** that the only licence gate compiled into the binary is `mobai/internal/license.ErrDeviceLimit` - consistent with "1 device at a time" being the sole free-tier restriction. No `signing requires Pro`-style gate was found in the binary.

**INFERRED** (from absence of a paywall symbol and absence of signing from every pricing surface): signing is a base feature available on the free tier. This is negative evidence. It would be settled in five minutes by installing MobAI and signing one IPA.

**COULD NOT ESTABLISH**: whether MobAI requires creating a MobAI account at all to use the free tier. The download page says "no credit card", not "no account".

One device at a time is exactly what this project needs (decision 15 on the map: one iPhone, iOS first-class).

---

## 3. Does a free Apple ID suffice?

**Answer: yes, end to end, with documented hard limits.**

All quotes below are Apple's own words.

**Free tier can sign and run on your own device - VERIFIED**
<https://developer.apple.com/support/compare-memberships/>
> "You can learn how to develop apps for Apple platforms for free without enrolling. With just an Apple Account, you can access Xcode, software downloads, documentation, sample code, forums, and Feedback Assistant, as well as test your apps on devices."
> "Xcode Personal Team. If you're signing in to Xcode with an Apple Account that's not affiliated with the Apple Developer Program, you'll be able to perform on-device testing for personal use (Xcode refers to this as a Personal Team)."

The comparison table marks "On-device testing" for both the free Apple Account column and the 99 USD Apple Developer Program column.

**The hard limits - VERIFIED**
<https://developer.apple.com/help/account/basics/about-your-developer-account/>
> "You can register up to 10 App IDs, which expire after 7 days."
> "You can register up to 3 devices, which expire after 7 days."
> "You can install up to 3 apps per device."
> "Provisioning profiles that enable apps to be installed on a device will expire 7 days from issuance. You'll need to rebuild and reinstall your app to your device after expiration."

<https://developer.apple.com/support/compare-memberships/> adds that the device limit is per-platform:
> "The number of test devices that can be registered to your account for each platform is limited to 3 and each expires after 7 days."

**Watch out:** the "3 apps per device" limit appears on the account-basics page **only**. It is absent from compare-memberships, which is the page most people read. Both pages were checked directly; the quote above is verbatim from the account-basics page.

**Paid membership price - VERIFIED**: 99 USD per membership year (<https://developer.apple.com/programs/enroll/>).

**What the free tier cannot do - VERIFIED**: App Store distribution and ad hoc distribution are marked only in the paid column of the comparison table. Archived TN QA1915 (<https://developer.apple.com/library/archive/qa/qa1915/_index.html>): "This team allows you to build apps for your personal use on devices owned by you, but it does not allow you to code sign apps destined for the App Store or for enterprise use."

PosePerfect is a personal tool for one person on one device (map decision 1), so none of this bites.

**COULD NOT ESTABLISH**: whether the personal-team *signing certificate* has its own expiry distinct from the 7-day profile expiry. Apple documents the 7-day figure for profiles, App IDs and devices, and states nothing about certificate lifetime. Community sources commonly claim 1 year; that is unverified. What settles it: read the `notAfter` field of the certificate MobAI mints on first sign.

---

## 4. Does `flutter attach` hot reload over USB actually work?

**Answer: yes for `flutter attach`. Absolutely not for `flutter run` or `flutter build ios`. The distinction is the whole answer, and it was traced end to end in Flutter's own source. The transport is USB, not WiFi and not mDNS.**

### First, what does not work from Linux, so nobody wastes time on it

`flutter run -d <iphone>` and `flutter build ios` are gated on the host being macOS, in six separate places in `flutter_tools`. **VERIFIED** against `flutter/flutter` master:

- `IOSWorkflow.appliesToHostPlatform => _featureFlags.isIOSEnabled && _platform.isMacOS` (`lib/src/ios/ios_workflow.dart`)
- `IOSDevices.supportsPlatform => _platform.isMacOS`, and `pollingGetDevices()` throws `UnsupportedError('Control of iOS devices or simulators only supported on macOS.')` (`lib/src/ios/devices.dart`)
- `BuildIOSCommand.supported => globals.platform.isMacOS`, with `throwToolExit('Building for iOS is only supported on macOS.')` (`lib/src/commands/build_ios.dart`)
- `DeviceManager` filters discoverers before polling: `deviceDiscoverers.where((d) => d.supportsPlatform)` (`lib/src/device.dart`)
- The iOS USB artifacts (libimobiledevice, iproxy, ios-deploy) are only downloaded on macOS (`IosUsbArtifacts.updateInner`, `lib/src/flutter_cache.dart`)

Docs agree: <https://docs.flutter.dev/install/custom> lists "Target iOS - On macOS only".

The tracking issue **"Support `flutter attach` on iOS devices on non-macOS devices"** (<https://github.com/flutter/flutter/issues/56511>) has been **open since 2020-05-07, P3, no PR landed**. Related requests were closed `not_planned` (#160175: "iOS apps are built and signed using Xcode... feedback would best be directed to Apple"). **Do not expect first-class Flutter support for this; it is not coming.**

This is exactly why the pipeline builds on a macOS runner and attaches through a *custom device* rather than through Flutter's iOS device discovery.

### Why the custom-device route escapes that gate

```dart
class CustomDevices extends PollingDeviceDiscovery {
  @override
  bool get supportsPlatform => true;
```

**VERIFIED**: `lib/src/custom_devices/custom_device.dart`. The custom-devices subsystem is deliberately not host-platform gated. That single line is what makes the whole approach legal.

### The chain, each link verified in source

**Step 1.** `builder dev flutter` calls `EnsureCustomDevice`, which runs `flutter config --enable-custom-devices` and writes `~/.config/flutter/custom_devices.json` on Linux (`$APPDATA/.flutter_custom_devices.json` on Windows) with a device `mobai-ios` whose commands shell back into `builder`:

```
ping        -> builder mobai --url <mobai> ping
install     -> builder mobai --url <mobai> install ${localPath}
runDebug    -> builder mobai --url <mobai> run-debug ${appName}
forwardPort -> builder mobai --url <mobai> forward ${devicePort} ${hostPort}
```

**VERIFIED**: `internal/dev/flutter.go` lines 221-285. <https://github.com/MobAI-App/ios-builder/blob/main/internal/dev/flutter.go>

**Step 2.** The session launches the app via MobAI's debug WebSocket, scrapes the Dart VM service URL out of the device's stdout with the regex `(?:Observatory|Dart VM service)[^h]*(http://[^\s]+)`, and then runs literally:

```
flutter attach -d mobai-ios --debug-url=<device VM service URL>
```

with `MOBAI_DEVICE_ID` in the environment. **VERIFIED**: `internal/dev/flutter.go` lines 84-134.

**Step 3.** Flutter's `attach` command, given `--debug-url`, calls `buildVMServiceUri(device, host, port, hostVmservicePort, authCode)`:

```dart
actualHostPort = hostVmservicePort == 0
    ? await device.portForwarder?.forward(devicePort)
    : hostVmservicePort;
return Uri(scheme: 'http', host: host, port: actualHostPort, path: path);
```

**VERIFIED**: `packages/flutter_tools/lib/src/commands/attach.dart` lines 407-419 and `packages/flutter_tools/lib/src/mdns_discovery.dart` lines 635-665. <https://github.com/flutter/flutter/blob/master/packages/flutter_tools/lib/src/commands/attach.dart>

This is the load-bearing detail: **because `--debug-url` is supplied, Flutter skips mDNS discovery entirely** and goes straight to the device's port forwarder. The mDNS/local-network path (the one that needs the device and host on the same WiFi) is never taken.

**Step 4.** For a custom device, `portForwarder` is a `CustomDevicePortForwarder` that interpolates and runs the configured `forwardPort` command. **VERIFIED**: `packages/flutter_tools/lib/src/custom_devices/custom_device.dart` lines 121-158, 365, 438-441. <https://github.com/flutter/flutter/blob/master/packages/flutter_tools/lib/src/custom_devices/custom_device.dart>

**Step 5.** That command hits `POST /api/v1/devices/{id}/forward` on MobAI, which tunnels over its bundled Linux `usbmuxd`. **VERIFIED**: `internal/mobai/client.go` `ForwardPort`, `cmd/builder/mobai.go` `runMobaiForward`, and the `resources/linux-amd64/usbmuxd/*` resource paths in the MobAI binary.

**Step 6.** Flutter custom devices are debug-mode only - `supportsRuntimeMode` returns `buildMode == BuildMode.debug` (`custom_device.dart` line 693). This matches the workflow's `Debug` default. **VERIFIED**, and it means you cannot use this device entry for release builds. That is fine; release IPAs are installed, not attached to.

**Inner-loop cost, INFERRED from the above:**

| Change type | Cost |
|---|---|
| Dart code in `lib/` | Hot reload, sub-second. `builder dev flutter` watches `lib/**.dart` (debounce 100ms, ignoring `.g.dart`/`.freezed.dart`) and sends `r` on the attached process. VERIFIED: `internal/dev/flutter.go` lines 185-219. |
| Swift/ObjC, Podfile, native plugin, new pubspec dependency with native code | Full `builder ios build` round trip to a macOS runner, then re-install. README: "Native code changes ... Run `builder ios build` and reinstall". |

**COULD NOT ESTABLISH**: the actual wall-clock of a cold `builder ios build`. The workflow has `timeout-minutes: 30` and caches DerivedData, Pods and node_modules. Issue #3 in the tracker is titled "How to increase the timeout limit ?" - so at least one user hit 30 minutes. <https://github.com/MobAI-App/ios-builder/issues/3>

**A correction to the map's build-budget assumption.** The README says "GitHub Actions free tier: 2,000 minutes/month (macOS uses 10x multiplier = ~200 effective minutes), approximately 15-20 builds per month". That is the *private repo* figure. Map decision 11 already chose a public repo, and GitHub confirms: **"The use of standard GitHub-hosted runners is free: In public repositories."** <https://docs.github.com/en/billing/managing-billing-for-your-products/about-billing-for-github-actions>. So the 15-20 builds/month ceiling does not apply here. **VERIFIED.**

---

## 5. The 7-day refresh loop in practice

**What expires - VERIFIED (Apple):** the provisioning profile, 7 days from issuance. Also the App ID and the device registration, same 7 days.

**What Apple says you must do - VERIFIED:** "You'll need to rebuild and reinstall your app to your device after expiration."

**What you actually have to do here - INFERRED:** Apple's "rebuild" wording assumes Xcode, where signing is part of the build. In this pipeline the build and the signing are separate steps, and the expired artifact is only the embedded `.mobileprovision`. So the weekly ritual is **re-sign the IPA you already have in `./dist/` and re-install it** - no GitHub Actions run, no macOS minutes, no rebuild. This inference is directly supported by MobAI shipping `signer.NeedsResigning` and `signer.ProfileValidForDevice`: it checks whether the existing signature is still good and re-signs only if not.

MobAI's own UI states the cycle in its own words, found verbatim in the Linux binary:

> "If you set this device up with a free Apple ID, it stops working for cloud agents after 7 days. Reconnect it and run the setup step again to renew. A paid Apple Developer account lasts a year."

**VERIFIED** (string in `MobAI_2.7.2_linux_amd64`). Note this string is about MobAI's cloud-agent device setup, not about your app's profile; but it is the same underlying 7-day free-team expiry.

**The ritual, as concretely as the evidence supports:**

1. Plug the iPhone in over USB. Start MobAI.
2. Re-sign and re-install. Two known ways:
   - `builder dev flutter` and answer `Yes` at the `Resign app` prompt, then Apple ID and password. **VERIFIED**: `internal/dev/session.go` lines 196-249.
   - `mobai app install ./dist/<build>.ipa` from the MobAI CLI (`npm i -g @mobai-app/cli`, ships a Linux x64 native binary). **VERIFIED**: <https://mobai.run/docs/cli/>. **COULD NOT ESTABLISH** whether this CLI path exposes a `--resign` flag; the CLI docs list `app install <path>` with no signing flags.
3. First install after a re-sign: on the phone, Settings > General > VPN & Device Management, trust the developer. `ios-builder` has a dedicated error for this: `"launch failed: developer not trusted - on device go to Settings > General > VPN & Device Management and trust the developer"`. **VERIFIED**: `internal/dev/session.go` line 294.
4. The bundle ID gains a team-ID suffix on re-sign (`com.example.myapp.TEAMID`), and subsequent runs need `builder dev flutter --skip-install --bundle-id com.example.myapp.TEAMID`. **VERIFIED**: README "Flutter Development" section.

**Can it be automated from Linux? Yes, mostly - and the best automation hook is not MobAI's.**

Three routes, best first:

1. **`plumesign` (Impactor's headless CLI) - VERIFIED to exist, INFERRED to fit.** `plumesign-linux-x86_64` is a real, published release artefact with `account login` and `sign --package <ipa> --apple-id --register-and-install --udid <UDID>`. This is a documented CLI, unlike MobAI's `sign` endpoint. A `justfile` recipe or weekly systemd timer around it is straightforward. **This is the recommended automation target even though MobAI is the recommended day-to-day tool.** See [Q7 rank 1](#rank-1-impactor--plumesign---the-scriptable-one).
2. **MobAI's local API.** `POST /api/v1/devices/{id}/sign` and `POST /api/v1/devices/{id}/sign/offline`, plus `signer.SignWithCachedCredentials` / `ClearCachedCredentials` (credentials cache after first interactive login; `ErrNoCachedCredentials` is the miss case). Workable, but **neither endpoint is in the published API docs**, so the request schema is unknown and unsupported. **INFERRED.**
3. **SideStore - eliminate the ritual rather than script it.** SideStore refreshes signatures on-device over WiFi with no computer attached at all. It does not remove the desktop step for a *new build*, but it removes it for *keeping the existing build alive*. See [Q7 rank 3](#rank-3-sidestore---the-one-that-kills-the-weekly-ritual). **VERIFIED** capability, **COULD NOT ESTABLISH** whether it can import an arbitrary locally-built IPA on-device.

**What cannot be automated:** plugging the phone in; Apple 2FA, which is interactive by construction and can re-prompt at any time; and the first-time Settings trust tap.

**Hazards the evidence surfaces:**

- `signer.ErrTooManyCertificates` and `signer.RevokeCertificate` exist in the binary. **VERIFIED.** Free Apple IDs have a low development-certificate ceiling, and the tool's remedy is to revoke. **Revoking invalidates every other app signed with that certificate** - so if the same Apple ID is also used by AltStore/SideStore for other sideloaded apps, a weekly re-sign can silently break them. This is the concrete reason the ios-builder README says: "Re-signing requires an iCloud account - we highly recommend creating a new one at icloud.com instead of using your primary account." **Follow that advice.**
- App ID quota: 10 per rolling 7 days. One app costs 1. Experimenting with bundle IDs burns the quota fast, and there is no way to clear it early.

---

## 6. Entitlement limits on a free team

**Answer: camera and photo library are fine. They are not capabilities at all, so membership tier is irrelevant to them.**

Apple's canonical list is <https://developer.apple.com/help/account/reference/supported-capabilities-ios/>, which opens: "The capabilities available to an iOS provisioning profile depend on your program membership."

**Camera and photo library do not appear anywhere in that table. VERIFIED.** They are gated by Info.plist usage strings and a runtime permission prompt, not by an entitlement:

- `NSCameraUsageDescription` - "This key is required if your app uses APIs that access the device's camera." <https://developer.apple.com/documentation/bundleresources/information-property-list/nscamerausagedescription>
- `AVCaptureDevice.requestAccess(for:completionHandler:)` - "Your app must provide an explanation for its use of capture devices using the NSCameraUsageDescription and NSMicrophoneUsageDescription Info.plist keys ... Calling this method or attempting to start a capture session without a usage description raises an exception." <https://developer.apple.com/documentation/avfoundation/avcapturedevice/requestaccess(for:completionhandler:)>
- `NSPhotoLibraryUsageDescription` - "This key is required if your app uses APIs that have read or write access to the user's photo library." <https://developer.apple.com/documentation/bundleresources/information-property-list/nsphotolibraryusagedescription>
- `NSPhotoLibraryAddUsageDescription` - add-only variant, "required if your app uses APIs that have write access to the user's photo library." <https://developer.apple.com/documentation/bundleresources/information-property-list/nsphotolibraryaddusagedescription>

Map decision 16 keeps photos app-private with explicit export. That export path will need `NSPhotoLibraryAddUsageDescription`; reading the library is not needed at all.

**The free-vs-paid capability matrix, extracted from the raw HTML of Apple's supported-capabilities page (the checkmark markup, since the rendered text is ambiguous). VERIFIED.** Of 57 capabilities, exactly 9 are available to a free Apple Account:

> **Free:** App groups · Background modes · Data protection · HealthKit · HomeKit · Inter-App Audio · Keychain sharing · Maps · Wireless Accessory Configuration

> **Paid only (48), including:** Push notifications · Associated domains · Sign in with Apple · iCloud (CloudKit, documents, key-value) · Apple Pay · Game Center · In-App Purchase · WeatherKit · Siri · Wallet · Network extensions · NFC · App Attest · Fonts · Personal VPN · Communication Notifications · Time Sensitive Notifications · Family Controls · Increased Debugging Memory Limit

**Relevant to this project:**

- **Background modes is free.** This matters for map decision 20 ("scoring must not block the session"). If background scoring ever needs to survive app backgrounding, the entitlement is available.
- **HealthKit and App Groups are free.** Both are commonly assumed paid-only; they are not.
- Nothing PosePerfect v1 needs is in the paid column. It is offline-absolute with no network permission (decision 20), no push, no iCloud, no sharing (out of scope).
- **Local notifications** (`UNUserNotificationCenter`) are not a capability and are unaffected. But *Time Sensitive* and *Communication* notifications **are** capabilities and are paid-only - relevant if session timing beats ever wanted to escalate a notification. Tones and TTS (decision 18) do not.

**INFERRED, flagged:** Apple's supported-capabilities page labels the free column "Apple Developer" (an Apple Account holder who agreed to the developer agreement) and never uses the phrase "Personal Team". Equating that column with the Xcode Personal Team is a reasonable reading but Apple does not state the equivalence.

---

## 7. Fallbacks if MobAI is paid-only or broken

MobAI is not paid-only (Q2), so this is contingency planning. Ranked by fitness for *this* project, not by general quality.

Every option in this list mints its certificate the same way, against the same private Apple endpoints, using an anisette server. None of them escapes the 7-day expiry or the 10/3/3 quotas. **Switching tools does not reduce the structural risk; it only reduces the vendor risk.**

### Rank 1. Impactor / `plumesign` - the scriptable one

<https://github.com/claration/Impactor> - MIT, 2,848 stars, v2.6.0 released 2026-07-02, last push 2026-07-23. **VERIFIED** via GitHub API.

The v2.6.0 release ships **`plumesign-linux-x86_64`**, a headless CLI, alongside `Impactor-linux-x86_64.appimage`. Also on Flathub as `dev.khcrysalis.PlumeImpactor`. **VERIFIED** (release asset list).

README, verbatim: "Sign and sideload applications on iOS 9.0+ & Mac with your Apple ID" and "we try to replicate what Xcode would do but in our own application, by using your Apple Account ... so we can request certificates, provisioning profiles, and register your device from Apple themselves".

`plumesign` exposes `sign`, `macho`, `account` (`login/logout/list/switch/certificates/devices/register-device/app-ids`) and `device`. The sign command takes `--package`, `--apple-id`, `--register-and-install`, `--udid`, `--custom-identifier`, `--output`.

**This is the only fully headless, Linux-native, free-Apple-ID signing pipeline found.** That makes it the strongest candidate for automating the weekly re-sign (Q5) - stronger than MobAI's own undocumented `sign/offline` endpoint.

Known blockers, all open issues: no custom anisette URL (<https://github.com/claration/Impactor/issues/191>, maintainer: "We don't have that as an option though"); an open "A valid provisioning profile for this executable was not found" bug (<https://github.com/claration/Impactor/issues/224>, opened 2026-07-30); 2FA friction (#218, #222). Its README also warns that on some distributions `usbmuxd` stops running when no device is attached - plug the phone in before starting the app.

### Rank 2. iloader - the reliable GUI one

<https://github.com/nab138/iloader> - MIT, 2,346 stars, **v2.3.1 released 2026-08-01**, last push same day. The most actively developed tool in this space, and the one SideStore officially recommends for installation. **VERIFIED** via GitHub API.

Linux artefacts in v2.3.1: `iloader-linux-amd64.deb`, `iloader-linux-x86_64.rpm`, `iloader-linux-amd64.AppImage` (plus arm64/aarch64, all `.sig`-signed). **VERIFIED** (release asset list).

Signs with a free Apple ID via <https://github.com/nab138/isideload> ("A Rust library for sideloading iOS applications using an Apple ID"). Features include "Import any IPA" and "See and revoke development certificates & app ids". Anisette server is selectable in Settings, defaulting to `ani.sidestore.io`. Handles 2FA interactively.

**This is the tool the ios-builder maintainer himself recommended when MobAI's 2FA broke** - see <https://github.com/MobAI-App/ios-builder/issues/1>. It is also, in `iloader-cli` form, embedded inside MobAI's own Linux binary. Using it directly is a well-trodden downgrade path.

**Specific risk on Pop!_OS:** open Wayland/Mesa blank-window bug, <https://github.com/nab138/iloader/issues/576> (opened 2026-07-25, unfixed) - the AppImage bundles its own older `libwayland-client.so`. **Prefer the `.deb` over the AppImage.** GUI only, so not scriptable.

### Rank 3. SideStore - the one that kills the weekly ritual

<https://github.com/SideStore/SideStore> - AGPL-3.0, 6,016 stars, v0.6.3 released 2026-05-05, last commit 2026-08-06. **VERIFIED**.

This is an *addition* to rank 1 or 2, not a replacement. SideStore is an on-device app that re-signs and refreshes your other sideloaded apps from the phone itself. From <https://sidestore.io/>: "No jailbreak needed, and **no computer** after the initial install, only a Wi-Fi connection." From <https://docs.sidestore.io/docs/faq>: "You only need a computer once during installation."

Bootstrap still needs a Linux desktop tool once (Impactor or iloader), a lockdown pairing file, and the StosVPN loopback shim (<https://github.com/SideStore/StosVPN>).

**Why it matters here:** it is the only credible answer to "can the 7-day loop stop requiring a laptop and a USB cable". **COULD NOT ESTABLISH** whether it can import an arbitrary locally-built IPA from the Files app post-setup; the FAQ says yes for sideloading generally but documents no custom-IPA flow. Assume you re-run the desktop tool for each new *build*, and let SideStore handle refreshes of the *existing* build between builds.

### Rank 4. Assemble the dev loop yourself: `iproxy` + `pymobiledevice3` + Flutter custom devices

If MobAI is what breaks (rather than signing), the three roles it plays are all just shell commands in `custom_devices.json`. `iproxy LOCAL_PORT:DEVICE_PORT` from `libusbmuxd` is a drop-in for `forwardPort`. `pymobiledevice3` (GPL-3.0, v10.3.1 released 2026-08-03, actively maintained, Linux-native, supports iOS 17.4+ tunnels without root - <https://doronz88.github.io/pymobiledevice3/guides/ios17-tunnels/>) covers install and debug launch.

**INFERRED, not tested.** This is a real engineering project, not a config change. Cost is measured in days.

### Rank 5. Dadoum/Sideloader - the ancestor, kept as a last resort

<https://github.com/Dadoum/Sideloader> - GPL-3.0, 989 stars. Ships `sideloader-cli-x86_64-linux-gnu.zip`. Genuinely does free-Apple-ID signing and reverse-engineered the endpoints the others now use. But **last release 1.0-pre4 on 2024-10-01, last commit 2026-02-12**. Semi-dormant. Fallback only.

### Companion, recommended regardless: self-hosted anisette

<https://github.com/Dadoum/anisette-v3-server> - last push 2026-08-01, 531 stars. `docker run -d --restart always --name anisette-v3 -p 6969:6969 dadoum/anisette-v3-server`.

SideStore's own docs warn: "Older Anisette servers that are used by many users are known to cause **locking of Apple ID's**" (<https://docs.sidestore.io/docs/faq>). Self-hosting removes both the availability risk and the account-lock risk. **Note this rules against Impactor slightly** - Impactor cannot point at a custom anisette URL (#191), whereas MobAI has a `--anisette-server` flag and iloader has a Settings field.

### Ruled out, with reasons

| Option | Why not |
|---|---|
| **AltServer-Linux** | **Obsolete.** Last real commit 2022-05-05; the 2025 push is a keepalive bot. Upstream `AltServer-Windows` frozen 2022-07-14. No documented 2FA path in `AltServerMain.cpp`. Superseded by ranks 1-2. <https://github.com/NyaMisty/AltServer-Linux> |
| **Sideloadly** | **No Linux build.** macOS 10.12+ and Windows 7+ only, and the project publishes no Wine guidance. <https://sideloadly.io/> |
| **libimobiledevice / `ideviceinstaller`** | **Cannot sign - at all.** Zero Apple-ID or certificate code in the suite. `installd` on the device rejects unsigned IPAs, so no host tool can route around it: `0xe8008015 "A valid provisioning profile for this executable was not found"`. Three independent reports across six years: <https://github.com/libimobiledevice/ideviceinstaller/issues/158>, <https://github.com/libimobiledevice/ideviceinstaller/issues/172>, <https://github.com/libimobiledevice/libimobiledevice/issues/1744>. It is the transport layer, never the signer. (Healthy project - 1.4.0 released 2025-10-10.) |
| **zsign** | **A component, not a solution.** It re-signs "with custom certificates and provisioning profiles" you must already hold. A free Apple ID cannot produce them without one of ranks 1-2 first. Its ad-hoc mode is rejected by non-jailbroken iOS. (This is exactly the role it plays *inside* MobAI.) <https://github.com/zhlynn/zsign> |
| **Feather / ESign / Ksign** | **Solves the opposite problem.** Feather's own description: "using certificates part of the **Apple Developer Program**", and `HOW_IT_WORKS.md` requires "a `.p12` and `.mobileprovision` pair". A free Apple ID cannot produce those. Also chicken-and-egg: Feather ships as an IPA you must already be able to sign. <https://github.com/claration/Feather> |
| **TestFlight** | **Paid only, categorically.** Apple's membership matrix marks "App distribution", "App management, testing, and analytics with App Store Connect" and "Ad hoc distribution" as Program-only, with no dot in the free column. TestFlight lives entirely inside App Store Connect, which a free Apple Account cannot access. <https://developer.apple.com/support/compare-memberships/> |
| **`flutter run` / `flutter build ios` from Linux** | **Hard-gated on `Platform.isMacOS` in six places in `flutter_tools`** - see Q4. Not a workaround target. |
| **Paying the 99 USD** | Worth stating plainly as the honest escape hatch: it does **not** remove the need for a signer on Linux, because Apple still documents no non-Xcode route to a certificate for an *individual* account (`"Individual keys aren't able to use Provisioning endpoints"`). It buys a 1-year profile instead of 7 days, and TestFlight. It does not buy a Mac-free build. |

---

## Risks

Ordered by how much of the map they would invalidate.

### 1. The signing step rests on undocumented Apple private APIs. This is the structural risk.

**VERIFIED**: Apple documents free provisioning *only* through Xcode. "Your account's App IDs, devices, certificates, and provisioning profiles are managed directly in Xcode" (<https://developer.apple.com/help/account/basics/about-your-developer-account/>). The two documented non-Xcode routes are both paid-gated: the Certificates, Identifiers & Profiles portal ("Once you're enrolled, you'll be able to access...") and the App Store Connect API (which requires an App Store Connect account, and where "Individual keys aren't able to use Provisioning endpoints" - <https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api>).

**COULD NOT ESTABLISH**: any Apple-published API by which a non-Xcode client obtains a free-team certificate. `developerservices2.apple.com/services/QH65B2/*` and `gsa.apple.com/grandslam/GsService2` are private, reverse-engineered, and Apple can change or block them without notice. Every tool in the fallback list shares this single point of failure - MobAI, iloader, Impactor, SideStore, Sideloadly and AltStore all hit the same endpoints. **Diversifying tools does not diversify this risk.**

This is not a reason to abandon the plan. It is a reason to (a) keep the app's iOS-specific surface thin so an Android-only fallback stays viable, which map decision 15 already does by keeping Android compiling, and (b) accept that if Apple closes this door, the only remaining route to an iPhone is 99 USD/year *plus a Mac* - and note from [Q7](#ruled-out-with-reasons) that paying alone does not fix it, because Apple's provisioning endpoints are still closed to individual App Store Connect keys.

### 2. Anisette servers are third-party and community-run.

The MobAI Linux binary hardcodes a list of remote anisette-v3 servers: `ani.sidestore.io`, `ani.sidestore.app`, `ani.sidestore.zip`, `ani.f1sh.me`, `ani.846969.xyz`, `ani.neoarz.com`, `anisette.crystall1ne.dev`. **VERIFIED** (strings). Probed 2026-08-07: all returned HTTP 200 except `ani.f1sh.me`, which failed to connect.

Anisette headers are required for Apple GrandSlam auth: Apple's `AOSKit`/`CoreADI` produce machine-identity headers (`X-Apple-I-MD`, `X-Apple-I-MD-M`) that no non-Apple platform can generate natively, so every free-Apple-ID signer on Linux proxies through an anisette server. If they go down, signing stops - for MobAI, iloader, Impactor and SideStore alike.

**Worse than availability: SideStore's own docs warn of account lockout.** <https://docs.sidestore.io/docs/faq>: "Older Anisette servers that are used by many users are known to cause **locking of Apple ID's**."

**Mitigation, and it is cheap: self-host.** `docker run -d --restart always --name anisette-v3 -p 6969:6969 dadoum/anisette-v3-server` (<https://github.com/Dadoum/anisette-v3-server>, last push 2026-08-01). MobAI has an `--anisette-server` flag and iloader has a Settings field, so both can be pointed at it. **VERIFIED** that the flag/field exist; **INFERRED** that self-hosting works end to end here.

### 3. The Linux desktop build is almost certainly untested by real users.

GitHub download counts on MobAI v2.7.2 as of 2026-08-07: `MobAI.exe` 48, `MobAI_2.7.2_darwin_arm64_app.tar.gz` 79, **`mobai.deb` 1, `MobAI_2.7.2_linux_amd64.tar.gz` 1, `mobai.rpm` 2**. **VERIFIED** via the GitHub releases API.

The Linux artefacts are complete and deliberate - the binary ships a full linux-amd64 usbmuxd stack and `iloader-cli`, which nobody builds by accident. But the userbase evidence says you would be among the first people to run the iOS signing path on Linux. Every troubleshooting thread in `MobAI-App/ios-builder` issues is Windows-flavoured: issue #1's fix is "credentials ... stored in the Windows Credentials Manager", and the README's only host-specific setup section is for WSL. **VERIFIED**: <https://github.com/MobAI-App/ios-builder/issues/1>

Expect to be the one filing the Linux bug reports.

### 4. Your Apple ID password is typed into a CLI and POSTed over plain HTTP.

`builder dev flutter` prompts for `Apple ID` and `Password` and sends them as JSON fields to `http://localhost:8686/api/v1/devices/{id}/install-app`. **VERIFIED**: `internal/mobai/types.go` `InstallAppRequest{Path, Resign, AppleID, Password}` and `internal/dev/session.go` lines 206-229. Loopback plaintext, but it is a full Apple ID credential handed to a third-party binary.

Mitigation, and it is the README's own advice: **use a throwaway iCloud account created at icloud.com, not your primary Apple ID.** This also contains the certificate-revocation blast radius from Risk 5.

Note also that MobAI's WSL instructions tell users to enable "Allow external connections" on the API server, which would expose that same plaintext endpoint on the LAN. **Do not enable that on Linux - it is unnecessary here.**

### 5. Apple 2FA is a known rough edge in this specific integration.

`ios-builder` issue #1 is exactly this: `"Error: install app: API error: signing failed: 2FA required but no handler configured"`. The maintainer's interim workaround was to use `nab138/iloader` directly, then "This should be fixed in MobAI 2.3.0" (2026-06-27). The current release is 2.7.2. The string `"2FA required but no handler configured"` is **still present** in the 2.7.2 Linux binary, alongside `"Failed to read 2FA code from stdin: "` - **VERIFIED**, which suggests the fix was to add an interactive stdin handler rather than to remove the failure mode. The original reporter's resolution was `"solved by using sideloadly, seems mobai not handling 2fa properly?"`. <https://github.com/MobAI-App/ios-builder/issues/1>

**INFERRED**: expect 2FA to require an interactive terminal, and expect it to be the flakiest part of the weekly ritual.

### 6. Certificate revocation can break unrelated sideloaded apps.

See [Q5 hazards](#5-the-7-day-refresh-loop-in-practice). Mitigated entirely by the throwaway-Apple-ID advice.

### 7. `ios-builder` is a young, thin-bus-factor project.

654 stars, MIT, last push 2026-07-31, 4 issues ever filed (3 closed), effectively one maintainer. **VERIFIED** via the GitHub API. It is a ~1,500-line Go CLI whose only hard dependency is MobAI's HTTP API. If it went unmaintained you could vendor or reimplement it; that is a real but bounded cost.

---

## What would settle the open questions

None of these need more reading. They need the iPhone.

0. **Create a throwaway iCloud account at icloud.com.** Do not use the primary Apple ID for any of the below. This bounds the certificate-revocation and account-lock blast radius (Risks 2, 4, 6).
1. **Stand up `dadoum/anisette-v3-server` in Docker**, and point the signer at it. Removes Risk 2 before it can bite.
2. **Install MobAI on Pop!_OS and sign one IPA.** Settles: whether signing is free-tier (Q2), whether the Linux signing path works at all (Risk 3), and whether 2FA is survivable (Risk 5).
3. **Read the minted certificate's `notAfter`.** Settles the certificate-vs-profile expiry question in Q3.
4. **Run `builder dev flutter`, edit a `.dart` file, watch for a hot reload.** Settles Q4 as executed fact rather than traced mechanism.
5. **Re-sign a 7-day-old IPA without rebuilding.** Settles the central inference in Q5 - that the weekly ritual costs no macOS minutes.
6. **Time one cold `builder ios build`.** Settles the native-change round-trip cost.
7. **Sign the same IPA once with `plumesign` too.** Confirms the fallback is live before you need it, and settles whether the weekly re-sign can be scripted.

This is the tracer bullet the map already calls for. It should be run before any further iOS delivery decisions are made.

---

## Sources

**Primary - `MobAI-App/ios-builder`**
- Repository and README: <https://github.com/MobAI-App/ios-builder>
- Build workflow template: <https://github.com/MobAI-App/ios-builder/blob/main/internal/workflow/templates/ios-build.yml>
- Flutter dev handler: <https://github.com/MobAI-App/ios-builder/blob/main/internal/dev/flutter.go>
- Dev session and resign prompt: <https://github.com/MobAI-App/ios-builder/blob/main/internal/dev/session.go>
- MobAI API client and types: <https://github.com/MobAI-App/ios-builder/blob/main/internal/mobai/client.go>, <https://github.com/MobAI-App/ios-builder/blob/main/internal/mobai/types.go>
- Issue #1, "your app is not properly signed for this device" (2FA, free account confirmation, iloader workaround): <https://github.com/MobAI-App/ios-builder/issues/1>
- Issue #3, build timeout: <https://github.com/MobAI-App/ios-builder/issues/3>

**Primary - MobAI**
- Product site and pricing: <https://mobai.run>
- Downloads and platform requirements: <https://mobai.run/download>
- HTTP API docs: <https://mobai.run/docs/>
- CLI docs: <https://mobai.run/docs/cli/>
- FAQ: <https://mobai.run/faq/>
- Release artefacts and download counts: <https://github.com/MobAI-App/releases/releases/tag/v2.7.2>
- Analysed binary: `MobAI_2.7.2_linux_amd64.tar.gz` (165 MB ELF, unstripped, Go build metadata intact)

**Primary - Apple**
- Compare memberships: <https://developer.apple.com/support/compare-memberships/>
- About your developer account (limits, 7-day expiry): <https://developer.apple.com/help/account/basics/about-your-developer-account/>
- Supported capabilities (iOS): <https://developer.apple.com/help/account/reference/supported-capabilities-ios/>
- Enrollment pricing: <https://developer.apple.com/programs/enroll/>
- `NSCameraUsageDescription`: <https://developer.apple.com/documentation/bundleresources/information-property-list/nscamerausagedescription>
- `NSPhotoLibraryUsageDescription`: <https://developer.apple.com/documentation/bundleresources/information-property-list/nsphotolibraryusagedescription>
- `NSPhotoLibraryAddUsageDescription`: <https://developer.apple.com/documentation/bundleresources/information-property-list/nsphotolibraryaddusagedescription>
- `AVCaptureDevice.requestAccess`: <https://developer.apple.com/documentation/avfoundation/avcapturedevice/requestaccess(for:completionhandler:)>
- App Store Connect API keys: <https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api>
- TN QA1915 (archived), personal team scope: <https://developer.apple.com/library/archive/qa/qa1915/_index.html>

**Primary - alternative signers and companions**
- Impactor / `plumesign`: <https://github.com/claration/Impactor>, release v2.6.0 <https://github.com/claration/Impactor/releases/tag/v2.6.0>
- iloader: <https://github.com/nab138/iloader>, release v2.3.1 <https://github.com/nab138/iloader/releases/tag/v2.3.1>, signing library <https://github.com/nab138/isideload>
- SideStore: <https://github.com/SideStore/SideStore>, <https://sidestore.io/>, docs <https://docs.sidestore.io/docs/faq>, StosVPN <https://github.com/SideStore/StosVPN>
- anisette-v3-server: <https://github.com/Dadoum/anisette-v3-server>, server list <https://github.com/SideStore/anisette-servers/blob/main/servers.json>
- Dadoum/Sideloader: <https://github.com/Dadoum/Sideloader>
- zsign: <https://github.com/zhlynn/zsign>
- Feather (ruled out): <https://github.com/claration/Feather>
- AltServer-Linux (ruled out): <https://github.com/NyaMisty/AltServer-Linux>
- Sideloadly (ruled out, no Linux build): <https://sideloadly.io/>
- libimobiledevice, unsigned-install rejections: <https://github.com/libimobiledevice/ideviceinstaller/issues/158>, <https://github.com/libimobiledevice/ideviceinstaller/issues/172>, <https://github.com/libimobiledevice/libimobiledevice/issues/1744>
- pymobiledevice3, iOS 17+ tunnels on Linux: <https://doronz88.github.io/pymobiledevice3/guides/ios17-tunnels/>

**Primary - Flutter**
- `attach` command: <https://github.com/flutter/flutter/blob/master/packages/flutter_tools/lib/src/commands/attach.dart>
- `buildVMServiceUri`: <https://github.com/flutter/flutter/blob/master/packages/flutter_tools/lib/src/mdns_discovery.dart>
- Custom device and port forwarder: <https://github.com/flutter/flutter/blob/master/packages/flutter_tools/lib/src/custom_devices/custom_device.dart>
- Custom devices config schema: <https://github.com/flutter/flutter/blob/master/packages/flutter_tools/static/custom-devices.schema.json>
- macOS host gates: `lib/src/ios/ios_workflow.dart`, `lib/src/ios/devices.dart`, `lib/src/commands/build_ios.dart`, `lib/src/device.dart`, `lib/src/flutter_cache.dart`
- Issue #56511, "Support `flutter attach` on iOS devices on non-macOS devices" (open since 2020): <https://github.com/flutter/flutter/issues/56511>
- CLI reference: <https://docs.flutter.dev/reference/flutter-cli>
- Custom install / target platform support: <https://docs.flutter.dev/install/custom>

**Primary - GitHub**
- Actions billing, public repositories: <https://docs.github.com/en/billing/managing-billing-for-your-products/about-billing-for-github-actions>
