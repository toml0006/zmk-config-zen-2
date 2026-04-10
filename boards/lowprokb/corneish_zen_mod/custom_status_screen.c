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
LV_IMG_DECLARE(pacman);
LV_IMG_DECLARE(ghost);

// Rotation cycle for the right-half pixel art. One refresh every
// ROTATE_INTERVAL_MS; at 30 min that's ~48 extra partial refreshes per
// day (~0.07 mAh on a 180 mAh battery — negligible).
#define ROTATE_INTERVAL_MS (30 * 60 * 1000)
static const lv_image_dsc_t *const pixel_art_cycle[] = {
    &invader,
    &pacman,
    &ghost,
};
#define PIXEL_ART_COUNT (sizeof(pixel_art_cycle) / sizeof(pixel_art_cycle[0]))

static lv_obj_t *rotating_art_obj = NULL;
static size_t rotating_art_index = 0;

static void rotate_pixel_art_cb(lv_timer_t *t) {
    if (rotating_art_obj == NULL) {
        return;
    }
    rotating_art_index = (rotating_art_index + 1) % PIXEL_ART_COUNT;
    lv_image_set_src(rotating_art_obj, pixel_art_cycle[rotating_art_index]);
}

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

    // Row y-anchors — 128 px display, 4-row layout with mod removed.
    //
    //   y=  4    row 1: battery (M26) + connection (M16)   ≈ 26 tall
    //   y= 44    row 2: device name                         16 tall
    //   y= 68    row 3: WPM                                 16 tall
    //   y=108    row 4: layer name                          16 tall  (bottom-aligned)
    //
    // Gaps: row1→row2 ≈ 14, row2→row3 ≈ 8, row3→row4 ≈ 24 (includes
    // natural space above the bottom-aligned layer).

    // ---- Row 1: battery (26pt, wider/taller) + connection (16pt) ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_BATTERY_TEXT)
    zmk_widget_battery_text_init(&battery_text_widget, screen);
    lv_obj_align(zmk_widget_battery_text_obj(&battery_text_widget), LV_ALIGN_TOP_LEFT, 4, 2);
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_OUTPUT_TEXT)
    zmk_widget_output_text_init(&output_text_widget, screen);
    // Vertically center connection text with the taller battery glyph.
    lv_obj_align(zmk_widget_output_text_obj(&output_text_widget), LV_ALIGN_TOP_RIGHT, -6, 7);
#endif

#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_PERIPHERAL_TEXT)
    zmk_widget_peripheral_text_init(&peripheral_text_widget, screen);
    lv_obj_align(zmk_widget_peripheral_text_obj(&peripheral_text_widget), LV_ALIGN_TOP_RIGHT, -6,
                 7);
#endif

    // ---- Row 2 (left): device name ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_DEVICE_NAME)
    zmk_widget_device_name_init(&device_name_widget, screen);
    lv_obj_align(zmk_widget_device_name_obj(&device_name_widget), LV_ALIGN_TOP_MID, 0, 44);
#endif

    // ---- Row 3 (left): WPM ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_WPM_STATUS)
    zmk_widget_wpm_status_init(&wpm_status_widget, screen);
    lv_obj_align(zmk_widget_wpm_status_obj(&wpm_status_widget), LV_ALIGN_TOP_MID, 0, 68);
#endif

    // ---- Row 4 (left): layer name ----
#if IS_ENABLED(CONFIG_CUSTOM_WIDGET_LAYER_STATUS)
    zmk_widget_layer_status_init(&layer_status_widget, screen);
    lv_obj_set_style_text_font(zmk_widget_layer_status_obj(&layer_status_widget),
                               &lv_font_montserrat_16, LV_PART_MAIN);
    lv_obj_align(zmk_widget_layer_status_obj(&layer_status_widget), LV_ALIGN_BOTTOM_MID, 0, -4);
#endif

#if !IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    // Rotating pixel art in the lower third. Starts on the classic
    // invader and cycles through pacman/ghost every 30 minutes.
    rotating_art_obj = lv_image_create(screen);
    lv_image_set_src(rotating_art_obj, pixel_art_cycle[0]);
    lv_obj_align(rotating_art_obj, LV_ALIGN_BOTTOM_MID, 0, -2);
    lv_timer_create(rotate_pixel_art_cb, ROTATE_INTERVAL_MS, NULL);
#endif

    return screen;
}
