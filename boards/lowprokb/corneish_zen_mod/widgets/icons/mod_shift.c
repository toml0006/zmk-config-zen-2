/*
 * Shift modifier icon — wide upward arrow with stem (⇧)
 * 16x16, 1-bit LVGL image
 */

#include <lvgl.h>

#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif

#ifndef LV_ATTRIBUTE_IMG_MOD_SHIFT
#define LV_ATTRIBUTE_IMG_MOD_SHIFT
#endif

const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_MOD_SHIFT uint8_t
    mod_shift_map[] = {
        0xff, 0xff, 0xff, 0xff,
        0x00, 0x00, 0x00, 0xff,

        /* row  0 */ 0x00, 0x00,
        /* row  1 */ 0x00, 0x00,
        /* row  2 */ 0x01, 0x00, /* .......X........ */
        /* row  3 */ 0x03, 0x80, /* ......XXX....... */
        /* row  4 */ 0x07, 0xC0, /* .....XXXXX...... */
        /* row  5 */ 0x0F, 0xE0, /* ....XXXXXXX..... */
        /* row  6 */ 0x1F, 0xF0, /* ...XXXXXXXXX.... */
        /* row  7 */ 0x3F, 0xF8, /* ..XXXXXXXXXXX... */
        /* row  8 */ 0x7F, 0xFC, /* .XXXXXXXXXXXXX.. */
        /* row  9 */ 0x03, 0x80, /* ......XXX....... */
        /* row 10 */ 0x03, 0x80,
        /* row 11 */ 0x03, 0x80,
        /* row 12 */ 0x03, 0x80,
        /* row 13 */ 0x03, 0x80,
        /* row 14 */ 0x00, 0x00,
        /* row 15 */ 0x00, 0x00,
};

const lv_image_dsc_t mod_shift = {
    .header = {
        .magic = LV_IMAGE_HEADER_MAGIC,
        .cf = LV_COLOR_FORMAT_I1,
        .w = 16,
        .h = 16,
        .stride = 2,
    },
    .data_size = sizeof(mod_shift_map),
    .data = mod_shift_map,
};
