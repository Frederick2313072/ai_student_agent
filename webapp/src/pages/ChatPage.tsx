import { useState } from 'react'
import { streamChat } from '../lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const initialMessages: Message[] = [
  {
    role: 'assistant',
    content: "Hello! What knowledge would you like to share with me today?",
  },
]

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = { role: 'user', content: input }
    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)

    await streamChat({
      topic: 'General Knowledge', // Placeholder topic
      explanation: input,
      short_term_memory: newMessages.slice(-10), // Send last 10 messages as memory
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
  }

  return (
    <div className="flex h-full w-full items-center justify-center">
      {/* Centered Chat Panel */}
      <div className="flex h-4/5 w-3/5 flex-col rounded-lg border border-gray-300 bg-white/70 shadow-lg backdrop-blur-sm">
        {/* Header */}
        <div className="flex-shrink-0 rounded-t-lg bg-gray-100/80 p-4 border-b border-gray-300">
          <h1 className="text-lg font-semibold text-gray-800">AI Student Feynman</h1>
        </div>

        {/* Chat History */}
        <div className="flex-grow overflow-y-auto p-4">
          <div className="flex flex-col space-y-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-xs rounded-lg px-4 py-2 lg:max-w-md text-gray-800 ${
                    msg.role === 'user'
                      ? 'bg-blue-200'
                      : 'bg-gray-200'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Message Input */}
        <form onSubmit={handleSubmit} className="flex-shrink-0 rounded-b-lg bg-gray-100/80 p-4 border-t border-gray-300">
          <input
            type="text"
            placeholder={isLoading ? 'Thinking...' : 'Teach something...'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="w-full rounded bg-white p-2 text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-400"
            disabled={isLoading}
          />
        </form>
      </div>
    </div>
  )
}
