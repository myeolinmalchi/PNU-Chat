type UserInfoType = {
  university: string;
  department: string;
  major?: string;
  grade: number;
};

type UnivInfoType = {
  [univ: string]: string[];
};

export type { UserInfoType, UnivInfoType };
