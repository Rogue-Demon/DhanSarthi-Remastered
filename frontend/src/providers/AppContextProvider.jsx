import React, { useState } from 'react';
import { AppContext } from '@/contexts';

export function AppContextProvider({ children }) {
  const [appState, setAppState] = useState({
    initialized: true,
  });

  return (
    <AppContext.Provider value={{ appState, setAppState }}>
      {children}
    </AppContext.Provider>
  );
}

export default AppContextProvider;
