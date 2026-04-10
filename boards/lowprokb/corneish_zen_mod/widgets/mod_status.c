/*
 * Copyright (c) 2026 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 *
 * Modifier state indicator using real Mac glyphs rendered via a
 * custom LVGL font built from Apple Symbols.ttf at 26 pt, 1-bit.
 * The font only contains the four code points we need:
 *
 *   U+2303  ⌃  Control
 *   U+21E7  ⇧  Shift
 *   U+2325  ⌥  Option
 *   U+2318  ⌘  Command
 *
 * Active modifiers are concatenated into a single label, centered
 * horizontally on the screen. The callback caches the last mods
 * bitmask and short-circuits when nothing has changed so non-modifier
 * keypresses don't trigger e-paper refreshes.
 */

#include <stdio.h>
#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include <zmk/display.h>
#include "mod_status.h"
#include <zmk/event_manager.h>
#include <zmk/events/keycode_state_changed.h>
#include <zmk/hid.h>
#include <zmk/keys.h>

// Custom font with the 4 Mac modifier glyphs (generated via lv_font_conv)
extern const lv_font_t mac_mods_26;

static sys_slist_t widgets = SYS_SLIST_STATIC_INIT(&widgets);

struct mod_status_state {
    zmk_mod_flags_t mods;
};

static struct mod_status_state get_state(const zmk_event_t *eh) {
    return (struct mod_status_state){.mods = zmk_hid_get_explicit_mods()};
}

static void set_mod_text(lv_obj_t *label, struct mod_status_state state) {
    uint8_t m = state.mods;
    bool ctrl  = (m & 0x01) || (m & 0x10);
    bool shift = (m & 0x02) || (m & 0x20);
    bool alt   = (m & 0x04) || (m & 0x40);
    bool gui   = (m & 0x08) || (m & 0x80);

    // UTF-8 encoded Mac modifier glyphs — only include the ones active.
    // Order: Ctrl, Shift, Option, Cmd (matches typical Mac notation).
    char buf[24];
    size_t n = 0;
    if (ctrl)  n += snprintf(buf + n, sizeof(buf) - n, "\xE2\x8C\x83");   // ⌃
    if (shift) n += snprintf(buf + n, sizeof(buf) - n, "\xE2\x87\xA7");   // ⇧
    if (alt)   n += snprintf(buf + n, sizeof(buf) - n, "\xE2\x8C\xA5");   // ⌥
    if (gui)   n += snprintf(buf + n, sizeof(buf) - n, "\xE2\x8C\x98");   // ⌘
    buf[n] = '\0';
    lv_label_set_text(label, buf);
}

// Dedup last-seen state so non-modifier keypresses don't trigger refreshes.
static uint8_t last_mods = 0xFF;

static void mod_status_update_cb(struct mod_status_state state) {
    if (state.mods == last_mods) {
        return;
    }
    last_mods = state.mods;

    struct zmk_widget_mod_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_mod_text(widget->obj, state); }
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_mod_status, struct mod_status_state, mod_status_update_cb,
                            get_state)
ZMK_SUBSCRIPTION(widget_mod_status, zmk_keycode_state_changed);

int zmk_widget_mod_status_init(struct zmk_widget_mod_status *widget, lv_obj_t *parent) {
    widget->obj = lv_label_create(parent);
    if (widget->obj != NULL) {
        lv_obj_set_style_text_font(widget->obj, &mac_mods_26, LV_PART_MAIN);
        // TEMP DIAGNOSTIC: show all 4 glyphs at boot so we can visually
        // verify the font can render multi-glyph strings. If only one
        // shows up at rest, the font advance widths are wrong. If all 4
        // show up at rest, concatenation works and the "only one at a
        // time" issue is pure e-paper lag catching the latest state.
        lv_label_set_text(widget->obj,
                          "\xE2\x8C\x83"    // ⌃
                          "\xE2\x87\xA7"    // ⇧
                          "\xE2\x8C\xA5"    // ⌥
                          "\xE2\x8C\x98");  // ⌘
    }

    sys_slist_append(&widgets, &widget->node);
    widget_mod_status_init();
    return 0;
}

lv_obj_t *zmk_widget_mod_status_obj(struct zmk_widget_mod_status *widget) {
    return widget->obj;
}
