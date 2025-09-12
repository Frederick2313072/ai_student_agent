import { GameInstructions } from '../ui/GameInstructions'
import { Html } from '@react-three/drei'
import '../../index.css' // Re-import styles for the <Html> component context

export function UIBridge() {
  return (
    // This <Html> component is for global, non-positioned UI like the instructions
    <Html fullscreen style={{ pointerEvents: 'none' }}>
      <GameInstructions />
    </Html>
  )
}
