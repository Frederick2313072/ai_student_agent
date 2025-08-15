import axios, { AxiosInstance, AxiosResponse } from 'axios';
import type {
  StartLearningRequest,
  StartLearningResponse,
  ContinueConversationRequest,
  ContinueConversationResponse,
  SessionSummaryResponse
} from '@/types/api';
import type { ApiError } from '@/types';

class FeynmanAPI {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('[API] Request error:', error);
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`[API] Response:`, response.status, response.data);
        return response;
      },
      (error) => {
        console.error('[API] Response error:', error);
        
        // 统一错误处理
        const apiError: ApiError = {
          code: error.response?.data?.code || 'UNKNOWN_ERROR',
          message: error.response?.data?.detail || error.message || '未知错误',
          details: error.response?.data
        };
        
        return Promise.reject(apiError);
      }
    );
  }

  // 会话管理
  async startLearning(request: StartLearningRequest): Promise<StartLearningResponse> {
    const response = await this.client.post<StartLearningResponse>('/start_learning', request);
    return response.data;
  }

  async continueConversation(request: ContinueConversationRequest): Promise<ContinueConversationResponse> {
    const response = await this.client.post<ContinueConversationResponse>('/continue_conversation', request);
    return response.data;
  }

  async getNextQuestion(sessionId: string): Promise<NextQuestionResponse> {
    const response = await this.client.post<NextQuestionResponse>('/continue_conversation', {
      session_id: sessionId,
      user_input: "" // 获取下一个问题
    });
    return response.data;
  }

  async submitAnswer(request: SubmitAnswerRequest): Promise<SubmitAnswerResponse> {
    const response = await this.client.post<SubmitAnswerResponse>('/continue_conversation', {
      session_id: request.sessionId,
      user_input: request.answer
    });
    return response.data;
  }

  async requestEvaluation(sessionId: string): Promise<EvaluationResponse> {
    // 注意：后端可能没有单独的评估端点，可能需要通过continue_conversation实现
    const response = await this.client.post<EvaluationResponse>('/continue_conversation', {
      session_id: sessionId,
      user_input: "请进行评估" // 触发评估
    });
    return response.data;
  }

  // 数据获取
  async getSessionReport(sessionId: string): Promise<SessionReport> {
    const response = await this.client.get<SessionReport>(`/session_summary/${sessionId}`);
    return response.data;
  }

  async getGraphData(sessionId: string): Promise<GraphResponse> {
    // 注意：后端可能没有图谱端点，这里先使用会话摘要
    const response = await this.client.get<GraphResponse>(`/session_summary/${sessionId}`);
    return response.data;
  }

  // 健康检查
  async getStatus(): Promise<StatusResponse> {
    const response = await this.client.get<StatusResponse>('/status');
    return response.data;
  }

  async getHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health', {
      baseURL: process.env.NEXT_PUBLIC_SSE_BASE_URL || 'http://localhost:8000'
    });
    return response.data;
  }

  // SSE连接URL
  getSSEUrl(sessionId: string, types?: string[]): string {
    const baseUrl = process.env.NEXT_PUBLIC_SSE_BASE_URL || 'http://localhost:8000';
    const url = new URL(`${baseUrl}/api/v1/single_round/stream/${sessionId}`);
    
    if (types && types.length > 0) {
      url.searchParams.set('types', types.join(','));
    }
    
    return url.toString();
  }

  // 重试机制
  async withRetry<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> {
    let lastError: any;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;
        
        if (attempt === maxRetries) {
          throw lastError;
        }
        
        console.warn(`[API] Attempt ${attempt} failed, retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        
        // 指数退避
        delay *= 2;
      }
    }
    
    throw lastError;
  }
}

// 单例模式
export const api = new FeynmanAPI();
export default api;
