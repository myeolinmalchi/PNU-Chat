import { useEffect, useState } from 'react';
import { useUnivModalStore } from 'stores/univModalStore';

const useUnivModalAnimation = () => {
  const { opened, openModal, closeModal } = useUnivModalStore();
  const [visible, setVisible] = useState(false);

  const zIndex = visible ? 'z-30' : 'z-[-999]';
  const opacity = opened ? 'opacity-100' : 'opacity-0';

  useEffect(() => {
    if (opened) {
      setVisible(true);
      return;
    }
    setTimeout(() => {
      setVisible(false);
    }, 300);
  }, [opened]);

  return {
    opened,
    openModal,
    closeModal,
    zIndex,
    opacity,
  };
};

export default useUnivModalAnimation;
