/*
 *
 * Copyright (c) 2021 Darryl deHaan
 * Copyright (c) 2026 Jackson Tomlinson (layout rewrite)
 * SPDX-License-Identifier: MIT
 */

#include "widgets/battery_status.h"
#include "widgets/layer_status.h"
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_OUTPUT_TEXT)
#include "widgets/output_text.h"
#endif
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_PERIPHERAL_TEXT)
#include "widgets/peripheral_text.h"
#endif
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

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_OUTPUT_TEXT)
static struct zmk_widget_output_text output_text_widget;
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_PERIPHERAL_TEXT)
static struct zmk_widget_peripheral_text peripheral_text_widget;
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

// Display is 80 × 128 (IL0323).
//
// LEFT half (central):
//   y=2..33    battery icon (native 40x31), left-aligned
//              text label (USB/BT1-5), right side, vertically centered on icon
//   y=40..58   WPM ("NN wpm"), throttled to once/minute
//   y=~62..125 layer heading + layer name (existing layer widget)
//
// RIGHT half (peripheral):
//   y=2..33    battery icon left, "OK"/"XX" text right
//   y=~60..125 space invader 3x scaled (pixel art)
//
// Notes:
//   * 1-bit indexed LVGL images can't be transformed, so we can't shrink
//     the stock 40x31 icons. Output status and peripheral status were
//     replaced with short text labels to save space.
//   * Modifier indicator is disabled — it fired on every keypress which
//     caused a full e-paper refresh per character. Unusable.
//   * WPM is computed on the central only (ZMK's wpm.c subscribes to
//     keycode_state_changed events which peripherals don't get).

lv_obj_t *zmk_display_status_screen() {

    lv_obj_t *screen;
    screen = lv_obj_create(NULL);

    // ---- Row 1: battery icon (left) + connection text (right) ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_BATTERY_STATUS)
    zmk_widget_battery_status_init(&battery_status_widget, screen);
    lv_obj_align(zmk_widget_battery_status_obj(&battery_status_widget), LV_ALIGN_TOP_LEFT, 0, 2);

    // Hide the percentage label — user wants just the icon, no text.
    lv_obj_t *batt_label = zmk_widget_battery_status_label(&battery_status_widget);
    if (batt_label != NULL) {
        lv_obj_add_flag(batt_label, LV_OBJ_FLAG_HIDDEN);
    }
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_OUTPUT_TEXT)
    zmk_widget_output_text_init(&output_text_widget, screen);
    lv_obj_align(zmk_widget_output_text_obj(&output_text_widget), LV_ALIGN_TOP_RIGHT, -4, 10);
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_PERIPHERAL_TEXT)
    zmk_widget_peripheral_text_init(&peripheral_text_widget, screen);
    lv_obj_align(zmk_widget_peripheral_text_obj(&peripheral_text_widget), LV_ALIGN_TOP_RIGHT, -4,
                 10);
#endif

    // ---- Row 2 (left): modifiers / WPM ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_MOD_STATUS)
    zmk_widget_mod_status_init(&mod_status_widget, screen);
    lv_obj_align(zmk_widget_mod_status_obj(&mod_status_widget), LV_ALIGN_TOP_MID, 0, 38);
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_WPM_STATUS)
    zmk_widget_wpm_status_init(&wpm_status_widget, screen);
    lv_obj_align(zmk_widget_wpm_status_obj(&wpm_status_widget), LV_ALIGN_TOP_MID, 0, 40);
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
    // Space invader pixel art on the right half. 16x16 source, 3x scale.
    // (lv_image_set_scale does work on RGB/argb images; invader is I1 so
    // scale may be ignored. If it doesn't render scaled, revisit later.)
    lv_obj_t *invader_icon = lv_image_create(screen);
    lv_image_set_src(invader_icon, &invader);
    lv_obj_align(invader_icon, LV_ALIGN_BOTTOM_MID, 0, -30);
#endif

    return screen;
}
