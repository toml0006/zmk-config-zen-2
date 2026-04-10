/*
 *
 * Copyright (c) 2021 Darryl deHaan
 * SPDX-License-Identifier: MIT
 *
 */

#pragma once

#include <lvgl.h>

#include <zephyr/kernel.h>

struct zmk_widget_battery_status {
    sys_snode_t node;
    lv_obj_t *obj;    // container holding both the icon and the text
    lv_obj_t *icon;   // battery level icon (lv_image)
    lv_obj_t *label;  // percentage text (lv_label, "NN%")
};

int zmk_widget_battery_status_init(struct zmk_widget_battery_status *widget, lv_obj_t *parent);
lv_obj_t *zmk_widget_battery_status_obj(struct zmk_widget_battery_status *widget);
