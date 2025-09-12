import { useState } from 'react'
import { useSpring, a } from '@react-spring/three'
import { useGameStore } from '../../stores/gameStore'
import type { ThreeEvent } from '@react-three/fiber'

type CabinComplexProps = JSX.IntrinsicElements['group']

/**
 * 小屋建筑群组件，模拟参考图片中的主要建筑和附属建筑
 */
export function CabinComplex(props: CabinComplexProps) {
  const [hovered, setHovered] = useState(false)

  const { scale, color, roofColor } = useSpring({
    scale: hovered ? 1.05 : 1,
    color: hovered ? '#d67548' : '#8b4513', // 温暖红棕色
    roofColor: hovered ? '#654321' : '#5d2f0a', // 深色屋顶
  })

  const openChat = (event: ThreeEvent<MouseEvent>) => {
    event.stopPropagation()
    const store = useGameStore.getState()
    // We need to provide the cabin's position to focus the camera
    if (props.position) {
      store.openChat('费曼学习法基础', props.position as [number, number, number])
    } else {
      console.error("Cabin position is not defined!")
    }
  }

  return (
    <a.group 
      {...props} 
      scale={scale}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
      onClick={openChat}
    >
      {/* 主屋 */}
      <group>
        {/* 主屋基座 */}
        <mesh 
          position={[0, 0.6, 0]} 
          castShadow
          onClick={openChat}
          onPointerOver={() => setHovered(true)}
          onPointerOut={() => setHovered(false)}
        >
          <boxGeometry args={[1.2, 1.2, 1.8]} />
          <a.meshStandardMaterial color={color} roughness={0.8} />
        </mesh>
        {/* 主屋屋顶 */}
        <mesh 
          position={[0, 1.45, 0]} 
          castShadow
          onClick={openChat}
          onPointerOver={() => setHovered(true)}
          onPointerOut={() => setHovered(false)}
        >
          <coneGeometry args={[1, 0.6, 4]} />
          <a.meshStandardMaterial color={roofColor} roughness={0.9} />
        </mesh>
        {/* 烟囱 */}
        <mesh position={[0.4, 1.9, -0.3]} castShadow>
          <boxGeometry args={[0.15, 0.4, 0.15]} />
          <meshStandardMaterial color="#666" roughness={0.9} />
        </mesh>
      </group>

      {/* 附属建筑 - 参考图片右侧的小建筑 */}
      <group position={[1.8, 0, 0.5]}>
        <mesh position={[0, 0.4, 0]} castShadow>
          <boxGeometry args={[0.8, 0.8, 1]} />
          <a.meshStandardMaterial color={color} roughness={0.8} />
        </mesh>
        <mesh position={[0, 0.95, 0]} castShadow>
          <coneGeometry args={[0.6, 0.4, 4]} />
          <a.meshStandardMaterial color={roofColor} roughness={0.9} />
        </mesh>
      </group>

      {/* 小木棚 */}
      <group position={[-1.2, 0, -0.5]}>
        <mesh position={[0, 0.3, 0]} castShadow>
          <boxGeometry args={[0.6, 0.6, 0.8]} />
          <a.meshStandardMaterial color={color} roughness={0.8} />
        </mesh>
        <mesh position={[0, 0.75, 0]} castShadow>
          <boxGeometry args={[0.7, 0.1, 0.9]} />
          <a.meshStandardMaterial color={roofColor} roughness={0.9} />
        </mesh>
      </group>

      {/* 装饰性栅栏 */}
      {Array.from({ length: 8 }).map((_, i) => {
        const angle = (i / 8) * Math.PI * 2
        const radius = 2.5
        return (
          <mesh 
            key={i}
            position={[
              Math.cos(angle) * radius,
              0.25,
              Math.sin(angle) * radius
            ]}
            castShadow
          >
            <boxGeometry args={[0.08, 0.5, 0.08]} />
            <meshStandardMaterial color="#4a3429" roughness={0.9} />
          </mesh>
        )
      })}

      {/* 小径的石头标记 */}
      <mesh position={[0, -0.05, 3]} receiveShadow>
        <cylinderGeometry args={[0.3, 0.3, 0.1, 8]} />
        <meshStandardMaterial color="#888" roughness={0.9} />
      </mesh>
      <mesh position={[0.5, -0.05, 2.2]} receiveShadow>
        <cylinderGeometry args={[0.25, 0.25, 0.1, 8]} />
        <meshStandardMaterial color="#777" roughness={0.9} />
      </mesh>
    </a.group>
  )
}
