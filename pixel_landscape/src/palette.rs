use image::Rgb;

pub struct Palette {
    pub colors: Vec<Rgb<u8>>,
}

impl Palette {
    pub fn lovecraftian() -> Self {
        let colors = vec![
            Rgb([20, 20, 30]),      // 0: deep black
            Rgb([40, 35, 50]),      // 1: dark purple
            Rgb([60, 50, 70]),      // 2: murky purple
            Rgb([80, 70, 90]),      // 3: medium purple
            Rgb([100, 80, 100]),    // 4: pale purple
            Rgb([45, 45, 60]),      // 5: dark blue
            Rgb([70, 70, 95]),      // 6: medium blue
            Rgb([95, 95, 130]),     // 7: light blue
            Rgb([60, 80, 60]),      // 8: dark green
            Rgb([80, 110, 80]),     // 9: muted green
            Rgb([100, 130, 100]),   // 10: sickly green
            Rgb([140, 120, 80]),    // 11: brown
            Rgb([180, 160, 120]),   // 12: light brown
            Rgb([120, 100, 80]),    // 13: dark brown
            Rgb([200, 180, 160]),   // 14: stone
            Rgb([220, 210, 200]),   // 15: light stone
        ];
        Palette { colors }
    }

    pub fn cosmic_horror() -> Self {
        let colors = vec![
            Rgb([10, 5, 15]),       // 0: abyss black
            Rgb([25, 15, 35]),      // 1: void
            Rgb([50, 30, 70]),      // 2: deep cosmic
            Rgb([80, 50, 120]),     // 3: cosmic purple
            Rgb([120, 80, 180]),    // 4: bright cosmic
            Rgb([30, 25, 50]),      // 5: dark matter
            Rgb([60, 55, 100]),     // 6: nebula dark
            Rgb([100, 90, 150]),    // 7: nebula light
            Rgb([40, 60, 80]),      // 8: alien ocean
            Rgb([70, 100, 130]),    // 9: alien ocean light
            Rgb([150, 80, 200]),    // 10: eldritch
            Rgb([200, 120, 255]),   // 11: eldritch light
            Rgb([80, 40, 100]),     // 12: shadow
            Rgb([120, 60, 150]),    // 13: shadow light
            Rgb([160, 100, 200]),   // 14: mystical
            Rgb([200, 150, 255]),   // 15: mystical light
        ];
        Palette { colors }
    }

    pub fn get_color(&self, index: usize) -> Rgb<u8> {
        self.colors[index % self.colors.len()]
    }
}
