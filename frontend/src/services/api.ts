import axios from 'axios';
import type { UploadResponse, ProcessResponse, StatusResponse, ResultsResponse } from '../types/invoice';

// API bāzes URL
const API_BASE = 'http://165.232.112.180/api/v1';

// Axios instance ar pamata konfigurāciju
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000, // 30 sekundes timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// API servisa klase
export class InvoiceAPI {
  
  /**
   * Augšupielādē failu
   */
  static async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post<UploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  }
  
  /**
   * Sāk faila apstrādi
   */
  static async processFile(fileId: number): Promise<ProcessResponse> {
    const response = await api.post<ProcessResponse>(`/process/${fileId}`);
    return response.data;
  }
  
  /**
   * Iegūst apstrādes statusu
   */
  static async getStatus(fileId: number): Promise<StatusResponse> {
    const response = await api.get<StatusResponse>(`/process/${fileId}/status`);
    return response.data;
  }
  
  /**
   * Iegūst detalizētus rezultātus
   */
  static async getResults(fileId: number): Promise<ResultsResponse> {
    const response = await api.get<ResultsResponse>(`/process/${fileId}/results`);
    return response.data;
  }
  
  /**
   * Pārbauda servera statusu
   */
  static async healthCheck(): Promise<{ status: string }> {
    const response = await api.get('/health');
    return response.data;
  }

  /**
   * Atjaunina invoice ar labojumiem un veic automātisku mācīšanos
   */
  static async updateInvoiceWithCorrections(fileId: number, corrections: Record<string, any>): Promise<any> {
    const response = await api.put(`/update/${fileId}`, corrections);
    return response.data;
  }

  /**
   * Mācās no lietotāja labojumiem bez datu atjaunināšanas
   */
  static async learnFromCorrections(fileId: number, corrections: Record<string, any>): Promise<any> {
    const response = await api.post(`/learn/${fileId}`, corrections);
    return response.data;
  }

  /**
   * Iegūst mācīšanās statistiku
   */
  static async getLearningStatistics(): Promise<any> {
    const response = await api.get('/learning/statistics');
    return response.data;
  }

  /**
   * Iegūst detalizētu AI mācīšanās debug informāciju
   */
  static async getLearningDebugInfo(fileId: number): Promise<any> {
    const response = await api.get(`/learning/debug/${fileId}`);
    return response.data;
  }

  /**
   * Simulē mācīšanos bez saglabāšanas - parāda kas notiktu ar AI
   */
  static async simulateCorrectionLearning(fileId: number, corrections: Record<string, any>): Promise<any> {
    const response = await api.post(`/learning/simulate/${fileId}`, corrections);
    return response.data;
  }

  /**
   * Iegūst iepriekš ievadītās vērtības konkrētam laukam kā ieteikumus
   */
  static async getFieldSuggestions(fieldName: string, limit: number = 10): Promise<string[]> {
    const response = await api.get(`/field-suggestions/${fieldName}?limit=${limit}`);
    return response.data.suggestions || [];
  }
}

// Error handling utility
export const handleApiError = (error: any): string => {
  if (error.response) {
    // Server atbildēja ar error status
    return error.response.data?.detail || error.response.data?.message || 'Servera kļūda';
  } else if (error.request) {
    // Request tika nosūtīts bet nav atbildes
    return 'Nav savienojuma ar serveri';
  } else {
    // Kaut kas cits
    return error.message || 'Nezināma kļūda';
  }
};

export default api;
