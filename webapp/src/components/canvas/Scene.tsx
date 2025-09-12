import { useMemo } from 'react'
import { OrbitControls } from '@react-three/drei'
import { Terrain } from './Terrain'
import { CabinComplex } from './CabinComplex'
import { PineTree } from './PineTree'
import { WisdomTree } from './WisdomTree'
import { SkyGradient } from './SkyGradient'
import { createNoise2D } from 'simplex-noise'
import { useGameStore } from '../../stores/gameStore'
import { UIBridge } from './UIBridge'
import { CameraManager } from './CameraManager'
import { FocusedChat } from './FocusedChat'

function Forest() {
  const trees = useMemo(() => {
    const noise2D = createNoise2D()
    const treeData = []
    const treeCount = 200
    const mapSize = 40

    for (let i = 0; i < treeCount; i++) {
      const x = (Math.random() - 0.5) * mapSize
      const z = (Math.random() - 0.5) * mapSize
      
      let y = noise2D(x / 20, z / 20)
      y = Math.pow(y, 2) * 8 // Same noise function as terrain

      // Only place trees in the lower, "snowy" areas
      if (y < 2.5) {
        treeData.push({
          position: [x, y + 0.1, z], // 略高于地面，确保可见性
          scale: 1 + Math.random() * 0.8,
          rotation: Math.random() * Math.PI,
        })
      }
    }
    return treeData
  }, [])

  return (
    <group>
      {trees.map((tree, i) => (
        <PineTree 
          key={i} 
          position={tree.position as [number, number, number]} 
          scale={tree.scale} 
          rotation-y={tree.rotation}
        />
      ))}
    </group>
  )
}

export function Scene() {
  const wisdomTrees = useGameStore((state) => state.wisdomTrees)
  const cameraFocusTarget = useGameStore((state) => state.cameraFocusTarget)
  const isCameraAnimating = useGameStore((state) => state.isCameraAnimating)
  
  return (
    <>
      <CameraManager />
      {/* 天空渐变背景 */}
      <SkyGradient />
      <fog attach="fog" args={['#d4a5c4', 35, 80]} />

      {/* Lighting - 模拟参考图片的黄昏光照 */}
      <ambientLight intensity={0.3} color="#b8a5d4" />
      {/* 主光源：暖色夕阳光，从左上方照射 */}
      <directionalLight 
        position={[-20, 30, 15]} 
        intensity={2.2} 
        color="#ff8c69" 
        castShadow
        shadow-camera-far={100}
        shadow-camera-left={-30}
        shadow-camera-right={30}
        shadow-camera-top={30}
        shadow-camera-bottom={-30}
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      {/* 补光：冷色调环境反射光 */}
      <directionalLight 
        position={[10, 8, -15]} 
        intensity={0.4} 
        color="#9bb5d4" 
      />
      
      {/* Scenery */}
      <Terrain />
      <CabinComplex 
        position={[0, (() => {
          const noise2D = createNoise2D();
          const y = noise2D(0 / 20, 2 / 20);
          return Math.pow(y, 2) * 8 + 0.1; // 确保建筑群在地面之上
        })(), 2]} 
        scale={1.2}
      />
      <Forest />
      
      {/* 智慧之树 - 动态生成 */}
      {wisdomTrees.map((tree, index) => {
        const noise2D = createNoise2D();
        const x = tree.position[0];
        const z = tree.position[2];
        const y = Math.pow(noise2D(x / 20, z / 20), 2) * 8;
        
        return (
          <WisdomTree
            key={index}
            position={[x, y + 0.2, z]} // 确保智慧之树在地面之上
            scale={tree.scale}
          />
        )
      })}

      {/* Controls for development - 添加约束防止穿透地面 */}
      <OrbitControls 
        minDistance={5}
        maxDistance={100}
        minPolarAngle={0}
        maxPolarAngle={Math.PI / 2.2} // 限制最大俯视角度，防止穿透地面
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        enableDamping={true}
        dampingFactor={0.05}
        enabled={!isCameraAnimating}
      />
      <UIBridge />

      {cameraFocusTarget && <FocusedChat position={cameraFocusTarget} />}
    </>
  )
}
