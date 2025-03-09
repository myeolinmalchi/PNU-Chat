import useChatForm from 'hooks/useChatForm';
import { ReactNode } from 'react';

type ChatExampleType = {
  preview: string;
  question: string;
};

const ChatExample = ({ preview, question }: ChatExampleType) => {
  const { send } = useChatForm();

  return (
    <button
      onClick={() => send(question)}
      className='py-2.5 px-4 flex justify-center leading-tight items-center rounded-full bg-main-bg text-main-font text-sm font-[500] align-middle'
    >
      {preview}
    </button>
  );
};

ChatExample.Container = ({ children }: { children: ReactNode }) => {
  return (
    <div className='flex flex-wrap items-center justify-center gap-2 main-content-slim mb-8'>
      {children}
    </div>
  );
};

export default ChatExample;
