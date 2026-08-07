import { STORAGE_KEYS } from '@/constants';

export const requestInterceptor = (options) => {
  const token = localStorage.getItem(STORAGE_KEYS.AUTH);
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${JSON.parse(token)}`;
  }
  
  return {
    ...options,
    headers,
  };
};

export const responseInterceptor = async (response) => {
  if (response.status === 401) {
    localStorage.removeItem(STORAGE_KEYS.AUTH);
    console.warn('Unauthorized request! Session expired.');
  }
  return response;
};

export default {
  request: requestInterceptor,
  response: responseInterceptor,
};
