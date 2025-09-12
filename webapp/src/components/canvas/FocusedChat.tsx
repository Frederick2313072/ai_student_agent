import { Html } from "@react-three/drei";
import { ChatModal } from "../ui/ChatModal";

type FocusedChatProps = JSX.IntrinsicElements['group']

export function FocusedChat(props: FocusedChatProps) {
  return (
    <group {...props}>
      {/* Position the Html component above the cabin's origin */}
      <Html 
        position={[0, 3, 0]} // y-offset to appear above the cabin
        center
        distanceFactor={10} // Makes it smaller so it feels like it's in the world
        // occlude="blending" // This can be performance intensive, enable if needed
        className="w-[800px] pointer-events-none" // Set a fixed width for the container
      >
        <ChatModal />
      </Html>
    </group>
  )
}
