/*
 *
 * Copyright (c) 2021 Darryl deHaan
 * Copyright (c) 2026 Jackson Tomlinson (layout rewrite)
 * SPDX-License-Identifier: MIT
 */

#include "widgets/battery_status.h"
#include "widgets/peripheral_status.h"
#include "widgets/output_status.h"
#include "widgets/layer_status.h"
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_WPM_STATUS)
#include "widgets/wpm_status.h"
#endif
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_MOD_STATUS)
#include "widgets/mod_status.h"
#endif
#include "custom_status_screen.h"

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

LV_IMG_DECLARE(layers2);
LV_IMG_DECLARE(invader);

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_BATTERY_STATUS)
static struct zmk_widget_battery_status battery_status_widget;
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_OUTPUT_STATUS)
static struct zmk_widget_output_status output_status_widget;
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_PERIPHERAL_STATUS)
static struct zmk_widget_peripheral_status peripheral_status_widget;
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_LAYER_STATUS)
static struct zmk_widget_layer_status layer_status_widget;
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_WPM_STATUS)
static struct zmk_widget_wpm_status wpm_status_widget;
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_MOD_STATUS)
static struct zmk_widget_mod_status mod_status_widget;
#endif

// Display is 80 × 128 (IL0323). Layout:
//
// LEFT (central):
//   y=2..28   battery icon (left) + BT/USB icon (right)  — row 1
//   y=30..44  battery percentage (below battery icon), small
//   y=48..66  modifier indicators (C S A G)              — row 2
//   y=70..125 layer heading + layer name                 — row 3
//
// RIGHT (peripheral):
//   y=2..28   battery icon (left) + check/X (right)      — row 1
//   y=30..44  battery percentage
//   y=48..70  WPM ("NN wpm")                             — row 2
//   y=78..118 16×16 space invader                        — row 3

lv_obj_t *zmk_display_status_screen() {

    lv_obj_t *screen;
    screen = lv_obj_create(NULL);

    // ---- Row 1: battery icon (left) + connection icon (right) ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_BATTERY_STATUS)
    zmk_widget_battery_status_init(&battery_status_widget, screen);
    lv_obj_t *batt_icon = zmk_widget_battery_status_obj(&battery_status_widget);
    lv_obj_align(batt_icon, LV_ALIGN_TOP_LEFT, 8, 4);

    lv_obj_t *batt_label = zmk_widget_battery_status_label(&battery_status_widget);
    if (batt_label != NULL) {
        // Percentage text centered under the battery icon
        lv_obj_align(batt_label, LV_ALIGN_TOP_LEFT, 2, 28);
    }
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_OUTPUT_STATUS)
    zmk_widget_output_status_init(&output_status_widget, screen);
    lv_obj_align(zmk_widget_output_status_obj(&output_status_widget), LV_ALIGN_TOP_RIGHT, -8, 4);
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_PERIPHERAL_STATUS)
    zmk_widget_peripheral_status_init(&peripheral_status_widget, screen);
    lv_obj_align(zmk_widget_peripheral_status_obj(&peripheral_status_widget), LV_ALIGN_TOP_RIGHT,
                 -8, 4);
#endif

    // ---- Row 2: modifier indicators (left) or WPM (right) ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_MOD_STATUS)
    zmk_widget_mod_status_init(&mod_status_widget, screen);
    lv_obj_align(zmk_widget_mod_status_obj(&mod_status_widget), LV_ALIGN_TOP_MID, 0, 48);
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_WPM_STATUS)
    zmk_widget_wpm_status_init(&wpm_status_widget, screen);
    lv_obj_align(zmk_widget_wpm_status_obj(&wpm_status_widget), LV_ALIGN_TOP_MID, 0, 48);
#endif

    // ---- Row 3: layer widget (left) or invader pixel art (right) ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_LAYER_STATUS)
    lv_obj_t *LayersHeading;
    LayersHeading = lv_image_create(screen);
    lv_obj_align(LayersHeading, LV_ALIGN_BOTTOM_MID, 0, -30);
    lv_image_set_src(LayersHeading, &layers2);

    zmk_widget_layer_status_init(&layer_status_widget, screen);
    lv_obj_set_style_text_font(zmk_widget_layer_status_obj(&layer_status_widget),
                               &lv_font_montserrat_16, LV_PART_MAIN);
    lv_obj_align(zmk_widget_layer_status_obj(&layer_status_widget), LV_ALIGN_BOTTOM_MID, 0, -5);
#endif

#if !IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    // Space invader pixel art on the right half.
    lv_obj_t *invader_icon = lv_image_create(screen);
    lv_image_set_src(invader_icon, &invader);
    // Scale the 16x16 to ~48x48 so it's visible.
    lv_image_set_scale(invader_icon, 768);  // 256 = 1x; 768 = 3x
    lv_obj_align(invader_icon, LV_ALIGN_BOTTOM_MID, 0, -20);
#endif

    return screen;
}
