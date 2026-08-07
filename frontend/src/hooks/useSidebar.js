import { useSidebarStore } from '@/store';

export const useSidebar = () => {
  const {
    expanded,
    collapsed,
    mobileOpen,
    setExpanded,
    setCollapsed,
    toggleSidebar,
    setMobileOpen,
    toggleMobileOpen,
  } = useSidebarStore();

  return {
    expanded,
    collapsed,
    mobileOpen,
    setExpanded,
    setCollapsed,
    toggleSidebar,
    setMobileOpen,
    toggleMobileOpen,
  };
};

export default useSidebar;
