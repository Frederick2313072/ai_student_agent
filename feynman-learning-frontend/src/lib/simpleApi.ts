import axios, { AxiosInstance, AxiosResponse } from 'axios';
import type {
  StartLearningRequest,
  StartLearningResponse,
  ContinueConversationRequest,
  ContinueConversationResponse,
} from '@/types/api';

interface ApiError {
  code: string;
  message: string;
  details?: any;
}

class SimpleAPI {
  private client: AxiosInstance;

  constructor() {
    const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';
    
    this.client = axios.create({
      baseURL,
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
        
        const apiError: ApiError = {
          code: error.response?.data?.code || 'UNKNOWN_ERROR',
          message: error.response?.data?.detail || error.message || '未知错误',
          details: error.response?.data
        };
        
        return Promise.reject(apiError);
      }
    );
  }

  async startLearning(request: StartLearningRequest): Promise<StartLearningResponse> {
    const response = await this.client.post<StartLearningResponse>('/start_learning', request);
    return response.data;
  }

  async continueConversation(request: ContinueConversationRequest): Promise<ContinueConversationResponse> {
    const response = await this.client.post<ContinueConversationResponse>('/continue_conversation', request);
    return response.data;
  }

  async getHealth(): Promise<{status: string}> {
    const response = await this.client.get<{status: string}>('/health');
    return response.data;
  }
}

// 单例模式
export const simpleApi = new SimpleAPI();
export default simpleApi;
