use image::Rgb;

pub struct Palette {
    pub colors: Vec<Rgb<u8>>,
}

impl Palette {
    pub fn chamber() -> Self {
        let colors = vec![
            Rgb([8, 8, 12]),         // 0: deep black/void
            Rgb([35, 35, 50]),       // 1: dark shadow
            Rgb([70, 70, 90]),       // 2: medium shadow
            Rgb([110, 110, 135]),    // 3: stone base (darker)
            Rgb([145, 145, 170]),    // 4: light stone
            Rgb([180, 180, 200]),    // 5: pale stone
            Rgb([220, 220, 235]),    // 6: bright stone
            Rgb([255, 255, 255]),    // 7: white highlight
            Rgb([15, 55, 15]),       // 8: very dark moss
            Rgb([45, 100, 45]),      // 9: dark moss green
            Rgb([80, 140, 80]),      // 10: moss green
            Rgb([110, 160, 100]),    // 11: moss with glow
            Rgb([140, 170, 120]),    // 12: eerie glow (muted)
            Rgb([100, 140, 200]),    // 13: supernatural blue (desaturated)
            Rgb([130, 80, 160]),     // 14: eldritch purple (darker)
            Rgb([180, 100, 140]),    // 15: unnatural tint (less bright)
        ];
        Palette { colors }
    }

    pub fn lovecraftian() -> Self {
        let colors = vec![
            Rgb([10, 10, 15]),       // 0: abyss
            Rgb([40, 40, 50]),       // 1: shadow
            Rgb([80, 70, 90]),       // 2: dark purple
            Rgb([120, 100, 140]),    // 3: medium purple
            Rgb([30, 30, 50]),       // 4: dark blue
            Rgb([80, 80, 120]),      // 5: medium blue
            Rgb([140, 140, 180]),    // 6: light blue
            Rgb([200, 200, 220]),    // 7: pale blue
            Rgb([20, 60, 20]),       // 8: dark forest green
            Rgb([60, 120, 60]),      // 9: forest green
            Rgb([120, 180, 120]),    // 10: light green
            Rgb([180, 220, 180]),    // 11: pale green
            Rgb([80, 50, 30]),       // 12: dark brown
            Rgb([140, 100, 60]),     // 13: medium brown
            Rgb([180, 140, 100]),    // 14: light brown
            Rgb([220, 180, 140]),    // 15: pale brown
        ];
        Palette { colors }
    }

    pub fn cosmic_horror() -> Self {
        let colors = vec![
            Rgb([5, 5, 10]),         // 0: void black
            Rgb([30, 20, 40]),       // 1: dark void
            Rgb([70, 40, 100]),      // 2: deep cosmic
            Rgb([120, 60, 180]),     // 3: cosmic purple
            Rgb([20, 30, 50]),       // 4: dark water
            Rgb([60, 80, 140]),      // 5: medium water
            Rgb([120, 150, 200]),    // 6: light water
            Rgb([200, 220, 255]),    // 7: foam white
            Rgb([40, 40, 40]),       // 8: dark rock
            Rgb([100, 80, 60]),      // 9: stone
            Rgb([160, 140, 120]),    // 10: light stone
            Rgb([220, 200, 180]),    // 11: pale stone
            Rgb([150, 50, 150]),     // 12: eldritch
            Rgb([200, 100, 200]),    // 13: bright eldritch
            Rgb([100, 200, 200]),    // 14: eerie teal
            Rgb([200, 100, 100]),    // 15: blood red
        ];
        Palette { colors }
    }

    pub fn get_color(&self, index: usize) -> Rgb<u8> {
        self.colors[index % self.colors.len()]
    }
}
