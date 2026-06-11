use macroquad::prelude::*;
use pixel_landscape::scene::FirstPersonScene;
use pixel_landscape::raycaster::{RaycasterState, RaycastMap};

const TILE_SIZE: f32 = 24.0;
const PLAYER_SPEED: f32 = 0.1;
const FOCAL_LENGTH: f32 = 0.8;

fn window_conf() -> Conf {
    Conf {
        window_title: "Cthulhu Horror Raycaster".to_owned(),
        window_width: 1280,
        window_height: 960,
        window_resizable: false,
        ..Default::default()
    }
}

fn draw_minimap(state: &RaycasterState) {
    let mini_scale = 10.0;

    // Draw map
    for (y, row) in state.map.iter().enumerate() {
        for (x, &tile) in row.iter().enumerate() {
            if tile != 0 {
                draw_rectangle(
                    x as f32 * mini_scale,
                    y as f32 * mini_scale,
                    mini_scale,
                    mini_scale,
                    Color::from_rgba(100, 100, 100, 255),
                );
            }
        }
    }

    // Draw player
    draw_circle(
        state.player_x * mini_scale,
        state.player_y * mini_scale,
        3.0,
        Color::from_rgba(255, 255, 0, 255),
    );

    // Draw direction
    let dx = 3.0 * state.player_angle.cos();
    let dy = 3.0 * state.player_angle.sin();
    draw_line(
        state.player_x * mini_scale,
        state.player_y * mini_scale,
        (state.player_x + dx) * mini_scale,
        (state.player_y + dy) * mini_scale,
        1.0,
        Color::from_rgba(0, 255, 0, 255),
    );
}

fn draw_first_person(state: &RaycasterState) {
    let screen_width = screen_width();
    let screen_height = screen_height();
    let mid_y = screen_height / 2.0;

    // Draw ceiling
    draw_rectangle(0.0, 0.0, screen_width, mid_y, Color::from_rgba(20, 20, 30, 255));

    // Draw floor
    draw_rectangle(
        0.0,
        mid_y,
        screen_width,
        mid_y,
        Color::from_rgba(60, 60, 80, 255),
    );

    // Draw columns via raycasting
    let num_rays = screen_width as i32;

    for col in 0..num_rays {
        let x = col as f32 / num_rays as f32 - 0.5;
        let angle = state.player_angle + x.atan2(FOCAL_LENGTH);

        let mut state_copy = RaycasterState {
            player_x: state.player_x,
            player_y: state.player_y,
            player_angle: state.player_angle,
            map: state.map.clone(),
        };

        let (ray_x, ray_y) = state_copy.cast_ray(angle, 40.0);

        // Calculate distance with perspective correction
        let dx = ray_x - state.player_x;
        let dy = ray_y - state.player_y;
        let raw_distance = (dx * dx + dy * dy).sqrt();
        let distance = raw_distance * x.atan2(FOCAL_LENGTH).cos();

        // Calculate wall height
        let wall_height = if distance > 0.1 {
            1000.0 / distance
        } else {
            screen_height
        };

        // Draw column with distance-based shading
        let brightness = (50.0 / (distance + 1.0)) as u8;
        let color = Color::from_rgba(brightness, brightness, brightness + 40, 255);

        draw_line(
            col as f32,
            mid_y - wall_height,
            col as f32,
            mid_y + wall_height,
            1.0,
            color,
        );
    }
}

#[macroquad::main(window_conf)]
async fn main() {
    println!("🎮 Cthulhu Horror Raycaster");
    println!("Controls: Arrow keys to move/turn, Z for minimap, X for 1P view, ESC to exit\n");

    // Generate scene
    println!("Generating stone chamber...");
    let scene = FirstPersonScene::generate_stone_chamber(80, 60, 999);
    println!("Converting to raycaster map...");
    let raycast_map = RaycastMap::from_scene(&scene);
    println!("Initializing raycaster state...");
    let mut state = RaycasterState::new(&raycast_map);

    let mut show_minimap = true;

    loop {
        clear_background(Color::from_rgba(40, 40, 50, 255));

        // Input
        if is_key_down(KeyCode::Up) {
            let dx = PLAYER_SPEED * state.player_angle.cos();
            let dy = PLAYER_SPEED * state.player_angle.sin();

            let new_x = state.player_x + dx;
            let new_y = state.player_y + dy;

            if (new_x.floor() as usize) < state.map.len()
                && (new_y.floor() as usize) < state.map[0].len()
                && state.map[new_y.floor() as usize][new_x.floor() as usize] == 0
            {
                state.player_x = new_x;
                state.player_y = new_y;
            }
        }

        if is_key_down(KeyCode::Down) {
            let dx = PLAYER_SPEED * state.player_angle.cos();
            let dy = PLAYER_SPEED * state.player_angle.sin();

            let new_x = state.player_x - dx;
            let new_y = state.player_y - dy;

            if (new_x.floor() as usize) < state.map.len()
                && (new_y.floor() as usize) < state.map[0].len()
                && state.map[new_y.floor() as usize][new_x.floor() as usize] == 0
            {
                state.player_x = new_x;
                state.player_y = new_y;
            }
        }

        if is_key_down(KeyCode::Left) {
            state.player_angle -= 0.05;
        }

        if is_key_down(KeyCode::Right) {
            state.player_angle += 0.05;
        }

        if is_key_pressed(KeyCode::Z) {
            show_minimap = !show_minimap;
        }

        if is_key_pressed(KeyCode::Escape) {
            break;
        }

        // Draw
        draw_first_person(&state);

        if show_minimap {
            draw_minimap(&state);
        }

        // HUD
        draw_text(
            &format!(
                "Pos: ({:.2}, {:.2}) | Angle: {:.2} | Minimap: {}",
                state.player_x,
                state.player_y,
                state.player_angle,
                if show_minimap { "ON" } else { "OFF" }
            ),
            10.0,
            screen_height() - 10.0,
            20.0,
            Color::from_rgba(0, 255, 0, 255),
        );

        next_frame().await;
    }
}
