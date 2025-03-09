import { create } from 'zustand';

type UnivModalState = {
  opened: boolean;
  openModal: () => void;
  closeModal: () => void;
};

export const useUnivModalStore = create<UnivModalState>((set) => ({
  opened: false,
  openModal: () => set((prev) => ({ ...prev, opened: true })),
  closeModal: () => set((prev) => ({ ...prev, opened: false })),
}));
