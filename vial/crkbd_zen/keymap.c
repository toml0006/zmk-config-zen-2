#include QMK_KEYBOARD_H

enum layers {
    _QWERTY,
    _LOWER,
    _RAISE,
    _FN,
};

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [_QWERTY] = LAYOUT_split_3x6_3(
        KC_TAB,                KC_Q,    KC_W,    KC_E,    KC_R,    KC_T,         KC_Y,    KC_U,    KC_I,    KC_O,    KC_P,    KC_BSPC,
        MT(MOD_LALT, KC_ESC),  KC_A,    KC_S,    KC_D,    KC_F,    KC_G,         KC_H,    KC_J,    KC_K,    KC_L,    KC_SCLN, KC_QUOT,
        KC_LSFT,               KC_Z,    KC_X,    KC_C,    KC_V,    KC_B,         KC_N,    KC_M,    KC_COMM, KC_DOT,  KC_SLSH, KC_RSFT,
                                              KC_LGUI, MO(_LOWER), KC_SPC,   KC_ENT, MO(_RAISE), KC_RCTL
    ),

    [_LOWER] = LAYOUT_split_3x6_3(
        KC_TILD, KC_1,    KC_2,    KC_3,    KC_4,    KC_5,         KC_6,    KC_7,    KC_8,    KC_9,    KC_0,    KC_BSPC,
        KC_TRNS, KC_NO,   KC_NO,   KC_NO,   KC_NO,   KC_NO,        KC_TRNS, KC_HOME, KC_UP,   KC_END,  KC_PGUP, KC_TRNS,
        KC_LSFT, KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS,      KC_TRNS, KC_LEFT, KC_DOWN, KC_RGHT, KC_PGDN, KC_TILD,
                                       KC_LGUI, MO(_LOWER), KC_SPC,   KC_ENT, MO(_RAISE), KC_RCTL
    ),

    [_RAISE] = LAYOUT_split_3x6_3(
        KC_TILD,              KC_EXLM,        KC_AT,          KC_HASH, KC_DLR,  KC_PERC,        KC_CIRC, KC_AMPR, KC_ASTR, KC_LPRN, KC_RPRN, KC_BSPC,
        MT(MOD_LALT, KC_ESC), S(G(KC_LBRC)),  S(G(KC_RBRC)),  KC_TRNS, KC_TRNS, KC_TRNS,        KC_MINS, KC_EQL,  KC_LBRC, KC_RBRC, KC_BSLS, KC_GRV,
        KC_LSFT,              G(KC_GRV),      S(G(KC_GRV)),   KC_TRNS, KC_TRNS, KC_TRNS,        KC_UNDS, KC_PLUS, KC_LCBR, KC_RCBR, KC_PIPE, KC_TILD,
                                                       KC_LGUI, MO(_LOWER), KC_SPC,   KC_ENT, MO(_RAISE), KC_RCTL
    ),

    [_FN] = LAYOUT_split_3x6_3(
        KC_TRNS, KC_F1,   KC_F2,   KC_F3,   KC_F4,   KC_F5,                KC_F6,         KC_F7,   KC_F8,   KC_F9,   KC_F10,  KC_DEL,
        KC_TRNS, KC_F12,  KC_MPRV, KC_MPLY, KC_MNXT, KC_TRNS,              KC_TRNS,       KC_VOLD, KC_VOLU, KC_MUTE, KC_TRNS, KC_TRNS,
        KC_LSFT, KC_TRNS, KC_TRNS, KC_TRNS, KC_TRNS, S(G(KC_4)),           C(S(G(KC_4))), KC_BRID, KC_BRIU, KC_TRNS, KC_TRNS, KC_TRNS,
                                            KC_LGUI, MO(_LOWER), KC_SPC,   KC_ENT, MO(_RAISE), KC_RCTL
    ),
};

layer_state_t layer_state_set_user(layer_state_t state) {
    return update_tri_layer_state(state, _LOWER, _RAISE, _FN);
}
