mod palette;
mod noise;
mod landscape;
mod scene;
mod renderer;

use palette::Palette;
use landscape::SceneDescription;
use scene::FirstPersonScene;
use renderer::Renderer;
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🎨 Pixel Scene Generator - Cthulhu Adventure\n");

    let output_dir = "generated";
    std::fs::create_dir_all(output_dir)?;

    // MAIN TEST: Stone Chamber (First-Person View)
    {
        let scene_desc = SceneDescription::stone_chamber();
        println!("═══════════════════════════════════════════════════════");
        println!("Generating: {} (FIRST-PERSON)", scene_desc.title);
        println!("═══════════════════════════════════════════════════════");
        println!("\n{}\n", scene_desc.text);

        let scene = FirstPersonScene::generate_stone_chamber(80, 60, 999);
        let palette = Palette::chamber();
        let renderer = Renderer::new(palette, 16);
        let path = Path::new(output_dir).join("stone_chamber_1p.png");
        renderer.render(&scene.tiles, scene.width, scene.height, &path)?;
        println!("✅ Saved to: {} (First-Person)\n", path.display());
    }

    // Additional first-person scenes
    {
        println!("Generating additional first-person scenes...\n");

        // Dark Forest Entrance (1st person)
        let scene = FirstPersonScene::generate_dark_forest_entrance(80, 60, 42);
        let palette = Palette::lovecraftian();
        let renderer = Renderer::new(palette, 16);
        let path = Path::new(output_dir).join("dark_forest_entrance_1p.png");
        renderer.render(&scene.tiles, scene.width, scene.height, &path)?;
        println!("✅ Dark Forest Entrance (1st person) generated");
    }

    println!("\n🎨 Done! Check the '{}' directory for generated scenes.", output_dir);

    Ok(())
}
