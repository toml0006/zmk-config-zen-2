/*
 * Option modifier icon — two bars with diagonal (⌥)
 * 16x16, 1-bit LVGL image
 */

#include <lvgl.h>

#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif

#ifndef LV_ATTRIBUTE_IMG_MOD_OPT
#define LV_ATTRIBUTE_IMG_MOD_OPT
#endif

const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_MOD_OPT uint8_t
    mod_opt_map[] = {
        0xff, 0xff, 0xff, 0xff,
        0x00, 0x00, 0x00, 0xff,

        /* row  0 */ 0x00, 0x00,
        /* row  1 */ 0x00, 0x00,
        /* row  2 */ 0x00, 0x00,
        /* row  3 */ 0x38, 0x7E, /* ..XXX....XXXXXX. */
        /* row  4 */ 0x00, 0x40, /* .........X...... */
        /* row  5 */ 0x00, 0x80, /* ........X....... */
        /* row  6 */ 0x01, 0x00, /* .......X........ */
        /* row  7 */ 0x02, 0x00, /* ......X......... */
        /* row  8 */ 0x04, 0x00, /* .....X.......... */
        /* row  9 */ 0x08, 0x00, /* ....X........... */
        /* row 10 */ 0x3C, 0x00, /* ..XXXX.......... */
        /* row 11 */ 0x00, 0x00,
        /* row 12 */ 0x00, 0x00,
        /* row 13 */ 0x00, 0x00,
        /* row 14 */ 0x00, 0x00,
        /* row 15 */ 0x00, 0x00,
};

const lv_image_dsc_t mod_opt = {
    .header = {
        .magic = LV_IMAGE_HEADER_MAGIC,
        .cf = LV_COLOR_FORMAT_I1,
        .w = 16,
        .h = 16,
        .stride = 2,
    },
    .data_size = sizeof(mod_opt_map),
    .data = mod_opt_map,
};
