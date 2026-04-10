/*
 * Copyright (c) 2026 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 *
 * Device name widget. Shows a short label identifying the current
 * connected host. Since Zephyr/ZMK don't expose the peer's GAP
 * device name easily without a GATT read, for now we just show
 * "Profile N" for BLE or "USB" for wired. User can edit the DEVICE_N
 * constants below to customize per-profile nicknames.
 */

#include <stdio.h>
#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include <zmk/display.h>
#include "device_name.h"
#include <zmk/event_manager.h>
#include <zmk/events/ble_active_profile_changed.h>
#include <zmk/events/endpoint_changed.h>
#include <zmk/ble.h>
#include <zmk/endpoints.h>

static sys_slist_t widgets = SYS_SLIST_STATIC_INIT(&widgets);

// Edit these to taste — shown on row 2 of the left display when the
// corresponding profile is active. Keep them short (≤8 chars) so they
// fit a 80px-wide display in Montserrat 16.
static const char *const DEVICE_NAMES[] = {
    "MacBook",  // Profile 1
    "iPad",     // Profile 2
    "iPhone",   // Profile 3
    "PC",       // Profile 4
    "Other",    // Profile 5
};

struct device_name_state {
    struct zmk_endpoint_instance endpoint;
};

static struct device_name_state get_state(const zmk_event_t *_eh) {
    return (struct device_name_state){.endpoint = zmk_endpoint_get_selected()};
}

static void set_text(lv_obj_t *label, struct device_name_state state) {
    if (state.endpoint.transport == ZMK_TRANSPORT_USB) {
        lv_label_set_text(label, "USB");
    } else {
        int idx = state.endpoint.ble.profile_index;
        if (idx >= 0 && idx < (int)(sizeof(DEVICE_NAMES) / sizeof(DEVICE_NAMES[0]))) {
            lv_label_set_text(label, DEVICE_NAMES[idx]);
        } else {
            char buf[12];
            snprintf(buf, sizeof(buf), "Profile %d", idx + 1);
            lv_label_set_text(label, buf);
        }
    }
}

static void device_name_update_cb(struct device_name_state state) {
    struct zmk_widget_device_name *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_text(widget->obj, state); }
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_device_name, struct device_name_state, device_name_update_cb,
                            get_state)
ZMK_SUBSCRIPTION(widget_device_name, zmk_endpoint_changed);
ZMK_SUBSCRIPTION(widget_device_name, zmk_ble_active_profile_changed);

int zmk_widget_device_name_init(struct zmk_widget_device_name *widget, lv_obj_t *parent) {
    widget->obj = lv_label_create(parent);
    if (widget->obj != NULL) {
        lv_obj_set_style_text_font(widget->obj, &lv_font_montserrat_16, LV_PART_MAIN);
        lv_label_set_text(widget->obj, "");
    }

    sys_slist_append(&widgets, &widget->node);
    widget_device_name_init();
    return 0;
}

lv_obj_t *zmk_widget_device_name_obj(struct zmk_widget_device_name *widget) {
    return widget->obj;
}
