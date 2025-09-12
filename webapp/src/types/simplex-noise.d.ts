declare module 'simplex-noise' {
  export function createNoise2D(random?: () => number): (x: number, y: number) => number;
  export function createNoise3D(random?: () => number): (x: number, y: number, z: number) => number;
  export function createNoise4D(random?: () => number): (x: number, y: number, z: number, w: number) => number;
}
