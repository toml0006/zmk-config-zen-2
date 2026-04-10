/*
 *
 * Copyright (c) 2021 Darryl deHaan
 * SPDX-License-Identifier: MIT
 *
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/sensor.h>

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

// Local approximation that matches ZMK's lithium_ion_mv_to_pct() in
// battery_common.c — we inline it because we call the sensor directly
// instead of going through the (broken) zmk_battery_update() loop.
static uint8_t local_lithium_mv_to_pct(int bat_mv) {
    if (bat_mv >= 4200) return 100;
    if (bat_mv <= 3450) return 0;
    return (uint8_t)(bat_mv * 2 / 15 - 459);
}

// Read the chosen battery sensor directly and return a percentage.
// Returns -1 if the sensor is unavailable.
static int read_battery_level_direct(void) {
#if DT_HAS_CHOSEN(zmk_battery)
    const struct device *batt = DEVICE_DT_GET(DT_CHOSEN(zmk_battery));
    if (!device_is_ready(batt)) {
        return -1;
    }
    if (sensor_sample_fetch_chan(batt, SENSOR_CHAN_GAUGE_VOLTAGE) != 0) {
        return -1;
    }
    struct sensor_value v;
    if (sensor_channel_get(batt, SENSOR_CHAN_GAUGE_VOLTAGE, &v) != 0) {
        return -1;
    }
    int mv = v.val1 * 1000 + (v.val2 / 1000);
    return local_lithium_mv_to_pct(mv);
#else
    return -1;
#endif
}

static void set_battery_symbol(lv_obj_t *icon, lv_obj_t *label,
                               struct battery_status_state state) {
    // Ignore ZMK's broken last_state_of_charge — compute directly from
    // the sensor. If the sensor is unavailable, fall back to whatever
    // ZMK gave us (probably 0).
    int direct = read_battery_level_direct();
    uint8_t level = (direct >= 0) ? (uint8_t)direct : state.level;

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
        // TEMP: query both SOC and VOLTAGE channels to see what the driver
        // actually has stored. SENSOR_CHAN_ALL fetch populates both.
        // Shows "soc:A.B" where A is raw val1 and B is raw val2 in mV units.
        char buf[20];
#if DT_HAS_CHOSEN(zmk_battery)
        const struct device *batt = DEVICE_DT_GET(DT_CHOSEN(zmk_battery));
        if (!device_is_ready(batt)) {
            snprintf(buf, sizeof(buf), "NODEV");
        } else {
            // Fetch all channels at once
            int rc = sensor_sample_fetch(batt);
            if (rc != 0) {
                snprintf(buf, sizeof(buf), "F%d", rc);
            } else {
                struct sensor_value soc, vlt;
                int rc1 = sensor_channel_get(batt, SENSOR_CHAN_GAUGE_STATE_OF_CHARGE, &soc);
                int rc2 = sensor_channel_get(batt, SENSOR_CHAN_GAUGE_VOLTAGE, &vlt);
                if (rc1 != 0 || rc2 != 0) {
                    snprintf(buf, sizeof(buf), "G%d,%d", rc1, rc2);
                } else {
                    // soc.val1 = percentage directly
                    // vlt.val1 = volts, vlt.val2 = microvolts remainder
                    int mv = vlt.val1 * 1000 + (vlt.val2 / 1000);
                    snprintf(buf, sizeof(buf), "%d:%d", (int)soc.val1, mv);
                }
            }
        }
#else
        snprintf(buf, sizeof(buf), "NOCHO");
#endif
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

// Periodic refresh callback — re-reads the sensor directly, since
// ZMK's zmk_battery_update() poll loop does not reliably run on this
// board under ZMK main (Zephyr 4.1).
static void battery_refresh_timer_cb(lv_timer_t *t) {
    struct zmk_widget_battery_status *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) {
        struct battery_status_state state = {
            .level = 0,  // will be overwritten with direct reading inside set_battery_symbol
#if IS_ENABLED(CONFIG_USB_DEVICE_STACK)
            .usb_present = zmk_usb_is_powered(),
#endif
        };
        set_battery_symbol(widget->obj, widget->label, state);
    }
}

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

    // Force one immediate read so we don't wait for the first event.
    battery_refresh_timer_cb(NULL);

    // Refresh every 30 seconds. We can't rely on ZMK's battery poll,
    // so we own the refresh cadence ourselves.
    lv_timer_create(battery_refresh_timer_cb, 30000, NULL);

    return 0;
}

lv_obj_t *zmk_widget_battery_status_obj(struct zmk_widget_battery_status *widget) {
    return widget->obj;
}

lv_obj_t *zmk_widget_battery_status_label(struct zmk_widget_battery_status *widget) {
    return widget->label;
}
