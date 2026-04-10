/*
 * Control modifier icon — upward chevron (⌃)
 * 16x16, 1-bit LVGL image
 */

#include <lvgl.h>

#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif

#ifndef LV_ATTRIBUTE_IMG_MOD_CTRL
#define LV_ATTRIBUTE_IMG_MOD_CTRL
#endif

const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_MOD_CTRL uint8_t
    mod_ctrl_map[] = {
        0xff, 0xff, 0xff, 0xff, /* off */
        0x00, 0x00, 0x00, 0xff, /* on  */

        /* row  0 */ 0x00, 0x00,
        /* row  1 */ 0x00, 0x00,
        /* row  2 */ 0x00, 0x00,
        /* row  3 */ 0x00, 0x00,
        /* row  4 */ 0x00, 0x00,
        /* row  5 */ 0x01, 0x00, /* .......X........ */
        /* row  6 */ 0x02, 0x80, /* ......X.X....... */
        /* row  7 */ 0x04, 0x40, /* .....X...X...... */
        /* row  8 */ 0x08, 0x20, /* ....X.....X..... */
        /* row  9 */ 0x10, 0x10, /* ...X.......X.... */
        /* row 10 */ 0x20, 0x08, /* ..X.........X... */
        /* row 11 */ 0x40, 0x04, /* .X...........X.. */
        /* row 12 */ 0x00, 0x00,
        /* row 13 */ 0x00, 0x00,
        /* row 14 */ 0x00, 0x00,
        /* row 15 */ 0x00, 0x00,
};

const lv_image_dsc_t mod_ctrl = {
    .header = {
        .magic = LV_IMAGE_HEADER_MAGIC,
        .cf = LV_COLOR_FORMAT_I1,
        .w = 16,
        .h = 16,
        .stride = 2,
    },
    .data_size = sizeof(mod_ctrl_map),
    .data = mod_ctrl_map,
};
