import React, { useState } from 'react';
import { AuthContext } from '@/contexts';

export function AuthPlaceholderProvider({ children }) {
  const [user, setUser] = useState({
    name: 'Guest User',
    email: 'guest@dhansarthi.com',
  });
  const [isAuthenticated, setIsAuthenticated] = useState(true);

  const login = () => setIsAuthenticated(true);
  const logout = () => setIsAuthenticated(false);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export default AuthPlaceholderProvider;
