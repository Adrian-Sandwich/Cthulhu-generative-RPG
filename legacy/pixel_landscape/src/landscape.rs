use crate::noise::NoiseGenerator;

pub struct Landscape {
    pub width: usize,
    pub height: usize,
    pub tiles: Vec<Vec<usize>>,
}

pub struct SceneDescription {
    pub title: &'static str,
    pub text: &'static str,
}

impl SceneDescription {
    pub fn stone_chamber() -> Self {
        SceneDescription {
            title: "STONE CHAMBER",
            text: "You find yourself in a decaying stone chamber. Moss creeps up ancient walls. \
                   A faint, unnatural glow emanates from the ceiling.",
        }
    }
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

    pub fn generate_stone_chamber(width: usize, height: usize, seed: u64) -> Self {
        let noise_gen = NoiseGenerator::new(seed);
        let mut tiles = vec![vec![0; width]; height];

        let glow_height = (height as f64 * 0.12) as usize;
        let wall_height = (height as f64 * 0.68) as usize;

        for y in 0..height {
            for x in 0..width {
                let fx = x as f64;
                let fy = y as f64;

                let tile = if y < glow_height {
                    // Thin glow layer at ceiling - SUBTLE
                    let glow = noise_gen.fbm(fx * 0.3, fy * 2.0, 2, 60.0);

                    if glow > 0.72 { 14 }                    // Rare: eldritch purple
                    else if glow > 0.60 { 13 }               // Supernatural blue (rare)
                    else if glow > 0.45 { 12 }               // Eerie glow
                    else { 2 }                                // Mostly shadow
                } else if y < wall_height {
                    // Walls - MOSTLY stone with occasional moss
                    let stone_texture = noise_gen.fbm(fx, fy, 5, 20.0);
                    let moss_growth = noise_gen.fbm(fx * 1.2, fy * 0.9, 4, 32.0);
                    let wall_cracks = noise_gen.fbm(fx * 2.5, fy, 2, 10.0);

                    // Moss is RARE (threshold high)
                    if moss_growth > 0.80 { 10 }             // Moss patches (rare)
                    else if moss_growth > 0.70 && wall_cracks > 0.6 { 9 }  // Dark moss in cracks
                    else if moss_growth > 0.65 { 11 }        // Light moss edges
                    else if stone_texture > 0.65 { 5 }       // Pale stone (common)
                    else if stone_texture > 0.50 { 4 }       // Light stone (common)
                    else if stone_texture > 0.35 { 3 }       // Medium stone
                    else { 2 }                                // Dark stone/shadow
                } else {
                    // Ground floor - crumbling stone
                    let floor_base = noise_gen.fbm(fx * 0.8, fy, 4, 25.0);
                    let floor_cracks = noise_gen.fbm(fx * 3.0, fy, 3, 8.0);

                    if floor_cracks > 0.75 { 0 }             // Deep cracks = abyss
                    else if floor_cracks > 0.65 { 1 }        // Dark cracks/shadow
                    else if floor_base > 0.70 { 5 }          // Pale stone (worn)
                    else if floor_base > 0.55 { 4 }          // Light stone
                    else if floor_base > 0.40 { 3 }          // Medium stone
                    else { 2 }                                // Dark stone
                };

                tiles[y][x] = tile;
            }
        }

        Landscape { width, height, tiles }
    }
}
