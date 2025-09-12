import React from 'react'
import * as THREE from 'three'
import { useSpring, a } from '@react-spring/three'

type WisdomTreeProps = JSX.IntrinsicElements['group'] & {
  scale?: number
}

export function WisdomTree({ scale = 1, ...props }: WisdomTreeProps) {
  // 生长动画
  const { growScale } = useSpring({
    from: { growScale: 0 },
    to: { growScale: scale },
    config: { tension: 120, friction: 14 }
  })

  return (
    <a.group {...props} scale={growScale}>
      {/* 树干 - 金色渐变 */}
      <mesh position-y={1} castShadow>
        <cylinderGeometry args={[0.2, 0.3, 2, 8]} />
        <meshStandardMaterial color="#FFD700" metalness={0.3} roughness={0.7} />
      </mesh>
      
      {/* 树冠 - 发光的智慧果实 */}
      <mesh position-y={2.5} castShadow>
        <sphereGeometry args={[1, 12, 12]} />
        <meshStandardMaterial 
          color="#FFE5B4" 
          emissive="#FFD700" 
          emissiveIntensity={0.3}
          metalness={0.1}
          roughness={0.3}
        />
      </mesh>
      
      {/* 光环效果 */}
      <mesh position-y={2.5}>
        <torusGeometry args={[1.5, 0.05, 16, 100]} />
        <meshStandardMaterial 
          color="#FFFACD" 
          emissive="#FFD700" 
          emissiveIntensity={0.5}
          transparent
          opacity={0.6}
        />
      </mesh>
      
      {/* 智慧光点 */}
      {Array.from({ length: 5 }).map((_, i) => {
        const angle = (i / 5) * Math.PI * 2
        const radius = 0.8
        return (
          <mesh 
            key={i}
            position={[
              Math.cos(angle) * radius,
              2.5 + Math.sin(i * 1.5) * 0.3,
              Math.sin(angle) * radius
            ]}
          >
            <sphereGeometry args={[0.1, 8, 8]} />
            <meshStandardMaterial 
              color="#FFFFFF"
              emissive="#FFD700"
              emissiveIntensity={1}
            />
          </mesh>
        )
      })}
    </a.group>
  )
}
