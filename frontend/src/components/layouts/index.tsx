import Header from './Header';
import { Outlet, useLocation } from 'react-router-dom';
import SideNav from './SideNav';
import UnivModal from './UnivModal';
import { useEffect } from 'react';
import { ChatInputField } from 'components/common';
import { useSideNavAction } from 'stores/sideNavStore';
import { useChatStore } from 'stores/chatStore';

const Layout = () => {
  const { closeSideNav } = useSideNavAction();
  const { pathname } = useLocation();
  const { resetHistory } = useChatStore();

  useEffect(() => {
    if (pathname === '/') {
      resetHistory();
    }
    closeSideNav();
  }, [pathname]);

  return (
    <div
      className={`
        w-full h-svh pt-[74px] pb-[calc(2rem+23px)] px-
        bg-cover bg-center relative mx-auto
        flex flex-col items-center justify-center
        desktop:justify-center
        font-['NotoSansKR'] overflow-hidden
      `}
    >
      <UnivModal />
      <SideNav />
      <Header />
      <Outlet />
      <ChatInputField className='fixed bottom-8' />
    </div>
  );
};

export default Layout;
