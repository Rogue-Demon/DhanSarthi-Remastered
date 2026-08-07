import React, { createContext, useContext, useState } from 'react';

const ModalContext = createContext(null);

export function ModalPlaceholderProvider({ children }) {
  const [modal, setModal] = useState({ isOpen: false, type: null, props: {} });

  const openModal = (type, props = {}) => setModal({ isOpen: true, type, props });
  const closeModal = () => setModal({ isOpen: false, type: null, props: {} });

  return (
    <ModalContext.Provider value={{ modal, openModal, closeModal }}>
      {children}
    </ModalContext.Provider>
  );
}

export const useGlobalModal = () => useContext(ModalContext);
export default ModalPlaceholderProvider;
