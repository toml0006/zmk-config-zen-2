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
//   y=48..62  modifier indicators ("C S A G")            — row 2a
//   y=62..78  WPM ("NN wpm")                             — row 2b
//   y=82..125 layer heading + layer name                 — row 3
//
// RIGHT (peripheral):
//   y=2..28   battery icon (left) + check/X (right)      — row 1
//   y=30..44  battery percentage
//   y=55..120 16×16 space invader (scaled 3x)            — row 2+3
//
// NOTE: WPM lives on the LEFT half because ZMK's WPM subsystem tracks
// keycode_state_changed events, which only fire on the central. The
// peripheral can't compute or proxy WPM without custom infrastructure.

lv_obj_t *zmk_display_status_screen() {

    lv_obj_t *screen;
    screen = lv_obj_create(NULL);

    // ---- Row 1: battery icon (left) + connection icon (right) ----
    // Icons are shrunk to ~60% of their native 40-54px size so two fit
    // in the 80px-wide display with breathing room.
    const int32_t ICON_SCALE = 160;  // 256 = 1x, 128 = 0.5x, 160 ≈ 0.63x

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_BATTERY_STATUS)
    zmk_widget_battery_status_init(&battery_status_widget, screen);
    lv_obj_t *batt_icon = zmk_widget_battery_status_obj(&battery_status_widget);
    lv_image_set_scale(batt_icon, ICON_SCALE);
    lv_obj_align(batt_icon, LV_ALIGN_TOP_LEFT, 4, 2);

    // Hide the percentage label — user wants just the icon, no text.
    lv_obj_t *batt_label = zmk_widget_battery_status_label(&battery_status_widget);
    if (batt_label != NULL) {
        lv_obj_add_flag(batt_label, LV_OBJ_FLAG_HIDDEN);
    }
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_OUTPUT_STATUS)
    zmk_widget_output_status_init(&output_status_widget, screen);
    lv_obj_t *out_icon = zmk_widget_output_status_obj(&output_status_widget);
    lv_image_set_scale(out_icon, ICON_SCALE);
    lv_obj_align(out_icon, LV_ALIGN_TOP_RIGHT, -4, 2);
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_PERIPHERAL_STATUS)
    zmk_widget_peripheral_status_init(&peripheral_status_widget, screen);
    lv_obj_t *per_icon = zmk_widget_peripheral_status_obj(&peripheral_status_widget);
    lv_image_set_scale(per_icon, ICON_SCALE);
    lv_obj_align(per_icon, LV_ALIGN_TOP_RIGHT, -4, 2);
#endif

    // ---- Row 2 (left half): WPM ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_MOD_STATUS)
    zmk_widget_mod_status_init(&mod_status_widget, screen);
    lv_obj_align(zmk_widget_mod_status_obj(&mod_status_widget), LV_ALIGN_TOP_MID, 0, 36);
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
    // Space invader pixel art on the right half.
    lv_obj_t *invader_icon = lv_image_create(screen);
    lv_image_set_src(invader_icon, &invader);
    // Scale the 16x16 to ~48x48 so it's visible.
    lv_image_set_scale(invader_icon, 768);  // 256 = 1x; 768 = 3x
    lv_obj_align(invader_icon, LV_ALIGN_BOTTOM_MID, 0, -20);
#endif

    return screen;
}
