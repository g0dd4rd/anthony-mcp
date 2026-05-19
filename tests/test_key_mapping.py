from anthony_mcp.utils import friendly_to_clutter_name, friendly_to_keyval, translate_combo


def test_ctrl_maps_to_control_l():
    assert friendly_to_clutter_name("Ctrl") == "Control_L"


def test_control_maps_to_control_l():
    assert friendly_to_clutter_name("Control") == "Control_L"


def test_shift_maps_to_shift_l():
    assert friendly_to_clutter_name("Shift") == "Shift_L"


def test_alt_maps_to_alt_l():
    assert friendly_to_clutter_name("Alt") == "Alt_L"


def test_super_maps_to_super_l():
    assert friendly_to_clutter_name("Super") == "Super_L"


def test_win_maps_to_super_l():
    assert friendly_to_clutter_name("Win") == "Super_L"


def test_meta_maps_to_super_l():
    assert friendly_to_clutter_name("Meta") == "Super_L"


def test_enter_maps_to_return():
    assert friendly_to_clutter_name("Enter") == "Return"


def test_return_maps_to_return():
    assert friendly_to_clutter_name("Return") == "Return"


def test_esc_maps_to_escape():
    assert friendly_to_clutter_name("Esc") == "Escape"


def test_del_maps_to_delete():
    assert friendly_to_clutter_name("Del") == "Delete"


def test_space_maps_to_space():
    assert friendly_to_clutter_name("Space") == "space"


def test_f_keys():
    for i in range(1, 13):
        assert friendly_to_clutter_name(f"F{i}") == f"F{i}"


def test_arrow_keys():
    assert friendly_to_clutter_name("Up") == "Up"
    assert friendly_to_clutter_name("Down") == "Down"
    assert friendly_to_clutter_name("Left") == "Left"
    assert friendly_to_clutter_name("Right") == "Right"


def test_explicit_right_modifier():
    assert friendly_to_clutter_name("Control_R") == "Control_R"


def test_single_letter():
    assert friendly_to_clutter_name("a") == "a"
    assert friendly_to_clutter_name("z") == "z"


def test_combo_translation():
    assert translate_combo("Ctrl+Alt+t") == "Control_L+Alt_L+t"
    assert translate_combo("Shift+F5") == "Shift_L+F5"
    assert translate_combo("Super+l") == "Super_L+l"


def test_keyval_known_keys():
    assert friendly_to_keyval("Return") == 65293
    assert friendly_to_keyval("Escape") == 65307
    assert friendly_to_keyval("Tab") == 65289
    assert friendly_to_keyval("BackSpace") == 65288
    assert friendly_to_keyval("Space") == 32


def test_keyval_ctrl():
    assert friendly_to_keyval("Ctrl") == 65507


def test_keyval_single_char():
    assert friendly_to_keyval("a") == ord("a")
    assert friendly_to_keyval("Z") == ord("Z")
