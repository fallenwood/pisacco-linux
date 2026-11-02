# Picasso Linux

English | [简体中文](README.zh-CN.md)

An experimental Linux port for **Redmi K30 5G (`picasso`, SM7250 / Snapdragon
765G)**, combining Fedora Server 44 aarch64 userspace, Linux 7.3.1 as the default,
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
| Fedora Server boot and systemd | Implemented | Native Fedora userspace and init. |
| Persistent XFS root filesystem | Implemented | Installation, normal restarts and file persistence demonstrated. |
| Linux 7.3.1 default and 6.18 rescue | Implemented | Default native boot and automatic screen/Wi-Fi startup demonstrated; verified 6.18 rescue retained. |
| Petitboot multi-kernel menu | Partial | Isolated loader candidate; native menu not accepted, physical keys unverified and kernel handoff unimplemented. |
| CPU and UFS storage | Implemented | CPU bring-up, frequency scaling and storage access; not full memory or storage-endurance qualification. |
| USB networking, serial console and SSH | Implemented | USB NCM/ACM and public-key SSH access. |
| Firewall and ZRAM | Implemented | Compressed swap; all service ports intentionally open. |
| Text console and backlight control | Implemented | Native tty1, idle backlight-off and volume-up wake using the inherited framebuffer. |
| 2.4 GHz Wi-Fi | Partial | WPA2/CCMP, DHCP, DNS and HTTPS demonstrated; historical link-loss issues remain unresolved. |
| Wi-Fi IPv4/IPv6 dual stack | Implemented | Native dual-stack connectivity. |
| Startup Wi-Fi priority and fallback | Partial | Fixed CN policy on both bands with working 2.4 GHz fallback; preferred 5 GHz remains unresolved. |
| Automatic Wi-Fi reconnection | Not enabled | The latest service does not automatically retry after link loss. |
| 5 GHz Wi-Fi | Unresolved | Historical association demonstrated; initial connection and AP disconnection issues remain unresolved. |
| Rootless Podman | Partial | A limited container workload demonstrated on 7.3.1; broad workload qualification remains pending. |
| Native DSI display, GPU and touch | Not implemented | The framebuffer text console is not a full native graphics stack. |
| Bluetooth, audio, cellular and cameras | Unavailable | Not ported or not validated as usable device features. |
| Battery, charging and fuel gauge | Unavailable | Telemetry and safe charging have not been established. |
| Full-system thermal safety | Unverified | Runtime temperature guards exist; they do not establish complete thermal or charging safety. |
| Suspend and resume | Not implemented | Turning off the backlight is not system suspend. |
| Power-button shutdown | Partial | Historical input/shutdown failures remain; the 7.3.1 power service is disabled. |
| Remaining powered off after shutdown | Unresolved | The device has restarted by itself after shutdown. |
| SELinux enforcement | Not enabled | SELinux is disabled in the native runtime. |
| Long-term stability | Unverified | No daily-driver, endurance or unattended-operation qualification. |

## Documentation

Build instructions, configuration, experiment procedures, validation evidence
and historical state belong in the [bilingual project notes](notes/INDEX.md).
See the [project map](notes/PROJECT-MAP.md) for repository structure and the
[stage log](notes/PROJECT-LOG.md) for recorded progress and limitations.
[AGENTS.md](AGENTS.md) defines contributor documentation rules;
see the [source notes](notes/SOURCES.md) and [LICENSE](LICENSE) for provenance and licensing.
