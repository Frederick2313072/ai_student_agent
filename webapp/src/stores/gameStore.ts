import { create } from 'zustand'

interface GameState {
  // 聊天界面状态
  isChatOpen: boolean
  currentTopic: string
  
  // 游戏世界状态
  wisdomTrees: { position: [number, number, number]; scale: number }[]
  completedTopics: string[]
  
  // 相机状态
  cameraFocusTarget: [number, number, number] | null
  isCameraAnimating: boolean

  // 动作
  openChat: (topic: string, position: [number, number, number]) => void
  closeChat: () => void
  addWisdomTree: (position: [number, number, number]) => void
  completeTopicTeaching: (topic: string) => void
  setCameraAnimating: (isAnimating: boolean) => void
}

export const useGameStore = create<GameState>((set) => ({
  // 初始状态
  isChatOpen: false,
  currentTopic: '',
  wisdomTrees: [],
  completedTopics: [],
  cameraFocusTarget: null,
  isCameraAnimating: false,
  
  // 动作实现
  openChat: (topic, position) => set({ 
    isChatOpen: true, 
    currentTopic: topic,
    cameraFocusTarget: position,
    isCameraAnimating: true,
  }),

  closeChat: () => set({ 
    isChatOpen: false,
    cameraFocusTarget: null,
    isCameraAnimating: true,
  }),
  
  setCameraAnimating: (isAnimating: boolean) => set({ isCameraAnimating: isAnimating }),

  addWisdomTree: (position) => 
    set((state) => ({
      wisdomTrees: [...state.wisdomTrees, { position, scale: 0.8 + Math.random() * 0.4 }]
    })),
    
  completeTopicTeaching: (topic) =>
    set((state) => ({
      completedTopics: [...state.completedTopics, topic]
    }))
}))
