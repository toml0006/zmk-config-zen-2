/*
 * Command modifier icon — four-corner loop (⌘)
 * 16x16, 1-bit LVGL image
 */

#include <lvgl.h>

#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif

#ifndef LV_ATTRIBUTE_IMG_MOD_CMD
#define LV_ATTRIBUTE_IMG_MOD_CMD
#endif

const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_MOD_CMD uint8_t
    mod_cmd_map[] = {
        0xff, 0xff, 0xff, 0xff,
        0x00, 0x00, 0x00, 0xff,

        /* row  0 */ 0x00, 0x00,
        /* row  1 */ 0x00, 0x00,
        /* row  2 */ 0x60, 0x0C, /* .XX.........XX.. (top-left and top-right corners) */
        /* row  3 */ 0x90, 0x12, /* X..X.......X..X. */
        /* row  4 */ 0x90, 0x12, /* X..X.......X..X. */
        /* row  5 */ 0x60, 0x0C, /* .XX.........XX.. */
        /* row  6 */ 0x20, 0x08, /* ..X.........X... */
        /* row  7 */ 0x3F, 0xF8, /* ..XXXXXXXXXXX... (top edge of center square) */
        /* row  8 */ 0x20, 0x08,
        /* row  9 */ 0x3F, 0xF8, /* bottom edge of center square */
        /* row 10 */ 0x20, 0x08,
        /* row 11 */ 0x60, 0x0C, /* .XX.........XX.. (bottom-left/bottom-right corners) */
        /* row 12 */ 0x90, 0x12,
        /* row 13 */ 0x90, 0x12,
        /* row 14 */ 0x60, 0x0C,
        /* row 15 */ 0x00, 0x00,
};

const lv_image_dsc_t mod_cmd = {
    .header = {
        .magic = LV_IMAGE_HEADER_MAGIC,
        .cf = LV_COLOR_FORMAT_I1,
        .w = 16,
        .h = 16,
        .stride = 2,
    },
    .data_size = sizeof(mod_cmd_map),
    .data = mod_cmd_map,
};
