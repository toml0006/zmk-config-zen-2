/*******************************************************************************
 * Size: 26 px
 * Bpp: 1
 * Opts: --font apple_symbols.ttf -r 0x2303,0x21E7,0x2325,0x2318 --size 26 --bpp 1 --format lvgl --no-compress --lv-include lvgl.h --lv-font-name mac_mods_26 -o mac_mods_26.c
 ******************************************************************************/

#ifdef LV_LVGL_H_INCLUDE_SIMPLE
#include "lvgl.h"
#else
#include "lvgl.h"
#endif

#ifndef MAC_MODS_26
#define MAC_MODS_26 1
#endif

#if MAC_MODS_26

/*-----------------
 *    BITMAPS
 *----------------*/

/*Store the image of the glyphs*/
static LV_ATTRIBUTE_LARGE_CONST const uint8_t glyph_bitmap[] = {
    /* U+21E7 "⇧" */
    0xe, 0x2, 0x21, 0x82, 0x38, 0xe1, 0x10, 0x22,
    0x4, 0x40, 0x88, 0x11, 0x2, 0x20, 0x44, 0x8,
    0x81, 0x10, 0x3e, 0x0,

    /* U+2303 "⌃" */
    0x0, 0x3, 0x0, 0xc0, 0x78, 0x12, 0xc, 0xc2,
    0x11, 0x86, 0x40, 0xb0, 0x30,

    /* U+2318 "⌘" */
    0x78, 0x3d, 0x98, 0xce, 0x11, 0xe, 0x22, 0x37,
    0xff, 0xc0, 0x88, 0x1, 0x10, 0x2, 0x20, 0x4,
    0x40, 0xff, 0xfb, 0x11, 0x1c, 0x22, 0x1c, 0xc6,
    0x6f, 0x7, 0x80,

    /* U+2325 "⌥" */
    0xf0, 0x38, 0x40, 0x1, 0x0, 0x4, 0x0, 0x10,
    0x0, 0x40, 0x1, 0xe0
};


/*---------------------
 *  GLYPH DESCRIPTION
 *--------------------*/

static const lv_font_fmt_txt_glyph_dsc_t glyph_dsc[] = {
    {.bitmap_index = 0, .adv_w = 0, .box_w = 0, .box_h = 0, .ofs_x = 0, .ofs_y = 0} /* id = 0 reserved */,
    {.bitmap_index = 0, .adv_w = 204, .box_w = 11, .box_h = 14, .ofs_x = 1, .ofs_y = -2},
    {.bitmap_index = 20, .adv_w = 197, .box_w = 10, .box_h = 10, .ofs_x = 1, .ofs_y = 4},
    {.bitmap_index = 33, .adv_w = 293, .box_w = 15, .box_h = 14, .ofs_x = 2, .ofs_y = 0},
    {.bitmap_index = 60, .adv_w = 261, .box_w = 13, .box_h = 7, .ofs_x = 2, .ofs_y = 1}
};

/*---------------------
 *  CHARACTER MAPPING
 *--------------------*/

static const uint16_t unicode_list_0[] = {
    0x0, 0x11c, 0x131, 0x13e
};

/*Collect the unicode lists and glyph_id offsets*/
static const lv_font_fmt_txt_cmap_t cmaps[] =
{
    {
        .range_start = 8679, .range_length = 319, .glyph_id_start = 1,
        .unicode_list = unicode_list_0, .glyph_id_ofs_list = NULL, .list_length = 4, .type = LV_FONT_FMT_TXT_CMAP_SPARSE_TINY
    }
};



/*--------------------
 *  ALL CUSTOM DATA
 *--------------------*/

#if LVGL_VERSION_MAJOR == 8
/*Store all the custom data of the font*/
static  lv_font_fmt_txt_glyph_cache_t cache;
#endif

#if LVGL_VERSION_MAJOR >= 8
static const lv_font_fmt_txt_dsc_t font_dsc = {
#else
static lv_font_fmt_txt_dsc_t font_dsc = {
#endif
    .glyph_bitmap = glyph_bitmap,
    .glyph_dsc = glyph_dsc,
    .cmaps = cmaps,
    .kern_dsc = NULL,
    .kern_scale = 0,
    .cmap_num = 1,
    .bpp = 1,
    .kern_classes = 0,
    .bitmap_format = 0,
#if LVGL_VERSION_MAJOR == 8
    .cache = &cache
#endif
};



/*-----------------
 *  PUBLIC FONT
 *----------------*/

/*Initialize a public general font descriptor*/
#if LVGL_VERSION_MAJOR >= 8
const lv_font_t mac_mods_26 = {
#else
lv_font_t mac_mods_26 = {
#endif
    .get_glyph_dsc = lv_font_get_glyph_dsc_fmt_txt,    /*Function pointer to get glyph's data*/
    .get_glyph_bitmap = lv_font_get_bitmap_fmt_txt,    /*Function pointer to get glyph's bitmap*/
    .line_height = 16,          /*The maximum line height required by the font*/
    .base_line = 2,             /*Baseline measured from the bottom of the line*/
#if !(LVGL_VERSION_MAJOR == 6 && LVGL_VERSION_MINOR == 0)
    .subpx = LV_FONT_SUBPX_NONE,
#endif
#if LV_VERSION_CHECK(7, 4, 0) || LVGL_VERSION_MAJOR >= 8
    .underline_position = -2,
    .underline_thickness = 1,
#endif
    .dsc = &font_dsc,          /*The custom font data. Will be accessed by `get_glyph_bitmap/dsc` */
#if LV_VERSION_CHECK(8, 2, 0) || LVGL_VERSION_MAJOR >= 9
    .fallback = NULL,
#endif
    .user_data = NULL,
};



#endif /*#if MAC_MODS_26*/

