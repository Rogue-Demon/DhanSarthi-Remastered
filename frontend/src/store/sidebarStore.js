import { create } from 'zustand';

export const useSidebarStore = create((set) => ({
  expanded: true,
  collapsed: false,
  mobileOpen: false,
  setExpanded: (expanded) => set({ expanded, collapsed: !expanded }),
  setCollapsed: (collapsed) => set({ collapsed, expanded: !collapsed }),
  toggleSidebar: () => set((state) => ({ 
    expanded: !state.expanded, 
    collapsed: !state.collapsed 
  })),
  setMobileOpen: (mobileOpen) => set({ mobileOpen }),
  toggleMobileOpen: () => set((state) => ({ mobileOpen: !state.mobileOpen })),
}));

export default useSidebarStore;
