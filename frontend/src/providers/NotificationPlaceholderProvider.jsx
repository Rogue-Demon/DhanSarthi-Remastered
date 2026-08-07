import React, { createContext, useContext } from 'react';

const NotificationContext = createContext(null);

export function NotificationPlaceholderProvider({ children }) {
  const showNotification = (message, type = 'info') => {
    console.log(`[Notification] [${type.toUpperCase()}] ${message}`);
  };

  return (
    <NotificationContext.Provider value={{ showNotification }}>
      {children}
    </NotificationContext.Provider>
  );
}

export const useNotification = () => useContext(NotificationContext);
export default NotificationPlaceholderProvider;
