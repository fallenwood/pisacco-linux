# Picasso Linux

English | [简体中文](README.zh-CN.md)

An experimental Linux port for **Redmi K30 5G (`picasso`, SM7250 / Snapdragon
765G)**, developed with Fedora Server 44 aarch64 userspace, Linux 7.3.1 as the default,
a retained Linux 6.18 LTS rescue kernel and local hardware adaptations.

The repository contains kernel patches, device trees, a rescue initramfs, boot
image and root filesystem build tools, and guarded display, Wi-Fi and power
experiments. This is **not a complete phone OS or stable ROM**, and is not intended
as a daily-driver phone or unattended server.

## Feature status

Implemented means demonstrated within the scope recorded in the notes, not full
hardware qualification or a live health report. Partial, unresolved and unverified
items are not complete.

| Feature | Status | Scope or limitation |
| --- | --- | --- |
| Fedora Server boot and systemd | Implemented | Native Fedora 44 and 45 userspace/init demonstrated. |
| Fedora 45 upgraded root | Partial | Permanent boot and screen/Wi-Fi autostart verified; historical radio stability remains unresolved. |
| Persistent XFS root filesystem | Implemented | Installation, normal restarts and file persistence demonstrated. |
| Linux 7.3.1 default and 6.18 rescue | Implemented | Default boot demonstrated on Fedora 44/45; historical 6.18 rescue acceptance does not qualify Fedora 45. |
| Petitboot multi-kernel menu | Partial | Isolated loader candidate; native menu not accepted, physical keys unverified and kernel handoff unimplemented. |
| CPU and UFS storage | Implemented | CPU bring-up, frequency scaling and storage access; not full memory or storage-endurance qualification. |
| USB networking, serial console and SSH | Implemented | USB NCM/ACM and public-key SSH access. |
| Firewall and ZRAM | Implemented | Compressed swap; all service ports intentionally open. |
| Text console and backlight control | Implemented | Native tty1, idle backlight-off and volume-up wake using the inherited framebuffer. |
| 2.4 GHz Wi-Fi | Partial | WPA2/CCMP, DHCP, DNS and HTTPS demonstrated; historical link-loss issues remain unresolved. |
| Wi-Fi IPv4/IPv6 dual stack | Implemented | Native dual-stack connectivity. |
| Startup Wi-Fi priority and fallback | Partial | Fixed CN policy on both bands with working 2.4 GHz fallback; preferred 5 GHz remains unresolved. |
| Automatic Wi-Fi reconnection | Not enabled | The latest service does not automatically retry after link loss. |
| 5 GHz Wi-Fi | Partial | Association and data access demonstrated; intermittent initial connection and historical AP disconnection issues remain unresolved. |
| Rootless Podman | Partial | A limited container workload demonstrated on 7.3.1; broad workload qualification remains pending. |
| Native DSI display, GPU and touch | Not implemented | The framebuffer text console is not a full native graphics stack. |
| Bluetooth, audio, cellular and cameras | Unavailable | Not ported or not validated as usable device features. |
| Battery, charging and fuel gauge | Unavailable | Telemetry and safe charging have not been established. |
| Early CPU cooling | Partial | Kernel passive cooling and Wi-Fi compatibility with stricter frequency caps; no endurance qualification. |
| Full-system thermal safety | Unverified | Runtime temperature guards and early cooling do not establish complete thermal or charging safety. |
| Suspend and resume | Not implemented | Turning off the backlight is not system suspend. |
| PON reason diagnostics | Partial | One guarded native 7.3.1 sample passed; power-failure causality remains unproven. |
| Power-button shutdown | Partial | Historical input/shutdown failures remain; the 7.3.1 power service is disabled. |
| Remaining powered off after shutdown | Unresolved | The device has restarted by itself after shutdown. |
| SELinux enforcement | Not enabled | SELinux is disabled in the native runtime. |
| Long-term stability | Unverified | No daily-driver, endurance or unattended-operation qualification. |

## Documentation

Build instructions, configuration, experiment procedures, validation evidence
and historical state belong in the [bilingual project notes](notes/INDEX.md).
See [Fedora 45 screen/autostart recovery](notes/FEDORA-45-SCREEN-AUTOSTART.md) for the accepted repair and remaining limitations.
Power-reason diagnostics: [7.3.1 port](notes/PON-AUDIT-7.3.1.md) and
[one-shot native capture](notes/PON-READ-7.3.1.md).
See [network recovery and early cooling](notes/NETWORK-THERMAL-REPAIR.md) for the
repair scope and remaining limits; the later [software temperature policy](notes/THERMAL-LIMIT-65.md)
covers the current limits. See the [project map](notes/PROJECT-MAP.md) for repository structure and the
[stage log](notes/PROJECT-LOG.md) for recorded progress and limitations.
[AGENTS.md](AGENTS.md) defines contributor documentation rules;
see the [source notes](notes/SOURCES.md) and [LICENSE](LICENSE) for provenance and licensing.
