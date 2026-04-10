/*
 * Copyright (c) 2026 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 *
 * Modifier state indicator using custom 16x16 pixel-art icons for the
 * Mac modifier keys: ⌃ Ctrl, ⇧ Shift, ⌥ Opt, ⌘ Cmd. Each icon has its
 * own lv_image object; only the ones corresponding to currently-held
 * modifiers are shown (the others are hidden via LV_OBJ_FLAG_HIDDEN).
 *
 * The widget caches the last mods bitmask and short-circuits the
 * update callback when nothing has changed, so non-modifier keypresses
 * don't cause e-paper refreshes.
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

LV_IMG_DECLARE(mod_ctrl);
LV_IMG_DECLARE(mod_shift);
LV_IMG_DECLARE(mod_opt);
LV_IMG_DECLARE(mod_cmd);

static sys_slist_t widgets = SYS_SLIST_STATIC_INIT(&widgets);

struct mod_status_state {
    zmk_mod_flags_t mods;
};

static struct mod_status_state get_state(const zmk_event_t *eh) {
    return (struct mod_status_state){.mods = zmk_hid_get_explicit_mods()};
}

static void show(lv_obj_t *icon, bool visible) {
    if (icon == NULL) return;
    if (visible) {
        lv_obj_clear_flag(icon, LV_OBJ_FLAG_HIDDEN);
    } else {
        lv_obj_add_flag(icon, LV_OBJ_FLAG_HIDDEN);
    }
}

static void set_mod_icons(struct zmk_widget_mod_status *widget,
                          struct mod_status_state state) {
    uint8_t m = state.mods;
    show(widget->ctrl_icon,  (m & 0x01) || (m & 0x10));
    show(widget->shift_icon, (m & 0x02) || (m & 0x20));
    show(widget->opt_icon,   (m & 0x04) || (m & 0x40));
    show(widget->cmd_icon,   (m & 0x08) || (m & 0x80));
}

// Dedup last-seen state so redundant events don't trigger refreshes.
static uint8_t last_mods = 0xFF;  // 0xFF == uninitialized sentinel

static void mod_status_update_cb(struct mod_status_state state) {
    if (state.mods == last_mods) {
        return;
    }
    last_mods = state.mods;

    struct zmk_widget_mod_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_mod_icons(widget, state); }
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_mod_status, struct mod_status_state, mod_status_update_cb,
                            get_state)
ZMK_SUBSCRIPTION(widget_mod_status, zmk_keycode_state_changed);

int zmk_widget_mod_status_init(struct zmk_widget_mod_status *widget, lv_obj_t *parent) {
    // Create the 4 icons as siblings of each other on the parent. They'll
    // be positioned individually by the status screen via the helper
    // accessors below (no explicit container — each icon is just a child
    // of the main screen).
    //
    // widget->obj is set to the Ctrl icon so the existing accessor
    // zmk_widget_mod_status_obj() returns something, but callers should
    // position each of the four icons explicitly.
    widget->ctrl_icon = lv_image_create(parent);
    lv_image_set_src(widget->ctrl_icon, &mod_ctrl);
    lv_obj_add_flag(widget->ctrl_icon, LV_OBJ_FLAG_HIDDEN);

    widget->shift_icon = lv_image_create(parent);
    lv_image_set_src(widget->shift_icon, &mod_shift);
    lv_obj_add_flag(widget->shift_icon, LV_OBJ_FLAG_HIDDEN);

    widget->opt_icon = lv_image_create(parent);
    lv_image_set_src(widget->opt_icon, &mod_opt);
    lv_obj_add_flag(widget->opt_icon, LV_OBJ_FLAG_HIDDEN);

    widget->cmd_icon = lv_image_create(parent);
    lv_image_set_src(widget->cmd_icon, &mod_cmd);
    lv_obj_add_flag(widget->cmd_icon, LV_OBJ_FLAG_HIDDEN);

    widget->obj = widget->ctrl_icon;  // placeholder for legacy accessor

    sys_slist_append(&widgets, &widget->node);
    widget_mod_status_init();
    return 0;
}

lv_obj_t *zmk_widget_mod_status_obj(struct zmk_widget_mod_status *widget) {
    return widget->obj;
}
