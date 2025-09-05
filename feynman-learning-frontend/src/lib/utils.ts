import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function generateId(): string {
  return Math.random().toString(36).substr(2, 9)
}

export function formatTimestamp(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatScore(score: number, max: number = 5): string {
  return `${score.toFixed(1)}/${max}`
}

export function getScoreColor(score: number, max: number = 5): string {
  const normalized = score / max
  if (normalized >= 0.8) return 'text-score-excellent'
  if (normalized >= 0.6) return 'text-score-good'
  if (normalized >= 0.4) return 'text-score-average'
  return 'text-score-poor'
}

export function getScoreBgColor(score: number, max: number = 5): string {
  const normalized = score / max
  if (normalized >= 0.8) return 'bg-score-excellent'
  if (normalized >= 0.6) return 'bg-score-good'
  if (normalized >= 0.4) return 'bg-score-average'
  return 'bg-score-poor'
}

export function getRoleColor(role: string): string {
  switch (role) {
    case 'student': return 'text-student'
    case 'teacher': return 'text-teacher'
    case 'system': return 'text-system'
    case 'user': return 'text-foreground'
    default: return 'text-muted-foreground'
  }
}

export function getRoleBgColor(role: string): string {
  switch (role) {
    case 'student': return 'bg-student/10'
    case 'teacher': return 'bg-teacher/10'
    case 'system': return 'bg-system/10'
    case 'user': return 'bg-primary/10'
    default: return 'bg-muted/10'
  }
}

export function getPhaseLabel(phase: string): string {
  const phaseLabels = {
    'EXTRACT': '知识提取',
    'PROBE': '问题生成',
    'PROBE_ASK': '提问',
    'USER_ANSWER': '回答',
    'TEACH_EVAL': '教师评估',
    'CLOSE': '总结'
  }
  return phaseLabels[phase as keyof typeof phaseLabels] || phase
}

export function getQuestionTypeLabel(type: string): string {
  const typeLabels = {
    'concept': '概念',
    'mechanism': '机制',
    'application': '应用',
    'comparison': '对比',
    'boundary': '边界'
  }
  return typeLabels[type as keyof typeof typeLabels] || type
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}
