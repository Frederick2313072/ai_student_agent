import React, { useMemo } from 'react'
import * as THREE from 'three'
import { createNoise2D } from 'simplex-noise'

export function Terrain() {
  const geometry = useMemo(() => {
    const size = 40
    const height = 8 // Increased height for more dramatic mountains
    const segments = 50

    const noise2D = createNoise2D()
    const geom = new THREE.PlaneGeometry(size, size, segments, segments)
    geom.rotateX(-Math.PI / 2)

    const vertices = geom.attributes.position.array as number[]
    const colors = []

    // 参考图片中山峰的暖色调和雪地对比
    const peakColor = new THREE.Color('#d67548') // 更暖的橙红色山峰
    const snowColor = new THREE.Color('#f8f4ff') // 带淡蓝色的雪白

    for (let i = 0; i <= segments; i++) {
      for (let j = 0; j <= segments; j++) {
        const index = (i * (segments + 1) + j) * 3
        const x = vertices[index]
        const z = vertices[index + 2]
        
        let noise = noise2D(x / 20, z / 20)
        noise = Math.pow(noise, 2) * height // Use power to create sharper peaks

        vertices[index + 1] = noise

        // 根据高度混合颜色，营造参考图片中的效果
        const color = new THREE.Color()
        const ratio = noise / height
        // 使用更陡峪的过渡，突出山峰的暖色
        const mixRatio = Math.pow(Math.max(0, ratio * 1.2 - 0.3), 1.5)
        color.lerpColors(snowColor, peakColor, mixRatio)
        
        colors.push(color.r, color.g, color.b)
      }
    }
    
    geom.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))
    geom.computeVertexNormals()
    return geom
  }, [])

  return (
    <mesh geometry={geometry} receiveShadow>
      <meshStandardMaterial 
        vertexColors={true}
        flatShading={true} 
        side={THREE.DoubleSide} 
      />
    </mesh>
  )
}
