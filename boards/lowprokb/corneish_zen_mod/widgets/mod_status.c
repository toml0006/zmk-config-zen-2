/*
 * Copyright (c) 2026 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 *
 * Modifier state indicator using 4 independent LVGL labels — one per
 * modifier. Each label holds a single Mac glyph rendered via the
 * custom mac_mods_26 font (extracted from Apple Symbols.ttf). Labels
 * are shown/hidden individually via LV_OBJ_FLAG_HIDDEN so multiple
 * modifiers can be displayed simultaneously without any string-
 * concatenation race conditions.
 *
 * U+2303 ⌃ Control  U+21E7 ⇧ Shift  U+2325 ⌥ Option  U+2318 ⌘ Command
 */

#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include <zmk/display.h>
#include "mod_status.h"
#include <zmk/event_manager.h>
#include <zmk/events/keycode_state_changed.h>
#include <zmk/hid.h>
#include <zmk/keys.h>

extern const lv_font_t mac_mods_26;

static sys_slist_t widgets = SYS_SLIST_STATIC_INIT(&widgets);

struct mod_status_state {
    zmk_mod_flags_t mods;
};

static struct mod_status_state get_state(const zmk_event_t *eh) {
    return (struct mod_status_state){.mods = zmk_hid_get_explicit_mods()};
}

static void show(lv_obj_t *label, bool visible) {
    if (label == NULL) return;
    if (visible) {
        lv_obj_clear_flag(label, LV_OBJ_FLAG_HIDDEN);
    } else {
        lv_obj_add_flag(label, LV_OBJ_FLAG_HIDDEN);
    }
}

static void apply_state(struct zmk_widget_mod_status *widget, struct mod_status_state state) {
    uint8_t m = state.mods;
    show(widget->ctrl_label,  (m & 0x01) || (m & 0x10));
    show(widget->shift_label, (m & 0x02) || (m & 0x20));
    show(widget->opt_label,   (m & 0x04) || (m & 0x40));
    show(widget->cmd_label,   (m & 0x08) || (m & 0x80));
}

// Dedup last-seen state so non-modifier keypresses don't invalidate anything.
static uint8_t last_mods = 0xFF;

static void mod_status_update_cb(struct mod_status_state state) {
    if (state.mods == last_mods) {
        return;
    }
    last_mods = state.mods;

    struct zmk_widget_mod_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { apply_state(widget, state); }
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_mod_status, struct mod_status_state, mod_status_update_cb,
                            get_state)
ZMK_SUBSCRIPTION(widget_mod_status, zmk_keycode_state_changed);

static lv_obj_t *make_mod_label(lv_obj_t *parent, const char *utf8_glyph) {
    lv_obj_t *label = lv_label_create(parent);
    if (label != NULL) {
        lv_obj_set_style_text_font(label, &mac_mods_26, LV_PART_MAIN);
        lv_label_set_text(label, utf8_glyph);
        lv_obj_add_flag(label, LV_OBJ_FLAG_HIDDEN);  // hidden by default
    }
    return label;
}

int zmk_widget_mod_status_init(struct zmk_widget_mod_status *widget, lv_obj_t *parent) {
    widget->ctrl_label  = make_mod_label(parent, "\xE2\x8C\x83");   // ⌃
    widget->shift_label = make_mod_label(parent, "\xE2\x87\xA7");   // ⇧
    widget->opt_label   = make_mod_label(parent, "\xE2\x8C\xA5");   // ⌥
    widget->cmd_label   = make_mod_label(parent, "\xE2\x8C\x98");   // ⌘
    widget->obj = widget->ctrl_label;

    sys_slist_append(&widgets, &widget->node);
    widget_mod_status_init();
    return 0;
}

lv_obj_t *zmk_widget_mod_status_obj(struct zmk_widget_mod_status *widget) {
    return widget->obj;
}
