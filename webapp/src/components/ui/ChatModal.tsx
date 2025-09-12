import React, { useState, useEffect } from 'react'
import { useGameStore } from '../../stores/gameStore'
import { streamChat } from '../../lib/api'
import styles from './ChatModal.module.css' // Final styles

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function ChatModal() {
  const { isChatOpen, currentTopic, closeChat, addWisdomTree, completeTopicTeaching } = useGameStore()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // 重置聊天内容当打开新话题时
  useEffect(() => {
    if (isChatOpen && currentTopic) {
      setMessages([{
        role: 'assistant',
        content: `你好！我想学习关于"${currentTopic}"的知识。你能用简单的语言教教我吗？`
      }])
    }
  }, [isChatOpen, currentTopic])

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = { role: 'user', content: input }
    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)

    await streamChat({
      topic: currentTopic,
      explanation: input,
      short_term_memory: newMessages.slice(-10),
      onReady: () => {
        setMessages((prev) => [...prev, { role: 'assistant', content: '' }])
      },
      onChunk: (chunk) => {
        setMessages((prev) => {
          const lastMessage = prev[prev.length - 1]
          if (lastMessage && lastMessage.role === 'assistant') {
            return [
              ...prev.slice(0, -1),
              { ...lastMessage, content: lastMessage.content + chunk },
            ]
          }
          return prev
        })
      },
    })

    setIsLoading(false)
    
    // 简单的教学评估：如果回复超过50个字，认为是一次成功的教学
    if (input.length > 50) {
      // 在小屋附近添加一棵智慧之树
      addWisdomTree([Math.random() * 6 - 3, 0, 2 + Math.random() * 4])
      completeTopicTeaching(currentTopic)
    }
  }

  if (!isChatOpen) return null

  return (
    <div className={styles.modalContainer}>
      {/* 聊天窗口 - 魔法书风格 */}
      <div className={styles.magicBook}>
        {/* 标题栏 */}
        <div className={styles.header}>
          <div>
            <h2 className={styles.title}>
              📖 智慧传承
            </h2>
            <p className={styles.subtitle}>{currentTopic}</p>
          </div>
          <button onClick={closeChat} className={styles.closeButton}>×</button>
        </div>
        
        {/* 聊天内容 */}
        <div className={styles.chatContent}>
          {messages.map((msg, i) => (
            <div key={i} className={`${styles.messageContainer} ${msg.role === 'user' ? styles.userMessage : styles.assistantMessage}`}>
              <div className={`${styles.messageBubble} ${msg.role === 'user' ? styles.userBubble : styles.assistantBubble}`}>
                <div className={styles.role}>
                  {msg.role === 'user' ? '🧙‍♂️ 导师' : '📚 学生'}
                </div>
                <div>{msg.content}</div>
              </div>
            </div>
          ))}
        </div>
        
        {/* 输入框 */}
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.inputContainer}>
            <input
              type="text"
              placeholder={isLoading ? '🤔 学生正在思考...' : '✨ 传授你的智慧...'}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className={styles.input}
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className={styles.submitButton}
            >
              📜 传授
            </button>
          </div>
          <div className={styles.hint}>
            💡 提示：详细的解释（50字以上）将在世界中种下智慧之树 🌳
          </div>
        </form>
      </div>
    </div>
  )
}
