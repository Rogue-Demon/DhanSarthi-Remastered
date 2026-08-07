import { envConfig } from '@/config';
import { requestInterceptor, responseInterceptor } from './interceptors';

export const apiClient = {
  request: async (url, options = {}) => {
    const fullUrl = `${envConfig.apiBaseUrl}${url}`;
    const interceptedOptions = requestInterceptor(options);
    
    try {
      const response = await fetch(fullUrl, interceptedOptions);
      const processedResponse = await responseInterceptor(response);
      
      if (!processedResponse.ok) {
        throw new Error(`HTTP error! status: ${processedResponse.status}`);
      }
      
      return await processedResponse.json();
    } catch (error) {
      console.error(`API Request to ${url} failed:`, error);
      throw error;
    }
  },
  get: (url, options = {}) => apiClient.request(url, { ...options, method: 'GET' }),
  post: (url, data, options = {}) => apiClient.request(url, { ...options, method: 'POST', body: JSON.stringify(data) }),
  put: (url, data, options = {}) => apiClient.request(url, { ...options, method: 'PUT', body: JSON.stringify(data) }),
  delete: (url, options = {}) => apiClient.request(url, { ...options, method: 'DELETE' }),
};

export default apiClient;
