import { useSideNavAction } from 'src/stores/sideNavStore';
import { twMerge } from 'tailwind-merge';
import { Link } from 'react-router-dom';
import signatureWhite from 'assets/images/signature-white.png';

import sideNavClose from 'assets/images/icons/sidenav-close.svg';
import settings from 'assets/images/icons/sidenav-settings.svg';
import useSideNavAnimation from 'hooks/useSideNavAnimation';
import { ChatListElementType } from 'types/chat';
import { useUserInfoStore } from 'stores/userInfoStore';
import { useUnivModalStore } from 'stores/univModalStore';
import { useChatStore } from 'stores/chatStore';

const UserInfoArea = () => {
  const { info } = useUserInfoStore();
  return (
    <div className='w-full flex flex-col gap-2 items-center justify-start text-white font-[400]'>
      <div className='w-full flex flex-row gap-3 items-center justify-between'>
        <span className='text-[12px] w-[48px]'>단과대학</span>
        <span className='text-[16px] flex-1'>
          {info?.university ?? '미입력'}
        </span>
      </div>
      <div className='w-full flex flex-row gap-3 items-center justify-between'>
        <span className='text-[12px] w-[48px]'>학과</span>
        <span className='text-[16px] flex-1'>
          {info?.department ?? '미입력'}
        </span>
      </div>
    </div>
  );
};

type ChatItemProps = {
  chat: ChatListElementType;
};

const ChatItem = ({ chat }: ChatItemProps) => {
  const { title, createdAt, uuid } = chat;

  const date = new Date(createdAt);
  const yy = date.getFullYear();
  const mm = (date.getMonth() + 1).toString().padStart(2, '0');
  const dd = date.getDate().toString().padStart(2, '0');

  const dateStr = `${yy}-${mm}-${dd}`;

  return (
    <Link
      to={`/chats/${encodeURIComponent(uuid)}`}
      className='flex flex-col items-start justify-center gap-1.5 px-3 py-2.5 w-full rounded-[0.25rem] bg-white'
    >
      <span className='text-point-3 text-sm font-[600]'>{title}</span>
      <span className='text-xs text-secondary font-[400]'>{dateStr}</span>
    </Link>
  );
};

const SideNav = () => {
  const { closeSideNav } = useSideNavAction();
  const { zIndex, opacity, translateX } = useSideNavAnimation();

  const { chats } = useChatStore();
  const { openModal } = useUnivModalStore();

  const onClickSettingsHandler = () => {
    closeSideNav();
    openModal();
  };

  return (
    <>
      <div
        onClick={closeSideNav}
        className={twMerge(
          'absolute w-full h-full top-0 bg-[rgba(25,25,25,0.50)] transition-opacity duration-300',
          zIndex,
          opacity
        )}
      ></div>
      <div
        className={twMerge(
          'absolute w-[70%] max-w-[320px] top-0 right-0 h-full bg-point-1 z-20 transition-all duration-300',
          'px-5 pt-6 pb-9 flex flex-col items-start justify-start gap-y-6',
          translateX
        )}
      >
        <div className='flex items-center justify-between w-full'>
          <button onClick={onClickSettingsHandler}>
            <img src={settings} />
          </button>
          <button onClick={closeSideNav}>
            <img src={sideNavClose} />
          </button>
        </div>
        <UserInfoArea />
        {chats.length > 0 ? (
          <div className='w-full flex flex-col items-start justify-start gap-3 flex-1 overflow-y-auto rounded-[0.25rem]'>
            {chats.map((chat) => (
              <ChatItem key={chat.uuid} chat={chat} />
            ))}
          </div>
        ) : (
          <div className='w-full flex items-start justify-center flex-1 overflow-y-auto text-white text-[12px] font-[400] h-full'>
            <span className='absolute top-[40%]'>검색 내역이 없습니다.</span>
          </div>
        )}

        <div className='w-full flex flex-col gap-[8px]'>
          <img className='w-[125px]' src={signatureWhite} />
          <span className='text-[8px] text-white font-[400]'>
            2, Busandaehak-ro 63beon-gil Geumjeong-gu, Busan 46241
          </span>
        </div>
      </div>
    </>
  );
};

export default SideNav;
