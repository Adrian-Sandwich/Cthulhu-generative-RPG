use crate::noise::NoiseGenerator;

pub struct FirstPersonScene {
    pub width: usize,
    pub height: usize,
    pub tiles: Vec<Vec<usize>>,
}

impl FirstPersonScene {
    /// Generate a first-person view of a stone chamber
    /// Layout:
    /// - Top: Ceiling with glow
    /// - Upper-mid: Far back wall
    /// - Mid: Walls on sides + objects
    /// - Lower-mid: Near ground objects
    /// - Bottom: Floor
    pub fn generate_stone_chamber(width: usize, height: usize, seed: u64) -> Self {
        let noise_gen = NoiseGenerator::new(seed);
        let mut tiles = vec![vec![0; width]; height];

        let ceiling_height = (height as f64 * 0.15) as usize;
        let far_wall_height = (height as f64 * 0.40) as usize;
        let mid_ground_height = (height as f64 * 0.65) as usize;
        let floor_height = height;

        let center_x = width / 2;
        let center_dist = width / 3;

        for y in 0..height {
            for x in 0..width {
                let fx = x as f64;
                let fy = y as f64;

                // Perspective: objects closer to center are "further away"
                let dist_from_center = ((x as f64 - center_x as f64).abs()).abs();

                let tile = if y < ceiling_height {
                    // CEILING - Unnatural glow from above
                    let glow = noise_gen.fbm(fx * 0.4, fy, 2, 40.0);

                    if glow > 0.70 { 14 }  // Eldritch purple (rare spots)
                    else if glow > 0.55 { 13 }  // Supernatural blue
                    else if glow > 0.40 { 12 }  // Eerie glow
                    else { 2 }  // Shadow
                } else if y < far_wall_height {
                    // FAR WALL (back of chamber) - perspective narrows toward center
                    let wall_detail = noise_gen.fbm(fx * 0.8, fy * 1.5, 4, 20.0);
                    let moss_rare = noise_gen.fbm(fx * 1.5, fy, 3, 15.0);

                    // Center is farther, sides are closer -> perspective
                    if dist_from_center < 20.0 {
                        // Far background - barely visible
                        if wall_detail > 0.65 { 5 } else { 2 }
                    } else if dist_from_center < center_dist as f64 {
                        // Visible back wall
                        if moss_rare > 0.78 { 10 }  // Rare moss
                        else if wall_detail > 0.68 { 5 }  // Light stone
                        else if wall_detail > 0.50 { 4 }  // Medium stone
                        else { 3 }  // Dark stone
                    } else {
                        // Sides - wall/shadows
                        if moss_rare > 0.80 { 9 }  // Dark moss in crevices
                        else if wall_detail > 0.6 { 4 }  // Stone
                        else { 2 }  // Shadow
                    }
                } else if y < mid_ground_height {
                    // MID GROUND - Side walls + central space
                    let side_wall = noise_gen.fbm(fx, fy, 3, 25.0);
                    let moss_coverage = noise_gen.fbm(fx * 0.7, fy * 1.2, 4, 30.0);

                    if dist_from_center < center_dist as f64 * 0.3 {
                        // Central open space
                        if moss_coverage > 0.72 { 11 }  // Glowing moss patches
                        else if moss_coverage > 0.60 { 10 }  // Moss
                        else { 2 }  // Shadow/air
                    } else if dist_from_center < center_dist as f64 * 0.7 {
                        // Mid walls
                        if moss_coverage > 0.75 { 10 }
                        else if side_wall > 0.65 { 5 }
                        else if side_wall > 0.45 { 4 }
                        else { 3 }
                    } else {
                        // Side edges - darker
                        if moss_coverage > 0.78 { 9 }
                        else if side_wall > 0.60 { 3 }
                        else { 1 }  // Deep shadow
                    }
                } else {
                    // FLOOR - Crumbling stone with cracks
                    let floor_decay = noise_gen.fbm(fx * 0.6, fy, 5, 18.0);
                    let cracks = noise_gen.fbm(fx * 2.0, fy * 1.5, 3, 10.0);

                    // Near ground is clearer
                    if cracks > 0.72 { 0 }  // Deep cracks = void
                    else if cracks > 0.65 { 1 }  // Dark cracks
                    else if floor_decay > 0.70 { 5 }  // Light stone (worn)
                    else if floor_decay > 0.55 { 4 }  // Medium stone
                    else if floor_decay > 0.40 { 3 }  // Dark stone
                    else { 2 }  // Very dark
                };

                tiles[y][x] = tile;
            }
        }

        FirstPersonScene { width, height, tiles }
    }

    pub fn generate_dark_forest_entrance(width: usize, height: usize, seed: u64) -> Self {
        let noise_gen = NoiseGenerator::new(seed);
        let mut tiles = vec![vec![0; width]; height];

        let canopy_height = (height as f64 * 0.35) as usize;
        let tree_line_height = (height as f64 * 0.60) as usize;
        let floor_height = height;

        let center_x = width / 2;
        let center_dist = width / 3;

        for y in 0..height {
            for x in 0..width {
                let fx = x as f64;
                let fy = y as f64;
                let dist_from_center = ((x as f64 - center_x as f64).abs()).abs();

                let tile = if y < canopy_height {
                    // SKY - Dark forest canopy above
                    let sky = noise_gen.fbm(fx * 0.3, fy, 2, 50.0);

                    if sky > 0.65 { 2 } else { 1 }
                } else if y < tree_line_height {
                    // TREES - Dense forest wall
                    let tree_density = noise_gen.fbm(fx * 0.5, fy * 0.8, 4, 20.0);

                    if dist_from_center < center_dist as f64 * 0.2 {
                        // Center - can see deeper into forest
                        if tree_density > 0.70 { 13 }
                        else if tree_density > 0.50 { 9 }
                        else { 8 }
                    } else if dist_from_center < center_dist as f64 {
                        // Mid trees
                        if tree_density > 0.72 { 13 }
                        else if tree_density > 0.60 { 9 }
                        else { 8 }
                    } else {
                        // Sides - solid tree wall
                        if tree_density > 0.65 { 13 }
                        else { 8 }
                    }
                } else {
                    // GROUND - Forest floor
                    let ground = noise_gen.fbm(fx * 0.7, fy, 4, 22.0);
                    let roots = noise_gen.fbm(fx * 1.5, fy, 2, 12.0);

                    if roots > 0.68 { 11 }  // Dark roots
                    else if ground > 0.65 { 8 }  // Dark ground
                    else if ground > 0.45 { 9 }  // Medium ground
                    else { 10 }  // Light undergrowth
                };

                tiles[y][x] = tile;
            }
        }

        FirstPersonScene { width, height, tiles }
    }
}
