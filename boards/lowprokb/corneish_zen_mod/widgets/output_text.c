/*
 * Copyright (c) 2026 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 *
 * Text-based output status widget. Uses LV_SYMBOL glyphs from the
 * Montserrat font (no separate image assets):
 *
 *   USB connected              →  LV_SYMBOL_USB
 *   BT profile N connected     →  LV_SYMBOL_BLUETOOTH + "N"
 *   BT profile N advertising   →  LV_SYMBOL_BLUETOOTH + "N" + "?"
 *   BT profile N bonded-but-   →  LV_SYMBOL_BLUETOOTH + "N" + "-"
 *     disconnected
 *   other                      →  "---"
 */

#include <stdio.h>
#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include <zmk/display.h>
#include "output_text.h"
#include <zmk/event_manager.h>
#include <zmk/events/ble_active_profile_changed.h>
#include <zmk/events/endpoint_changed.h>
#include <zmk/usb.h>
#include <zmk/ble.h>
#include <zmk/endpoints.h>

static sys_slist_t widgets = SYS_SLIST_STATIC_INIT(&widgets);

struct output_text_state {
    struct zmk_endpoint_instance selected_endpoint;
    bool active_profile_connected;
    bool active_profile_bonded;
};

static struct output_text_state get_state(const zmk_event_t *_eh) {
    return (struct output_text_state){
        .selected_endpoint = zmk_endpoint_get_selected(),
        .active_profile_connected = zmk_ble_active_profile_is_connected(),
        .active_profile_bonded = !zmk_ble_active_profile_is_open(),
    };
}

static void set_output_text(lv_obj_t *label, struct output_text_state state) {
    char buf[16];
    switch (state.selected_endpoint.transport) {
    case ZMK_TRANSPORT_USB:
        snprintf(buf, sizeof(buf), LV_SYMBOL_USB);
        break;
    case ZMK_TRANSPORT_BLE: {
        int idx = state.selected_endpoint.ble.profile_index + 1;
        if (!state.active_profile_bonded) {
            snprintf(buf, sizeof(buf), LV_SYMBOL_BLUETOOTH "%d?", idx);
        } else if (!state.active_profile_connected) {
            snprintf(buf, sizeof(buf), LV_SYMBOL_BLUETOOTH "%d-", idx);
        } else {
            snprintf(buf, sizeof(buf), LV_SYMBOL_BLUETOOTH "%d", idx);
        }
        break;
    }
    default:
        snprintf(buf, sizeof(buf), "---");
        break;
    }
    lv_label_set_text(label, buf);
}

static void output_text_update_cb(struct output_text_state state) {
    struct zmk_widget_output_text *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_output_text(widget->obj, state); }
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_output_text, struct output_text_state, output_text_update_cb,
                            get_state)
ZMK_SUBSCRIPTION(widget_output_text, zmk_endpoint_changed);
ZMK_SUBSCRIPTION(widget_output_text, zmk_ble_active_profile_changed);

int zmk_widget_output_text_init(struct zmk_widget_output_text *widget, lv_obj_t *parent) {
    widget->obj = lv_label_create(parent);
    if (widget->obj != NULL) {
        lv_obj_set_style_text_font(widget->obj, &lv_font_montserrat_16, LV_PART_MAIN);
        lv_label_set_text(widget->obj, "---");
    }

    sys_slist_append(&widgets, &widget->node);
    widget_output_text_init();
    return 0;
}

lv_obj_t *zmk_widget_output_text_obj(struct zmk_widget_output_text *widget) {
    return widget->obj;
}
