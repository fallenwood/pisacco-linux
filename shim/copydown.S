/* SPDX-License-Identifier: GPL-2.0-only
 * Position-independent ARM64 copydown shim for Picasso's stock ABL.
 * Preserves EL1/EL2: Linux supports both. Requires the normal ARM64 boot
 * contract (MMU off, coherent image, interrupts masked). No sunstone MMIO.
 * IMAGE_PATH and DTB_PATH are supplied as quoted preprocessor definitions.
 */
.section .text, "ax"
.global _start, linux_image, linux_end, copy_entry, runtime_dtb, runtime_dtb_end, image_end
.balign 8
_start:
    b entry
    .long 0
    .quad 0x80000
    .quad image_end - _start
    .quad 0xa                 /* little-endian, 4K pages, physical placement */
    .quad 0, 0, 0
    .ascii "ARM\x64"
    .long 0
entry:
    msr daifset, #0xf
    /* SM7250 uses the APCS timer layout: WDT_EN at +0x40. Bring-up only. */
    movz x9, #0x17c1, lsl #16
    str wzr, [x9, #0x40]
    dsb sy
    adrp x9, copy_entry
    add x9, x9, :lo12:copy_entry
    br x9

/* Some Xiaomi ABL versions enter at Image base + text_offset. */
.org 0x80000
    b entry

.balign 0x200000
linux_image:
    .incbin IMAGE_PATH
linux_end:
.balign 8
/* Trampoline must remain outside the copy destination, even for large Images. */
.balign 4096
copy_entry:
    adrp x10, _start
    add x10, x10, :lo12:_start
    adrp x11, linux_image
    add x11, x11, :lo12:linux_image
    adrp x12, linux_end
    add x12, x12, :lo12:linux_end
    mov x13, x10
1:
    cmp x11, x12
    b.hs 2f
    ldrb w14, [x11], #1
    strb w14, [x13], #1
    b 1b
2:
    /* Clean destination and runtime DTB to PoC, then invalidate I-cache. */
    mrs x14, ctr_el0
    ubfx x14, x14, #16, #4
    mov x15, #4
    lsl x15, x15, x14
    sub x16, x15, #1
    bic x11, x10, x16
3:
    dc cvac, x11
    add x11, x11, x15
    cmp x11, x13
    b.lo 3b
    adrp x0, runtime_dtb
    add x0, x0, :lo12:runtime_dtb
    adrp x12, runtime_dtb_end
    add x12, x12, :lo12:runtime_dtb_end
    bic x11, x0, x16
4:
    dc cvac, x11
    add x11, x11, x15
    cmp x11, x12
    b.lo 4b
    dsb sy
    ic iallu
    dsb sy
    isb
    mov x1, xzr
    mov x2, xzr
    mov x3, xzr
    br x10
.balign 8
runtime_dtb:
    .incbin DTB_PATH
runtime_dtb_end:
.balign 8
image_end:
