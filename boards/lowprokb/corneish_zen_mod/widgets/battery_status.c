/*
 *
 * Copyright (c) 2021 Darryl deHaan
 * SPDX-License-Identifier: MIT
 *
 */

#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include <zmk/display.h>
#include <zmk/battery.h>
#include "battery_status.h"
#include <zmk/usb.h>
#include <zmk/events/usb_conn_state_changed.h>
#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>

static sys_slist_t widgets = SYS_SLIST_STATIC_INIT(&widgets);

struct battery_status_state {
    uint8_t level;
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
    bool usb_present;
#endif
};

LV_IMG_DECLARE(batt_100);
LV_IMG_DECLARE(batt_100_chg);
LV_IMG_DECLARE(batt_75);
LV_IMG_DECLARE(batt_75_chg);
LV_IMG_DECLARE(batt_50);
LV_IMG_DECLARE(batt_50_chg);
LV_IMG_DECLARE(batt_25);
LV_IMG_DECLARE(batt_25_chg);
LV_IMG_DECLARE(batt_5);
LV_IMG_DECLARE(batt_5_chg);
LV_IMG_DECLARE(batt_0);
LV_IMG_DECLARE(batt_0_chg);

static void set_battery_symbol(lv_obj_t *icon, lv_obj_t *label,
                               struct battery_status_state state) {
    uint8_t level = state.level;

#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
    bool usb = state.usb_present;
#else
    bool usb = false;
#endif

    if (level > 95) {
        lv_image_set_src(icon, usb ? &batt_100_chg : &batt_100);
    } else if (level > 74) {
        lv_image_set_src(icon, usb ? &batt_75_chg : &batt_75);
    } else if (level > 49) {
        lv_image_set_src(icon, usb ? &batt_50_chg : &batt_50);
    } else if (level > 24) {
        lv_image_set_src(icon, usb ? &batt_25_chg : &batt_25);
    } else if (level > 5) {
        lv_image_set_src(icon, usb ? &batt_5_chg : &batt_5);
    } else {
        lv_image_set_src(icon, usb ? &batt_0_chg : &batt_0);
    }

    if (label != NULL) {
        char buf[6];
        snprintf(buf, sizeof(buf), "%d%%", level);
        lv_label_set_text(label, buf);
    }
}

void battery_status_update_cb(struct battery_status_state state) {
    struct zmk_widget_battery_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) {
        set_battery_symbol(widget->obj, widget->label, state);
    }
}

static struct battery_status_state battery_status_get_state(const zmk_event_t *eh) {
    const struct zmk_battery_state_changed *ev = as_zmk_battery_state_changed(eh);

    return (struct battery_status_state){
        .level = (ev != NULL) ? ev->state_of_charge : zmk_battery_state_of_charge(),
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
        .usb_present = zmk_usb_is_powered(),
#endif /* IS_ENABLED(CONFIG_USB_DEVICE_STACK) */
    };
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_battery_status, struct battery_status_state,
                            battery_status_update_cb, battery_status_get_state)

ZMK_SUBSCRIPTION(widget_battery_status, zmk_battery_state_changed);
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
ZMK_SUBSCRIPTION(widget_battery_status, zmk_usb_conn_state_changed);
#endif /* IS_ENABLED(CONFIG_USB_DEVICE_STACK) */

int zmk_widget_battery_status_init(struct zmk_widget_battery_status *widget, lv_obj_t *parent) {
    // obj is the battery level icon (unchanged from stock).
    widget->obj = lv_image_create(parent);

    // label is a sibling — positioned by the status screen. Uses the small
    // 16pt font since the display is only 80px wide. If LVGL runs out of
    // memory creating it, leave widget->label NULL and guard updates below
    // so we crash-loop-free (just no percentage shown).
    widget->label = lv_label_create(parent);
    if (widget->label != NULL) {
        lv_obj_set_style_text_font(widget->label, &lv_font_montserrat_16, LV_PART_MAIN);
        lv_label_set_text(widget->label, "");
    } else {
        LOG_WRN("battery_status: could not allocate percentage label (OOM)");
    }

    sys_slist_append(&widgets, &widget->node);
    widget_battery_status_init();

    return 0;
}

lv_obj_t *zmk_widget_battery_status_obj(struct zmk_widget_battery_status *widget) {
    return widget->obj;
}

lv_obj_t *zmk_widget_battery_status_label(struct zmk_widget_battery_status *widget) {
    return widget->label;
}
