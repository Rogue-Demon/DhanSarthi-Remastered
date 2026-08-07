import { QueryClient } from '@tanstack/react-query';
import { queryConfig } from '@/config';

export const queryClient = new QueryClient(queryConfig);

export default queryClient;
