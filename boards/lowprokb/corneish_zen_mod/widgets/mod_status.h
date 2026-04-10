/*
 * Copyright (c) 2026 The ZMK Contributors
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include <lvgl.h>
#include <zephyr/kernel.h>

struct zmk_widget_mod_status {
    sys_snode_t node;
    lv_obj_t *obj;          // "leading" label (Ctrl) — used by legacy getter
    lv_obj_t *ctrl_label;
    lv_obj_t *shift_label;
    lv_obj_t *opt_label;
    lv_obj_t *cmd_label;
};

int zmk_widget_mod_status_init(struct zmk_widget_mod_status *widget, lv_obj_t *parent);
lv_obj_t *zmk_widget_mod_status_obj(struct zmk_widget_mod_status *widget);
