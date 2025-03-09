import { UnivInfoType, UserInfoType } from 'types/user';
import { create } from 'zustand';

interface UserInfoState {
  info: UserInfoType | null;
  allUnivInfo: UnivInfoType | null;

  loadUnivInfo: () => Promise<void>;

  getUniversities: () => string[];
  getDepartments: (univ: string) => string[];

  setUserInfo: (param: UserInfoType) => void;
  resetUserInfo: () => void;
}

const loadUserInfo = () => {
  const userInfoString = localStorage.getItem('user');
  if (!userInfoString) {
    return null;
  }

  const userInfo: UserInfoType = JSON.parse(userInfoString);
  return userInfo;
};

export const useUserInfoStore = create<UserInfoState>((set, get) => ({
  info: loadUserInfo(),
  allUnivInfo: null,
  loadUnivInfo: async () => {
    fetch('/api/universities')
      .then((res) => {
        if (res.status === 200) {
          return res.json();
        }
      })
      .then((body) => {
        const univInfos: UnivInfoType = body;
        set((prev) => ({ ...prev, allUnivInfo: univInfos }));
      });
  },

  getUniversities: () => {
    const univInfos = get().allUnivInfo;
    if (univInfos) {
      return Object.keys(univInfos);
    }
    return [];
  },

  getDepartments: (univ: string) => {
    const univInfos = get().allUnivInfo;
    if (univInfos) {
      return univInfos[univ];
    }
    return [];
  },

  setUserInfo: (param: UserInfoType) => {
    set((prev) => ({ ...prev, info: param }));
    localStorage.setItem('user', JSON.stringify(param));
  },

  resetUserInfo: () => set((prev) => ({ ...prev, info: null })),
}));
