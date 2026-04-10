/*
 * Copyright (c) 2026 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 *
 * Modifier state indicator for the Corne-ish Zen left-half status screen.
 * Shows which modifier keys are currently held as a compact text line:
 *
 *   "C S A G"  all four modifiers held
 *   "  S   G"  shift + cmd held
 *   "       "  nothing held
 *
 * C=Ctrl, S=Shift, A=Alt/Option, G=GUI/Cmd. Same letter for left/right
 * since user-visible distinction rarely matters. Updates on every
 * keycode state change so it reacts immediately.
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

static sys_slist_t widgets = SYS_SLIST_STATIC_INIT(&widgets);

struct mod_status_state {
    zmk_mod_flags_t mods;
};

static struct mod_status_state get_state(const zmk_event_t *eh) {
    return (struct mod_status_state){.mods = zmk_hid_get_explicit_mods()};
}

static void set_mod_text(lv_obj_t *label, struct mod_status_state state) {
    // Each slot is 2 chars ("C ", "S ", etc.) so length is known.
    // Bits per HID spec:
    //   0x01 = LCTL   0x10 = RCTL
    //   0x02 = LSFT   0x20 = RSFT
    //   0x04 = LALT   0x40 = RALT
    //   0x08 = LGUI   0x80 = RGUI
    uint8_t m = state.mods;
    bool ctrl  = (m & 0x01) || (m & 0x10);
    bool shift = (m & 0x02) || (m & 0x20);
    bool alt   = (m & 0x04) || (m & 0x40);
    bool gui   = (m & 0x08) || (m & 0x80);

    char text[10];
    snprintf(text, sizeof(text), "%c %c %c %c",
             ctrl  ? 'C' : ' ',
             shift ? 'S' : ' ',
             alt   ? 'A' : ' ',
             gui   ? 'G' : ' ');
    lv_label_set_text(label, text);
}

static void mod_status_update_cb(struct mod_status_state state) {
    struct zmk_widget_mod_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_mod_text(widget->obj, state); }
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_mod_status, struct mod_status_state, mod_status_update_cb,
                            get_state)
ZMK_SUBSCRIPTION(widget_mod_status, zmk_keycode_state_changed);

int zmk_widget_mod_status_init(struct zmk_widget_mod_status *widget, lv_obj_t *parent) {
    widget->obj = lv_label_create(parent);
    if (widget->obj != NULL) {
        lv_obj_set_style_text_font(widget->obj, &lv_font_montserrat_16, LV_PART_MAIN);
        lv_label_set_text(widget->obj, "       ");
    }

    sys_slist_append(&widgets, &widget->node);
    widget_mod_status_init();
    return 0;
}

lv_obj_t *zmk_widget_mod_status_obj(struct zmk_widget_mod_status *widget) {
    return widget->obj;
}
