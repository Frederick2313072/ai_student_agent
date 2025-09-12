import React, { useState } from 'react'
import * as THREE from 'three'
import { useSpring, a } from '@react-spring/three'
import { useGameStore } from '../../stores/gameStore'

type CabinProps = JSX.IntrinsicElements['group']

export function Cabin(props: CabinProps) {
  const [hovered, setHovered] = useState(false)

  const { scale, color, roofColor } = useSpring({
    scale: hovered ? 1.1 : 1,
    color: hovered ? '#d67548' : '#8b4513', // 参考图片中小屋的温暖红棕色
    roofColor: hovered ? '#654321' : '#5d2f0a', // 更深的屋顶颜色
  })

  return (
    <a.group 
      {...props} 
      scale={scale}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
      onClick={() => {
        const openChat = useGameStore.getState().openChat
        openChat('费曼学习法基础')
      }}
    >
      {/* Base */}
      <mesh position-y={0.5} castShadow>
        <boxGeometry args={[1, 1, 1.5]} />
        <a.meshStandardMaterial color={color} />
      </mesh>
      {/* Roof */}
      <mesh position-y={1.25} castShadow>
        <coneGeometry args={[0.9, 0.5, 4]} rotation={[0, THREE.MathUtils.degToRad(45), 0]} />
        <a.meshStandardMaterial color={roofColor} roughness={0.8} />
      </mesh>
    </a.group>
  )
}
