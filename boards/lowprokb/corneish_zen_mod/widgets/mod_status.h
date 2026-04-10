/*
 * Copyright (c) 2026 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include <lvgl.h>
#include <zephyr/kernel.h>

struct zmk_widget_mod_status {
    sys_snode_t node;
    lv_obj_t *obj;          // container (for positioning in status screen)
    lv_obj_t *ctrl_icon;    // individual icon images, shown/hidden per state
    lv_obj_t *shift_icon;
    lv_obj_t *opt_icon;
    lv_obj_t *cmd_icon;
};

int zmk_widget_mod_status_init(struct zmk_widget_mod_status *widget, lv_obj_t *parent);
lv_obj_t *zmk_widget_mod_status_obj(struct zmk_widget_mod_status *widget);
