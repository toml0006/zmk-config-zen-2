/*
 * Copyright (c) 2026 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 *
 * Text-based battery widget for the Corne-ish Zen Mod. Renders the
 * battery level as a single character from LVGL's symbol font —
 * LV_SYMBOL_BATTERY_FULL / _3 / _2 / _1 / _EMPTY — instead of using
 * the 40x31 image icons from the stock shield. Reads the sensor
 * directly (bypassing the zmk_battery_state_of_charge cache) so it
 * works even if the BQ274xx isn't ready at SYS_INIT time.
 */

#include <stdio.h>
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/sensor.h>

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

#include <zmk/display.h>
#include <zmk/battery.h>
#include "battery_text.h"
#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>

static sys_slist_t widgets = SYS_SLIST_STATIC_INIT(&widgets);

struct battery_text_state {
    uint8_t level;
};

static int read_level_direct(void) {
#if DT_HAS_CHOSEN(zmk_battery)
    const struct device *batt = DEVICE_DT_GET(DT_CHOSEN(zmk_battery));
    if (!device_is_ready(batt)) {
        return -1;
    }
    if (sensor_sample_fetch(batt) != 0) {
        return -1;
    }
    struct sensor_value v;
    if (sensor_channel_get(batt, SENSOR_CHAN_GAUGE_STATE_OF_CHARGE, &v) != 0) {
        return -1;
    }
    return (int)v.val1;
#else
    return -1;
#endif
}

static const char *level_to_symbol(uint8_t level) {
    if (level >= 88) return LV_SYMBOL_BATTERY_FULL;   // 4 bars
    if (level >= 63) return LV_SYMBOL_BATTERY_3;      // 3 bars
    if (level >= 38) return LV_SYMBOL_BATTERY_2;      // 2 bars
    if (level >= 13) return LV_SYMBOL_BATTERY_1;      // 1 bar
    return LV_SYMBOL_BATTERY_EMPTY;
}

static void set_text(lv_obj_t *label, struct battery_text_state state) {
    lv_label_set_text(label, level_to_symbol(state.level));
}

static struct battery_text_state get_state(const zmk_event_t *eh) {
    int direct = read_level_direct();
    uint8_t level = (direct >= 0) ? (uint8_t)direct : zmk_battery_state_of_charge();
    return (struct battery_text_state){.level = level};
}

static void battery_text_update_cb(struct battery_text_state state) {
    struct zmk_widget_battery_text *widget;
    SYS_SLIST_FOR_EACH_CONTAINER(&widgets, widget, node) { set_text(widget->obj, state); }
}

ZMK_DISPLAY_WIDGET_LISTENER(widget_battery_text, struct battery_text_state, battery_text_update_cb,
                            get_state)
ZMK_SUBSCRIPTION(widget_battery_text, zmk_battery_state_changed);

// Periodic refresh timer — fires every 5 minutes so we re-read even
// if no state_changed event arrives (which is likely given ZMK's poll
// loop may not run on this board).
static void battery_text_refresh_cb(lv_timer_t *t) {
    struct battery_text_state state = get_state(NULL);
    battery_text_update_cb(state);
}

int zmk_widget_battery_text_init(struct zmk_widget_battery_text *widget, lv_obj_t *parent) {
    widget->obj = lv_label_create(parent);
    if (widget->obj != NULL) {
        // Use the bigger 26pt font so the battery glyph is prominent.
        lv_obj_set_style_text_font(widget->obj, &lv_font_montserrat_26, LV_PART_MAIN);
        lv_label_set_text(widget->obj, LV_SYMBOL_BATTERY_EMPTY);
    }

    sys_slist_append(&widgets, &widget->node);
    widget_battery_text_init();

    // Immediate first read (in case the event-based init hasn't fired yet)
    battery_text_refresh_cb(NULL);

    // Refresh every 5 minutes
    lv_timer_create(battery_text_refresh_cb, 300000, NULL);

    return 0;
}

lv_obj_t *zmk_widget_battery_text_obj(struct zmk_widget_battery_text *widget) {
    return widget->obj;
}
