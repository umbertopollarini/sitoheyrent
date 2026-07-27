// ============================================================
// HeyRent! keychain
// Front: plain
// Back: GC397WD + HeyRent!
// Flat bottom for printing, decorated top face.
// ============================================================

$fn = 96;

// Main dimensions
BODY_W       = 66;
BODY_H       = 28;
BODY_T       = 5.0;
BODY_R       = 4.8;

// Double-face recessed panels
PANEL_W      = 53;
PANEL_H      = 19;
PANEL_R      = 3.2;
PANEL_DEPTH  = 0.95;
TEXT_RELIEF  = 0.58;   // stays below the outer surface

// Keyring side
HOLE_D       = 6.2;
RING_OUTER_D = 15.6;
RING_X       = -(BODY_W / 2 + 6.8);
RING_Y       = BODY_H / 2 - 7.6;
ACCENT_D     = 9.2;
ACCENT_X     = RING_X - 2.0;
ACCENT_Y     = RING_Y + 4.2;

// Typography
FONT_MAIN    = "Poppins:style=Bold";
FONT_FALLBACK= "Liberation Sans:style=Bold";

TOP_TEXT     = "HeyRent!";
PLATE_TEXT   = "GC397WD";

module rounded_rect_2d(w, h, r) {
    offset(r = r)
        offset(r = -r)
            square([w, h], center = true);
}

module outer_profile_2d() {
    difference() {
        union() {
            rounded_rect_2d(BODY_W, BODY_H, BODY_R);

            hull() {
                translate([-(BODY_W / 2) + 1.8, BODY_H / 2 - 10.8])
                    circle(d = 8.8);
                translate([-(BODY_W / 2) - 4.8, BODY_H / 2 - 7.4])
                    circle(d = 9.2);
                translate([RING_X + 1.9, RING_Y - 0.2])
                    circle(d = 8.7);
            }

            translate([RING_X, RING_Y])
                circle(d = RING_OUTER_D);

            translate([ACCENT_X, ACCENT_Y])
                circle(d = ACCENT_D);
        }

        translate([RING_X - 0.2, RING_Y - 0.35])
            circle(d = HOLE_D);
    }
}

module panel_2d() {
    translate([1.0, 0])
        rounded_rect_2d(PANEL_W, PANEL_H, PANEL_R);
}

module bottom_text_2d() {
    translate([0.8, 0.0])
        text(
            PLATE_TEXT,
            size = 8.8,
            font = FONT_MAIN,
            halign = "center",
            valign = "center",
            spacing = 1.08
        );
}

module badge_text_2d() {
    translate([0.8, -8.8])
        text(
            "HeyRent!",
            size = 3.9,
            font = FONT_MAIN,
            halign = "center",
            valign = "center",
            spacing = 1.0
        );
}

module safe_text_extrude(height) {
    linear_extrude(height = height)
        children();
}

module base_body() {
    linear_extrude(height = BODY_T, center = true)
        outer_profile_2d();
}

module recessed_shell() {
    difference() {
        base_body();

        translate([0, 0, BODY_T / 2 - PANEL_DEPTH])
            linear_extrude(height = PANEL_DEPTH + 0.02)
                panel_2d();

        translate([0, 0, -BODY_T / 2 - 0.02])
            linear_extrude(height = PANEL_DEPTH + 0.02)
                panel_2d();
    }
}

module top_face_details() {
    translate([0, 0, BODY_T / 2 - PANEL_DEPTH])
        union() {
            safe_text_extrude(TEXT_RELIEF)
                bottom_text_2d();

            safe_text_extrude(0.36)
                badge_text_2d();
        }
}

union() {
    recessed_shell();
    top_face_details();
}
