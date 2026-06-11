use crate::scene::FirstPersonScene;

pub struct RaycastMap {
    pub map: Vec<Vec<usize>>,
    pub width: usize,
    pub height: usize,
}

impl RaycastMap {
    /// Convert FirstPersonScene to a simple binary map for raycasting
    /// Walls (non-shadow) = 1, empty/air = 0
    pub fn from_scene(scene: &FirstPersonScene) -> Self {
        let width = scene.width;
        let height = scene.height;
        let mut map = vec![vec![0; width]; height];

        for y in 0..height {
            for x in 0..width {
                let tile_index = scene.tiles[y][x];

                // Simplify: walls are solid (1), everything else is empty (0)
                // For a stone chamber: colors 0-6 are walls/stone, 7+ are air/moss
                // This is terrain-dependent, so we'll use a simple threshold
                map[y][x] = if tile_index < 7 { 1 } else { 0 };
            }
        }

        RaycastMap { map, width, height }
    }
}

pub struct RaycasterState {
    pub player_x: f32,
    pub player_y: f32,
    pub player_angle: f32,
    pub map: Vec<Vec<usize>>,
}

impl RaycasterState {
    pub fn new(raycaster_map: &RaycastMap) -> Self {
        // Start player in the middle of the first open space
        let mut player_x = 1.5;
        let mut player_y = 1.5;

        for y in 0..raycaster_map.height {
            for x in 0..raycaster_map.width {
                if raycaster_map.map[y][x] == 0 {
                    player_x = x as f32 + 0.5;
                    player_y = y as f32 + 0.5;
                    break;
                }
            }
        }

        RaycasterState {
            player_x,
            player_y,
            player_angle: 0.0,
            map: raycaster_map.map.clone(),
        }
    }

    pub fn cast_ray(&mut self, angle: f32, max_distance: f32) -> (f32, f32) {
        let sin = angle.sin();
        let cos = angle.cos();
        let tan = sin / cos;
        let cot = cos / sin;

        let mut current_x = self.player_x;
        let mut current_y = self.player_y;
        let mut distance = 0.0;

        while distance < max_distance {
            // X-axis intersection
            let dx_x = if cos < 0.0 {
                (current_x - 1.0).ceil() - current_x
            } else {
                (current_x + 1.0).floor() - current_x
            };

            let dx_y = dx_x * tan;
            let len_x = (dx_x * dx_x + dx_y * dx_y).sqrt();

            // Y-axis intersection
            let dy_x = if sin < 0.0 {
                (current_y - 1.0).ceil() - current_y
            } else {
                (current_y + 1.0).floor() - current_y
            };

            let dy_y = dy_x * cot;
            let len_y = (dy_x * dy_x + dy_y * dy_y).sqrt();

            if len_x < len_y {
                current_x += dx_x;
                current_y += dx_y;
                distance += len_x;
            } else {
                current_x += dy_x;
                current_y += dy_y;
                distance += len_y;
            }

            let xi = current_x.floor() as usize;
            let yi = current_y.floor() as usize;

            if xi >= self.map.len() || yi >= self.map[0].len() {
                break;
            }

            if self.map[yi][xi] != 0 {
                break;
            }
        }

        (current_x, current_y)
    }
}
