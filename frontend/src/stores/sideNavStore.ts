import { create } from 'zustand';

interface SideNavState {
  hamburgerOpened: boolean;
}

interface SideNavAction {
  actions: {
    toggleSideNav: () => void;
    closeSideNav: () => void;
    openSideNav: () => void;
  };
}

const initialState = {
  hamburgerOpened: false,
};

export const useSideNavStore = create<SideNavState & SideNavAction>((set) => {
  return {
    ...initialState,
    actions: {
      toggleSideNav: () =>
        set(({ hamburgerOpened }) => ({ hamburgerOpened: !hamburgerOpened })),
      openSideNav: () => set(() => ({ hamburgerOpened: true })),
      closeSideNav: () => set(() => ({ hamburgerOpened: false })),
    },
  };
});

export const useSideNavOpened = () =>
  useSideNavStore(({ hamburgerOpened }) => hamburgerOpened);

export const useSideNavAction = () => useSideNavStore(({ actions }) => actions);
