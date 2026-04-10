/*
 *
 * Copyright (c) 2021 Darryl deHaan
 * Copyright (c) 2026 Jackson Tomlinson (layout rewrite)
 * SPDX-License-Identifier: MIT
 */

#include "widgets/layer_status.h"
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_BATTERY_TEXT)
#include "widgets/battery_text.h"
#endif
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_OUTPUT_TEXT)
#include "widgets/output_text.h"
#endif
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_PERIPHERAL_TEXT)
#include "widgets/peripheral_text.h"
#endif
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_WPM_STATUS)
#include "widgets/wpm_status.h"
#endif
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_DEVICE_NAME)
#include "widgets/device_name.h"
#endif
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_MOD_STATUS)
#include "widgets/mod_status.h"
#endif
#include "custom_status_screen.h"

#include <zephyr/logging/log.h>
LOG_MODULE_DECLARE(zmk, CONFIG_ZMK_LOG_LEVEL);

LV_IMG_DECLARE(layers2);
LV_IMG_DECLARE(invader);

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_BATTERY_TEXT)
static struct zmk_widget_battery_text battery_text_widget;
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

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_DEVICE_NAME)
static struct zmk_widget_device_name device_name_widget;
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_MOD_STATUS)
static struct zmk_widget_mod_status mod_status_widget;
#endif

// Display is 80 × 128 (IL0323). Layout:
//
// LEFT half (central):
//   y ≈ 4     [battery symbol]   [connection symbol + BT#]   (row 1)
//   y ≈ 24    device name                                    (row 2)
//   y ≈ 44    WPM ("NN wpm")                                 (row 3)
//   y ≈ 70+   layer heading + layer name                     (row 4)
//
// RIGHT half (peripheral):
//   y ≈ 4     [battery symbol]   [OK / X]                    (row 1)
//   y ≈ 30    (empty — modifier indicators would go here but
//             HID state is central-only and not proxied)
//   y ≈ 60+   space invader pixel art
//
// All row-1 elements use LV_SYMBOL_* glyphs from Montserrat 16, which
// renders them at a consistent 16px tall so battery and connection
// icons are automatically vertically aligned on their baseline.

lv_obj_t *zmk_display_status_screen() {

    lv_obj_t *screen;
    screen = lv_obj_create(NULL);

    // ---- Row 1: battery symbol (left) + connection symbol (right) ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_BATTERY_TEXT)
    zmk_widget_battery_text_init(&battery_text_widget, screen);
    lv_obj_align(zmk_widget_battery_text_obj(&battery_text_widget), LV_ALIGN_TOP_LEFT, 6, 4);
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_OUTPUT_TEXT)
    zmk_widget_output_text_init(&output_text_widget, screen);
    lv_obj_align(zmk_widget_output_text_obj(&output_text_widget), LV_ALIGN_TOP_RIGHT, -6, 4);
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_PERIPHERAL_TEXT)
    zmk_widget_peripheral_text_init(&peripheral_text_widget, screen);
    lv_obj_align(zmk_widget_peripheral_text_obj(&peripheral_text_widget), LV_ALIGN_TOP_RIGHT, -6,
                 4);
#endif

    // ---- Row 2 (left): device name ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_DEVICE_NAME)
    zmk_widget_device_name_init(&device_name_widget, screen);
    lv_obj_align(zmk_widget_device_name_obj(&device_name_widget), LV_ALIGN_TOP_MID, 0, 26);
#endif

    // ---- Row 3 (left): WPM ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_WPM_STATUS)
    zmk_widget_wpm_status_init(&wpm_status_widget, screen);
    lv_obj_align(zmk_widget_wpm_status_obj(&wpm_status_widget), LV_ALIGN_TOP_MID, 0, 44);
#endif

    // ---- Row 4 (left): modifier indicators ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_MOD_STATUS)
    zmk_widget_mod_status_init(&mod_status_widget, screen);
    lv_obj_align(zmk_widget_mod_status_obj(&mod_status_widget), LV_ALIGN_TOP_MID, 0, 62);
#endif

    // ---- Row 5 (left): layer name (no heading image to save space) ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_LAYER_STATUS)
    zmk_widget_layer_status_init(&layer_status_widget, screen);
    lv_obj_set_style_text_font(zmk_widget_layer_status_obj(&layer_status_widget),
                               &lv_font_montserrat_16, LV_PART_MAIN);
    lv_obj_align(zmk_widget_layer_status_obj(&layer_status_widget), LV_ALIGN_BOTTOM_MID, 0, -5);
#endif

#if !IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    lv_obj_t *invader_icon = lv_image_create(screen);
    lv_image_set_src(invader_icon, &invader);
    lv_obj_align(invader_icon, LV_ALIGN_BOTTOM_MID, 0, -30);
#endif

    return screen;
}
