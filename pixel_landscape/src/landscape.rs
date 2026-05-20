use crate::noise::NoiseGenerator;
use crate::palette::Palette;

pub struct Landscape {
    pub width: usize,
    pub height: usize,
    pub tiles: Vec<Vec<usize>>,
}

impl Landscape {
    pub fn generate_dark_forest(width: usize, height: usize, seed: u64) -> Self {
        let noise_gen = NoiseGenerator::new(seed);
        let mut tiles = vec![vec![0; width]; height];

        for y in 0..height {
            for x in 0..width {
                let fx = x as f64;
                let fy = y as f64;

                let height_noise = noise_gen.fbm(fx, fy, 4, 30.0);
                let detail_noise = noise_gen.fbm(fx, fy, 2, 10.0);

                let tile = if fy < height as f64 * 0.6 {
                    // Sky/background
                    if detail_noise > 0.6 {
                        1
                    } else {
                        0
                    }
                } else {
                    // Terrain
                    if height_noise > 0.7 {
                        13 // Dark brown (trees)
                    } else if height_noise > 0.5 {
                        8 // Dark green
                    } else if height_noise > 0.3 {
                        9 // Muted green
                    } else {
                        10 // Sickly green
                    }
                };

                tiles[y][x] = tile;
            }
        }

        Landscape {
            width,
            height,
            tiles,
        }
    }

    pub fn generate_coastal_ruins(width: usize, height: usize, seed: u64) -> Self {
        let noise_gen = NoiseGenerator::new(seed);
        let mut tiles = vec![vec![0; width]; height];

        for y in 0..height {
            for x in 0..width {
                let fx = x as f64;
                let fy = y as f64;

                let height_noise = noise_gen.fbm(fx, fy, 5, 40.0);
                let wave_noise = (noise_gen.get_noise(fx, fy, 15.0) * 3.14159 * 2.0).sin();

                let tile = if fy < height as f64 * 0.3 {
                    // Sky
                    if wave_noise > 0.3 {
                        7
                    } else {
                        5
                    }
                } else if fy < height as f64 * 0.65 {
                    // Water/waves
                    if wave_noise.abs() > 0.5 {
                        7 // Light blue
                    } else {
                        6 // Medium blue
                    }
                } else {
                    // Shore/rocks
                    if height_noise > 0.7 {
                        13 // Brown ruins
                    } else if height_noise > 0.4 {
                        14 // Stone
                    } else {
                        15 // Light stone
                    }
                };

                tiles[y][x] = tile;
            }
        }

        Landscape {
            width,
            height,
            tiles,
        }
    }

    pub fn generate_swamp_cemetery(width: usize, height: usize, seed: u64) -> Self {
        let noise_gen = NoiseGenerator::new(seed);
        let mut tiles = vec![vec![0; width]; height];

        for y in 0..height {
            for x in 0..width {
                let fx = x as f64;
                let fy = y as f64;

                let terrain_noise = noise_gen.fbm(fx, fy, 3, 25.0);
                let mist_noise = noise_gen.get_noise(fx * 0.5, fy, 50.0);

                let tile = if fy < height as f64 * 0.4 {
                    // Mist sky
                    if mist_noise > 0.6 {
                        4 // Pale purple
                    } else {
                        2 // Murky purple
                    }
                } else {
                    // Swamp ground
                    if terrain_noise > 0.7 {
                        8 // Dark green (vegetation)
                    } else if terrain_noise > 0.4 {
                        10 // Sickly green (swamp water)
                    } else {
                        11 // Brown (mud)
                    }
                };

                tiles[y][x] = tile;
            }
        }

        Landscape {
            width,
            height,
            tiles,
        }
    }
}
