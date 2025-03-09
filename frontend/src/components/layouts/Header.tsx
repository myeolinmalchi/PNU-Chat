import signature from 'assets/images/signature.png';
import hamburgerOpen from 'assets/images/icons/sidenav-open.svg';
import newChat from 'assets/images/icons/new-chat.svg';
import { useSideNavAction } from 'stores/sideNavStore';
import { Link } from 'react-router-dom';

const Header = () => {
  const { openSideNav } = useSideNavAction();
  return (
    <div className='fixed top-0 w-full px-5 bg-white flex items-center justify-between h-[74px]'>
      <Link to='/'>
        <img className='w-[97px]' src={signature} alt='부산대학교 챗봇' />
      </Link>
      <div className='flex items-center justify-between gap-3.5'>
        <Link to='/'>
          <img src={newChat} />
        </Link>
        <button onClick={openSideNav}>
          <img src={hamburgerOpen} />
        </button>
      </div>
    </div>
  );
};

export default Header;
