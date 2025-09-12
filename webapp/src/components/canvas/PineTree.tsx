import React from 'react'

type PineTreeProps = JSX.IntrinsicElements['group']

export function PineTree(props: PineTreeProps) {
  return (
    <group {...props}>
      {/* Trunk - 树干 */}
      <mesh position-y={0.5} castShadow>
        <boxGeometry args={[0.2, 1, 0.2]} />
        <meshStandardMaterial color="#4a3429" roughness={0.9} />
      </mesh>
      {/* Leaves - 松叶，参考图片中的深绿色 */}
      <mesh position-y={1.25} castShadow>
        <coneGeometry args={[0.5, 0.5, 4]} />
        <meshStandardMaterial 
          color="#1a5d1a" 
          roughness={0.8} 
          metalness={0.1}
        />
      </mesh>
      <mesh position-y={1.75} castShadow>
        <coneGeometry args={[0.4, 0.5, 4]} />
        <meshStandardMaterial 
          color="#1e6b1e" 
          roughness={0.8}
          metalness={0.1}
        />
      </mesh>
    </group>
  )
}
