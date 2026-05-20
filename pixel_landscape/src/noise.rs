use noise::{NoiseFn, Perlin};
use rand::Rng;

pub struct NoiseGenerator {
    perlin: Perlin,
    seed: u64,
}

impl NoiseGenerator {
    pub fn new(seed: u64) -> Self {
        NoiseGenerator {
            perlin: Perlin::new(seed as u32),
            seed,
        }
    }

    pub fn get_noise(&self, x: f64, y: f64, scale: f64) -> f64 {
        let value = self.perlin.get([x / scale, y / scale]);
        (value + 1.0) / 2.0
    }

    pub fn fbm(&self, x: f64, y: f64, octaves: usize, scale: f64) -> f64 {
        let mut value = 0.0;
        let mut amplitude = 1.0;
        let mut frequency = 1.0;
        let mut max_value = 0.0;

        for _ in 0..octaves {
            value += self.get_noise(x * frequency, y * frequency, scale) * amplitude;
            max_value += amplitude;
            amplitude *= 0.5;
            frequency *= 2.0;
        }

        value / max_value
    }

    pub fn random_value(&self, range: u32) -> u32 {
        let mut rng = rand::thread_rng();
        rng.gen_range(0..range)
    }
}
