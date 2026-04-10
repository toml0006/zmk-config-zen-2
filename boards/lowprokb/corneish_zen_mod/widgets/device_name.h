/*
 * Copyright (c) 2026 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include <lvgl.h>
#include <zephyr/kernel.h>

struct zmk_widget_device_name {
    sys_snode_t node;
    lv_obj_t *obj;
};

int zmk_widget_device_name_init(struct zmk_widget_device_name *widget, lv_obj_t *parent);
lv_obj_t *zmk_widget_device_name_obj(struct zmk_widget_device_name *widget);
