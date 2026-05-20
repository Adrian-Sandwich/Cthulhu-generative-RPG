use image::Rgb;

pub struct Palette {
    pub colors: Vec<Rgb<u8>>,
}

impl Palette {
    pub fn chamber() -> Self {
        let colors = vec![
            Rgb([5, 5, 10]),         // 0: abyssal black
            Rgb([30, 30, 45]),       // 1: deep shadow
            Rgb([65, 65, 85]),       // 2: dark gray/shadow
            Rgb([105, 105, 130]),    // 3: medium stone
            Rgb([145, 145, 165]),    // 4: light stone
            Rgb([185, 185, 205]),    // 5: pale stone (walls)
            Rgb([220, 220, 240]),    // 6: bright stone (highlights)
            Rgb([255, 255, 255]),    // 7: pure white
            Rgb([20, 60, 20]),       // 8: very dark moss
            Rgb([50, 110, 50]),      // 9: dark moss (crevasses)
            Rgb([90, 150, 90]),      // 10: moss green (primary)
            Rgb([130, 170, 110]),    // 11: moss with luminescence
            Rgb([160, 180, 130]),    // 12: eerie glow yellow
            Rgb([110, 150, 210]),    // 13: supernatural cyan
            Rgb([140, 100, 180]),    // 14: eldritch purple
            Rgb([200, 120, 160]),    // 15: unnatural magenta
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
