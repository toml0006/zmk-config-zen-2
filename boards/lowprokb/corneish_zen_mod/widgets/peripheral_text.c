/*
 * Copyright (c) 2026 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 *
 * Text-based peripheral-to-central connection status for the right
 * half. Shows a simple "OK" when the halves are paired, "XX" when
 * disconnected. Uses plain text so we don't need scalable icons.
 */

#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include <zmk/display.h>
#include "peripheral_text.h"
#include <zmk/event_manager.h>
#include <zmk/split/bluetooth/peripheral.h>
#include <zmk/events/split_peripheral_status_changed.h>

static sys_slist_t widgets = SYS_SLIST_STATIC_INIT(&widgets);

struct peripheral_text_state {
    bool connected;
};

static struct peripheral_text_state get_state(const zmk_event_t *_eh) {
    return (struct peripheral_text_state){.connected = zmk_split_bt_peripheral_is_connected()};
}

static void set_text(lv_obj_t *label, struct peripheral_text_state state) {
    lv_label_set_text(label, state.connected ? "OK" : "XX");
}

static void peripheral_text_update_cb(struct peripheral_text_state state) {
    struct zmk_widget_peripheral_text *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_text(widget->obj, state); }
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_peripheral_text, struct peripheral_text_state,
                            peripheral_text_update_cb, get_state)
ZMK_SUBSCRIPTION(widget_peripheral_text, zmk_split_peripheral_status_changed);

int zmk_widget_peripheral_text_init(struct zmk_widget_peripheral_text *widget, lv_obj_t *parent) {
    widget->obj = lv_label_create(parent);
    if (widget->obj != NULL) {
        lv_obj_set_style_text_font(widget->obj, &lv_font_montserrat_16, LV_PART_MAIN);
        lv_label_set_text(widget->obj, "XX");
    }

    sys_slist_append(&widgets, &widget->node);
    widget_peripheral_text_init();
    return 0;
}

lv_obj_t *zmk_widget_peripheral_text_obj(struct zmk_widget_peripheral_text *widget) {
    return widget->obj;
}
