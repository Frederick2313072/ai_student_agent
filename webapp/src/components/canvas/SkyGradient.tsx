import { useMemo } from 'react'
import * as THREE from 'three'

/**
 * 天空渐变背景组件，模拟参考图片中的黄昏天空效果
 */
export function SkyGradient() {
  const skyGeometry = useMemo(() => {
    const geometry = new THREE.SphereGeometry(100, 32, 32)
    
    // 创建顶点颜色数组
    const colors = []
    const positions = geometry.attributes.position.array
    
    // 定义渐变颜色
    const topColor = new THREE.Color('#b19cd9') // 顶部偏紫色
    const middleColor = new THREE.Color('#d4a5c4') // 中部粉紫色  
    const bottomColor = new THREE.Color('#ffd4cc') // 底部温暖色
    
    for (let i = 0; i < positions.length; i += 3) {
      const y = positions[i + 1]
      const normalizedY = (y + 100) / 200 // 归一化到0-1范围
      
      const color = new THREE.Color()
      if (normalizedY > 0.7) {
        // 上部：紫色到粉紫色
        const ratio = (normalizedY - 0.7) / 0.3
        color.lerpColors(middleColor, topColor, ratio)
      } else if (normalizedY > 0.3) {
        // 中部：保持粉紫色
        color.copy(middleColor)
      } else {
        // 下部：粉紫色到温暖色
        const ratio = normalizedY / 0.3
        color.lerpColors(bottomColor, middleColor, ratio)
      }
      
      colors.push(color.r, color.g, color.b)
    }
    
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))
    return geometry
  }, [])

  return (
    <mesh geometry={skyGeometry}>
      <meshBasicMaterial 
        vertexColors={true} 
        side={THREE.BackSide}
        fog={false}
      />
    </mesh>
  )
}
