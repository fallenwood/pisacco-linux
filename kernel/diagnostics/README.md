# Attended Picasso Wi-Fi diagnostics (not the normal patch series)

These optional patches are **not** in `kernel/patches/series`, not enabled by
normal builds, and not a production Wi-Fi fix. The parameters default to false,
are read-only after insertion, and apply only to Picasso + ath10k SNOC.

- `ath10k-picasso-mgmt-observer.patch`: log only auth/assoc completion frame-control,
  descriptor, raw firmware status, raw ACK RSSI field and length. No addresses,
  keys, NV data, packet dumps, synthetic ACKs or altered completion handling.
- `ath10k-picasso-ht20-only.patch`: opt-in conservative HT20/legacy advertisement;
  remove HT40/SGI40 and VHT capabilities. Does not change calibration, regulatory
  rules/channel flags, power, antenna masks, firmware or protection controls.
- `ath10k-picasso-link-observer.patch`: apply after the two patches above. The
  read-only `picasso_link_observe=1` opt-in logs scan/roam reasons, matched own-AP
  beacon counts/status before the existing RX filter, beacon age, delayed-loss
  work and key command/completion metadata. No addresses, keys or frame payloads;
  it does not change callbacks, counters used for decisions, key results, RX
  filtering, beacon/probe timers, or any protection. Leave management TX logging
  off during WPA2 (`picasso_mgmt_status=0`). See
  [WIFI-LINK-LOSS.md](../../WIFI-LINK-LOSS.md) for actual causality/limitations.

Apply only in a separate/temporarily backed-up prepared 6.18.58 source tree using
matching wifi2 config and Module.symvers. Compile `M=drivers/net/wireless/ath/ath10k`
with the existing AArch64 LLVM build settings. Preserve source/patch/module hashes;
restore the prepared source and baseline host artifacts afterward. The M= output
is in the source ath10k directory, **not** a potentially stale O= module directory.

Stage the resulting core under a unique `/opt/picasso-wifi-trial/modules/` path;
never replace installed `/lib/modules` files, run depmod for it, or flash boot.
After verifying exact native wifi2/config/FDT, no active WLAN/DSP, private-copy NV
checkpoint, memory and userspace hashes, unload the offline experiment Wi-Fi stack,
load normal ath/mac80211 dependencies, then insert the exact staged core with
`picasso_mgmt_status=1 picasso_ht20_only=1`. Keep the separate guarded SNOC module,
DMS→WLFW device-MAC provisioning and actual SG regulatory audit requirements.

An accepted parameter is not verification. Check read-only Y parameter values,
HT20-only PHY capabilities, current/permanent device MAC, actual SG limits and
actual channel-context width 0/1 (20_NOHT/20). Preserve firmware status values;
nonzero is treated as unacknowledged by ath10k, but do not assign a more specific
vendor status meaning without the matching ABI definition.

Use a bounded PID-1 service with independent ExecStopPost, continuous temperature
checks during waits, start below 40°C, abort at 45°C, no automatic DSP recovery.
Cleanup disconnects/unloads WLAN, stops DSP/private proxy/TFTP, clears the validated
RMTFS RAM, unloads diagnostic core, and reloads the untouched installed core. Verify
its file hash and diagnostic-parameter absence. Recheck original NV/master files,
installed files, boot/protected/GPT. No password is needed for Open System auth.

Actual hardware tests and their failures are described in
[WIFI-TX-DIAGNOSTICS.md](../../WIFI-TX-DIAGNOSTICS.md). The observer was exercised
on native wifi2; the HT20 variant actually selected 20 MHz but did **not** fix the
three status-3 authentication completions. Neither patch establishes association,
DHCP, Internet, persistent enablement, charging safety or stability.
