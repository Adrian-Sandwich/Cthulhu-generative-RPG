use crate::noise::NoiseGenerator;

pub struct Landscape {
    pub width: usize,
    pub height: usize,
    pub tiles: Vec<Vec<usize>>,
}

impl Landscape {
    pub fn generate_dark_forest(width: usize, height: usize, seed: u64) -> Self {
        let noise_gen = NoiseGenerator::new(seed);
        let mut tiles = vec![vec![0; width]; height];

        let sky_height = (height as f64 * 0.30) as usize;
        let forest_height = (height as f64 * 0.70) as usize;

        for y in 0..height {
            for x in 0..width {
                let fx = x as f64;
                let fy = y as f64;

                let tile = if y < sky_height {
                    // Sky - minimal
                    let sky_noise = noise_gen.fbm(fx, fy, 2, 80.0);
                    if sky_noise > 0.7 { 2 } else { 1 }
                } else if y < forest_height {
                    // Forest canopy - clustered trees
                    let tree_density = noise_gen.fbm(fx * 0.6, fy * 0.8, 4, 25.0);
                    let detail = noise_gen.fbm(fx * 2.0, fy * 1.5, 3, 12.0);

                    if tree_density > 0.68 { 13 }       // Dark tree trunks
                    else if tree_density > 0.55 && detail > 0.6 { 8 }  // Dense canopy
                    else if tree_density > 0.45 { 9 }   // Medium foliage
                    else { 10 }                         // Light undergrowth
                } else {
                    // Ground - dense vegetation
                    let ground = noise_gen.fbm(fx, fy, 5, 20.0);
                    let roots = noise_gen.fbm(fx * 1.5, fy * 2.0, 2, 8.0);

                    if ground > 0.7 && roots > 0.55 { 11 }  // Dark roots/debris
                    else if ground > 0.6 { 8 }              // Dark green ground
                    else if ground > 0.4 { 9 }              // Moss
                    else { 10 }                             // Sickly undergrowth
                };

                tiles[y][x] = tile;
            }
        }

        Landscape { width, height, tiles }
    }

    pub fn generate_coastal_ruins(width: usize, height: usize, seed: u64) -> Self {
        let noise_gen = NoiseGenerator::new(seed);
        let mut tiles = vec![vec![0; width]; height];

        let sky_height = (height as f64 * 0.28) as usize;
        let water_height = (height as f64 * 0.65) as usize;

        for y in 0..height {
            for x in 0..width {
                let fx = x as f64;
                let fy = y as f64;

                let tile = if y < sky_height {
                    // Sky - ominous
                    let sky_noise = noise_gen.fbm(fx, fy, 2, 70.0);
                    if sky_noise > 0.65 { 7 } else { 5 }
                } else if y < water_height {
                    // Ocean - turbulent
                    let wave = noise_gen.fbm(fx * 1.0, fy * 0.8, 5, 22.0);
                    let foam = (fx * 0.4 + fy * 0.15).sin().abs();

                    if wave > 0.72 && foam > 0.4 { 7 }  // Foam crests
                    else if wave > 0.55 { 6 }           // Medium water
                    else { 5 }                          // Deep water
                } else {
                    // Ruins - jagged rocks and stones
                    let rocks = noise_gen.fbm(fx * 0.7, fy, 6, 16.0);
                    let rubble = noise_gen.fbm(fx * 2.0, fy * 1.5, 3, 10.0);

                    if rocks > 0.75 { 13 }              // Dark ruin stone
                    else if rocks > 0.60 && rubble > 0.55 { 14 }  // Light stone
                    else if rocks > 0.45 { 15 }        // Pale stone
                    else { 12 }                         // Shadow crevasse
                };

                tiles[y][x] = tile;
            }
        }

        Landscape { width, height, tiles }
    }

    pub fn generate_swamp_cemetery(width: usize, height: usize, seed: u64) -> Self {
        let noise_gen = NoiseGenerator::new(seed);
        let mut tiles = vec![vec![0; width]; height];

        let mist_height = (height as f64 * 0.35) as usize;

        for y in 0..height {
            for x in 0..width {
                let fx = x as f64;
                let fy = y as f64;

                let tile = if y < mist_height {
                    // Mist - thick and oppressive
                    let mist = noise_gen.fbm(fx * 0.3, fy * 0.5, 3, 100.0);
                    let fog_swirl = noise_gen.fbm(fx * 0.5, fy, 2, 80.0);

                    if mist + fog_swirl > 1.2 { 4 }  // Pale mist
                    else if mist > 0.6 { 3 }         // Medium mist
                    else { 2 }                       // Dark mist
                } else {
                    // Swamp - vegetation and decay
                    let vegetation = noise_gen.fbm(fx * 0.8, fy, 4, 24.0);
                    let rot = noise_gen.fbm(fx * 1.5, fy * 1.2, 3, 18.0);
                    let water = noise_gen.fbm(fx, fy * 0.9, 2, 35.0);

                    if vegetation > 0.7 { 8 }           // Dense vegetation (trees)
                    else if rot > 0.68 { 11 }          // Rotting matter
                    else if vegetation > 0.5 && water > 0.5 { 10 }  // Murky water
                    else if water > 0.55 { 9 }         // Swamp water
                    else { 13 }                        // Mud/earth
                };

                tiles[y][x] = tile;
            }
        }

        Landscape { width, height, tiles }
    }
}
