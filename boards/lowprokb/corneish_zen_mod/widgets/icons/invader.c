/*
 * 16x16 classic space invader — pixel art for the Corne-ish Zen Mod
 * right-half status screen. 1-bit LVGL image.
 *
 * Bitmap, X = on pixel:
 *   ................
 *   ................
 *   ................
 *   ....X......X....
 *   .....X....X.....
 *   ....XXXXXXXX....
 *   ...XX.XXXX.XX...
 *   ..XXXXXXXXXXXX..
 *   ..X.XXXXXXXX.X..
 *   ..X.X......X.X..
 *   .....XX..XX.....
 *   ................
 *   ................
 *   ................
 *   ................
 *   ................
 */

#include <lvgl.h>

#ifndef LV_ATTRIBUTE_MEM_ALIGN
#define LV_ATTRIBUTE_MEM_ALIGN
#endif

#ifndef LV_ATTRIBUTE_IMG_INVADER
#define LV_ATTRIBUTE_IMG_INVADER
#endif

const LV_ATTRIBUTE_MEM_ALIGN LV_ATTRIBUTE_LARGE_CONST LV_ATTRIBUTE_IMG_INVADER uint8_t
    invader_map[] = {
        0xff, 0xff, 0xff, 0xff, /* Color of index 0 (off, white) */
        0x00, 0x00, 0x00, 0xff, /* Color of index 1 (on, black)  */

        /* Row 0  */ 0x00, 0x00,
        /* Row 1  */ 0x00, 0x00,
        /* Row 2  */ 0x00, 0x00,
        /* Row 3  */ 0x08, 0x10, /* ....X......X....  */
        /* Row 4  */ 0x04, 0x20, /* .....X....X.....  */
        /* Row 5  */ 0x0F, 0xF0, /* ....XXXXXXXX....  */
        /* Row 6  */ 0x1B, 0xD8, /* ...XX.XXXX.XX...  */
        /* Row 7  */ 0x3F, 0xFC, /* ..XXXXXXXXXXXX..  */
        /* Row 8  */ 0x2F, 0xF4, /* ..X.XXXXXXXX.X..  */
        /* Row 9  */ 0x28, 0x14, /* ..X.X......X.X..  */
        /* Row 10 */ 0x06, 0x60, /* .....XX..XX.....  (legs) */
        /* Row 11 */ 0x00, 0x00,
        /* Row 12 */ 0x00, 0x00,
        /* Row 13 */ 0x00, 0x00,
        /* Row 14 */ 0x00, 0x00,
        /* Row 15 */ 0x00, 0x00,
};

const lv_image_dsc_t invader = {
    .header =
        {
            .magic = LV_IMAGE_HEADER_MAGIC,
            .cf = LV_COLOR_FORMAT_I1,
            .w = 16,
            .h = 16,
            .stride = 2,
        },
    .data_size = sizeof(invader_map),
    .data = invader_map,
};
