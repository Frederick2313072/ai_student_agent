import { useEffect } from 'react'
import { useThree } from '@react-three/fiber'
import { useGameStore } from '../../stores/gameStore'
import * as THREE from 'three'
import { useSpring } from '@react-spring/three'

const DEFAULT_CAMERA_POSITION = new THREE.Vector3(20, 25, 20)
const DEFAULT_CAMERA_TARGET = new THREE.Vector3(0, 0, 0)

export function CameraManager() {
  const { controls } = useThree()
  const { cameraFocusTarget, setCameraAnimating, isCameraAnimating } = useGameStore()

  const [{ pos, target }, api] = useSpring(() => ({
    pos: DEFAULT_CAMERA_POSITION.toArray(),
    target: DEFAULT_CAMERA_TARGET.toArray(),
    config: { mass: 1.5, tension: 170, friction: 80, precision: 0.0001 },
  }))

  useEffect(() => {
    let newPos: THREE.Vector3
    let newTarget: THREE.Vector3

    if (cameraFocusTarget) {
      newTarget = new THREE.Vector3().fromArray(cameraFocusTarget)
      // A much more cinematic and effective camera angle
      newPos = new THREE.Vector3(
        newTarget.x,
        newTarget.y + 4,
        newTarget.z + 8
      )
    } else {
      newPos = DEFAULT_CAMERA_POSITION
      newTarget = DEFAULT_CAMERA_TARGET
    }

    api.start({
      pos: newPos.toArray(),
      target: newTarget.toArray(),
      onRest: () => {
        // When animation is done, re-enable controls
        if (controls) {
          controls.enabled = true
        }
        setCameraAnimating(false)
      },
    })
  }, [cameraFocusTarget, api, setCameraAnimating, controls])

  // Apply the animated values to the camera and controls on every frame
  useThree((state) => {
    if (isCameraAnimating && state.controls) {
      const currentPos = new THREE.Vector3(...pos.get())
      const currentTarget = new THREE.Vector3(...target.get())
      
      state.camera.position.copy(currentPos)
      state.controls.target.copy(currentTarget)
    }
  })

  return null
}
