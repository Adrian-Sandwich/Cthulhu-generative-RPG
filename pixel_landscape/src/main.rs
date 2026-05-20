mod palette;
mod noise;
mod landscape;
mod renderer;

use palette::Palette;
use landscape::{Landscape, SceneDescription};
use renderer::Renderer;
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🎨 Pixel Scene Generator - Cthulhu Adventure\n");

    let output_dir = "generated";
    std::fs::create_dir_all(output_dir)?;

    // MAIN TEST: Stone Chamber with Moss
    {
        let scene = SceneDescription::stone_chamber();
        println!("═══════════════════════════════════════════════════════");
        println!("Generating: {}", scene.title);
        println!("═══════════════════════════════════════════════════════");
        println!("\n{}\n", scene.text);

        let landscape = Landscape::generate_stone_chamber(80, 60, 999);
        let palette = Palette::chamber();
        let renderer = Renderer::new(palette, 16);
        let path = Path::new(output_dir).join("stone_chamber.png");
        renderer.render(&landscape, &path)?;
        println!("✅ Saved to: {}\n", path.display());
    }

    // Additional scenes for reference
    {
        println!("Generating additional scenes for reference...\n");

        // Dark Forest
        let landscape = Landscape::generate_dark_forest(80, 60, 42);
        let palette = Palette::lovecraftian();
        let renderer = Renderer::new(palette, 16);
        let path = Path::new(output_dir).join("dark_forest.png");
        renderer.render(&landscape, &path)?;
        println!("✅ Dark Forest generated");

        // Coastal Ruins
        let landscape = Landscape::generate_coastal_ruins(80, 60, 123);
        let palette = Palette::cosmic_horror();
        let renderer = Renderer::new(palette, 16);
        let path = Path::new(output_dir).join("coastal_ruins.png");
        renderer.render(&landscape, &path)?;
        println!("✅ Coastal Ruins generated");

        // Swamp Cemetery
        let landscape = Landscape::generate_swamp_cemetery(80, 60, 456);
        let palette = Palette::lovecraftian();
        let renderer = Renderer::new(palette, 16);
        let path = Path::new(output_dir).join("swamp_cemetery.png");
        renderer.render(&landscape, &path)?;
        println!("✅ Swamp Cemetery generated");
    }

    println!("\n🎨 Done! Check the '{}' directory for generated scenes.", output_dir);

    Ok(())
}
