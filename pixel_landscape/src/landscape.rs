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

        let sky_height = (height as f64 * 0.45) as usize;
        let canopy_height = (height as f64 * 0.65) as usize;

        for y in 0..height {
            for x in 0..width {
                let fx = x as f64;
                let fy = y as f64;

                let tile = if y < sky_height {
                    // Sky layer - dark atmosphere
                    let sky_noise = noise_gen.fbm(fx, fy, 2, 60.0);
                    if sky_noise > 0.65 { 2 } else { 1 }
                } else if y < canopy_height {
                    // Canopy layer - tree tops and shadows
                    let canopy_noise = noise_gen.fbm(fx, fy, 5, 20.0);
                    let shadow_noise = noise_gen.fbm(fx * 1.5, fy, 3, 15.0);

                    if canopy_noise > 0.75 { 13 }      // Dark tree
                    else if canopy_noise > 0.55 && shadow_noise > 0.6 { 11 }  // Brown shadow
                    else if canopy_noise > 0.45 { 9 }   // Muted green
                    else { 8 }                           // Dark green
                } else {
                    // Ground layer - undergrowth
                    let ground_noise = noise_gen.fbm(fx, fy, 4, 25.0);
                    let moss_noise = noise_gen.fbm(fx * 2.0, fy, 2, 8.0);

                    if ground_noise > 0.7 { 8 }         // Dark green
                    else if moss_noise > 0.6 { 10 }     // Sickly moss
                    else { 9 }                           // Muted undergrowth
                };

                tiles[y][x] = tile;
            }
        }

        Landscape { width, height, tiles }
    }

    pub fn generate_coastal_ruins(width: usize, height: usize, seed: u64) -> Self {
        let noise_gen = NoiseGenerator::new(seed);
        let mut tiles = vec![vec![0; width]; height];

        let sky_height = (height as f64 * 0.35) as usize;
        let water_height = (height as f64 * 0.7) as usize;

        for y in 0..height {
            for x in 0..width {
                let fx = x as f64;
                let fy = y as f64;

                let tile = if y < sky_height {
                    // Sky layer - distant and mysterious
                    let sky_noise = noise_gen.fbm(fx, fy, 3, 50.0);
                    if sky_noise > 0.6 { 7 } else { 5 }
                } else if y < water_height {
                    // Ocean layer - waves and currents
                    let wave_h = noise_gen.fbm(fx * 0.8, fy, 4, 30.0);
                    let current = noise_gen.fbm(fx, fy * 0.5, 2, 40.0);

                    let wave_pattern = (fx * 0.3 + fy * 0.1 + (current * 10.0)).sin();
                    if wave_pattern > 0.3 && wave_h > 0.55 { 7 }  // White foam
                    else if wave_h > 0.45 { 6 }                    // Medium blue
                    else { 5 }                                      // Dark blue
                } else {
                    // Shore/ruins layer - ancient stones
                    let ruin_noise = noise_gen.fbm(fx, fy, 5, 18.0);
                    let rubble = noise_gen.fbm(fx * 1.5, fy * 1.2, 2, 12.0);

                    if rubble > 0.7 { 13 }      // Dark brown ruins
                    else if ruin_noise > 0.65 { 14 }  // Stone
                    else if ruin_noise > 0.4 { 15 }   // Light stone
                    else { 12 }                        // Shadow
                };

                tiles[y][x] = tile;
            }
        }

        Landscape { width, height, tiles }
    }

    pub fn generate_swamp_cemetery(width: usize, height: usize, seed: u64) -> Self {
        let noise_gen = NoiseGenerator::new(seed);
        let mut tiles = vec![vec![0; width]; height];

        let mist_height = (height as f64 * 0.5) as usize;

        for y in 0..height {
            for x in 0..width {
                let fx = x as f64;
                let fy = y as f64;

                let tile = if y < mist_height {
                    // Mist layer - oppressive atmosphere
                    let mist1 = noise_gen.fbm(fx * 0.4, fy, 3, 80.0);
                    let mist2 = noise_gen.fbm(fx * 0.6, fy * 0.8, 2, 100.0);
                    let mist_blend = mist1 * 0.6 + mist2 * 0.4;

                    if mist_blend > 0.65 { 4 }   // Pale purple
                    else if mist_blend > 0.45 { 3 }  // Medium purple
                    else { 2 }                   // Murky purple
                } else {
                    // Swamp layer - water, vegetation, decay
                    let veg_noise = noise_gen.fbm(fx, fy, 4, 22.0);
                    let water_noise = noise_gen.fbm(fx * 1.2, fy * 0.9, 3, 28.0);
                    let rot_noise = noise_gen.fbm(fx * 0.5, fy * 1.5, 2, 15.0);

                    if veg_noise > 0.75 { 8 }           // Dense green vegetation
                    else if veg_noise > 0.60 && rot_noise > 0.5 { 13 }  // Rotting wood
                    else if water_noise > 0.55 { 10 }   // Sickly water
                    else if water_noise > 0.35 { 11 }   // Mud
                    else { 9 }                           // Peat
                };

                tiles[y][x] = tile;
            }
        }

        Landscape { width, height, tiles }
    }
}
