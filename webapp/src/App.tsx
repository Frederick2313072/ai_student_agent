import { Canvas } from '@react-three/fiber'
import { Scene } from './components/canvas/Scene'

function App() {
  return (
    <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', zIndex: 0 }}>
      <Canvas camera={{ position: [20, 25, 20], fov: 25 }}>
        <Scene />
      </Canvas>
    </div>
  )
}

export default App
