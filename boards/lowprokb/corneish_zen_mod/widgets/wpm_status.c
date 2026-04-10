/*
 * Copyright (c) 2026 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 *
 * WPM status widget for the Corne-ish Zen right-half status screen.
 * Shows "NN wpm" using Montserrat 16. Updates on zmk_wpm_state_changed
 * events (ZMK fires these periodically as typing accumulates).
 */

#include <stdio.h>
#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include <zmk/display.h>
#include "wpm_status.h"
#include <zmk/event_manager.h>
#include <zmk/events/wpm_state_changed.h>
#include <zmk/wpm.h>

static sys_slist_t widgets = SYS_SLIST_STATIC_INIT(&widgets);

struct wpm_status_state {
    uint8_t wpm;
};

static struct wpm_status_state get_state(const zmk_event_t *eh) {
    return (struct wpm_status_state){.wpm = zmk_wpm_get_state()};
}

static void set_wpm_text(lv_obj_t *label, struct wpm_status_state state) {
    char text[12];
    snprintf(text, sizeof(text), "%d wpm", state.wpm);
    lv_label_set_text(label, text);
}

static void wpm_status_update_cb(struct wpm_status_state state) {
    struct zmk_widget_wpm_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_wpm_text(widget->obj, state); }
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_wpm_status, struct wpm_status_state, wpm_status_update_cb,
                            get_state)
ZMK_SUBSCRIPTION(widget_wpm_status, zmk_wpm_state_changed);

int zmk_widget_wpm_status_init(struct zmk_widget_wpm_status *widget, lv_obj_t *parent) {
    widget->obj = lv_label_create(parent);
    if (widget->obj != NULL) {
        lv_obj_set_style_text_font(widget->obj, &lv_font_montserrat_16, LV_PART_MAIN);
        lv_label_set_text(widget->obj, "0 wpm");
    }

    sys_slist_append(&widgets, &widget->node);
    widget_wpm_status_init();
    return 0;
}

lv_obj_t *zmk_widget_wpm_status_obj(struct zmk_widget_wpm_status *widget) {
    return widget->obj;
}
