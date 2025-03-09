import { useEffect, useState } from 'react';
import { useSideNavOpened } from 'stores/sideNavStore';

const useSideNavAnimation = () => {
  const opened = useSideNavOpened();
  const [visible, setVisible] = useState(false);

  const zIndex = visible ? 'z-10' : 'z-[-999]';
  const opacity = opened ? 'opacity-100' : 'opacity-0';
  const translateX = opened ? 'translate-x-0' : 'translate-x-[100%]';

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
    zIndex,
    opacity,
    translateX,
  };
};

export default useSideNavAnimation;
