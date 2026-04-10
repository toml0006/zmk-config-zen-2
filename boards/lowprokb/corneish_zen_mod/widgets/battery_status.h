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
    lv_obj_t *obj;    // battery level icon (lv_image) — unchanged top-level object
    lv_obj_t *label;  // percentage text (lv_label, "NN%") sibling of obj
};

int zmk_widget_battery_status_init(struct zmk_widget_battery_status *widget, lv_obj_t *parent);
lv_obj_t *zmk_widget_battery_status_obj(struct zmk_widget_battery_status *widget);
lv_obj_t *zmk_widget_battery_status_label(struct zmk_widget_battery_status *widget);
