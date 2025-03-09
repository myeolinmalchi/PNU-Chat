import { ReactNode } from 'react';

type ChatContainerProps = {
  children: ReactNode;
};

const ChatContainer = ({ children }: ChatContainerProps) => {
  return (
    <div className='chat-container w-full pt-6 flex-1 overflow-y-auto flex flex-col-reverse'>
      <div className='main-content mb-16 mx-auto flex flex-col gap-6 justify-end'>
        {children}
      </div>
    </div>
  );
};

export default ChatContainer;
