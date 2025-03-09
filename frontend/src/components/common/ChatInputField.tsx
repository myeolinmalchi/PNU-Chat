import sendButton from 'assets/images/icons/send-chat.svg';
import useChatForm from 'hooks/useChatForm';
import { useUnivModalStore } from 'stores/univModalStore';
import { useUserInfoStore } from 'stores/userInfoStore';
import { twMerge } from 'tailwind-merge';

type ChatInputField = {
  placeholder?: string;
  className?: string;
};

const InputFieldBlocker = () => {
  const { openModal } = useUnivModalStore();
  return (
    <button
      onClick={openModal}
      className='w-full h-[46px] rounded-full border-[1px] border-[#005BAA] flex items-center justify-center pl-[18px] pr-[7px] gap-[6px] bg-[#005BAA] shadow-[0px_0px_4px_0px_rgba(0,0,0,0.20)] text-center text-white text-[12px] font-[400] active:bg-[#004785] transition-colors'
    >
      소속 단과대학과 학과를 먼저 설정해주세요
      <svg
        width='14'
        height='14'
        viewBox='0 0 14 14'
        fill='none'
        xmlns='http://www.w3.org/2000/svg'
      >
        <path
          d='M9.69908 7.4375H3.0625C2.93835 7.4375 2.83442 7.3956 2.75071 7.3118C2.6669 7.22809 2.625 7.12416 2.625 7C2.625 6.87585 2.6669 6.77192 2.75071 6.68821C2.83442 6.60441 2.93835 6.5625 3.0625 6.5625H9.69908L6.68369 3.54711C6.59697 3.46039 6.55414 3.35889 6.55521 3.24261C6.55638 3.12633 6.60217 3.02293 6.69258 2.93242C6.7831 2.84793 6.88557 2.80418 7 2.80117C7.11443 2.79816 7.2169 2.84191 7.30742 2.93242L11.0059 6.6309C11.0605 6.68554 11.099 6.74314 11.1214 6.80371C11.1439 6.86428 11.1551 6.92971 11.1551 7C11.1551 7.0703 11.1439 7.13573 11.1214 7.1963C11.099 7.25687 11.0605 7.31447 11.0059 7.36911L7.30742 11.0676C7.22662 11.1484 7.12658 11.1897 7.00729 11.1915C6.888 11.1934 6.7831 11.1521 6.69258 11.0676C6.60217 10.9771 6.55696 10.8731 6.55696 10.7558C6.55696 10.6384 6.60217 10.5344 6.69258 10.4439L9.69908 7.4375Z'
          fill='#E8EAED'
        />
      </svg>
    </button>
  );
};

const ChatInputField = ({ placeholder, className }: ChatInputField) => {
  const { send, input, setInput, pending } = useChatForm();
  const { info } = useUserInfoStore();

  return (
    <div
      className={twMerge(
        'main-content px-auto mt-[24px] desktop:order-2 ',
        className
      )}
    >
      {info === null && <InputFieldBlocker />}
      {info !== null && (
        <div className='w-full h-[46px] rounded-full border-[1px] border-[#005AA9] flex items-center justify-between pl-[18px] pr-[7px] gap-[12px] bg-white shadow-[0px_0px_4px_0px_rgba(0,0,0,0.20)]'>
          <input
            className='outline-none text-base font-[400] text-primary placeholder:text-secondary flex-1'
            type='text'
            value={input}
            placeholder={placeholder ?? '무엇을 도와드릴까요?'}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                send();
              }
            }}
          />
          <button disabled={pending} onClick={() => send()}>
            <img
              className={twMerge(
                'w-[32px] aspect-square transition-opacity',
                pending && 'opacity-60'
              )}
              src={sendButton}
            />
          </button>
        </div>
      )}
    </div>
  );
};

export default ChatInputField;
