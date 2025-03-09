import { ChangeEvent, useEffect, useState } from 'react';
import { useUnivModalStore } from 'stores/univModalStore';
import { useUserInfoStore } from 'stores/userInfoStore';
import { UserInfoType } from 'types/user';

const useUnivModal = () => {
  const [univ, setUniv] = useState<string | null>(null);
  const [department, setDepartment] = useState<string | null>(null);

  const { getUniversities, getDepartments, loadUnivInfo, setUserInfo } =
    useUserInfoStore();

  const { closeModal } = useUnivModalStore();

  useEffect(() => {
    loadUnivInfo();
  }, []);

  const universities = getUniversities();
  const departments = univ ? getDepartments(univ) : null;

  const handleSelectUniv = (e: ChangeEvent<HTMLSelectElement>) =>
    setUniv(e.target.value);
  const handleSelectDepartment = (e: ChangeEvent<HTMLSelectElement>) =>
    setDepartment(e.target.value);

  const submitEnabled = !!univ && !!department;

  const handleSubmit = () => {
    if (!submitEnabled) {
      return;
    }

    const userInfo: UserInfoType = {
      university: univ,
      department,
      grade: 2,
    };

    setUserInfo(userInfo);
    closeModal();
  };

  return {
    submitEnabled,
    universities,
    departments,

    selected: {
      univ,
      department,
    },
    handlers: {
      handleSelectUniv,
      handleSelectDepartment,
      handleSubmit,
    },
  };
};

export default useUnivModal;
