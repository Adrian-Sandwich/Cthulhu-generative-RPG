mod palette;
mod noise;
mod landscape;
mod renderer;

use palette::Palette;
use landscape::Landscape;
use renderer::Renderer;
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🎨 Pixel Landscape Generator - Retro Horror/Adventure\n");

    let output_dir = "generated";
    std::fs::create_dir_all(output_dir)?;

    // Dark Forest - Lovecraftian palette
    {
        println!("Generating: Dark Forest (Lovecraftian)...");
        let landscape = Landscape::generate_dark_forest(20, 12, 42);
        let palette = Palette::lovecraftian();
        let renderer = Renderer::new(palette, 16);
        let path = Path::new(output_dir).join("dark_forest.png");
        renderer.render(&landscape, &path)?;
        println!("✅ Saved to: {}\n", path.display());
    }

    // Coastal Ruins - Cosmic Horror palette
    {
        println!("Generating: Coastal Ruins (Cosmic Horror)...");
        let landscape = Landscape::generate_coastal_ruins(20, 12, 123);
        let palette = Palette::cosmic_horror();
        let renderer = Renderer::new(palette, 16);
        let path = Path::new(output_dir).join("coastal_ruins.png");
        renderer.render(&landscape, &path)?;
        println!("✅ Saved to: {}\n", path.display());
    }

    // Swamp Cemetery - Lovecraftian palette
    {
        println!("Generating: Swamp Cemetery (Lovecraftian)...");
        let landscape = Landscape::generate_swamp_cemetery(20, 12, 456);
        let palette = Palette::lovecraftian();
        let renderer = Renderer::new(palette, 16);
        let path = Path::new(output_dir).join("swamp_cemetery.png");
        renderer.render(&landscape, &path)?;
        println!("✅ Saved to: {}\n", path.display());
    }

    // Multiple seeds for variety
    {
        println!("Generating variations...");
        for seed in [789, 1011, 1213].iter() {
            let landscape = Landscape::generate_dark_forest(20, 12, *seed);
            let palette = Palette::lovecraftian();
            let renderer = Renderer::new(palette, 16);
            let path = Path::new(output_dir).join(format!("dark_forest_var_{}.png", seed));
            renderer.render(&landscape, &path)?;
            println!("✅ Variation {} generated", seed);
        }
    }

    println!("\n🎨 Done! Check the '{}' directory for generated landscapes.", output_dir);

    Ok(())
}
