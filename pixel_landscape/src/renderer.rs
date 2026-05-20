use image::{ImageBuffer, Rgb};
use crate::landscape::Landscape;
use crate::palette::Palette;
use std::path::Path;

pub struct Renderer {
    tile_size: usize,
    palette: Palette,
}

impl Renderer {
    pub fn new(palette: Palette, tile_size: usize) -> Self {
        Renderer { palette, tile_size }
    }

    pub fn render(&self, landscape: &Landscape, output_path: &Path) -> Result<(), Box<dyn std::error::Error>> {
        let width = (landscape.width * self.tile_size) as u32;
        let height = (landscape.height * self.tile_size) as u32;

        let mut img = ImageBuffer::new(width, height);

        for (y, row) in landscape.tiles.iter().enumerate() {
            for (x, &tile_index) in row.iter().enumerate() {
                let color = self.palette.get_color(tile_index);
                let start_x = x * self.tile_size;
                let start_y = y * self.tile_size;

                for py in 0..self.tile_size {
                    for px in 0..self.tile_size {
                        let pixel_x = (start_x + px) as u32;
                        let pixel_y = (start_y + py) as u32;
                        img.put_pixel(pixel_x, pixel_y, color);
                    }
                }
            }
        }

        img.save(output_path)?;
        Ok(())
    }
}
